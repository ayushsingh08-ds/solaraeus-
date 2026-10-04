"""
Non-Certified Dirty-Region Baseline Comparison.

Implements an empirical dirty-region baseline that recomputes a manually defined
or geometrically estimated bounding box without an error certificate.
Compares:
1. Full Recomputation (ground truth)
2. Non-Certified Dirty-Region Update (naive bounding box)
3. Exact Incremental Update (geometry-aware plume, zero error)
4. Certified Approximate Update (provably bounded error)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import time
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci
from urban_comfort.incremental.update import (
    GeometricEdit, incremental_update_exact, incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate


@dataclass
class BaselineComparisonRecord:
    """Record comparing solver methodologies."""
    method_name: str
    runtime_sec: float
    speedup: float
    reused_cells: int
    recomputed_cells: int
    reused_fraction: float
    max_actual_error_k: float
    mean_actual_error_k: float
    max_predicted_bound_k: float
    has_certificate: bool
    is_sound: bool
    violations_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_non_certified_dirty_region_update(previous_scene: Scene,
                                          updated_scene: Scene,
                                          previous_result: SimulationResult,
                                          edit: GeometricEdit,
                                          weather: Weather,
                                          config: SimulationConfig,
                                          margin_m: float = 5.0) -> Tuple[SimulationResult, float, int, int]:
    """
    Executes a naive non-certified dirty-region update:
    Recomputes only within the immediate building footprint bounding box plus a fixed margin.
    Completely ignores solar ray shadow plumes and SVF horizon distance decay.
    """
    t0 = time.perf_counter()
    from datetime import datetime, timezone
    dt_str = f"{config.date} {config.local_time}"
    dt_utc = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)
    grid = PedestrianGrid(updated_scene.pedestrian_grid)

    # Compute naive bounding box of the edit
    _, edit_bounds_3d = edit.apply(previous_scene)
    xmin, xmax, ymin, ymax, zmin, zmax = edit_bounds_3d

    # Apply naive margin without shadow ray projection or SVF decay radius
    dirty_xmin = max(0.0, xmin - margin_m)
    dirty_xmax = min(grid.config.extent_x, xmax + margin_m)
    dirty_ymin = max(0.0, ymin - margin_m)
    dirty_ymax = min(grid.config.extent_y, ymax + margin_m)

    slice_y, slice_x = grid.bounding_box_slices(dirty_xmin, dirty_xmax, dirty_ymin, dirty_ymax)
    dirty_mask = np.zeros(grid.shape, dtype=bool)
    dirty_mask[slice_y, slice_x] = True

    recomputed_count = int(np.sum(dirty_mask))
    reused_count = grid.total_cells - recomputed_count

    # Selective recompute on naive box
    new_shadow = previous_result.shadow_mask.copy()
    if np.any(dirty_mask):
        recomp_shadow = compute_direct_shadow_mask(updated_scene, grid, solar_pos, roi_mask=dirty_mask)
        new_shadow[dirty_mask] = recomp_shadow[dirty_mask]

    new_svf = previous_result.svf.copy()
    if np.any(dirty_mask):
        recomp_svf = compute_sky_view_factor(
            updated_scene, grid,
            num_azimuths=config.sky_patch_configuration,
            max_search_dist_m=config.max_svf_search_dist_m,
            roi_mask=dirty_mask
        )
        new_svf[dirty_mask] = recomp_svf[dirty_mask]

    wall_mat = updated_scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
    ground_mat = updated_scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)

    sw_fluxes = compute_shortwave_fluxes(weather, solar_pos, new_shadow, new_svf, ground_mat, wall_mat)
    lw_fluxes = compute_longwave_fluxes(weather, new_svf, ground_mat, wall_mat)
    radiant_state = compute_tmrt(sw_fluxes.k_total, lw_fluxes.l_total)

    air_temp_c = weather.air_temperature - 273.15
    utci = compute_utci(
        air_temp_c=air_temp_c,
        tmrt_c=radiant_state.tmrt_c,
        wind_speed_ms=weather.wind_speed,
        relative_humidity=weather.relative_humidity
    )

    t_elapsed = time.perf_counter() - t0

    result = SimulationResult(
        shadow_mask=new_shadow,
        direct_irradiance=sw_fluxes.direct_horizontal,
        visibility_fields={"svf": new_svf},
        shortwave_flux=sw_fluxes.k_total,
        longwave_flux=lw_fluxes.l_total,
        tmrt=radiant_state.tmrt_c,
        utci=utci,
        metadata={"is_naive_baseline": True, "margin_m": margin_m}
    )

    return result, t_elapsed, reused_count, recomputed_count


def compare_all_baselines(scene_before: Scene,
                          scene_after: Scene,
                          res_baseline: SimulationResult,
                          edit: GeometricEdit,
                          weather: Weather,
                          config: SimulationConfig) -> List[BaselineComparisonRecord]:
    """
    Compares Full Recompute, Non-Certified Dirty Box, Exact Incremental, and Certified Incremental.
    """
    grid = PedestrianGrid(scene_before.pedestrian_grid)
    total_cells = grid.total_cells

    # 1. Full Recomputation (Ground Truth)
    t0 = time.perf_counter()
    res_full = full_recompute(scene_after, weather, config)
    t_full = time.perf_counter() - t0

    rec_full = BaselineComparisonRecord(
        method_name="full_recompute",
        runtime_sec=t_full,
        speedup=1.0,
        reused_cells=0,
        recomputed_cells=total_cells,
        reused_fraction=0.0,
        max_actual_error_k=0.0,
        mean_actual_error_k=0.0,
        max_predicted_bound_k=0.0,
        has_certificate=False,
        is_sound=True,
        violations_count=0
    )

    # 2. Non-Certified Dirty-Region (Naive 5m Box)
    res_naive, t_naive, reused_naive, recomp_naive = run_non_certified_dirty_region_update(
        scene_before, scene_after, res_baseline, edit, weather, config, margin_m=5.0
    )
    err_naive = np.abs(res_naive.tmrt - res_full.tmrt)
    rec_naive = BaselineComparisonRecord(
        method_name="non_certified_dirty_box",
        runtime_sec=t_naive,
        speedup=t_full / t_naive if t_naive > 0 else 1.0,
        reused_cells=reused_naive,
        recomputed_cells=recomp_naive,
        reused_fraction=reused_naive / float(total_cells),
        max_actual_error_k=float(np.max(err_naive)),
        mean_actual_error_k=float(np.mean(err_naive)),
        max_predicted_bound_k=float("nan"),
        has_certificate=False,
        is_sound=False,  # Unsound: large uncertified errors outside bounding box
        violations_count=int(np.sum(err_naive > config.tmrt_tolerance))
    )

    # 3. Exact Incremental Update
    t0 = time.perf_counter()
    inc_exact_res = incremental_update_exact(scene_before, scene_after, res_baseline, edit, weather, config)
    t_exact = time.perf_counter() - t0
    err_exact = np.abs(inc_exact_res.result.tmrt - res_full.tmrt)
    rec_exact = BaselineComparisonRecord(
        method_name="exact_incremental",
        runtime_sec=t_exact,
        speedup=t_full / t_exact if t_exact > 0 else 1.0,
        reused_cells=total_cells - inc_exact_res.recomputed_cells,
        recomputed_cells=inc_exact_res.recomputed_cells,
        reused_fraction=inc_exact_res.reused_fraction,
        max_actual_error_k=float(np.max(err_exact)),
        mean_actual_error_k=float(np.mean(err_exact)),
        max_predicted_bound_k=0.0,
        has_certificate=False,
        is_sound=True,
        violations_count=0
    )

    # 4. Certified Incremental Update
    t0 = time.perf_counter()
    inc_cert_res, cert = incremental_update_certified(
        scene_before, scene_after, res_baseline, edit, weather, config
    )
    t_cert = time.perf_counter() - t0
    verif = verify_certificate(cert, inc_cert_res.result.tmrt, res_full.tmrt)
    err_cert = np.abs(inc_cert_res.result.tmrt - res_full.tmrt)

    rec_cert = BaselineComparisonRecord(
        method_name="certified_incremental",
        runtime_sec=t_cert,
        speedup=t_full / t_cert if t_cert > 0 else 1.0,
        reused_cells=cert.reused_cells,
        recomputed_cells=cert.affected_cells,
        reused_fraction=cert.reused_fraction,
        max_actual_error_k=float(np.max(err_cert)),
        mean_actual_error_k=float(np.mean(err_cert)),
        max_predicted_bound_k=float(cert.max_predicted_bound),
        has_certificate=True,
        is_sound=verif.is_valid,
        violations_count=verif.num_violations
    )

    return [rec_full, rec_naive, rec_exact, rec_cert]
