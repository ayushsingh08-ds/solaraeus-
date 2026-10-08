"""
SOLARAEUS Tree-Aware Scene Representation (API Version 2.2.0-tree).
Extends TerrainAwareScene with provisional Level 1 tree objects.
Maintains 100% backward compatibility with flat-ground and terrain scenes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from urban_comfort.geometry.primitives import Building
from urban_comfort.geometry.scene import Scene
from urban_comfort.terrain.dtm import TerrainGrid
from urban_comfort.terrain.terrain_scene import TerrainAwareScene
from urban_comfort.vegetation.tree import Tree


@dataclass
class TreeAwareScene:
    """
    Extends TerrainAwareScene with provisional Level 1 Tree geometries.
    """
    terrain_scene: TerrainAwareScene
    trees: List[Tree] = field(default_factory=list)
    version: str = "2.2.0-tree"

    @classmethod
    def from_base_scene(
        cls,
        base_scene: Scene,
        terrain: Optional[TerrainGrid] = None,
        trees: Optional[List[Tree]] = None,
    ) -> TreeAwareScene:
        t_scene = TerrainAwareScene(base_scene=base_scene, terrain=terrain)
        return cls(terrain_scene=t_scene, trees=trees or [])

    @property
    def base_scene(self) -> Scene:
        return self.terrain_scene.base_scene

    @property
    def terrain(self) -> Optional[TerrainGrid]:
        return self.terrain_scene.terrain

    @property
    def buildings(self) -> List[Building]:
        return self.terrain_scene.buildings

    @property
    def materials(self) -> Dict[str, Any]:
        return self.terrain_scene.materials

    @property
    def pedestrian_grid(self) -> Any:
        return self.terrain_scene.pedestrian_grid

    def get_active_buildings(self) -> List[Building]:
        return self.terrain_scene.get_active_buildings()

    def has_terrain(self) -> bool:
        return self.terrain_scene.has_terrain()

    def has_trees(self) -> bool:
        return len(self.trees) > 0

    def add_tree(self, tree: Tree):
        self.trees.append(tree)

    def remove_tree(self, tree_id: str):
        self.trees = [t for t in self.trees if t.tree_id != tree_id]

    def get_tree(self, tree_id: str) -> Optional[Tree]:
        for t in self.trees:
            if t.tree_id == tree_id:
                return t
        return None

    def clone(self) -> TreeAwareScene:
        return TreeAwareScene(
            terrain_scene=TerrainAwareScene(
                base_scene=self.base_scene,
                terrain=self.terrain,
            ),
            trees=list(self.trees),
            version=self.version,
        )
