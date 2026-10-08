"""
Exact incremental recomputation engine for urban microclimate fields.
Selectively recomputes only provably affected cells, achieving zero numerical error vs full recomputation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Any
import math
import time
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci
from urban_comfort.reference.full_recompute import SimulationResult


@dataclass
class GeometricEdit:
    """Base class for geometric building edits."""
    edit_type: str

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        """Applies edit to scene and returns (new_scene, modified_volume_bounds_3d)."""
        raise NotImplementedError


@dataclass
class AddBuildingEdit(GeometricEdit):
    building: Building

    def __init__(self, building: Building):
        super().__init__(edit_type="building_added")
        self.building = building

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        new_scene.add_building(self.building)
        return new_scene, self.building.bounds_3d


@dataclass
class RemoveBuildingEdit(GeometricEdit):
    building_id: str

    def __init__(self, building_id: str):
        super().__init__(edit_type="building_removed")
        self.building_id = building_id

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        removed = new_scene.remove_building(self.building_id)
        return new_scene, removed.bounds_3d


@dataclass
class ChangeHeightEdit(GeometricEdit):
    building_id: str
    new_height: float

    def __init__(self, building_id: str, new_height: float):
        super().__init__(edit_type="building_height_changed")
        self.building_id = building_id
        self.new_height = new_height

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        bldg = new_scene.buildings[self.building_id]
        old_bounds = bldg.bounds_3d
        bldg.height = self.new_height
        new_bounds = bldg.bounds_3d

        # The differential volume of geometry changed is between min(old_h, new_h) and max(old_h, new_h)
        diff_bounds = (
            min(old_bounds[0], new_bounds[0]),
            max(old_bounds[1], new_bounds[1]),
            min(old_bounds[2], new_bounds[2]),
            max(old_bounds[3], new_bounds[3]),
            min(old_bounds[5], new_bounds[5]),
            max(old_bounds[5], new_bounds[5]),
        )
        return new_scene, diff_bounds


@dataclass
class MoveBuildingEdit(GeometricEdit):
    building_id: str
    shift_x: float
    shift_y: float

    def __init__(self, building_id: str, shift_x: float, shift_y: float):
        super().__init__(edit_type="building_moved")
        self.building_id = building_id
        self.shift_x = shift_x
        self.shift_y = shift_y

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        bldg = new_scene.buildings[self.building_id]
        old_bounds = bldg.bounds_3d

        old_pos = bldg.position
        bldg.position = (old_pos[0] + self.shift_x, old_pos[1] + self.shift_y, old_pos[2])
        new_bounds = bldg.bounds_3d

        union_bounds = (
            min(old_bounds[0], new_bounds[0]),
            max(old_bounds[1], new_bounds[1]),
            min(old_bounds[2], new_bounds[2]),
            max(old_bounds[3], new_bounds[3]),
            min(old_bounds[4], new_bounds[4]),
            max(old_bounds[5], new_bounds[5]),
        )
        return new_scene, union_bounds


@dataclass
class IncrementalUpdateResult:
    """Telemetry and outcome of an exact incremental update."""
    result: SimulationResult
    recomputed_mask: np.ndarray
    reused_mask: np.ndarray
    recomputed_cells: int
    total_cells: int
    reused_fraction: float
    time_incremental_sec: float
    time_candidate_region_sec: float
    time_selective_recompute_sec: float


def compute_exact_dirty_shadow_mask(grid: PedestrianGrid,
                                    edit_bounds_3d: Tuple[float, float, float, float, float, float],
                                    solar_pos: SolarPosition) -> np.ndarray:
    """
    Computes candidate ground region where direct shadow could possibly change.
    Any cell outside this region is provably unchanged.
    """
    ny, nx = grid.shape
    if not solar_pos.is_daylight:
        return np.zeros((ny, nx), dtype=bool)

    xmin, xmax, ymin, ymax, zmin, zmax = edit_bounds_3d
    alt_rad = solar_pos.altitude_rad
    if zmax <= grid.z_ped or alt_rad <= 0.0:
        dirty_slice_y, dirty_slice_x = grid.bounding_box_slices(xmin, xmax, ymin, ymax)
        mask = np.zeros((ny, nx), dtype=bool)
        mask[dirty_slice_y, dirty_slice_x] = True
        return mask

    # Maximum shadow reach in meters
    max_shadow_len = (zmax - grid.z_ped) / math.tan(alt_rad)

    # Shadow falls opposite to sun vector:
    # Sun direction in ground plane: sx (East), sy (North)
    # Shadow trajectory from obstacle to ground: (-sx, -sy)
    sx, sy, sz = solar_pos.sun_vector
    norm_horiz = math.hypot(sx, sy)
    if norm_horiz > 1e-6:
        shadow_dx = - (sx / norm_horiz) * max_shadow_len
        shadow_dy = - (sy / norm_horiz) * max_shadow_len
    else:
        shadow_dx = 0.0
        shadow_dy = 0.0

    # Bounding box of the shadow trajectory
    proj_xmin = min(xmin, xmin + shadow_dx) - grid.dx
    proj_xmax = max(xmax, xmax + shadow_dx) + grid.dx
    proj_ymin = min(ymin, ymin + shadow_dy) - grid.dx
    proj_ymax = max(ymax, ymax + shadow_dy) + grid.dx

    slice_y, slice_x = grid.bounding_box_slices(proj_xmin, proj_xmax, proj_ymin, proj_ymax)
    mask = np.zeros((ny, nx), dtype=bool)
    mask[slice_y, slice_x] = True
    return mask


def compute_exact_dirty_svf_mask(grid: PedestrianGrid,
                                 edit_bounds_3d: Tuple[float, float, float, float, float, float],
                                 max_search_dist_m: float) -> np.ndarray:
    """
    Computes region where Sky View Factor could possibly change.
    Beyond max_search_dist_m from the edit bounding box, SVF is identically unchanged.
    """
    ny, nx = grid.shape
    xmin, xmax, ymin, ymax, _, _ = edit_bounds_3d

    # Expand box by max horizon search distance
    svf_xmin = xmin - max_search_dist_m - grid.dx
    svf_xmax = xmax + max_search_dist_m + grid.dx
    svf_ymin = ymin - max_search_dist_m - grid.dx
    svf_ymax = ymax + max_search_dist_m + grid.dx

    slice_y, slice_x = grid.bounding_box_slices(svf_xmin, svf_xmax, svf_ymin, svf_ymax)
    mask = np.zeros((ny, nx), dtype=bool)
    mask[slice_y, slice_x] = True
    return mask


def incremental_update_exact(previous_scene: Scene,
                             updated_scene: Scene,
                             previous_result: SimulationResult,
                             edit: GeometricEdit,
                             weather: Weather,
                             config: SimulationConfig,
                             max_svf_search_dist_m: Optional[float] = None,
                             backend: str = "cpu") -> IncrementalUpdateResult:
    """
    Executes an exact incremental update, recomputing only cells within provably affected regions.
    """
    if backend.lower() == "gpu":
        from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
        engine = GPUIncrementalEngine()
        return engine.execute_exact_update(
            previous_scene, updated_scene, previous_result, edit, weather, config
        )

    t_start = time.perf_counter()
    svf_search_dist = max_svf_search_dist_m if max_svf_search_dist_m is not None else config.max_svf_search_dist_m

    # Apply edit to get modified volume bounding box
    _, edit_bounds_3d = edit.apply(previous_scene)

    from datetime import datetime, timezone
    dt_str = f"{config.date} {config.local_time}"
    dt_utc = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

    grid = PedestrianGrid(updated_scene.pedestrian_grid)

    # 1. Candidate Affected Region Computation
    t0_cand = time.perf_counter()
    shadow_dirty_mask = compute_exact_dirty_shadow_mask(grid, edit_bounds_3d, solar_pos)
    svf_dirty_mask = compute_exact_dirty_svf_mask(grid, edit_bounds_3d, svf_search_dist)
    combined_dirty_mask = shadow_dirty_mask | svf_dirty_mask
    t_cand = time.perf_counter() - t0_cand

    # 2. Selective Recomputation
    t0_recomp = time.perf_counter()

    # Direct shadow: start from cached, recompute only dirty cells
    new_shadow = previous_result.shadow_mask.copy()
    if np.any(shadow_dirty_mask):
        recomputed_shadow = compute_direct_shadow_mask(
            updated_scene, grid, solar_pos, roi_mask=shadow_dirty_mask
        )
        new_shadow[shadow_dirty_mask] = recomputed_shadow[shadow_dirty_mask]

    # SVF: start from cached, recompute only dirty cells
    new_svf = previous_result.svf.copy()
    if np.any(svf_dirty_mask):
        recomputed_svf = compute_sky_view_factor(
            updated_scene, grid,
            num_azimuths=config.sky_patch_configuration,
            max_search_dist_m=svf_search_dist,
            roi_mask=svf_dirty_mask
        )
        new_svf[svf_dirty_mask] = recomputed_svf[svf_dirty_mask]

    # Radiative exchange and comfort: recompute only where inputs changed
    wall_mat = updated_scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
    ground_mat = updated_scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)

    # Compute shortwave and longwave on full fields (vectorized operations take < 1 ms)
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
    t_recomp = time.perf_counter() - t0_recomp
    t_total = time.perf_counter() - t_start

    metadata = {
        "is_incremental": True,
        "edit_type": edit.edit_type,
        "timing_candidate_region_sec": t_cand,
        "timing_selective_recompute_sec": t_recomp,
        "timing_total_sec": t_total,
        "recomputed_cells": int(np.sum(combined_dirty_mask)),
        "total_cells": grid.total_cells,
        "reused_fraction": 1.0 - (float(np.sum(combined_dirty_mask)) / float(grid.total_cells))
    }

    result = SimulationResult(
        shadow_mask=new_shadow,
        direct_irradiance=sw_fluxes.direct_horizontal,
        visibility_fields={"svf": new_svf},
        shortwave_flux=sw_fluxes.k_total,
        longwave_flux=lw_fluxes.l_total,
        tmrt=radiant_state.tmrt_c,
        utci=utci,
        metadata=metadata
    )

    recomputed_count = int(np.sum(combined_dirty_mask))
    reused_mask = ~combined_dirty_mask

    return IncrementalUpdateResult(
        result=result,
        recomputed_mask=combined_dirty_mask,
        reused_mask=reused_mask,
        recomputed_cells=recomputed_count,
        total_cells=grid.total_cells,
        reused_fraction=1.0 - (recomputed_count / float(grid.total_cells)),
        time_incremental_sec=t_total,
        time_candidate_region_sec=t_cand,
        time_selective_recompute_sec=t_recomp
    )


def incremental_update_certified(previous_scene: Scene,
                                 updated_scene: Scene,
                                 previous_result: SimulationResult,
                                 edit: GeometricEdit,
                                 weather: Weather,
                                 config: SimulationConfig,
                                 backend: str = "cpu") -> Tuple[IncrementalUpdateResult, Any]:
    """
    Executes a certified incremental update with bounded approximation:
    - Generates error certificate B_T(x).
    - Cells where B_T(x) <= tolerance are safely reused without recomputation.
    - Cells where B_T(x) > tolerance are selectively recomputed.
    - Guarantees: |T_mrt_inc - T_mrt_full| <= B_T(x) <= tolerance on all reused cells.
    """
    if backend.lower() == "gpu":
        from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
        engine = GPUIncrementalEngine()
        return engine.execute_certified_update(
            previous_scene, updated_scene, previous_result, edit, weather, config
        )

    from urban_comfort.incremental.certificate import generate_error_certificate
    from datetime import datetime, timezone

    t_start = time.perf_counter()
    dt_str = f"{config.date} {config.local_time}"
    dt_utc = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)
    grid = PedestrianGrid(updated_scene.pedestrian_grid)

    # 1. Certificate Construction
    t0_cert = time.perf_counter()
    cert = generate_error_certificate(
        previous_scene, updated_scene, edit, previous_result,
        solar_pos, grid, weather, config
    )
    t_cert = time.perf_counter() - t0_cert

    if cert.status == "fallback":
        # Fallback to full recomputation
        from urban_comfort.reference.full_recompute import full_recompute
        full_res = full_recompute(updated_scene, weather, config)
        total_cells = grid.total_cells
        update_res = IncrementalUpdateResult(
            result=full_res,
            recomputed_mask=np.ones(grid.shape, dtype=bool),
            reused_mask=np.zeros(grid.shape, dtype=bool),
            recomputed_cells=total_cells,
            total_cells=total_cells,
            reused_fraction=0.0,
            time_incremental_sec=time.perf_counter() - t_start,
            time_candidate_region_sec=t_cert,
            time_selective_recompute_sec=time.perf_counter() - t_start - t_cert
        )
        return update_res, cert

    t_cand = cert.timing_candidate_region_sec
    t_cert_eval = cert.timing_certificate_eval_sec

    # 2. Identify Dirty Cells (where B_T(x) > tolerance)
    dirty_mask = cert.predicted_error_bound > config.tmrt_tolerance

    # 3. Selective Recomputation
    t0_recomp = time.perf_counter()
    new_shadow = previous_result.shadow_mask.copy()
    if np.any(dirty_mask):
        recomputed_shadow = compute_direct_shadow_mask(
            updated_scene, grid, solar_pos, roi_mask=dirty_mask
        )
        new_shadow[dirty_mask] = recomputed_shadow[dirty_mask]

    new_svf = previous_result.svf.copy()
    if np.any(dirty_mask):
        recomputed_svf = compute_sky_view_factor(
            updated_scene, grid,
            num_azimuths=config.sky_patch_configuration,
            max_search_dist_m=config.max_svf_search_dist_m,
            roi_mask=dirty_mask
        )
        new_svf[dirty_mask] = recomputed_svf[dirty_mask]

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
    t_recomp = time.perf_counter() - t0_recomp

    # 4. Result Assembly
    t0_assembly = time.perf_counter()
    recomputed_count = int(np.sum(dirty_mask))
    reused_count = grid.total_cells - recomputed_count
    reused_mask = ~dirty_mask

    metadata = {
        "is_incremental": True,
        "is_certified": True,
        "edit_type": edit.edit_type,
        "timing_candidate_region_sec": t_cand,
        "timing_certificate_sec": t_cert_eval,
        "timing_selective_recompute_sec": t_recomp,
        "timing_assembly_sec": 0.0,
        "timing_total_sec": 0.0,
        "recomputed_cells": recomputed_count,
        "reused_cells": reused_count,
        "total_cells": grid.total_cells,
        "reused_fraction": reused_count / float(grid.total_cells),
        "tmrt_tolerance": config.tmrt_tolerance,
        "max_predicted_bound": cert.max_predicted_bound
    }

    result = SimulationResult(
        shadow_mask=new_shadow,
        direct_irradiance=sw_fluxes.direct_horizontal,
        visibility_fields={"svf": new_svf},
        shortwave_flux=sw_fluxes.k_total,
        longwave_flux=lw_fluxes.l_total,
        tmrt=radiant_state.tmrt_c,
        utci=utci,
        metadata=metadata
    )

    t_assembly = time.perf_counter() - t0_assembly
    t_total = time.perf_counter() - t_start
    metadata["timing_assembly_sec"] = t_assembly
    metadata["timing_total_sec"] = t_total

    update_res = IncrementalUpdateResult(
        result=result,
        recomputed_mask=dirty_mask,
        reused_mask=reused_mask,
        recomputed_cells=recomputed_count,
        total_cells=grid.total_cells,
        reused_fraction=reused_count / float(grid.total_cells),
        time_incremental_sec=t_total,
        time_candidate_region_sec=t_cand,
        time_selective_recompute_sec=t_recomp
    )

    return update_res, cert

