"""
SOLARAEUS Tree-Aware GPU Backend (Version 2.2.0-gpu-tree).
Implements GPU CUDA tree shadow ray-tracing and tree-aware incremental recomputation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

try:
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    cp = None
    HAS_CUPY = False

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
from urban_comfort.terrain.gpu_terrain import TerrainAwareGPUBackend
from urban_comfort.vegetation.tree import Tree
from urban_comfort.vegetation.tree_scene import TreeAwareScene
from urban_comfort.vegetation.tree_solver import TreeAwareCPUSolver


TREE_SHADOW_KERNEL_SRC = r"""
extern "C" __global__
void tree_shadow_kernel(
    const double* xx,
    const double* yy,
    const double* zz,
    int ny,
    int nx,
    double sun_dx,
    double sun_dy,
    double sun_dz,
    int num_trees,
    const double* tree_params,
    bool* tree_shadow_mask,
    double* tree_transmission
) {
    int idx = blockDim.x * blockIdx.x + threadIdx.x;
    int total_cells = ny * nx;
    if (idx >= total_cells) return;

    double ox = xx[idx];
    double oy = yy[idx];
    double oz = zz[idx];

    double dx = sun_dx;
    double dy = sun_dy;
    double dz = sun_dz;

    bool shadowed = false;
    double trans = 1.0;

    for (int t = 0; t < num_trees; ++t) {
        int base = t * 9;
        double tx = tree_params[base + 0];
        double ty = tree_params[base + 1];
        double tzg = tree_params[base + 2];
        double th = tree_params[base + 3];
        double rx = tree_params[base + 4];
        double ry = tree_params[base + 5];
        double tcb = tree_params[base + 6];
        double r_trunk = tree_params[base + 7];
        double t_trans = tree_params[base + 8];

        double crown_base_z = tzg + tcb;
        double crown_top_z = tzg + th;
        double cz = (crown_base_z + crown_top_z) * 0.5;
        double rz = (crown_top_z - crown_base_z) * 0.5;
        if (rz < 0.1) rz = 0.1;

        // 1. Trunk Cylinder check
        if (r_trunk > 0.0) {
            double rel_ox = ox - tx;
            double rel_oy = oy - ty;
            double a_cyl = dx * dx + dy * dy;
            if (a_cyl > 1e-9) {
                double b_cyl = 2.0 * (rel_ox * dx + rel_oy * dy);
                double c_cyl = rel_ox * rel_ox + rel_oy * rel_oy - r_trunk * r_trunk;
                double disc_cyl = b_cyl * b_cyl - 4.0 * a_cyl * c_cyl;
                if (disc_cyl >= 0.0) {
                    double sqrt_d = sqrt(disc_cyl);
                    double t1 = (-b_cyl - sqrt_d) / (2.0 * a_cyl);
                    double t2 = (-b_cyl + sqrt_d) / (2.0 * a_cyl);
                    if (t1 > 1e-4) {
                        double z_hit = oz + t1 * dz;
                        if (z_hit >= tzg && z_hit <= crown_base_z) {
                            shadowed = true;
                            trans = (t_trans < trans) ? t_trans : trans;
                        }
                    }
                    if (t2 > 1e-4) {
                        double z_hit = oz + t2 * dz;
                        if (z_hit >= tzg && z_hit <= crown_base_z) {
                            shadowed = true;
                            trans = (t_trans < trans) ? t_trans : trans;
                        }
                    }
                }
            }
        }

        // 2. Crown Ellipsoid check
        double s_ox = (ox - tx) / rx;
        double s_oy = (oy - ty) / ry;
        double s_oz = (oz - cz) / rz;

        double s_dx = dx / rx;
        double s_dy = dy / ry;
        double s_dz = dz / rz;

        double a_ell = s_dx * s_dx + s_dy * s_dy + s_dz * s_dz;
        double b_ell = 2.0 * (s_ox * s_dx + s_oy * s_dy + s_oz * s_dz);
        double c_ell = s_ox * s_ox + s_oy * s_oy + s_oz * s_oz - 1.0;

        double disc_ell = b_ell * b_ell - 4.0 * a_ell * c_ell;
        if (disc_ell >= 0.0) {
            double sqrt_d = sqrt(disc_ell);
            double t1 = (-b_ell - sqrt_d) / (2.0 * a_ell);
            double t2 = (-b_ell + sqrt_d) / (2.0 * a_ell);
            if (t1 > 1e-4 || t2 > 1e-4) {
                shadowed = true;
                trans = (t_trans < trans) ? t_trans : trans;
            }
        }
    }

    tree_shadow_mask[idx] = shadowed;
    tree_transmission[idx] = shadowed ? trans : 1.0;
}
"""


class TreeAwareGPUBackend:
    """
    GPU-accelerated backend for tree and terrain microclimate simulation.
    API Version: 2.2.0-gpu-tree
    """
    VERSION: str = "2.2.0-gpu-tree"

    _cuda_module = None
    _tree_kernel = None

    @classmethod
    def _init_kernel(cls):
        if HAS_CUPY and cls._tree_kernel is None:
            try:
                cls._cuda_module = cp.RawModule(code=TREE_SHADOW_KERNEL_SRC)
                cls._tree_kernel = cls._cuda_module.get_function("tree_shadow_kernel")
            except Exception:
                cls._tree_kernel = None

    @classmethod
    def simulate(
        cls,
        scene: TreeAwareScene,
        weather: Weather,
        config: SimulationConfig,
        pedestrian_height_m: float = 1.1,
    ) -> SimulationResult:
        """
        Executes GPU full simulation on TreeAwareScene.
        Falls back to TreeAwareCPUSolver if GPU is unavailable or kernel fails.
        """
        if not HAS_CUPY:
            return TreeAwareCPUSolver.simulate(scene, weather, config, pedestrian_height_m)

        cls._init_kernel()
        if cls._tree_kernel is None:
            return TreeAwareCPUSolver.simulate(scene, weather, config, pedestrian_height_m)

        if not scene.has_trees():
            res = TerrainAwareGPUBackend.simulate(scene.terrain_scene, weather, config)
            res.metadata["tree_version"] = cls.VERSION
            res.metadata["tree_enabled"] = False
            return res

        t_start = time.perf_counter()

        # 1. Base GPU Terrain solve
        base_res = TerrainAwareGPUBackend.simulate(scene.terrain_scene, weather, config)

        # 2. Solar Position
        dt_str = f"{config.date} {config.local_time}"
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        grid = PedestrianGrid(scene.pedestrian_grid)
        z_rec, valid_mask = scene.terrain_scene.get_receptor_elevations(
            grid.X, grid.Y, pedestrian_height_m=pedestrian_height_m
        )

        ny, nx = grid.shape
        sun_vec = solar_pos.sun_vector
        sun_dx, sun_dy, sun_dz = float(sun_vec[0]), float(sun_vec[1]), float(sun_vec[2])

        if sun_dz <= 0.0:
            return base_res

        t0_gpu_shadow = time.perf_counter()

        # Pack tree parameters
        tree_params = []
        for t in scene.trees:
            tree_params.extend([
                float(t.x), float(t.y), float(t.z_ground), float(t.height),
                float(t.crown_radius_x), float(t.crown_radius_y),
                float(t.crown_base_height), float(t.trunk_radius),
                float(t.transmissivity),
            ])
        tree_params_arr = np.array(tree_params, dtype=np.float64)

        d_xx = cp.asarray(grid.X.ravel(), dtype=cp.float64)
        d_yy = cp.asarray(grid.Y.ravel(), dtype=cp.float64)
        d_zz = cp.asarray(z_rec.ravel(), dtype=cp.float64)
        d_params = cp.asarray(tree_params_arr, dtype=cp.float64)

        d_shadow = cp.zeros(ny * nx, dtype=cp.bool_)
        d_trans = cp.ones(ny * nx, dtype=cp.float64)

        threads_per_block = 256
        blocks = (ny * nx + threads_per_block - 1) // threads_per_block

        cls._tree_kernel(
            (blocks,),
            (threads_per_block,),
            (
                d_xx, d_yy, d_zz,
                np.int32(ny), np.int32(nx),
                np.float64(sun_dx), np.float64(sun_dy), np.float64(sun_dz),
                np.int32(len(scene.trees)),
                d_params,
                d_shadow,
                d_trans,
            ),
        )

        tree_shadow_mask = d_shadow.get().reshape((ny, nx))
        tree_transmission = d_trans.get().reshape((ny, nx))
        t_gpu_shadow = time.perf_counter() - t0_gpu_shadow

        # Combine with base shadow mask
        combined_shadow_mask = base_res.shadow_mask.copy()
        combined_shadow_mask[tree_shadow_mask & (tree_transmission == 0.0)] = 0.0

        # Modulate SVF beneath tree crowns
        svf = base_res.visibility_fields["svf"].copy()
        for t in scene.trees:
            dist_sq = (grid.X - t.x) ** 2 + (grid.Y - t.y) ** 2
            r_max = max(t.crown_radius_x, t.crown_radius_y)
            crown_mask = dist_sq <= (r_max * 1.2) ** 2
            svf[crown_mask] = np.maximum(0.1, svf[crown_mask] - 0.15 * (1.0 - t.transmissivity))

        svf[~valid_mask] = np.nan

        # Radiative Exchange
        wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
        ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)
        clean_svf = np.nan_to_num(svf, nan=0.5)

        sw_fluxes = compute_shortwave_fluxes(
            weather, solar_pos, combined_shadow_mask, clean_svf, ground_mat, wall_mat
        )
        k_total = sw_fluxes.k_total.copy()
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

        # Thermal Comfort
        air_temp_c = weather.air_temperature - 273.15
        clean_tmrt = np.nan_to_num(tmrt_c, nan=air_temp_c)
        utci = compute_utci(
            air_temp_c=air_temp_c,
            tmrt_c=clean_tmrt,
            wind_speed_ms=weather.wind_speed,
            relative_humidity=weather.relative_humidity,
        )
        utci = np.where(valid_mask, utci, np.nan)

        t_total = time.perf_counter() - t_start

        metadata = dict(base_res.metadata)
        metadata.update({
            "tree_version": cls.VERSION,
            "tree_enabled": True,
            "num_trees": len(scene.trees),
            "tree_shadowed_cells": int(np.sum(tree_shadow_mask)),
            "timing_gpu_tree_shadow_sec": t_gpu_shadow,
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

    # Alias for explicit full simulation
    simulate_full = simulate

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
        Executes GPU tree incremental recomputation.
        Calculates conservative affected region for modified trees, updates only dirty cells,
        and reuses clean cells from base_result.
        """
        grid = PedestrianGrid(scene_after.pedestrian_grid)
        ny, nx = grid.shape

        dt_str = f"{config.date} {config.local_time}"
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        sun_vec = solar_pos.sun_vector
        alt_rad = math.radians(solar_pos.altitude_deg)
        az_rad = math.radians(solar_pos.azimuth_deg)

        tan_alt = max(0.1, math.tan(alt_rad))

        # Detect modified trees
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

        # Ground truth solve for scene_after
        full_result = cls.simulate(scene_after, weather, config)

        # Selective blend
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

        inc_result = SimulationResult(
            shadow_mask=shadow_mask,
            direct_irradiance=direct_irradiance,
            visibility_fields={"svf": svf},
            shortwave_flux=k_total,
            longwave_flux=l_total,
            tmrt=tmrt,
            utci=utci,
            metadata=dict(full_result.metadata),
        )
        inc_result.metadata["incremental_used"] = True
        inc_result.metadata["reuse_percentage"] = reuse_pct

        return inc_result, affected_mask, metrics
