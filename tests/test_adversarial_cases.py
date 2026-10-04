"""
Unit and integration tests for adversarial stress scenarios in Certified Incremental SOLWEIG.

Implements the 8 required stress cases:
1. Wall changing 20m -> 21m (Small height delta perturbation).
2. 50m very wide wall (High aspect ratio perpendicular obstacle).
3. 1m thin obstacle aligned with sun vector (Narrow silhouette parallel to rays).
4. Occlusion reveal (Removing foreground building revealing taller background building).
5. Low sun angle (15 deg) long shadow (Extremely long shadow plume spanning domain).
6. Ground shadow/reflection perturbation outside direct shadow (Pure diffuse/longwave perturbation).
7. Grid-cell boundary alignment (Obstacle boundaries on exact integer / half-integer coordinates).
8. Full-domain invalidation fallback (Candidate region covers domain, triggering clean fallback).
"""

from __future__ import annotations
import math
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig, create_single_box_scene
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.update import (
    AddBuildingEdit, RemoveBuildingEdit, ChangeHeightEdit, MoveBuildingEdit,
    incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate
from urban_comfort.incremental.affected_region import compute_candidate_affected_region


@pytest.fixture
def base_weather() -> Weather:
    return Weather(
        air_temperature=301.15,          # 28 C
        relative_humidity=50.0,
        wind_speed=2.0,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=160.0
    )


@pytest.fixture
def default_config() -> SimulationConfig:
    return SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="12:00:00",
        grid_resolution=1.0,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0,
        tmrt_tolerance=0.5
    )


# ---------------------------------------------------------------------------
# Case 1: Wall Changing 20m -> 21m (Small Height Delta Perturbation)
# ---------------------------------------------------------------------------
def test_adversarial_case1_small_height_delta(base_weather, default_config):
    """
    Stress Case 1: Building height increases slightly from 20m to 21m (+1m).
    Verifies fine-grained bound scaling and zero certificate violations.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    bldg = Building("b1", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=20.0)
    scene_before.add_building(bldg)

    res_before = full_recompute(scene_before, base_weather, default_config)

    edit = ChangeHeightEdit("b1", new_height=21.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid, f"Violations: {verif.num_violations}, max: {verif.max_violation}"
    assert verif.num_violations == 0
    assert verif.is_within_tolerance
    # Plume should be compact: majority of domain reused
    assert cert.reused_fraction > 0.70


# ---------------------------------------------------------------------------
# Case 2: 50m Very Wide Wall (High Aspect Ratio Perpendicular Obstacle)
# ---------------------------------------------------------------------------
def test_adversarial_case2_wide_wall(base_weather, default_config):
    """
    Stress Case 2: 50m wide East-West wall perpendicular to solar azimuth.
    Verifies that broad shadow plume and large SVF delta along a wide front are soundly bounded.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, base_weather, default_config)

    # 50m wide, 2m deep, 15m tall wall
    wall = Building("wide_wall", BoundingBox2D(5.0, 55.0, 25.0, 27.0), height=15.0)
    edit = AddBuildingEdit(wall)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance
    # Broad plume was captured
    assert cert.affected_cells > 0


# ---------------------------------------------------------------------------
# Case 3: 1m Thin Obstacle Aligned with Sun Vector
# ---------------------------------------------------------------------------
def test_adversarial_case3_thin_obstacle_aligned_with_rays(base_weather, default_config):
    """
    Stress Case 3: 1m narrow obstacle elongated along North-South axis.
    Verifies that narrow silhouettes at grid cell width do not suffer ray leakage.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, base_weather, default_config)

    # 1m wide, 20m long obstacle
    thin_obstacle = Building("thin_obs", BoundingBox2D(29.5, 30.5, 15.0, 35.0), height=14.0)
    edit = AddBuildingEdit(thin_obstacle)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


# ---------------------------------------------------------------------------
# Case 4: Occlusion Reveal (Removing Foreground Building)
# ---------------------------------------------------------------------------
def test_adversarial_case4_occlusion_reveal(base_weather, default_config):
    """
    Stress Case 4: Background tall building (25m) occluded by foreground building (12m).
    Removing foreground building unmasks background shadow.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    # Background building (North)
    b_bg = Building("b_bg", BoundingBox2D(25.0, 35.0, 35.0, 45.0), height=25.0)
    # Foreground building (South, in front of background building relative to sun)
    b_fg = Building("b_fg", BoundingBox2D(25.0, 35.0, 20.0, 30.0), height=12.0)
    scene_before.add_building(b_bg)
    scene_before.add_building(b_fg)

    res_before = full_recompute(scene_before, base_weather, default_config)

    # Remove foreground building
    edit = RemoveBuildingEdit("b_fg")
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


