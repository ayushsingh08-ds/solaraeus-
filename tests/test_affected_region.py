"""
Unit tests for the conservative candidate affected-region generator.
Verifies 100% spatial containment of direct shadow changes and low-sun fallback behavior.
"""

import math
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig, create_single_box_scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.incremental.update import (
    AddBuildingEdit, RemoveBuildingEdit, ChangeHeightEdit, MoveBuildingEdit
)
from urban_comfort.incremental.affected_region import (
    compute_candidate_affected_region, project_box_shadow
)


@pytest.fixture
def base_setup():
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1))
    alt_rad = math.radians(40.0)
    az_rad = math.radians(160.0)
    sun_vec = (
        math.cos(alt_rad) * math.sin(az_rad),
        math.cos(alt_rad) * math.cos(az_rad),
        math.sin(alt_rad)
    )
    solar_pos = SolarPosition(
        altitude_deg=40.0, azimuth_deg=160.0, zenith_deg=50.0,
        sun_vector=sun_vec, is_daylight=True
    )
    return grid, solar_pos


def test_candidate_affected_region_add_building_containment(base_setup):
    grid, solar_pos = base_setup
    scene_before = Scene(pedestrian_grid=grid.config)
    bldg = Building("b_new", BoundingBox2D(35.0, 45.0, 35.0, 45.0), height=18.0)
    edit = AddBuildingEdit(bldg)
    scene_after, _ = edit.apply(scene_before)

    # Actual ground shadow difference
    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)
    actual_diff = (shadow_before != shadow_after)

    # Candidate region
    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    assert not cand_res.is_fallback
    assert np.any(actual_diff), "Adding building must produce shadow differences!"
    # 100% containment check: every single altered cell must fall inside candidate mask
    assert np.all(cand_res.candidate_mask[actual_diff]), "Shadow change escaped candidate affected region!"


def test_candidate_affected_region_remove_building_containment(base_setup):
    grid, solar_pos = base_setup
    scene_before = create_single_box_scene(extent_m=80.0, box_size=14.0, box_height=20.0)
    edit = RemoveBuildingEdit("bldg_center")
    scene_after, _ = edit.apply(scene_before)

    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)
    actual_diff = (shadow_before != shadow_after)

    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    assert not cand_res.is_fallback
    assert np.all(cand_res.candidate_mask[actual_diff])


def test_candidate_affected_region_height_change_containment(base_setup):
    grid, solar_pos = base_setup
    scene_before = create_single_box_scene(extent_m=80.0, box_size=12.0, box_height=10.0)
    edit = ChangeHeightEdit("bldg_center", new_height=25.0)
    scene_after, _ = edit.apply(scene_before)

    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)
    actual_diff = (shadow_before != shadow_after)

    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    assert not cand_res.is_fallback
    assert np.all(cand_res.candidate_mask[actual_diff])


def test_candidate_affected_region_move_building_containment(base_setup):
    grid, solar_pos = base_setup
    scene_before = create_single_box_scene(extent_m=80.0, box_size=10.0, box_height=14.0)
    edit = MoveBuildingEdit("bldg_center", shift_x=12.0, shift_y=-10.0)
    scene_after, _ = edit.apply(scene_before)

    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)
    actual_diff = (shadow_before != shadow_after)

    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    assert not cand_res.is_fallback
    assert np.all(cand_res.candidate_mask[actual_diff])


def test_low_sun_angle_fallback(base_setup):
    grid, _ = base_setup
    scene_before = create_single_box_scene(extent_m=60.0)
    edit = ChangeHeightEdit("bldg_center", 20.0)
    scene_after, _ = edit.apply(scene_before)

    # Very low solar altitude (3.0 deg < 5.0 deg threshold)
    low_sun = SolarPosition(
        altitude_deg=3.0, azimuth_deg=180.0, zenith_deg=87.0,
        sun_vector=(0.0, -0.998, 0.052), is_daylight=True
    )

    cand_res = compute_candidate_affected_region(
        scene_before, scene_after, edit, low_sun, grid, min_altitude_deg=5.0
    )

    assert cand_res.is_fallback is True
    assert cand_res.fallback_reason is not None
    assert "below numerical stability limit" in cand_res.fallback_reason
    # When falling back, entire domain mask is marked dirty for safety
    assert np.all(cand_res.candidate_mask)
