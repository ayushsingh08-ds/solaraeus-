"""
Incremental geometric edits for triangular meshes.

Supports additions, removals, replacements, movements, and height adjustments
of TriangleMesh objects within the certified incremental recomputation framework.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.geometry.scene import Scene
from urban_comfort.incremental.update import GeometricEdit


@dataclass
class AddMeshEdit(GeometricEdit):
    """Incremental edit adding a new TriangleMesh to the scene."""
    mesh: TriangleMesh

    def __init__(self, mesh: TriangleMesh):
        super().__init__(edit_type="mesh_added")
        self.mesh = mesh

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        new_scene.add_mesh(self.mesh)
        return new_scene, self.mesh.bounds_3d


@dataclass
class RemoveMeshEdit(GeometricEdit):
    """Incremental edit removing an existing TriangleMesh from the scene."""
    mesh_id: str

    def __init__(self, mesh_id: str):
        super().__init__(edit_type="mesh_removed")
        self.mesh_id = mesh_id

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        removed = new_scene.remove_mesh(self.mesh_id)
        return new_scene, removed.bounds_3d


@dataclass
class ReplaceMeshEdit(GeometricEdit):
    """Incremental edit replacing an existing TriangleMesh with a new TriangleMesh."""
    mesh_id: str
    new_mesh: TriangleMesh

    def __init__(self, mesh_id: str, new_mesh: TriangleMesh):
        super().__init__(edit_type="mesh_replaced")
        self.mesh_id = mesh_id
        self.new_mesh = new_mesh

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        old_mesh = new_scene.meshes[self.mesh_id]
        old_b = old_mesh.bounds_3d
        new_b = self.new_mesh.bounds_3d

        new_scene.meshes[self.mesh_id] = self.new_mesh

        union_bounds = (
            min(old_b[0], new_b[0]), max(old_b[1], new_b[1]),
            min(old_b[2], new_b[2]), max(old_b[3], new_b[3]),
            min(old_b[4], new_b[4]), max(old_b[5], new_b[5]),
        )
        return new_scene, union_bounds


@dataclass
class MoveMeshEdit(GeometricEdit):
    """Incremental edit translating all vertices of a TriangleMesh in 3D."""
    mesh_id: str
    shift_x: float
    shift_y: float
    shift_z: float = 0.0

    def __init__(self, mesh_id: str, shift_x: float, shift_y: float, shift_z: float = 0.0):
        super().__init__(edit_type="mesh_moved")
        self.mesh_id = mesh_id
        self.shift_x = shift_x
        self.shift_y = shift_y
        self.shift_z = shift_z

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        old_mesh = new_scene.meshes[self.mesh_id]
        old_b = old_mesh.bounds_3d

        # Clone vertices and translate
        translated_vertices = old_mesh.vertices.copy()
        translated_vertices[:, 0] += self.shift_x
        translated_vertices[:, 1] += self.shift_y
        translated_vertices[:, 2] += self.shift_z

        moved_mesh = TriangleMesh(
            id=old_mesh.id,
            vertices=translated_vertices,
            triangles=old_mesh.triangles.copy(),
            material_id=old_mesh.material_id,
            enabled=old_mesh.enabled,
            metadata=dict(old_mesh.metadata)
        )
        new_scene.meshes[self.mesh_id] = moved_mesh
        new_b = moved_mesh.bounds_3d

        union_bounds = (
            min(old_b[0], new_b[0]), max(old_b[1], new_b[1]),
            min(old_b[2], new_b[2]), max(old_b[3], new_b[3]),
            min(old_b[4], new_b[4]), max(old_b[5], new_b[5]),
        )
        return new_scene, union_bounds


@dataclass
class ChangeMeshHeightEdit(GeometricEdit):
    """Incremental edit scaling the vertical height of a TriangleMesh."""
    mesh_id: str
    new_height: float

    def __init__(self, mesh_id: str, new_height: float):
        super().__init__(edit_type="mesh_height_changed")
        self.mesh_id = mesh_id
        self.new_height = new_height

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        old_mesh = new_scene.meshes[self.mesh_id]
        old_b = old_mesh.bounds_3d
        zmin = old_mesh.zmin
        current_span = max(1e-6, old_mesh.zmax - zmin)
        target_span = max(1e-6, self.new_height - zmin)
        scale_factor = target_span / current_span

        scaled_vertices = old_mesh.vertices.copy()
        scaled_vertices[:, 2] = zmin + (scaled_vertices[:, 2] - zmin) * scale_factor

        scaled_mesh = TriangleMesh(
            id=old_mesh.id,
            vertices=scaled_vertices,
            triangles=old_mesh.triangles.copy(),
            material_id=old_mesh.material_id,
            enabled=old_mesh.enabled,
            metadata=dict(old_mesh.metadata)
        )
        new_scene.meshes[self.mesh_id] = scaled_mesh
        new_b = scaled_mesh.bounds_3d

        diff_bounds = (
            min(old_b[0], new_b[0]), max(old_b[1], new_b[1]),
            min(old_b[2], new_b[2]), max(old_b[3], new_b[3]),
            min(old_b[4], new_b[4]), max(old_b[5], new_b[5]),
        )
        return new_scene, diff_bounds
