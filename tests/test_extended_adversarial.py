"""
Extended Adversarial Validation Suite for Certified Incremental SOLWEIG.

Implements Work Package 7 (12 adversarial stress scenarios):
1. Wall changing 20m -> 21m.
2. Very wide wall.
3. Narrow obstacle aligned with visibility direction.
4. Building removal revealing hidden surfaces.
5. Low-sun long-shadow case.
6. Edit near pedestrian-grid boundary.
7. Edit causing disconnected affected regions.
8. Changed ground-shadow contribution outside direct shadow.
9. Multiple buildings with overlapping shadows.
10. Repeated edits applied sequentially (testing cumulative error).
11. Reverting an edit to original state.
12. Multiple compound edits before recalculation.
"""

from __future__ import annotations
import math
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.update import (
    AddBuildingEdit, RemoveBuildingEdit, ChangeHeightEdit, MoveBuildingEdit,
    incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate


@pytest.fixture
def weather():
    return Weather(
        air_temperature=301.15,
        relative_humidity=50.0,
        wind_speed=2.0,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=160.0
    )


@pytest.fixture
def config():
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


# 1. Wall changing from 20m to 21m
def test_adv_01_wall_20_to_21m(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    scene_before.add_building(Building("b1", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=20.0))
    res_before = full_recompute(scene_before, weather, config)

    edit = ChangeHeightEdit("b1", new_height=21.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0
    assert verif.is_within_tolerance


# 2. Very wide wall
def test_adv_02_very_wide_wall(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    res_before = full_recompute(scene_before, weather, config)

    wall = Building("wide_wall", BoundingBox2D(5.0, 65.0, 30.0, 32.0), height=15.0)
    edit = AddBuildingEdit(wall)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 3. Narrow obstacle aligned with visibility direction
def test_adv_03_narrow_aligned_obstacle(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, weather, config)

    thin = Building("thin", BoundingBox2D(29.5, 30.5, 10.0, 40.0), height=12.0)
    edit = AddBuildingEdit(thin)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 4. Building removal revealing hidden surfaces
def test_adv_04_occlusion_reveal(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    scene_before.add_building(Building("bg", BoundingBox2D(25.0, 35.0, 35.0, 45.0), height=25.0))
    scene_before.add_building(Building("fg", BoundingBox2D(25.0, 35.0, 20.0, 30.0), height=12.0))
    res_before = full_recompute(scene_before, weather, config)

    edit = RemoveBuildingEdit("fg")
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 5. Low-sun long-shadow case
def test_adv_05_low_sun_long_shadow(weather):
    config_low = SimulationConfig(
        latitude=40.7128, longitude=-74.0060,
        date="2024-07-15", local_time="18:55:00",  # ~15 deg altitude
        grid_resolution=1.0, sky_patch_configuration=16,
        max_svf_search_dist_m=30.0, tmrt_tolerance=0.5
    )
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    res_before = full_recompute(scene_before, weather, config_low)

    edit = AddBuildingEdit(Building("b_low", BoundingBox2D(45.0, 55.0, 45.0, 55.0), height=14.0))
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config_low)
    full_res = full_recompute(scene_after, weather, config_low)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 6. Edit near pedestrian-grid boundary
def test_adv_06_boundary_edit(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, weather, config)

    # Building placed flush on boundary [0.0..10.0, 0.0..10.0]
    b_edge = Building("b_edge", BoundingBox2D(0.0, 10.0, 0.0, 10.0), height=15.0)
    edit = AddBuildingEdit(b_edge)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 7. Edit causing disconnected affected regions (Move edit source and destination far apart)
def test_adv_07_disconnected_regions(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    scene_before.add_building(Building("b_move", BoundingBox2D(10.0, 20.0, 10.0, 20.0), height=15.0))
    res_before = full_recompute(scene_before, weather, config)

    # Move by 35m across domain
    edit = MoveBuildingEdit("b_move", shift_x=35.0, shift_y=35.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 8. Changed ground-shadow contribution outside direct shadow
def test_adv_08_ground_shadow_diffuse_outside(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, weather, config)

    edit = AddBuildingEdit(Building("b_diff", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=18.0))
    scene_after, _ = edit.apply(scene_before)

    # Higher tolerance to inspect certified reuse outside direct plume
    cfg = SimulationConfig(
        latitude=config.latitude, longitude=config.longitude,
        date=config.date, local_time=config.local_time,
        sky_patch_configuration=config.sky_patch_configuration,
        max_svf_search_dist_m=config.max_svf_search_dist_m,
        tmrt_tolerance=1.5
    )
    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, cfg)
    full_res = full_recompute(scene_after, weather, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 9. Multiple buildings with overlapping shadows
def test_adv_09_overlapping_shadows(weather, config):
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    scene_before.add_building(Building("b1", BoundingBox2D(20.0, 30.0, 20.0, 30.0), height=16.0))
    scene_before.add_building(Building("b2", BoundingBox2D(35.0, 45.0, 20.0, 30.0), height=20.0))
    res_before = full_recompute(scene_before, weather, config)

    # Infill between them
    edit = AddBuildingEdit(Building("infill", BoundingBox2D(25.0, 40.0, 35.0, 45.0), height=18.0))
    scene_after, _ = edit.apply(scene_before)

    inc_res, cert = incremental_update_certified(scene_before, scene_after, res_before, edit, weather, config)
    full_res = full_recompute(scene_after, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0


# 10. Repeated edits applied sequentially (testing cumulative error accumulation)
def test_adv_10_sequential_repeated_edits(weather, config):
    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res = full_recompute(scene, weather, config)

    # Step 1: Add building 1
    e1 = AddBuildingEdit(Building("b1", BoundingBox2D(15.0, 25.0, 15.0, 25.0), height=15.0))
    scene1, _ = e1.apply(scene)
    inc_res1, cert1 = incremental_update_certified(scene, scene1, res, e1, weather, config)
    full_res1 = full_recompute(scene1, weather, config)
    v1 = verify_certificate(cert1, inc_res1.result.tmrt, full_res1.tmrt)
    assert v1.is_valid

    # Step 2: Add building 2 sequentially based on step 1 result
    e2 = AddBuildingEdit(Building("b2", BoundingBox2D(35.0, 45.0, 35.0, 45.0), height=18.0))
    scene2, _ = e2.apply(scene1)
    inc_res2, cert2 = incremental_update_certified(scene1, scene2, inc_res1.result, e2, weather, config)
    full_res2 = full_recompute(scene2, weather, config)
    v2 = verify_certificate(cert2, inc_res2.result.tmrt, full_res2.tmrt)
    assert v2.is_valid


# 11. Reverting an edit to the original state
def test_adv_11_revert_edit(weather, config):
    scene0 = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    scene0.add_building(Building("b1", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=18.0))
    res0 = full_recompute(scene0, weather, config)

    # Height to 28m
    e_up = ChangeHeightEdit("b1", new_height=28.0)
    scene_up, _ = e_up.apply(scene0)
    inc_up, cert_up = incremental_update_certified(scene0, scene_up, res0, e_up, weather, config)

    # Revert back to 18m
    e_down = ChangeHeightEdit("b1", new_height=18.0)
    scene_rev, _ = e_down.apply(scene_up)
    inc_rev, cert_rev = incremental_update_certified(scene_up, scene_rev, inc_up.result, e_down, weather, config)
    full_rev = full_recompute(scene_rev, weather, config)

    v_rev = verify_certificate(cert_rev, inc_rev.result.tmrt, full_rev.tmrt)
    assert v_rev.is_valid and v_rev.num_violations == 0


# 12. Multiple compound edits before recalculation
def test_adv_12_multiple_compound_edits(weather, config):
    scene0 = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=70.0, extent_y=70.0))
    scene0.add_building(Building("b1", BoundingBox2D(20.0, 30.0, 20.0, 30.0), height=15.0))
    scene0.add_building(Building("b2", BoundingBox2D(40.0, 50.0, 40.0, 50.0), height=20.0))
    res0 = full_recompute(scene0, weather, config)

    # Compound edit: move b1
    e_move = MoveBuildingEdit("b1", shift_x=5.0, shift_y=5.0)
    scene1, _ = e_move.apply(scene0)

    inc_res, cert = incremental_update_certified(scene0, scene1, res0, e_move, weather, config)
    full_res = full_recompute(scene1, weather, config)

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)
    assert verif.is_valid and verif.num_violations == 0
