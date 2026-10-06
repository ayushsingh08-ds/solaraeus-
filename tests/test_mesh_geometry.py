"""
Unit tests for TriangleMesh data structure, geometric validation, and synthetic constructors.
"""

from __future__ import annotations
import math
import pytest
import numpy as np

from urban_comfort.geometry.mesh import (
    TriangleMesh,
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_overhang_mesh,
    create_wall_mesh,
    create_l_shaped_mesh
)
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D


def test_triangle_mesh_valid_construction():
    # Single triangle in XY plane
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tris = np.array([[0, 1, 2]])
    mesh = TriangleMesh(id="tri_0", vertices=verts, triangles=tris)

    assert mesh.num_vertices == 3
    assert mesh.num_triangles == 1
    assert mesh.xmin == 0.0 and mesh.xmax == 1.0
    assert mesh.ymin == 0.0 and mesh.ymax == 1.0
    assert mesh.zmin == 0.0 and mesh.zmax == 0.0
    assert mesh.bounds_3d == (0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
    assert mesh.footprint_bounds_2d == (0.0, 1.0, 0.0, 1.0)
    assert pytest.approx(mesh.total_surface_area) == 0.5
    # Normal should point in +Z direction
    assert np.allclose(mesh.face_normals[0], [0.0, 0.0, 1.0])


def test_triangle_mesh_invalid_vertex_shapes():
    # Only 2 vertices
    with pytest.raises(ValueError, match="at least 3 vertices"):
        TriangleMesh(id="m", vertices=np.zeros((2, 3)), triangles=np.zeros((1, 3), dtype=int))

    # 2D vertices instead of 3D
    with pytest.raises(ValueError, match="shape \\(N, 3\\)"):
        TriangleMesh(id="m", vertices=np.zeros((4, 2)), triangles=np.zeros((1, 3), dtype=int))


def test_triangle_mesh_invalid_triangle_shapes():
    verts = np.zeros((4, 3))
    # 0 triangles
    with pytest.raises(ValueError, match="at least 1 triangle"):
        TriangleMesh(id="m", vertices=verts, triangles=np.zeros((0, 3), dtype=int))

    # Quad faces instead of triangles
    with pytest.raises(ValueError, match="shape \\(M, 3\\)"):
        TriangleMesh(id="m", vertices=verts, triangles=np.zeros((2, 4), dtype=int))


def test_triangle_mesh_non_finite_coordinates():
    verts = np.array([[0.0, 0.0, 0.0], [1.0, float("nan"), 0.0], [0.0, 1.0, 0.0]])
    tris = np.array([[0, 1, 2]])
    with pytest.raises(ValueError, match="finite"):
        TriangleMesh(id="m", vertices=verts, triangles=tris)


def test_triangle_mesh_out_of_bounds_indices():
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    # Index 3 does not exist for 3 vertices
    with pytest.raises(ValueError, match="out of bounds"):
        TriangleMesh(id="m", vertices=verts, triangles=np.array([[0, 1, 3]]))

    # Negative index
    with pytest.raises(ValueError, match="out of bounds"):
        TriangleMesh(id="m", vertices=verts, triangles=np.array([[0, -1, 2]]))


def test_triangle_mesh_duplicate_indices_in_triangle():
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    with pytest.raises(ValueError, match="duplicate vertex indices"):
        TriangleMesh(id="m", vertices=verts, triangles=np.array([[0, 0, 1]]))


def test_triangle_mesh_degenerate_collinear_vertices():
    # 3 collinear points
    verts = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="zero surface area"):
        TriangleMesh(id="m", vertices=verts, triangles=np.array([[0, 1, 2]]))


def test_create_box_mesh():
    box = create_box_mesh("box_1", 10.0, 20.0, 30.0, 50.0, 0.0, 15.0)
    assert box.num_vertices == 8
    assert box.num_triangles == 12
    assert box.bounds_3d == (10.0, 20.0, 30.0, 50.0, 0.0, 15.0)

    # Surface area: 2 * (10*20 + 10*15 + 20*15) = 2 * (200 + 150 + 300) = 1300 m^2
    expected_area = 2.0 * (10.0 * 20.0 + 10.0 * 15.0 + 20.0 * 15.0)
    assert pytest.approx(box.total_surface_area) == expected_area


def test_create_rotated_box_mesh():
    # Square 10x10 rotated by 45 degrees
    rbox = create_rotated_box_mesh(
        "rbox", center_x=50.0, center_y=50.0,
        width_x=10.0, width_y=10.0, height=20.0,
        angle_deg=45.0
    )
    assert rbox.num_vertices == 8
    assert rbox.num_triangles == 12

    # A square of diagonal 10*sqrt(2) ~ 14.142m centered at 50,50
    half_diag = 5.0 * math.sqrt(2.0)
    assert pytest.approx(rbox.xmin) == 50.0 - half_diag
    assert pytest.approx(rbox.xmax) == 50.0 + half_diag
    assert pytest.approx(rbox.ymin) == 50.0 - half_diag
    assert pytest.approx(rbox.ymax) == 50.0 + half_diag
    assert rbox.zmin == 0.0 and rbox.zmax == 20.0

    # Total surface area is invariant under rotation
    expected_area = 2.0 * (10.0 * 10.0 + 10.0 * 20.0 + 10.0 * 20.0)
    assert pytest.approx(rbox.total_surface_area) == expected_area


