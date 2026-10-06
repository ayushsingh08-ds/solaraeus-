"""
Unit tests for conservative candidate affected-region calculation on triangular meshes.
"""

from __future__ import annotations
import math
import pytest
import numpy as np

from urban_comfort.geometry.mesh import (
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_overhang_mesh
)
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.incremental.affected_region import (
    compute_candidate_affected_region, project_box_shadow
)
from urban_comfort.incremental.mesh_affected_region import (
    project_mesh_shadow, compute_mesh_candidate_affected_region
)
from urban_comfort.incremental.mesh_update import (
    AddMeshEdit, RemoveMeshEdit, ReplaceMeshEdit, MoveMeshEdit, ChangeMeshHeightEdit
)


@pytest.fixture
def solar_and_grid():
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0)
    grid = PedestrianGrid(grid_cfg)

    # Solar position at 45 deg altitude, azimuth 180 deg (South)
    alt_deg = 45.0
    az_deg = 180.0
    alt_rad = math.radians(alt_deg)
    az_rad = math.radians(az_deg)
    sx = math.sin(az_rad) * math.cos(alt_rad)
    sy = math.cos(az_rad) * math.cos(alt_rad)
    sz = math.sin(alt_rad)

    solar_pos = SolarPosition(
        altitude_deg=alt_deg,
        azimuth_deg=az_deg,
        zenith_deg=45.0,
        sun_vector=(sx, sy, sz),
        is_daylight=True
    )
    return solar_pos, grid


def test_mesh_project_shadow_box_vs_aabb_consistency(solar_and_grid):
    solar_pos, grid = solar_and_grid

    # Bounding box [25, 45] x [20, 35] of height 18m
    box_3d = (25.0, 45.0, 20.0, 35.0, 0.0, 18.0)
    mesh_box = create_box_mesh("b_box", 25.0, 45.0, 20.0, 35.0, 0.0, 18.0)

    proj_aabb = project_box_shadow(box_3d, solar_pos, grid.z_ped)
    proj_mesh = project_mesh_shadow(mesh_box, solar_pos, grid.z_ped)

    # Bounding boxes and shadow length must match
    for val_a, val_m in zip(proj_aabb, proj_mesh):
        assert abs(val_a - val_m) < 1e-6, f"Mismatch: AABB={val_a}, Mesh={val_m}"


def test_mesh_shadow_containment_rotated_box(solar_and_grid):
    solar_pos, grid = solar_and_grid

    scene_before = Scene(pedestrian_grid=grid.config)
    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)

    # Add 45-degree rotated box at center
    mesh = create_rotated_box_mesh("rot_box", center_x=40.0, center_y=40.0,
                                   width_x=16.0, width_y=16.0, height=20.0, angle_deg=45.0)
    edit = AddMeshEdit(mesh)
    scene_after, _ = edit.apply(scene_before)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)

    # Actual direct shadow changes
    shadow_diff = np.abs(shadow_before - shadow_after) > 1e-6
    changed_cells = int(np.sum(shadow_diff))
    assert changed_cells > 0, "Adding rotated building must cast shadows"

    # Candidate region
    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)
    assert not cand_res.is_fallback

    # Soundness verification: candidate mask must cover 100% of shadow change cells
    uncovered_changes = shadow_diff & (~cand_res.candidate_mask)
    num_uncovered = int(np.sum(uncovered_changes))
    assert num_uncovered == 0, f"Soundness violation! {num_uncovered} altered cells were outside candidate mask"

    # Efficiency: candidate region must be reasonably selective (< 35% of total grid)
    affected_fraction = float(np.mean(cand_res.candidate_mask))
    assert affected_fraction < 0.35, f"Candidate mask too large: {affected_fraction:.2%}"


def test_mesh_shadow_containment_pitched_roof(solar_and_grid):
    solar_pos, grid = solar_and_grid

    scene_before = Scene(pedestrian_grid=grid.config)
    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)

    # Pitched roof building
    mesh = create_pitched_roof_mesh(
        "pitch_bldg", xmin=30.0, xmax=50.0, ymin=25.0, ymax=45.0,
        eave_height=12.0, ridge_height=22.0, ridge_orientation="x"
    )
    edit = AddMeshEdit(mesh)
    scene_after, _ = edit.apply(scene_before)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)

    shadow_diff = np.abs(shadow_before - shadow_after) > 1e-6
    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    uncovered = shadow_diff & (~cand_res.candidate_mask)
    assert np.sum(uncovered) == 0, "All shadow changes must be within candidate mask"


