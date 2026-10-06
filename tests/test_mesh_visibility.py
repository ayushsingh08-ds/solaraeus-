"""
Unit tests for directional visibility and Sky View Factor (SVF) on triangular meshes.
"""

from __future__ import annotations
import math
import pytest
import numpy as np

from urban_comfort.geometry.mesh import (
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_overhang_mesh,
    create_l_shaped_mesh
)
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.visibility.mesh_visibility import (
    compute_mesh_sky_view_factor,
    rasterize_mesh_to_height_grid,
    rasterize_scene_meshes_to_height_grid
)


@pytest.fixture
def svf_grid():
    grid_cfg = PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0)
    return PedestrianGrid(grid_cfg)


def test_open_scene_mesh_svf(svf_grid):
    grid = svf_grid
    scene = Scene(pedestrian_grid=grid.config)

    # 1. No meshes
    svf_empty = compute_sky_view_factor(scene, grid, num_azimuths=16)
    assert np.allclose(svf_empty, 1.0)

    # 2. Disabled mesh
    mesh = create_box_mesh("m_disabled", 20.0, 40.0, 20.0, 40.0, 0.0, 20.0)
    mesh.enabled = False
    scene.add_mesh(mesh)
    svf_disabled = compute_sky_view_factor(scene, grid, num_azimuths=16)
    assert np.allclose(svf_disabled, 1.0)


def test_mesh_box_vs_aabb_svf_parity(svf_grid):
    grid = svf_grid

    # 1. AABB Building
    bldg = Building("b_aabb", BoundingBox2D(25.0, 35.0, 25.0, 35.0), height=20.0)
    scene_aabb = Scene(pedestrian_grid=grid.config)
    scene_aabb.add_building(bldg)
    svf_aabb = compute_sky_view_factor(scene_aabb, grid, num_azimuths=16, max_search_dist_m=30.0)

    # 2. Triangulated Box Mesh with identical geometry
    mesh_box = create_box_mesh("b_mesh", 25.0, 35.0, 25.0, 35.0, 0.0, 20.0)
    scene_mesh = Scene(pedestrian_grid=grid.config)
    scene_mesh.add_mesh(mesh_box)
    svf_mesh = compute_sky_view_factor(scene_mesh, grid, num_azimuths=16, max_search_dist_m=30.0)

    diff = np.abs(svf_aabb - svf_mesh)
    mae = float(np.mean(diff))
    max_diff = float(np.max(diff))

    # SVF between continuous AABB checks and rasterized mesh height sampling
    # agrees within MAE < 0.005 and max difference < 0.02
    assert mae < 0.005, f"Expected MAE < 0.005, got {mae:.6f}"
    assert max_diff < 0.02, f"Expected max diff < 0.02, got {max_diff:.6f}"

    # Receptors inside building footprint must be exactly 0.0 in both
    inside_mask = (grid.X >= 25.0) & (grid.X <= 35.0) & (grid.Y >= 25.0) & (grid.Y <= 35.0)
    assert np.all(svf_aabb[inside_mask] == 0.0)
    assert np.all(svf_mesh[inside_mask] == 0.0)