def test_create_pitched_roof_mesh():
    # Ridge parallel to X
    pitch_x = create_pitched_roof_mesh(
        "pitch_x", xmin=10.0, xmax=30.0, ymin=10.0, ymax=20.0,
        eave_height=12.0, ridge_height=18.0, ridge_orientation="x"
    )
    assert pitch_x.num_vertices == 10
    assert pitch_x.num_triangles == 16
    assert pitch_x.bounds_3d == (10.0, 30.0, 10.0, 20.0, 0.0, 18.0)

    # Ridge parallel to Y
    pitch_y = create_pitched_roof_mesh(
        "pitch_y", xmin=10.0, xmax=30.0, ymin=10.0, ymax=20.0,
        eave_height=12.0, ridge_height=18.0, ridge_orientation="y"
    )
    assert pitch_y.num_vertices == 10
    assert pitch_y.num_triangles == 16
    assert pitch_y.bounds_3d == (10.0, 30.0, 10.0, 20.0, 0.0, 18.0)

    # Error if ridge height <= eave height
    with pytest.raises(ValueError, match="must be greater than"):
        create_pitched_roof_mesh("p_bad", 0, 10, 0, 10, eave_height=15.0, ridge_height=15.0)


def test_create_overhang_mesh():
    overhang = create_overhang_mesh(
        "oh", xmin=20.0, xmax=40.0, ymin=20.0, ymax=40.0,
        base_height=16.0, overhang_depth=6.0, overhang_direction="north"
    )
    assert overhang.num_vertices == 16
    assert overhang.num_triangles == 24
    assert overhang.xmin == 20.0 and overhang.xmax == 40.0
    assert overhang.ymin == 20.0 and overhang.ymax == 46.0  # extended by 6m to the north
    assert overhang.zmin == 0.0 and overhang.zmax == 16.0

    with pytest.raises(ValueError, match="strictly less than"):
        create_overhang_mesh("oh_bad", 0, 10, 0, 10, base_height=10.0, overhang_depth=2.0, overhang_thickness=12.0)


def test_create_wall_mesh():
    # 45-degree diagonal wall
    wall = create_wall_mesh(
        "diag_wall", start_pt=(10.0, 10.0), end_pt=(20.0, 20.0),
        thickness=0.5, height=8.0
    )
    assert wall.num_vertices == 8
    assert wall.num_triangles == 12
    assert wall.zmin == 0.0 and wall.zmax == 8.0
    assert wall.xmin < 10.0 and wall.xmax > 20.0  # due to thickness


def test_create_l_shaped_mesh():
    l_mesh = create_l_shaped_mesh(
        "l_bldg", xmin=10.0, ymin=10.0,
        total_width=30.0, total_length=40.0,
        wing_width=12.0, wing_length=15.0,
        height=22.0
    )
    assert l_mesh.num_vertices == 12
    assert l_mesh.num_triangles == 20
    assert l_mesh.bounds_3d == (10.0, 40.0, 10.0, 50.0, 0.0, 22.0)

    with pytest.raises(ValueError, match="wing_width"):
        create_l_shaped_mesh("l_bad", 0, 0, 20, 20, wing_width=25, wing_length=10, height=10)


def test_scene_mesh_integration_and_serialization():
    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=80.0, extent_y=80.0))
    # Add regular AABB building
    bldg = Building(id="bldg_1", footprint=BoundingBox2D(10, 20, 10, 20), height=15.0)
    scene.add_building(bldg)

    # Add triangular mesh
    mesh = create_box_mesh("mesh_1", 30.0, 40.0, 30.0, 40.0, 0.0, 18.0)
    scene.add_mesh(mesh)

    assert len(scene.get_active_buildings()) == 1
    assert len(scene.get_active_meshes()) == 1

    # Serialization round-trip
    data = scene.to_dict()
    assert "meshes" in data
    assert len(data["meshes"]) == 1
    assert data["meshes"][0]["id"] == "mesh_1"

    rebuilt = Scene.from_dict(data)
    assert "mesh_1" in rebuilt.meshes
    assert rebuilt.meshes["mesh_1"].bounds_3d == (30.0, 40.0, 30.0, 40.0, 0.0, 18.0)
    assert len(rebuilt.get_active_buildings()) == 1

    # Test removing mesh
    removed = rebuilt.remove_mesh("mesh_1")
    assert removed.id == "mesh_1"
    assert len(rebuilt.get_active_meshes()) == 0
