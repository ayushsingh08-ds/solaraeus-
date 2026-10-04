"""
Unit tests for CPU Ray-AABB intersection routines.
"""

import math
import numpy as np
import pytest

from urban_comfort.visibility.ray_intersection import (
    intersect_ray_aabb, intersect_rays_aabb_batch
)


def test_single_ray_intersection_hit():
    box = (10.0, 20.0, 10.0, 20.0, 0.0, 15.0)

    # Ray starting at (0, 15, 5) pointing East (+X, 1, 0, 0)
    origin = (0.0, 15.0, 5.0)
    direction = (1.0, 0.0, 0.0)
    t = intersect_ray_aabb(origin, direction, box)

    assert t is not None
    assert math.isclose(t, 10.0, abs_tol=1e-5)


def test_single_ray_intersection_miss():
    box = (10.0, 20.0, 10.0, 20.0, 0.0, 15.0)

    # Ray pointing opposite direction (-X)
    origin = (0.0, 15.0, 5.0)
    direction = (-1.0, 0.0, 0.0)
    assert intersect_ray_aabb(origin, direction, box) is None

    # Ray pointing above box (z = 25 > 15)
    origin_high = (0.0, 15.0, 25.0)
    direction_x = (1.0, 0.0, 0.0)
    assert intersect_ray_aabb(origin_high, direction_x, box) is None


def test_ray_rooftop_hit():
    box = (10.0, 20.0, 10.0, 20.0, 0.0, 15.0)

    # Ray starting above at (15, 15, 30) pointing down (-Z)
    origin = (15.0, 15.0, 30.0)
    direction = (0.0, 0.0, -1.0)
    t = intersect_ray_aabb(origin, direction, box)

    assert t is not None
    assert math.isclose(t, 15.0, abs_tol=1e-5)  # Hits rooftop at z=15 (dist = 30 - 15 = 15)


def test_ray_origin_inside_box():
    box = (10.0, 20.0, 10.0, 20.0, 0.0, 15.0)
    origin = (15.0, 15.0, 5.0)
    direction = (0.0, 1.0, 0.0)
    t = intersect_ray_aabb(origin, direction, box)
    assert t is not None
    assert t == 0.0


def test_batch_ray_intersection():
    box = (10.0, 20.0, 10.0, 20.0, 0.0, 15.0)
    origins = np.array([
        [0.0, 15.0, 5.0],   # Hit at t=10
        [0.0, 25.0, 5.0],   # Miss (y=25 > 20)
        [0.0, 15.0, 20.0],  # Miss (z=20 > 15)
        [15.0, 15.0, 5.0],  # Inside -> Hit at t=0
    ])
    direction = (1.0, 0.0, 0.0)

    hits, t_hits = intersect_rays_aabb_batch(origins, direction, box)

    assert hits[0] is True or hits[0] == 1
    assert math.isclose(t_hits[0], 10.0, abs_tol=1e-5)

    assert not hits[1]
    assert not hits[2]

    assert hits[3] is True or hits[3] == 1
    assert math.isclose(t_hits[3], 0.0, abs_tol=1e-5)
