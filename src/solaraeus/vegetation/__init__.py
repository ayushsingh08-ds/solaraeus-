"""
SOLARAEUS Vegetation & Tree Modeling Module (API Version 2.2.0-tree).
"""

from solaraeus.vegetation.tree import Tree, get_core_trees
from solaraeus.vegetation.tree_scene import TreeAwareScene
from solaraeus.vegetation.tree_solver import TreeAwareCPUSolver
from solaraeus.vegetation.gpu_tree import TreeAwareGPUBackend

__all__ = [
    "Tree",
    "get_core_trees",
    "TreeAwareScene",
    "TreeAwareCPUSolver",
    "TreeAwareGPUBackend",
]
