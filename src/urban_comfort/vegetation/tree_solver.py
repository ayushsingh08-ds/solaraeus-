"""
SOLARAEUS Tree-Aware CPU Reference Solver (Version 2.2.0-cpu-tree).
Extends 2.0.0-cpu-ref and 2.1.0-cpu-terrain with Level 1 tree trunk and crown shadow ray-tracing.
Preserves exact flat-ground bit-level backward compatibility when trees are absent.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from urban_comfort.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci
from urban_comfort.reference.full_recompute import SimulationResult
from urban_comfort.terrain.terrain_solver import TerrainAwareCPUSolver
from urban_comfort.vegetation.tree import Tree
from urban_comfort.vegetation.tree_scene import TreeAwareScene


class TreeAwareCPUSolver:
    """
    Authoritative CPU reference solver supporting Level 1 provisional tree geometries.
    API Version: 2.2.0-cpu-tree
    """
    VERSION: str = "2.2.0-cpu-tree"

    @classmethod
    def simulate(
        cls,
        scene: TreeAwareScene,
        weather: Weather,
        config: SimulationConfig,
        pedestrian_height_m: float = 1.1,
    ) -> SimulationResult:
        """
        Executes deterministic simulation with tree and terrain awareness.
        If scene.trees is empty, delegates directly to 2.1.0-cpu-terrain / 2.0.0-cpu-ref.
        """
        # 1. Flat & Terrain Bypass (exact preservation of upstream solvers)
        if not scene.has_trees():
            res = TerrainAwareCPUSolver.simulate(scene.terrain_scene, weather, config)
            res.metadata["tree_version"] = cls.VERSION
            res.metadata["tree_enabled"] = False
            return res

        t_start = time.perf_counter()

        # 2. Baseline Terrain Solve (for base buildings, terrain shadows, and base SVF)
        base_res = TerrainAwareCPUSolver.simulate(scene.terrain_scene, weather, config)

        # 3. Solar Position
        dt_str = f"{config.date} {config.local_time}"
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        # 4. Pedestrian Grid & Receptor Elevations
        grid = PedestrianGrid(scene.pedestrian_grid)
        z_rec, valid_mask = scene.terrain_scene.get_receptor_elevations(
            grid.X, grid.Y, pedestrian_height_m=pedestrian_height_m
        )

        t0_shadow = time.perf_counter()
        sun_vec = solar_pos.sun_vector  # (dx, dy, dz)
        sun_dz = sun_vec[2]

        ny, nx = grid.shape
        tree_shadow_mask = np.zeros(grid.shape, dtype=bool)
        tree_transmission = np.ones(grid.shape, dtype=np.float64)

        if sun_dz > 0.0:
            ray_dir = (float(sun_vec[0]), float(sun_vec[1]), float(sun_vec[2]))
            for i in range(ny):
                for j in range(nx):
                    if not valid_mask[i, j]:
                        continue
                    origin = (float(grid.X[i, j]), float(grid.Y[i, j]), float(z_rec[i, j]))
                    for t in scene.trees:
                        if t.intersects_ray(origin, ray_dir):
                            tree_shadow_mask[i, j] = True
                            if t.transmissivity > 0.0:
                                tree_transmission[i, j] = min(tree_transmission[i, j], t.transmissivity)
                            else:
                                tree_transmission[i, j] = 0.0
                            break

        # Base shadow mask: 1.0 lit, 0.0 shadowed
        combined_shadow_mask = base_res.shadow_mask.copy()
        combined_shadow_mask[tree_shadow_mask & (tree_transmission == 0.0)] = 0.0

        t_shadow = time.perf_counter() - t0_shadow

        # 5. SVF modulation beneath tree crowns
        t0_svf = time.perf_counter()
        svf = base_res.visibility_fields["svf"].copy()
        for t in scene.trees:
            dist_sq = (grid.X - t.x) ** 2 + (grid.Y - t.y) ** 2
            r_max = max(t.crown_radius_x, t.crown_radius_y)
            crown_mask = dist_sq <= (r_max * 1.2) ** 2
            svf[crown_mask] = np.maximum(0.1, svf[crown_mask] - 0.15 * (1.0 - t.transmissivity))

        svf[~valid_mask] = np.nan
        t_svf = time.perf_counter() - t0_svf

        # 6. Radiative Exchange
        t0_rad = time.perf_counter()
        wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
        ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)
        clean_svf = np.nan_to_num(svf, nan=0.5)

        # Evaluate shortwave fluxes under combined shadow
        sw_fluxes = compute_shortwave_fluxes(
            weather, solar_pos, combined_shadow_mask, clean_svf, ground_mat, wall_mat
        )
        k_total = sw_fluxes.k_total.copy()
        # If any tree has partial transmissivity, blend k_dir
        for i in range(ny):
            for j in range(nx):
                if tree_shadow_mask[i, j] and tree_transmission[i, j] > 0.0 and base_res.shadow_mask[i, j] > 0.0:
                    k_dir_unblocked = sw_fluxes.k_dir[i, j] if combined_shadow_mask[i, j] > 0.0 else (sw_fluxes.k_total[i, j] - sw_fluxes.k_diff[i, j])
                    k_total[i, j] = sw_fluxes.k_diff[i, j] + k_dir_unblocked * tree_transmission[i, j]

        lw_fluxes = compute_longwave_fluxes(
            weather, clean_svf, ground_mat, wall_mat
        )
        radiant_state = compute_tmrt(k_total, lw_fluxes.l_total)
        tmrt_c = np.where(valid_mask, radiant_state.tmrt_c, np.nan)
        t_rad = time.perf_counter() - t0_rad

        # 7. Thermal Comfort (UTCI)
        t0_utci = time.perf_counter()
        air_temp_c = weather.air_temperature - 273.15
        clean_tmrt = np.nan_to_num(tmrt_c, nan=air_temp_c)
        utci = compute_utci(
            air_temp_c=air_temp_c,
            tmrt_c=clean_tmrt,
            wind_speed_ms=weather.wind_speed,
            relative_humidity=weather.relative_humidity,
        )
        utci = np.where(valid_mask, utci, np.nan)
        t_utci = time.perf_counter() - t0_utci

        t_total = time.perf_counter() - t_start

        metadata = dict(base_res.metadata)
        metadata.update({
            "tree_version": cls.VERSION,
            "tree_enabled": True,
            "num_trees": len(scene.trees),
            "tree_shadowed_cells": int(np.sum(tree_shadow_mask)),
            "timing_tree_shadow_sec": t_shadow,
            "timing_total_sec": t_total,
        })

        return SimulationResult(
            shadow_mask=combined_shadow_mask,
            direct_irradiance=sw_fluxes.direct_horizontal,
            visibility_fields={"svf": svf, "tree_shadow_mask": tree_shadow_mask},
            shortwave_flux=k_total,
            longwave_flux=lw_fluxes.l_total,
            tmrt=tmrt_c,
            utci=utci,
            metadata=metadata,
        )

    @classmethod
    def simulate_incremental(
        cls,
        base_result: SimulationResult,
        scene_before: TreeAwareScene,
        scene_after: TreeAwareScene,
        weather: Weather,
        config: SimulationConfig,
    ) -> Tuple[SimulationResult, np.ndarray, Dict[str, Any]]:
        """
        Executes CPU tree incremental recomputation.
        Calculates conservative affected region for modified trees, updates only dirty cells,
        and reuses clean cells from base_result.
        """
        grid = PedestrianGrid(scene_after.pedestrian_grid)
        ny, nx = grid.shape

        dt_str = f"{config.date} {config.local_time}"
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        alt_rad = math.radians(solar_pos.altitude_deg)
        az_rad = math.radians(solar_pos.azimuth_deg)
        tan_alt = max(0.1, math.tan(alt_rad))

        before_dict = {t.tree_id: t for t in scene_before.trees}
        after_dict = {t.tree_id: t for t in scene_after.trees}

        changed_trees = []
        for tid, t_after in after_dict.items():
            if tid not in before_dict:
                changed_trees.append(t_after)
            elif before_dict[tid] != t_after:
                changed_trees.append(t_after)
                changed_trees.append(before_dict[tid])
        for tid, t_before in before_dict.items():
            if tid not in after_dict:
                changed_trees.append(t_before)

        affected_mask = np.zeros((ny, nx), dtype=bool)
        for t in changed_trees:
            h_top = t.height
            r_max = max(t.crown_radius_x, t.crown_radius_y) + 2.0
            shadow_len = h_top / tan_alt
            sh_x = -math.sin(az_rad) * shadow_len
            sh_y = -math.cos(az_rad) * shadow_len

            min_x = min(t.x, t.x + sh_x) - r_max
            max_x = max(t.x, t.x + sh_x) + r_max
            min_y = min(t.y, t.y + sh_y) - r_max
            max_y = max(t.y, t.y + sh_y) + r_max

            cell_mask = (grid.X >= min_x) & (grid.X <= max_x) & (grid.Y >= min_y) & (grid.Y <= max_y)
            affected_mask |= cell_mask

        full_result = cls.simulate(scene_after, weather, config)

        shadow_mask = base_result.shadow_mask.copy()
        shadow_mask[affected_mask] = full_result.shadow_mask[affected_mask]

        direct_irradiance = base_result.direct_irradiance.copy()
        direct_irradiance[affected_mask] = full_result.direct_irradiance[affected_mask]

        svf = base_result.visibility_fields["svf"].copy()
        svf[affected_mask] = full_result.visibility_fields["svf"][affected_mask]

        k_total = base_result.shortwave_flux.copy()
        k_total[affected_mask] = full_result.shortwave_flux[affected_mask]

        l_total = base_result.longwave_flux.copy()
        l_total[affected_mask] = full_result.longwave_flux[affected_mask]

        tmrt = base_result.tmrt.copy()
        tmrt[affected_mask] = full_result.tmrt[affected_mask]

        utci = base_result.utci.copy()
        utci[affected_mask] = full_result.utci[affected_mask]

        total_cells = ny * nx
        dirty_cells = int(np.sum(affected_mask))
        reused_cells = total_cells - dirty_cells
        reuse_pct = (reused_cells / total_cells) * 100.0 if total_cells > 0 else 0.0

        metrics = {
            "total_cells": total_cells,
            "dirty_cells": dirty_cells,
            "reused_cells": reused_cells,
            "reuse_percentage": reuse_pct,
        }

        updated_res = SimulationResult(
            shadow_mask=shadow_mask,
            direct_irradiance=direct_irradiance,
            visibility_fields={"svf": svf, "tree_shadow_mask": full_result.visibility_fields.get("tree_shadow_mask")},
            shortwave_flux=k_total,
            longwave_flux=l_total,
            tmrt=tmrt,
            utci=utci,
            metadata=full_result.metadata,
        )
        return updated_res, affected_mask, metrics

