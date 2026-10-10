"""
SOLARAEUS Vegetation & Tree Modeling Module (API Version 2.2.0-tree).
"""

from solaraeus.extensions.vegetation.tree import Tree, get_core_trees
from solaraeus.extensions.vegetation.scene import TreeAwareScene
from solaraeus.extensions.vegetation.solver import TreeAwareCPUSolver
from solaraeus.extensions.vegetation.gpu import TreeAwareGPUBackend

__all__ = [
    "Tree",
    "get_core_trees",
    "TreeAwareScene",
    "TreeAwareCPUSolver",
    "TreeAwareGPUBackend",
]