def test_pitched_roof_vs_flat_svf(svf_grid):
    grid = svf_grid

    # Pitched roof: eave 10m, ridge 20m
    eave_h = 10.0
    ridge_h = 20.0
    pitched_mesh = create_pitched_roof_mesh(
        "pitched", 20.0, 40.0, 20.0, 40.0,
        eave_height=eave_h, ridge_height=ridge_h, ridge_orientation="x"
    )
    scene_pitch = Scene(pedestrian_grid=grid.config)
    scene_pitch.add_mesh(pitched_mesh)
    svf_pitch = compute_sky_view_factor(scene_pitch, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Flat roof at ridge height 20m
    flat_ridge = create_box_mesh("flat_ridge", 20.0, 40.0, 20.0, 40.0, 0.0, ridge_h)
    scene_ridge = Scene(pedestrian_grid=grid.config)
    scene_ridge.add_mesh(flat_ridge)
    svf_ridge = compute_sky_view_factor(scene_ridge, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Flat roof at eave height 10m
    flat_eave = create_box_mesh("flat_eave", 20.0, 40.0, 20.0, 40.0, 0.0, eave_h)
    scene_eave = Scene(pedestrian_grid=grid.config)
    scene_eave.add_mesh(flat_eave)
    svf_eave = compute_sky_view_factor(scene_eave, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Outside the building footprint:
    outside = (grid.X < 20.0) | (grid.X > 40.0) | (grid.Y < 20.0) | (grid.Y > 40.0)

    mean_pitch = float(np.mean(svf_pitch[outside]))
    mean_ridge = float(np.mean(svf_ridge[outside]))
    mean_eave = float(np.mean(svf_eave[outside]))

    # Physical monotonicity: eave SVF > pitched SVF > ridge SVF
    assert mean_eave > mean_pitch > mean_ridge, (
        f"Monotonicity violation: eave={mean_eave:.4f}, pitch={mean_pitch:.4f}, ridge={mean_ridge:.4f}"
    )


def test_rotated_box_svf_symmetry(svf_grid):
    grid = svf_grid

    # Square building 16x16 at center (30, 30), rotated 45 degrees
    mesh = create_rotated_box_mesh(
        "rot_box", center_x=30.0, center_y=30.0,
        width_x=16.0, width_y=16.0, height=20.0,
        angle_deg=45.0
    )
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)
    svf = compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=30.0)

    # Inside diamond footprint, SVF = 0.0
    assert svf[30, 30] == 0.0

    # 4 cardinal points at distance 15m from center (x=30, y=15; x=30, y=45; x=15, y=30; x=45, y=30)
    svf_s = svf[15, 30]
    svf_n = svf[45, 30]
    svf_w = svf[30, 15]
    svf_e = svf[30, 45]

    # Cardinal symmetry check: all 4 sides should have nearly identical SVF
    vals = [svf_s, svf_n, svf_w, svf_e]
    assert np.max(vals) - np.min(vals) < 0.03, f"Rotated box asymmetry: {vals}"


def test_overhang_building_svf(svf_grid):
    grid = svf_grid

    # Main core [25, 35] x [20, 30] with overhang extending to y=40m
    mesh = create_overhang_mesh(
        "overhang", xmin=25.0, xmax=35.0,
        ymin=20.0, ymax=30.0,
        base_height=16.0, overhang_depth=10.0,
        overhang_direction="north",
        overhang_thickness=4.0
    )
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)
    svf = compute_sky_view_factor(scene, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Under overhang: x=30, y=35
    assert svf[35, 30] == 0.0, "Receptor under overhang canopy must have SVF = 0.0"

    # Beyond overhang: x=30, y=45
    assert 0.0 < svf[45, 30] < 1.0, "Receptor north of overhang must have reduced SVF"


def test_mesh_svf_selective_roi(svf_grid):
    grid = svf_grid
    mesh = create_box_mesh("m_roi", 20.0, 40.0, 20.0, 40.0, 0.0, 20.0)
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(mesh)

    # Full SVF
    full_svf = compute_sky_view_factor(scene, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Selective ROI mask
    roi = np.zeros(grid.shape, dtype=bool)
    roi[15:25, 15:25] = True

    roi_svf = compute_sky_view_factor(scene, grid, num_azimuths=16, max_search_dist_m=30.0, roi_mask=roi)

    # Inside ROI, roi_svf must identically match full_svf
    assert np.array_equal(roi_svf[roi], full_svf[roi])
    # Outside ROI, defaults to 1.0
    assert np.all(roi_svf[~roi] == 1.0)


def test_hybrid_scene_aabb_and_mesh_svf(svf_grid):
    grid = svf_grid

    # Scene with 1 AABB building (west) and 1 TriangleMesh (east)
    bldg = Building("west_aabb", BoundingBox2D(10.0, 20.0, 25.0, 35.0), height=15.0)
    mesh = create_box_mesh("east_mesh", 40.0, 50.0, 25.0, 35.0, 0.0, 15.0)

    scene = Scene(pedestrian_grid=grid.config)
    scene.add_building(bldg)
    scene.add_mesh(mesh)

    svf = compute_sky_view_factor(scene, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Inside west building: SVF = 0.0
    assert svf[30, 15] == 0.0
    # Inside east mesh: SVF = 0.0
    assert svf[30, 45] == 0.0
    # Center between them: x=30, y=30 has sky view obstructed from both east and west
    assert 0.7 < svf[30, 30] < 0.95