def test_mesh_replacement_containment(solar_and_grid):
    solar_pos, grid = solar_and_grid

    # Baseline scene has flat roof building of height 12m
    flat_mesh = create_box_mesh("roof_edit", 30.0, 50.0, 20.0, 40.0, 0.0, 12.0)
    scene_before = Scene(pedestrian_grid=grid.config)
    scene_before.add_mesh(flat_mesh)
    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)

    # Replace with pitched roof building of ridge height 24m
    pitched_mesh = create_pitched_roof_mesh(
        "roof_edit", 30.0, 50.0, 20.0, 40.0,
        eave_height=12.0, ridge_height=24.0, ridge_orientation="x"
    )
    edit = ReplaceMeshEdit("roof_edit", pitched_mesh)
    scene_after, _ = edit.apply(scene_before)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)

    shadow_diff = np.abs(shadow_before - shadow_after) > 1e-6
    assert np.sum(shadow_diff) > 0, "Raising ridge height must extend shadow"

    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)
    uncovered = shadow_diff & (~cand_res.candidate_mask)
    assert np.sum(uncovered) == 0, "Candidate mask must cover entire shadow extension"


def test_mesh_move_containment(solar_and_grid):
    solar_pos, grid = solar_and_grid

    # Initial building at [20, 35] x [20, 35]
    mesh = create_box_mesh("move_mesh", 20.0, 35.0, 20.0, 35.0, 0.0, 16.0)
    scene_before = Scene(pedestrian_grid=grid.config)
    scene_before.add_mesh(mesh)
    shadow_before = compute_direct_shadow_mask(scene_before, grid, solar_pos)

    # Shift building by dx=+15, dy=+10
    edit = MoveMeshEdit("move_mesh", shift_x=15.0, shift_y=10.0)
    scene_after, _ = edit.apply(scene_before)
    shadow_after = compute_direct_shadow_mask(scene_after, grid, solar_pos)

    shadow_diff = np.abs(shadow_before - shadow_after) > 1e-6
    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)

    uncovered = shadow_diff & (~cand_res.candidate_mask)
    assert np.sum(uncovered) == 0, "Candidate mask must cover both vacated and newly occupied shadows"


def test_low_solar_altitude_fallback(solar_and_grid):
    _, grid = solar_and_grid
    low_sun = SolarPosition(
        altitude_deg=3.0,  # Below 5.0 deg threshold
        azimuth_deg=180.0,
        zenith_deg=87.0,
        sun_vector=(0.0, -0.998, 0.052),
        is_daylight=True
    )
    mesh = create_box_mesh("m_low", 30.0, 50.0, 30.0, 50.0, 0.0, 20.0)
    edit = AddMeshEdit(mesh)
    scene = Scene(pedestrian_grid=grid.config)

    cand_res = compute_candidate_affected_region(scene, scene, edit, low_sun, grid)
    assert cand_res.is_fallback, "Low sun angle must safely trigger full fallback"
    assert np.all(cand_res.candidate_mask), "Fallback mask must cover entire domain"


def test_nighttime_zero_affected_region(solar_and_grid):
    _, grid = solar_and_grid
    night_sun = SolarPosition(
        altitude_deg=-10.0,
        azimuth_deg=0.0,
        zenith_deg=100.0,
        sun_vector=(0.0, 0.0, -1.0),
        is_daylight=False
    )
    mesh = create_box_mesh("m_night", 30.0, 50.0, 30.0, 50.0, 0.0, 20.0)
    edit = AddMeshEdit(mesh)
    scene = Scene(pedestrian_grid=grid.config)

    cand_res = compute_candidate_affected_region(scene, scene, edit, night_sun, grid)
    assert not cand_res.is_fallback
    assert np.sum(cand_res.candidate_mask) == 0, "Nighttime must have zero affected cells"
