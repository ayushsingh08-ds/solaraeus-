"""
Unit tests for direct solar shadow mask calculation on triangular meshes.
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
from urban_comfort.visibility.mesh_shadow import compute_mesh_direct_shadow_mask


@pytest.fixture
def solar_setup():
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0)
    grid = PedestrianGrid(grid_cfg)

    # Sun at 45 degrees altitude, azimuth 180 degrees (due South: +Y points North, so sun is South, shadow projects North)
    alt_deg = 45.0
    az_deg = 180.0
    alt_rad = math.radians(alt_deg)
    az_rad = math.radians(az_deg)

    # sun_vector: sx = sin(az)*cos(alt) = 0.0, sy = cos(az)*cos(alt) = -cos(45), sz = sin(45)
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
    return grid, solar_pos


def test_triangulated_box_vs_aabb_exact_parity(solar_setup):
    grid, solar_pos = solar_setup

    # 1. AABB Building scene
    bldg = Building(id="bldg_aabb", footprint=BoundingBox2D(30.0, 50.0, 20.0, 40.0), height=15.0)
    scene_aabb = Scene(pedestrian_grid=grid.config)
    scene_aabb.add_building(bldg)
    shadow_aabb = compute_direct_shadow_mask(scene_aabb, grid, solar_pos)

    # 2. Triangulated Mesh scene with identical dimensions
    mesh = create_box_mesh("mesh_box", 30.0, 50.0, 20.0, 40.0, 0.0, 15.0)
    scene_mesh = Scene(pedestrian_grid=grid.config)
    scene_mesh.add_mesh(mesh)
    shadow_mesh = compute_direct_shadow_mask(scene_mesh, grid, solar_pos)

    # Parity check: shadow masks must be 100% identical across all 6,400 cells
    diff_cells = int(np.sum(shadow_aabb != shadow_mesh))
    assert diff_cells == 0, f"Expected 0 cell differences between AABB and mesh box, found {diff_cells}"
    assert np.array_equal(shadow_aabb, shadow_mesh)

    # Also test dedicated compute_mesh_direct_shadow_mask function
    shadow_mesh_dedicated = compute_mesh_direct_shadow_mask(scene_mesh, grid, solar_pos)
    assert np.array_equal(shadow_mesh, shadow_mesh_dedicated)


def test_rotated_box_shadow_direction(solar_setup):
    grid, solar_pos = solar_setup

    # Square building 16x16 at center (40, 40), rotated 45 degrees
    mesh = create_rotated_box_mesh(
        "rot_box", center_x=40.0, center_y=40.0,
        width_x=16.0, width_y=16.0, height=20.0,
        angle_deg=45.0
    )
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)
    shadow = compute_direct_shadow_mask(scene, grid, solar_pos)

    # Receptors strictly South of building tip (y < 40 - 8*sqrt(2) ≈ 28.68m) should not be shaded
    receptors_south = shadow[grid.Y < 28.0]
    assert np.all(receptors_south == 1.0), "South of building must be fully illuminated"

    # Receptors North of building (y > 40) should contain shadow
    receptors_north = shadow[grid.Y > 40.0]
    assert np.any(receptors_north == 0.0), "North of building must contain shadow"


def test_pitched_roof_shadow_reach(solar_setup):
    grid, solar_pos = solar_setup

    # Eave height 10m, Ridge height 20m, Ridge parallel to X at y = 30m
    eave_h = 10.0
    ridge_h = 20.0
    pitched_mesh = create_pitched_roof_mesh(
        "pitched", xmin=30.0, xmax=50.0, ymin=20.0, ymax=40.0,
        eave_height=eave_h, ridge_height=ridge_h, ridge_orientation="x"
    )
    flat_mesh = create_box_mesh("flat_ridge", 30.0, 50.0, 20.0, 40.0, 0.0, ridge_h)

    scene_pitch = Scene(pedestrian_grid=grid.config)
    scene_pitch.add_mesh(pitched_mesh)
    shadow_pitch = compute_direct_shadow_mask(scene_pitch, grid, solar_pos)

    scene_flat = Scene(pedestrian_grid=grid.config)
    scene_flat.add_mesh(flat_mesh)
    shadow_flat = compute_direct_shadow_mask(scene_flat, grid, solar_pos)

    # Analytical maximum shadow reach from ridge:
    # delta_h = ridge_h - z_ped = 20.0 - 1.1 = 18.9m
    # At 45 deg sun, shadow_len = delta_h / tan(45) = 18.9m
    # Ridge is at y = 30m, so shadow tip should reach y = 30 + 18.9 = 48.9m
    # Pitch shadow should have smaller shaded area than flat box of height ridge_h
    shaded_pitch_count = int(np.sum(shadow_pitch == 0.0))
    shaded_flat_count = int(np.sum(shadow_flat == 0.0))

    assert shaded_pitch_count < shaded_flat_count, "Pitched roof must cast less shadow than flat roof of same peak height"
    # At x=40, y=48 (< 48.9m) must be shaded, while y=50 (> 48.9m) must be lit
    assert shadow_pitch[48, 40] == 0.0, "Cell at y=48 must be shaded by ridge"
    assert shadow_pitch[50, 40] == 1.0, "Cell at y=50 must be illuminated beyond shadow tip"


def test_overhang_building_shadow(solar_setup):
    grid, solar_pos = solar_setup

    # Building [30, 50] x [20, 35] of height 16m with 10m overhang extending North (up to y = 45m)
    # The overhang is suspended between z=12m and z=16m
    oh_mesh = create_overhang_mesh(
        "oh_bldg", xmin=30.0, xmax=50.0, ymin=20.0, ymax=35.0,
        base_height=16.0, overhang_depth=10.0, overhang_direction="north",
        overhang_thickness=4.0
    )
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(oh_mesh)
    shadow = compute_direct_shadow_mask(scene, grid, solar_pos)

    # With sun from South (az=180, alt=45), the overhang projects shadow even further north
    # Ground at (x=40, y=40) is directly under the overhang and should be shaded
    assert shadow[40, 40] == 0.0


def test_multiple_overlapping_meshes(solar_setup):
    grid, solar_pos = solar_setup

    mesh1 = create_box_mesh("m1", 20.0, 35.0, 20.0, 35.0, 0.0, 15.0)
    mesh2 = create_box_mesh("m2", 30.0, 45.0, 20.0, 35.0, 0.0, 15.0)

    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh1)
    scene.add_mesh(mesh2)
    shadow_combined = compute_direct_shadow_mask(scene, grid, solar_pos)

    # Individual shadows
    s1 = Scene(pedestrian_grid=grid.config)
    s1.add_mesh(mesh1)
    shadow1 = compute_direct_shadow_mask(s1, grid, solar_pos)

    s2 = Scene(pedestrian_grid=grid.config)
    s2.add_mesh(mesh2)
    shadow2 = compute_direct_shadow_mask(s2, grid, solar_pos)

    # Combined shadow should be exact elementwise minimum (or logical AND of lit masks)
    expected_combined = np.minimum(shadow1, shadow2)
    assert np.array_equal(shadow_combined, expected_combined)


def test_mesh_removal_and_addition(solar_setup):
    grid, solar_pos = solar_setup

    scene = Scene(pedestrian_grid=grid.config)
    mesh = create_box_mesh("m", 30.0, 50.0, 30.0, 50.0, 0.0, 20.0)

    # Empty scene: all 1.0 (sunlit)
    assert np.all(compute_direct_shadow_mask(scene, grid, solar_pos) == 1.0)

    # Add mesh: shadow appears
    scene.add_mesh(mesh)
    shadow_with = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.any(shadow_with == 0.0)

    # Remove mesh: shadow disappears
    scene.remove_mesh("m")
    shadow_without = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.all(shadow_without == 1.0)


def test_nighttime_zero_illumination(solar_setup):
    grid, _ = solar_setup
    night_sun = SolarPosition(
        altitude_deg=-15.0,
        azimuth_deg=0.0,
        zenith_deg=105.0,
        sun_vector=(0.0, 0.0, -1.0),
        is_daylight=False
    )
    mesh = create_box_mesh("m", 30.0, 50.0, 30.0, 50.0, 0.0, 20.0)
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)

    shadow = compute_direct_shadow_mask(scene, grid, night_sun)
    assert np.all(shadow == 0.0), "Nighttime must produce zero direct solar illumination everywhere"


def test_mesh_shadow_selective_roi(solar_setup):
    grid, solar_pos = solar_setup
    mesh = create_box_mesh("m", 30.0, 50.0, 30.0, 50.0, 0.0, 20.0)
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)

    # Full shadow
    full_shadow = compute_direct_shadow_mask(scene, grid, solar_pos)

    # ROI mask covering the dirty quadrant [25:55, 25:55]
    roi_mask = np.zeros(grid.shape, dtype=bool)
    roi_mask[25:55, 25:55] = True

    roi_shadow = compute_direct_shadow_mask(scene, grid, solar_pos, roi_mask=roi_mask)

    # Inside ROI, roi_shadow must exactly match full_shadow
    assert np.array_equal(roi_shadow[roi_mask], full_shadow[roi_mask])
    # Outside ROI, roi_shadow defaults to 1.0
    assert np.all(roi_shadow[~roi_mask] == 1.0)