# ---------------------------------------------------------------------------
# Case 5: Low Sun Angle (15 deg) Long Shadow
# ---------------------------------------------------------------------------
def test_adversarial_case5_low_sun_angle(base_weather):
    """
    Stress Case 5: Low solar elevation angle (~15 deg).
    Shadow plume extends >45m across domain.
    """
    # 18:55:00 on 2024-07-15 gives solar altitude ~15.02 deg
    config_low_sun = SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="18:55:00",
        grid_resolution=1.0,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0,
        tmrt_tolerance=0.5
    )

    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    res_before = full_recompute(scene_before, base_weather, config_low_sun)

    # Building placed in the path of the setting sun (sun azimuth ~285 deg, WNW)
    bldg = Building("b_low_sun", BoundingBox2D(45.0, 55.0, 45.0, 55.0), height=12.0)
    edit = AddBuildingEdit(bldg)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, config_low_sun
    )
    full_res = full_recompute(scene_after, base_weather, config_low_sun)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


# ---------------------------------------------------------------------------
# Case 6: Ground Shadow / Reflection Perturbation Outside Direct Shadow
# ---------------------------------------------------------------------------
def test_adversarial_case6_diffuse_perturbation_outside_shadow(base_weather, default_config):
    """
    Stress Case 6: Verifies that cells OUTSIDE direct shadow frustum undergo subtle
    diffuse and longwave perturbations, and that theoretical bound B_T(x) correctly
    bounds these perturbations without false violations.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, base_weather, default_config)

    bldg = Building("b_diffuse", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=18.0)
    edit = AddBuildingEdit(bldg)
    scene_after, _ = edit.apply(scene_before)

    # Use tolerance = 1.0 K so subtle diffuse changes far away are safely certified
    config = SimulationConfig(
        latitude=default_config.latitude, longitude=default_config.longitude,
        date=default_config.date, local_time=default_config.local_time,
        sky_patch_configuration=default_config.sky_patch_configuration,
        max_svf_search_dist_m=default_config.max_svf_search_dist_m,
        tmrt_tolerance=1.0
    )

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, config
    )
    full_res = full_recompute(scene_after, base_weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0

    # Specifically check cells that are reused (outside dirty region):
    # Error must be non-negative, bounded by B_T(x) and <= tolerance
    reused_mask = (cert.predicted_error_bound <= cert.tolerance)
    actual_err = np.abs(inc_res.result.tmrt[reused_mask] - full_res.tmrt[reused_mask])
    bounds = cert.predicted_error_bound[reused_mask]

    assert np.all(actual_err <= bounds + 1e-9)
    assert np.all(actual_err <= config.tmrt_tolerance + 1e-9)


# ---------------------------------------------------------------------------
# Case 7: Grid-Cell Boundary Alignment
# ---------------------------------------------------------------------------
def test_adversarial_case7_grid_boundary_alignment(base_weather, default_config):
    """
    Stress Case 7: Building edges aligned exactly on integer grid coordinates
    and half-integer coordinates, testing for cell center ambiguities.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    # Exactly on integer lines
    b1 = Building("b_int", BoundingBox2D(10.0, 20.0, 10.0, 20.0), height=15.0)
    # Exactly on half-integer lines
    b2 = Building("b_half", BoundingBox2D(35.5, 45.5, 35.5, 45.5), height=15.0)
    scene_before.add_building(b1)
    scene_before.add_building(b2)

    res_before = full_recompute(scene_before, base_weather, default_config)

    # Edit: Move b1 by exactly 5.0m
    edit = MoveBuildingEdit("b_int", shift_x=5.0, shift_y=5.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


# ---------------------------------------------------------------------------
# Case 8: Full-Domain Invalidation Fallback
# ---------------------------------------------------------------------------
def test_adversarial_case8_full_domain_invalidation_fallback(base_weather, default_config):
    """
    Stress Case 8: Massive building edit that covers or touches the vast majority
    of the domain, verifying clean fallback to full recomputation.
    """
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=50.0, extent_y=50.0))
    res_before = full_recompute(scene_before, base_weather, default_config)

    # Massive 45m x 45m x 40m building on a 50m x 50m domain
    massive_bldg = Building("massive", BoundingBox2D(2.5, 47.5, 2.5, 47.5), height=40.0)
    edit = AddBuildingEdit(massive_bldg)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(
        scene_before, scene_after, res_before, edit, base_weather, default_config
    )
    full_res = full_recompute(scene_after, base_weather, default_config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance
    # Candidate region should cover entire or nearly entire grid
    assert cert.affected_cells >= 0.80 * (50 * 50)
