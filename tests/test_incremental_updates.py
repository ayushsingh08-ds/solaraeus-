"""
Unit tests for exact incremental updates across all 4 core building edits:
AddBuilding, RemoveBuilding, ChangeHeight, and MoveBuilding.
Verifies exact numerical equivalence (actual error <= 1e-10) against full recomputation.
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
    incremental_update_exact
)
from urban_comfort.validation.comparisons import compare_results


@pytest.fixture
def test_env():
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
        max_svf_search_dist_m=20.0
    )
    return weather, config


def test_exact_incremental_add_building(test_env):
    weather, config = test_env
    # 60x60m domain
    scene_before = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=60.0, extent_y=60.0))
    res_before = full_recompute(scene_before, weather, config)

    # Add 12x12x18m building at center
    bldg = Building("b_new", BoundingBox2D(24.0, 36.0, 24.0, 36.0), height=18.0)
    edit = AddBuildingEdit(bldg)
    scene_after, _ = edit.apply(scene_before)

    # 1. Incremental update
    inc_res = incremental_update_exact(
        scene_before, scene_after, res_before, edit, weather, config,
        max_svf_search_dist_m=20.0
    )

    # 2. Full recomputation
    full_res = full_recompute(scene_after, weather, config)

    # Check exact numerical equivalence (error <= 1e-10)
    comps = compare_results(inc_res.result, full_res, tmrt_tolerance=1e-10, numerical_tolerance=1e-10)

    for field_name, m in comps.items():
        assert m.is_within_tolerance, (
            f"AddBuilding exact incremental update failed on '{field_name}'! "
            f"Max error: {m.max_absolute_error:.6e}"
        )

    # Verify significant reuse
    assert inc_res.reused_fraction > 0.0


def test_exact_incremental_remove_building(test_env):
    weather, config = test_env
    scene_before = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = RemoveBuildingEdit("bldg_center")
    scene_after, _ = edit.apply(scene_before)

    # Incremental update
    inc_res = incremental_update_exact(
        scene_before, scene_after, res_before, edit, weather, config,
        max_svf_search_dist_m=20.0
    )
    full_res = full_recompute(scene_after, weather, config)

    comps = compare_results(inc_res.result, full_res, tmrt_tolerance=1e-10, numerical_tolerance=1e-10)
    for field_name, m in comps.items():
        assert m.is_within_tolerance, (
            f"RemoveBuilding exact incremental update failed on '{field_name}'! "
            f"Max error: {m.max_absolute_error:.6e}"
        )


def test_exact_incremental_change_height(test_env):
    weather, config = test_env
    scene_before = create_single_box_scene(extent_m=60.0, box_size=12.0, box_height=12.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = ChangeHeightEdit("bldg_center", new_height=26.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res = incremental_update_exact(
        scene_before, scene_after, res_before, edit, weather, config,
        max_svf_search_dist_m=20.0
    )
    full_res = full_recompute(scene_after, weather, config)

    comps = compare_results(inc_res.result, full_res, tmrt_tolerance=1e-10, numerical_tolerance=1e-10)
    for field_name, m in comps.items():
        assert m.is_within_tolerance, (
            f"ChangeHeight exact incremental update failed on '{field_name}'! "
            f"Max error: {m.max_absolute_error:.6e}"
        )


def test_exact_incremental_move_building(test_env):
    weather, config = test_env
    scene_before = create_single_box_scene(extent_m=60.0, box_size=10.0, box_height=15.0)
    res_before = full_recompute(scene_before, weather, config)

    edit = MoveBuildingEdit("bldg_center", shift_x=10.0, shift_y=10.0)
    scene_after, _ = edit.apply(scene_before)

    inc_res = incremental_update_exact(
        scene_before, scene_after, res_before, edit, weather, config,
        max_svf_search_dist_m=20.0
    )
    full_res = full_recompute(scene_after, weather, config)

    comps = compare_results(inc_res.result, full_res, tmrt_tolerance=1e-10, numerical_tolerance=1e-10)
    for field_name, m in comps.items():
        assert m.is_within_tolerance, (
            f"MoveBuilding exact incremental update failed on '{field_name}'! "
            f"Max error: {m.max_absolute_error:.6e}"
        )
