"""
Unit tests for the error certificate engine and mathematical soundness checks:
Verifies actual_error(x) <= predicted_bound(x) <= tolerance across all 4 building edits.
"""

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
from urban_comfort.incremental.certificate import (
    verify_certificate, CertificateViolationError
)


@pytest.fixture
def baseline_setup():
    weather = Weather(
        air_temperature=301.15,
        relative_humidity=50.0,
        wind_speed=2.0,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=160.0
    )
    config = SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="12:00:00",
        grid_resolution=1.0,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0,
        tmrt_tolerance=0.5
    )
    return weather, config


@pytest.mark.parametrize("tol", [0.1, 0.5, 1.0, 2.0])
def test_certificate_soundness_add_building(baseline_setup, tol):
    weather, config = baseline_setup
    config = SimulationConfig(
        latitude=config.latitude, longitude=config.longitude,
        date=config.date, local_time=config.local_time,
        sky_patch_configuration=config.sky_patch_configuration,
        max_svf_search_dist_m=config.max_svf_search_dist_m,
        tmrt_tolerance=tol
    )

    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, weather, config)

    bldg = Building("b_add", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=18.0)
    edit = AddBuildingEdit(bldg)
    scene_after, _ = edit.apply(scene_before)

    # 1. Certified incremental update
    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    # 2. Ground truth full recomputation
    full_res = full_recompute(scene_after, weather, config)

    # 3. Verify mathematical soundness
    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)

    assert verif.is_valid, f"Certificate violated! {verif.num_violations} violations with max {verif.max_violation} K"
    assert verif.num_violations == 0
    assert verif.is_within_tolerance, "Reused cells exceeded user tolerance threshold!"


def test_certificate_soundness_remove_building(baseline_setup):
    weather, config = baseline_setup
    scene_before = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = RemoveBuildingEdit("bldg_center")
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


def test_certificate_soundness_height_change(baseline_setup):
    weather, config = baseline_setup
    scene_before = create_single_box_scene(extent_m=60.0, box_size=12.0, box_height=12.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = ChangeHeightEdit("bldg_center", new_height=26.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


def test_certificate_soundness_move_building(baseline_setup):
    weather, config = baseline_setup
    scene_before = create_single_box_scene(extent_m=60.0, box_size=10.0, box_height=15.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = MoveBuildingEdit("bldg_center", shift_x=12.0, shift_y=12.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid
    assert verif.num_violations == 0
    assert verif.is_within_tolerance


def test_artificial_violation_detection(baseline_setup):
    weather, config = baseline_setup
    scene_before = create_single_box_scene(extent_m=40.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = ChangeHeightEdit("bldg_center", 20.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    # Intentionally corrupt incremental result with a massive +50K error spike
    corrupted_tmrt = inc_res.result.tmrt.copy()
    corrupted_tmrt[5, 5] += 50.0

    # Must raise CertificateViolationError!
    with pytest.raises(CertificateViolationError) as exc_info:
        verify_certificate(cert, corrupted_tmrt, full_res.tmrt)

    assert "Certificate violation detected!" in str(exc_info.value)
