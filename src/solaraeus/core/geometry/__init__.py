"""
Geometry subpackage for urban scenes, building primitives, and footprints.
"""

from solaraeus.core.geometry.primitives import BoundingBox2D, Building
from solaraeus.core.geometry.scene import (
    Scene, GroundPlane, PedestrianGridConfig,
    create_single_box_scene, create_canyon_scene, create_occlusion_scene
)

__all__ = [
    "BoundingBox2D",
    "Building",
    "Scene",
    "GroundPlane",
    "PedestrianGridConfig",
    "create_single_box_scene",
    "create_canyon_scene",
    "create_occlusion_scene",
]
