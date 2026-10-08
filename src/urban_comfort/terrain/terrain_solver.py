"""
Terrain-aware CPU reference solver (SOLARAEUS Version 2.1.0-cpu-terrain).
Computes full microclimatic fields incorporating digital terrain models
while maintaining exact bit-level parity with 2.0.0-cpu-ref when terrain is disabled.
"""

from __future__ import annotations
from datetime import datetime, timezone
import time
from typing import Optional, Dict, Any, Tuple
import numpy as np

from urban_comfort.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci
from urban_comfort.reference.full_recompute import SimulationResult, full_recompute
from urban_comfort.terrain.terrain_scene import TerrainAwareScene


class TerrainAwareCPUSolver:
    """
    Authoritative CPU reference solver supporting optional terrain models.
    API Version: 2.1.0-cpu-terrain
    """
    VERSION: str = "2.1.0-cpu-terrain"

    @classmethod
    def simulate(cls, scene: TerrainAwareScene, weather: Weather,
                 config: SimulationConfig) -> SimulationResult:
        """
        Executes a deterministic simulation with terrain awareness.
        If scene.terrain is None, delegates directly to 2.0.0-cpu-ref for 100% parity.
        """
        # 1. Flat-Ground Bypass (Exact bit-level preservation of 2.0.0-cpu-ref)
        if not scene.has_terrain():
            res = full_recompute(scene.base_scene, weather, config, backend="cpu")
            res.metadata["terrain_version"] = cls.VERSION
            res.metadata["terrain_enabled"] = False
            return res

        t_start = time.perf_counter()

        # 2. Solar Position
        dt_str = f"{config.date} {config.local_time}"
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        # 3. Pedestrian Grid & Terrain Sampling
        grid = PedestrianGrid(scene.pedestrian_grid)
        z_rec, valid_mask = scene.get_receptor_elevations(grid.X, grid.Y, pedestrian_height_m=1.1)

        # 4. Direct Shadows with Terrain Elevation Offset
        # Ray origin is at (X, Y, z_rec)
        # First compute building shadows using relative building heights (building.z - local_terrain)
        # Or standard box intersection with ray origins at actual 3D receptor heights
        t0_shadow = time.perf_counter()
        
        # We ray trace against active buildings
        shadow_mask = np.zeros(grid.shape, dtype=np.float64)
        sun_vec = solar_pos.sun_vector
        s_norm = np.linalg.norm(sun_vec)
        if s_norm > 1e-9:
            ray_dir = sun_vec / s_norm
        else:
            ray_dir = np.array([0.0, 0.0, 1.0])

        buildings = scene.get_active_buildings()

        # If sun is below horizon, entire domain is in shadow
        if not solar_pos.is_daylight or ray_dir[2] <= 0:
            shadow_mask.fill(0.0)
        else:
            # Domain cells illuminated unless occluded by building or terrain
            shadow_mask.fill(1.0)
            
            # Kay-Kajiya slab test against building 3D bounding boxes
            inv_dir = np.where(np.abs(ray_dir) > 1e-9, 1.0 / ray_dir, np.inf)
            
            # Vectorized test per building
            for b in buildings:
                # b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax
                tx1 = (b.xmin - grid.X) * inv_dir[0]
                tx2 = (b.xmax - grid.X) * inv_dir[0]
                tmin_x = np.minimum(tx1, tx2)
                tmax_x = np.maximum(tx1, tx2)

                ty1 = (b.ymin - grid.Y) * inv_dir[1]
                ty2 = (b.ymax - grid.Y) * inv_dir[1]
                tmin_y = np.minimum(ty1, ty2)
                tmax_y = np.maximum(ty1, ty2)

                tz1 = (b.zmin - z_rec) * inv_dir[2]
                tz2 = (b.zmax - z_rec) * inv_dir[2]
                tmin_z = np.minimum(tz1, tz2)
                tmax_z = np.maximum(tz1, tz2)

                t_enter = np.maximum(np.maximum(tmin_x, tmin_y), tmin_z)
                t_exit = np.minimum(np.minimum(tmax_x, tmax_y), tmax_z)

                hit = (t_enter <= t_exit) & (t_exit > 1e-4)
                shadow_mask[hit] = 0.0

            # Terrain self-shadowing: check along ray for terrain intersection
            # Sample ray at steps towards sun
            if scene.terrain is not None:
                step_dist = 2.0
                max_dist = min(60.0, float(scene.terrain.bounds.xmax - scene.terrain.bounds.xmin))
                num_steps = int(max_dist / step_dist)
                for s in range(1, num_steps + 1):
                    dist = s * step_dist
                    rx = grid.X + ray_dir[0] * dist
                    ry = grid.Y + ray_dir[1] * dist
                    rz = z_rec + ray_dir[2] * dist
                    
                    z_terrain_sample, v_sample = scene.terrain.sample_elevation(rx, ry)
                    terrain_hit = v_sample & (z_terrain_sample > rz)
                    shadow_mask[terrain_hit] = 0.0

        # Cells outside terrain validity or NoData are masked to 0
        shadow_mask[~valid_mask] = 0.0
        t_shadow = time.perf_counter() - t0_shadow

        # 5. Sky View Factor
        t0_svf = time.perf_counter()
        # For SVF, compute baseline building SVF then modulate by terrain slope horizon
        svf = compute_sky_view_factor(
            scene.base_scene, grid,
            num_azimuths=config.sky_patch_configuration,
            max_search_dist_m=config.max_svf_search_dist_m
        )
        # If terrain has slope, SVF is bounded by (1 + cos(slope))/2
        if scene.terrain is not None:
            nx, ny, nz = scene.terrain.compute_surface_normals()
            # Sample normal onto grid
            gx = np.clip((grid.X - scene.terrain.bounds.xmin) / max(1e-9, scene.terrain.dx), 0, scene.terrain.nx - 1).astype(int)
            gy = np.clip((grid.Y - scene.terrain.bounds.ymin) / max(1e-9, scene.terrain.dy), 0, scene.terrain.ny - 1).astype(int)
            local_nz = nz[gy, gx]
            slope_svf_limit = 0.5 * (1.0 + np.clip(local_nz, 0.0, 1.0))
            svf = np.minimum(svf, slope_svf_limit)

        svf[~valid_mask] = np.nan
        t_svf = time.perf_counter() - t0_svf

        # 6. Radiative Exchange (Shortwave + Longwave)
        t0_rad = time.perf_counter()
        wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
        ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)

        # Substitute valid values for radiation evaluation
        clean_svf = np.nan_to_num(svf, nan=0.5)
        sw_fluxes = compute_shortwave_fluxes(
            weather, solar_pos, shadow_mask, clean_svf, ground_mat, wall_mat
        )
        lw_fluxes = compute_longwave_fluxes(
            weather, clean_svf, ground_mat, wall_mat
        )
        radiant_state = compute_tmrt(sw_fluxes.k_total, lw_fluxes.l_total)
        
        # Mask invalid cells to NaN
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
            relative_humidity=weather.relative_humidity
        )
        utci = np.where(valid_mask, utci, np.nan)
        t_utci = time.perf_counter() - t0_utci

        t_total = time.perf_counter() - t_start

        metadata = {
            "terrain_version": cls.VERSION,
            "terrain_enabled": True,
            "terrain_crs": scene.terrain.crs if scene.terrain else "None",
            "solar_altitude_deg": solar_pos.altitude_deg,
            "solar_azimuth_deg": solar_pos.azimuth_deg,
            "sun_vector": solar_pos.sun_vector,
            "is_daylight": solar_pos.is_daylight,
            "timing_shadow_sec": t_shadow,
            "timing_svf_sec": t_svf,
            "timing_radiation_sec": t_rad,
            "timing_utci_sec": t_utci,
            "timing_total_sec": t_total,
            "num_buildings": len(buildings),
            "total_cells": grid.total_cells,
            "valid_cells": int(np.sum(valid_mask)),
            "invalid_cells": int(np.sum(~valid_mask)),
            "air_temperature_c": air_temp_c
        }

        return SimulationResult(
            shadow_mask=shadow_mask,
            direct_irradiance=sw_fluxes.direct_horizontal,
            visibility_fields={"svf": svf},
            shortwave_flux=sw_fluxes.k_total,
            longwave_flux=lw_fluxes.l_total,
            tmrt=tmrt_c,
            utci=utci,
            metadata=metadata
        )
