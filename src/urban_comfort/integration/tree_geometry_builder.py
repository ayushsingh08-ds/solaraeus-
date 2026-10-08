"""
Authoritative 3D Tree Geometry Builder for SOLARAEUS.

Constructs 3D meshes (trunks and canopies) for municipal trees,
anchoring trunk bases to sampled terrain elevation.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import trimesh

from urban_comfort.integration.tree_loader import TreeRecord, tree_loader
from urban_comfort.integration.terrain_loader import terrain_loader


class TreeGeometryBuilder:
    """Constructs 3D geometric meshes for trees across uncertainty states."""

    def __init__(self):
        pass

    def build_tree_mesh(
        self,
        tree: TreeRecord,
        uncertainty_state: str = "nominal",
        terrain_profile: str = "flat",
    ) -> trimesh.Trimesh:
        """
        Build a combined trunk and crown mesh for a given tree in local Cartesian coordinates.
        uncertainty_state: 'small', 'nominal', 'large'
        """
        state_key = uncertainty_state.lower()
        if state_key not in ["small", "nominal", "large"]:
            state_key = "nominal"

        height = tree.height_bounds.get(state_key, tree.height_bounds["nominal"])
        crown_diam = tree.crown_diameter_bounds.get(
            state_key, tree.crown_diameter_bounds["nominal"]
        )
        crown_base_h = tree.crown_base_height_bounds.get(
            state_key, tree.crown_base_height_bounds["nominal"]
        )

        trunk_r = tree.trunk_radius
        crown_r_x = crown_diam / 2.0
        crown_r_y = crown_diam / 2.0
        crown_r_z = max(0.5, (height - crown_base_h) / 2.0)

        # 1. Sample terrain elevation at tree base
        base_z = terrain_loader.sample_elevation(
            tree.local_x, tree.local_y, terrain_profile
        )

        # 2. Build Trunk (Cylinder)
        trunk_height = crown_base_h
        trunk_center_z = base_z + trunk_height / 2.0
        trunk_mesh = trimesh.creation.cylinder(
            radius=trunk_r, height=trunk_height, sections=16
        )
        trunk_mesh.apply_translation([tree.local_x, tree.local_y, trunk_center_z])

        # 3. Build Crown (Ellipsoid)
        crown_center_z = base_z + crown_base_h + crown_r_z
        crown_mesh = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        # Scale to semi-axes
        crown_mesh.apply_scale([crown_r_x, crown_r_y, crown_r_z])
        crown_mesh.apply_translation([tree.local_x, tree.local_y, crown_center_z])

        # 4. Combine meshes
        combined = trimesh.util.concatenate([trunk_mesh, crown_mesh])
        combined.metadata["tree_id"] = tree.tree_id
        combined.metadata["species"] = tree.species
        combined.metadata["uncertainty_state"] = state_key
        combined.metadata["physics_participation"] = "PHYSICAL"
        return combined

    def build_forest_scene(
        self,
        trees: Optional[List[TreeRecord]] = None,
        uncertainty_state: str = "nominal",
        terrain_profile: str = "flat",
    ) -> trimesh.Scene:
        """Build a unified trimesh Scene of all trees."""
        if trees is None:
            trees = tree_loader.get_core_trees()

        scene = trimesh.Scene()
        for t in trees:
            mesh = self.build_tree_mesh(t, uncertainty_state, terrain_profile)
            scene.add_geometry(mesh, node_name=f"tree_{t.tree_id}")

        return scene


tree_geometry_builder = TreeGeometryBuilder()
