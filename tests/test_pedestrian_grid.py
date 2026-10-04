"""
Unit tests for the pedestrian calculation grid.
"""

import numpy as np
import pytest

from urban_comfort.geometry.scene import PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid


def test_pedestrian_grid_initialization():
    cfg = PedestrianGridConfig(extent_x=50.0, extent_y=30.0, resolution=2.0, pedestrian_height=1.1)
    grid = PedestrianGrid(cfg)

    assert grid.nx == 25
    assert grid.ny == 15
    assert grid.shape == (15, 25)
    assert grid.total_cells == 375
    assert grid.dx == 2.0
    assert grid.z_ped == 1.1

    # Check coordinate bounds
    assert np.isclose(grid.X[0, 0], 1.0) # Center of first cell: [0, 2] -> 1.0
    assert np.isclose(grid.Y[0, 0], 1.0)
    assert np.isclose(grid.X[-1, -1], 49.0) # Center of last cell: [48, 50] -> 49.0
    assert np.isclose(grid.Y[-1, -1], 29.0)
    assert np.all(grid.Z == 1.1)


def test_pedestrian_grid_index_mappings():
    cfg = PedestrianGridConfig(extent_x=40.0, extent_y=40.0, resolution=1.0)
    grid = PedestrianGrid(cfg)

    # Roundtrip test
    for linear_idx in [0, 15, 39, 40, 100, 1599]:
        iy, ix = grid.linear_to_2d(linear_idx)
        recon_linear = grid.coords_2d_to_linear(iy, ix)
        assert recon_linear == linear_idx

    # Out of range checks
    with pytest.raises(IndexError):
        grid.linear_to_2d(-1)
    with pytest.raises(IndexError):
        grid.linear_to_2d(1600)
    with pytest.raises(IndexError):
        grid.coords_2d_to_linear(40, 0)


def test_world_to_cell_and_cell_to_world():
    cfg = PedestrianGridConfig(extent_x=50.0, extent_y=50.0, origin_x=10.0, origin_y=20.0, resolution=1.0)
    grid = PedestrianGrid(cfg)

    cell = grid.world_to_cell(15.4, 25.6)
    assert cell == (5, 5) # (25.6 - 20) -> 5, (15.4 - 10) -> 5

    wx, wy, wz = grid.cell_to_world(5, 5)
    assert np.isclose(wx, 15.5)
    assert np.isclose(wy, 25.5)
    assert np.isclose(wz, 1.1)

    # Out of domain coordinate returns None
    assert grid.world_to_cell(5.0, 25.0) is None
    assert grid.world_to_cell(65.0, 25.0) is None


def test_bounding_box_slices():
    cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=2.0)
    grid = PedestrianGrid(cfg)

    # Box [20, 40] x [30, 50]
    slice_y, slice_x = grid.bounding_box_slices(20.0, 40.0, 30.0, 50.0)
    # 20/2 = 10, 40/2 = 20 -> slice(10, 21)
    # 30/2 = 15, 50/2 = 25 -> slice(15, 26)
    assert slice_x == slice(10, 21)
    assert slice_y == slice(15, 26)


def test_flat_points_array():
    cfg = PedestrianGridConfig(extent_x=10.0, extent_y=10.0, resolution=5.0)
    grid = PedestrianGrid(cfg)
    pts = grid.get_flat_points()

    assert pts.shape == (4, 3) # 2x2 cells, each with 3 coordinates
    assert np.all(pts[:, 2] == 1.1)
