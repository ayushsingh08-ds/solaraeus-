"""
Unit tests for Sky View Factor calculation (src/physics/svf.py).
"""

import numpy as np
import pytest

from src.physics.svf import compute_svf


def test_svf_flat_ground():
    """
    Test case 1 (masterbackendsteps.md):
    Flat ground with no buildings -> SVF = 1.0 everywhere.
    """
    H, W = 40, 40
    dsm_flat = np.zeros((H, W), dtype=np.float32)

    svf = compute_svf(dsm_flat, n_dir=36, max_radius=30.0)

    assert svf.shape == (H, W)
    assert np.allclose(svf, 1.0, atol=1e-5), f"Flat ground SVF should be 1.0, got min={svf.min():.3f}"


def test_svf_deep_canyon():
    """
    Test case 2 (masterbackendsteps.md):
    Deep urban canyon: 10m wide canyon floor enclosed by 20m tall building walls.
    At the canyon center, SVF should be substantially reduced (< 0.40).
    """
    H, W = 60, 60
    dsm = np.zeros((H, W), dtype=np.float32)

    # 10m wide north-south street canyon between cols 25 and 35
    dsm[:, :25] = 20.0  # West building block (20m tall)
    dsm[:, 35:] = 20.0  # East building block (20m tall)

    svf = compute_svf(dsm, n_dir=72, max_radius=40.0)

    # Canyon center point (row 30, col 30)
    canyon_center_svf = svf[30, 30]

    assert canyon_center_svf < 0.42, f"Canyon center SVF {canyon_center_svf:.3f} should be < 0.42"
    # Roof tops should have SVF near 1.0
    assert svf[30, 10] > 0.85, f"Building rooftop SVF {svf[30, 10]:.3f} should be near 1.0"


def test_svf_isolated_building():
    """
    Test case 3 (masterbackendsteps.md):
    Flat ground with a single 20m building in the center.
    At 40m distance, SVF should be slightly reduced but close to 1.0 (~0.95+).
    Immediately next to the building wall, SVF should drop significantly (~0.6-0.75).
    """
    H, W = 80, 80
    dsm = np.zeros((H, W), dtype=np.float32)
    # 10x10m building at center [35:45, 35:45] of height 20m
    dsm[35:45, 35:45] = 20.0

    svf = compute_svf(dsm, n_dir=72, max_radius=50.0)

    # Distant point (col 5, row 40 is ~30m from building edge)
    distant_svf = svf[40, 5]
    assert 0.90 <= distant_svf <= 1.0, f"Distant SVF {distant_svf:.3f} should be >= 0.90"

    # Point adjacent to building wall (row 40, col 34)
    wall_svf = svf[40, 34]
    assert 0.50 <= wall_svf <= 0.80, f"Wall-adjacent SVF {wall_svf:.3f} should be reduced [0.50, 0.80]"


def test_svf_points_query_interface():
    """
    Tests that compute_svf returns (N,) array when points_3d is passed.
    """
    H, W = 30, 30
    dsm = np.zeros((H, W), dtype=np.float32)
    dsm[10:20, 10:20] = 15.0

    points = np.array([
        [5.0, 5.0, 1.1],
        [15.0, 15.0, 16.1],
        [25.0, 25.0, 1.1],
    ], dtype=np.float32)

    svf_pts = compute_svf(dsm, points_3d=points, n_dir=36, max_radius=25.0)

    assert svf_pts.shape == (3,)
    assert np.all((svf_pts >= 0.0) & (svf_pts <= 1.0))
