"""
SOLARAEUS Vegetation & Tree Modeling Module (API Version 2.2.0-tree).
"""

from urban_comfort.vegetation.tree import Tree, get_core_trees
from urban_comfort.vegetation.tree_scene import TreeAwareScene
from urban_comfort.vegetation.tree_solver import TreeAwareCPUSolver
from urban_comfort.vegetation.gpu_tree import TreeAwareGPUBackend

__all__ = [
    "Tree",
    "get_core_trees",
    "TreeAwareScene",
    "TreeAwareCPUSolver",
    "TreeAwareGPUBackend",
]
