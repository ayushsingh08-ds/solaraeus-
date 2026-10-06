"""
Unit tests for CPU ray-triangle and ray-mesh intersection routines.
"""

from __future__ import annotations
import math
import pytest
import numpy as np

from urban_comfort.visibility.mesh_ray_intersection import (
    intersect_ray_triangle,
    intersect_ray_mesh,
    intersect_rays_mesh_batch,
    intersect_rays_scene_meshes
)
from urban_comfort.geometry.mesh import create_box_mesh, TriangleMesh


@pytest.fixture
def canonical_triangle():
    # Right triangle in XY plane at z = 5.0
    # Normal points in +Z: cross((2,0,0), (0,2,0)) = (0, 0, 4)
    v0 = np.array([0.0, 0.0, 5.0])
    v1 = np.array([2.0, 0.0, 5.0])
    v2 = np.array([0.0, 2.0, 5.0])
    return v0, v1, v2


def test_ray_hits_triangle_front_face(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    # Ray origin at (0.5, 0.5, 10.0), shooting downwards along -Z
    # Facing the front face (opposing +Z normal)
    origin = (0.5, 0.5, 10.0)
    direction = (0.0, 0.0, -1.0)

    res = intersect_ray_triangle(origin, direction, v0, v1, v2)
    assert res is not None
    t, u, v = res
    assert pytest.approx(t) == 5.0  # from z=10 to z=5 is 5m
    assert pytest.approx(u) == 0.25
    assert pytest.approx(v) == 0.25


def test_ray_hits_triangle_back_face(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    # Ray origin below the triangle at (0.5, 0.5, 0.0), shooting upwards along +Z
    # Hitting the back face (same direction as +Z normal)
    origin = (0.5, 0.5, 0.0)
    direction = (0.0, 0.0, 1.0)

    # Two-sided evaluation by default
    res = intersect_ray_triangle(origin, direction, v0, v1, v2, cull_backfaces=False)
    assert res is not None
    t, u, v = res
    assert pytest.approx(t) == 5.0

    # With cull_backfaces=True, should be rejected
    res_culled = intersect_ray_triangle(origin, direction, v0, v1, v2, cull_backfaces=True)
    assert res_culled is None


def test_ray_misses_triangle(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    direction = (0.0, 0.0, -1.0)

    # Miss outside hypotenuse (x + y > 2.0)
    res_hyp = intersect_ray_triangle((1.5, 1.5, 10.0), direction, v0, v1, v2)
    assert res_hyp is None

    # Miss outside x=0 (x < 0)
    res_x = intersect_ray_triangle((-0.1, 0.5, 10.0), direction, v0, v1, v2)
    assert res_x is None

    # Miss outside y=0 (y < 0)
    res_y = intersect_ray_triangle((0.5, -0.1, 10.0), direction, v0, v1, v2)
    assert res_y is None


def test_ray_parallel_to_triangle(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    # Ray parallel to XY plane (dz = 0)
    origin = (0.5, 0.5, 10.0)
    direction = (1.0, 0.0, 0.0)

    res = intersect_ray_triangle(origin, direction, v0, v1, v2)
    assert res is None


def test_ray_hits_shared_triangle_edge():
    # Two adjacent triangles sharing the diagonal edge between (1,0,0) and (0,1,0)
    v0 = np.array([0.0, 0.0, 0.0])
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    v3 = np.array([1.0, 1.0, 0.0])

    # Shared edge points: midpoint is (0.5, 0.5, 0.0)
    origin = (0.5, 0.5, 10.0)
    direction = (0.0, 0.0, -1.0)

    # Ray hitting exactly on the shared hypotenuse
    hit_t1 = intersect_ray_triangle(origin, direction, v0, v1, v2)
    hit_t2 = intersect_ray_triangle(origin, direction, v1, v3, v2)

    # With barycentric epsilon tolerance, both should acknowledge hit without seam dropout
    assert hit_t1 is not None or hit_t2 is not None


def test_ray_starting_on_or_near_surface(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    # Ray starting almost on the surface at z = 5.0 + 1e-8 shooting down
    origin = (0.5, 0.5, 5.0 + 1e-8)
    direction = (0.0, 0.0, -1.0)

    # Default eps_origin = 1e-6: hit at 1e-8 should be rejected to prevent self-intersection
    res = intersect_ray_triangle(origin, direction, v0, v1, v2, eps_origin=1e-6)
    assert res is None

    # But with origin at z = 5.0 + 1e-4, hit distance is 1e-4 > 1e-6 -> accepted
    res_valid = intersect_ray_triangle((0.5, 0.5, 5.0 + 1e-4), direction, v0, v1, v2, eps_origin=1e-6)
    assert res_valid is not None


def test_zero_or_nan_direction(canonical_triangle):
    v0, v1, v2 = canonical_triangle
    assert intersect_ray_triangle((0, 0, 10), (0, 0, 0), v0, v1, v2) is None
    assert intersect_ray_triangle((0, 0, 10), (float("nan"), 0, -1), v0, v1, v2) is None


def test_intersect_ray_mesh_nearest_hit():
    # Box from z=0 to z=10
    box = create_box_mesh("box", 0.0, 10.0, 0.0, 10.0, 0.0, 10.0)

    # Ray shooting downwards from z=25 at center (5, 5)
    # Enters top face at z=10 (dist = 15m), exits bottom face at z=0 (dist = 25m)
    origin = (5.0, 5.0, 25.0)
    direction = (0.0, 0.0, -1.0)

    nearest_t = intersect_ray_mesh(origin, direction, box)
    assert nearest_t is not None
    assert pytest.approx(nearest_t) == 15.0  # Closest hit is the top roof face


def test_batch_vs_scalar_ray_mesh_consistency():
    box = create_box_mesh("box", 10.0, 20.0, 10.0, 20.0, 0.0, 15.0)
    direction = (0.0, 0.0, -1.0)

    # Grid of ray origins above the scene
    xs = np.linspace(5.0, 25.0, 21)
    ys = np.linspace(5.0, 25.0, 21)
    X, Y = np.meshgrid(xs, ys)
    origins = np.column_stack([X.flatten(), Y.flatten(), np.full(X.size, 30.0)])

    # Batch intersection
    batch_hits, batch_t = intersect_rays_mesh_batch(origins, direction, box)

    # Scalar intersection for comparison
    scalar_hits = np.zeros(len(origins), dtype=bool)
    scalar_t = np.full(len(origins), np.inf, dtype=np.float64)
    for i, orig in enumerate(origins):
        hit = intersect_ray_mesh(tuple(orig), direction, box)
        if hit is not None:
            scalar_hits[i] = True
            scalar_t[i] = hit

    assert np.array_equal(batch_hits, scalar_hits)
    assert np.allclose(batch_t[batch_hits], scalar_t[scalar_hits], atol=1e-8)


def test_intersect_rays_scene_multiple_meshes():
    mesh1 = create_box_mesh("b1", 10.0, 20.0, 10.0, 20.0, 0.0, 10.0)
    mesh2 = create_box_mesh("b2", 30.0, 40.0, 10.0, 20.0, 0.0, 10.0)

    origins = np.array([
        [15.0, 15.0, 25.0],  # over mesh1
        [35.0, 15.0, 25.0],  # over mesh2
        [25.0, 15.0, 25.0],  # in between (gap)
    ])
    direction = (0.0, 0.0, -1.0)

    hits, t_hits = intersect_rays_scene_meshes(origins, direction, [mesh1, mesh2])
    assert bool(hits[0]) and pytest.approx(t_hits[0]) == 15.0
    assert bool(hits[1]) and pytest.approx(t_hits[1]) == 15.0
    assert not bool(hits[2]) and math.isinf(t_hits[2])
