"""
Unit tests for 2.5D shadow casting (src/physics/shadows.py).
"""

import math
import numpy as np
import pytest

from src.physics.shadows import cast_shadows


def test_shadow_length_and_direction_single_building():
    """
    Test case 1 (validation criteria in README.md):
    A 20m building at 60° sun altitude casts a shadow ~11.5m long in the direction opposite the sun.
    With sun due South (azimuth = 180°), shadows point due North.
    - Point 5m to the north of the building (in shadow direction) -> SHADED.
    - Point 15m to the north of the building (beyond 11.55m shadow) -> SUNLIT.
    - Point 5m to the south/side of the building -> SUNLIT.
    """
    H, W = 80, 80
    dsm = np.zeros((H, W), dtype=np.float32)

    # 10x10 building at rows 40:50, cols 35:45, height 20m
    dsm[40:50, 35:45] = 20.0

    alt_rad = math.radians(60.0)
    az_rad = math.radians(180.0)  # Sun due South

    sunlit = cast_shadows(dsm, alt_rad=alt_rad, az_rad=az_rad, max_distance=50.0)

    assert sunlit.shape == (H, W)

    # Point 5m north of building (row 35, col 40): inside shadow -> False
    assert not sunlit[35, 40], "Point 5m north of 20m building should be in shadow"

    # Point 15m north of building (row 25, col 40): beyond 11.55m shadow -> True
    assert sunlit[25, 40], "Point 15m north of 20m building should be sunlit"

    # Point 5m south of building (row 55, col 40): sun-facing side -> True
    assert sunlit[55, 40], "Point 5m south of building facing the sun should be sunlit"

    # Point 5m east of building (row 45, col 50): side point -> True
    assert sunlit[45, 52], "Point 5m east of building should be sunlit"

    # Building rooftop itself (row 45, col 40) -> True
    assert sunlit[45, 40], "Building rooftop should be sunlit"


def test_shadow_sun_below_horizon():
    """
    Test case 2: Sun at or below horizon (alt <= 0) -> 100% shaded.
    """
    H, W = 30, 30
    dsm = np.zeros((H, W), dtype=np.float32)
    dsm[10:20, 10:20] = 10.0

    sunlit = cast_shadows(dsm, alt_rad=0.0, az_rad=math.pi)
    assert not np.any(sunlit), "All cells must be shaded when sun is at horizon"

    sunlit_neg = cast_shadows(dsm, alt_rad=-0.1, az_rad=math.pi)
    assert not np.any(sunlit_neg), "All cells must be shaded when sun is below horizon"


def test_shadow_zenith_sun():
    """
    Test case 3: Sun directly overhead at zenith (alt = 90°) -> No lateral shadows cast.
    """
    H, W = 40, 40
    dsm = np.zeros((H, W), dtype=np.float32)
    dsm[15:25, 15:25] = 25.0

    sunlit = cast_shadows(dsm, alt_rad=math.pi / 2.0, az_rad=0.0)
    assert np.all(sunlit), "All cells must be sunlit when sun is at zenith"


def test_shadow_points_query_interface():
    """
    Test case 4: Returns (N,) bool array when points_3d is provided.
    """
    H, W = 50, 50
    dsm = np.zeros((H, W), dtype=np.float32)
    dsm[20:30, 20:30] = 20.0

    points = np.array([
        [25.0, 15.0, 1.1],  # North of building (shaded)
        [25.0, 35.0, 1.1],  # South of building (sunlit)
        [25.0, 25.0, 21.1], # Roof (sunlit)
    ], dtype=np.float32)

    sunlit_pts = cast_shadows(
        dsm,
        alt_rad=math.radians(60.0),
        az_rad=math.radians(180.0),
        points_3d=points,
    )

    assert sunlit_pts.shape == (3,)
    assert isinstance(sunlit_pts[0], (bool, np.bool_))
