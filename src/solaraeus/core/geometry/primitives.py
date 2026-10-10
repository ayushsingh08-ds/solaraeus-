"""
Geometric primitives representing buildings, footprints, and bounding volumes.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass(frozen=True)
class BoundingBox2D:
    """Axis-aligned 2D footprint bounding box in world space (meters)."""
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    def __post_init__(self):
        if self.xmax < self.xmin:
            raise ValueError(f"xmax ({self.xmax}) cannot be less than xmin ({self.xmin})")
        if self.ymax < self.ymin:
            raise ValueError(f"ymax ({self.ymax}) cannot be less than ymin ({self.ymin})")

    @property
    def width_x(self) -> float:
        return self.xmax - self.xmin

    @property
    def width_y(self) -> float:
        return self.ymax - self.ymin

    @property
    def area(self) -> float:
        return self.width_x * self.width_y

    def contains(self, x: float, y: float) -> bool:
        return self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax

    def intersects(self, other: BoundingBox2D) -> bool:
        return not (
            self.xmax < other.xmin or
            self.xmin > other.xmax or
            self.ymax < other.ymin or
            self.ymin > other.ymax
        )


@dataclass
class Building:
    """
    Opaque 3D building represented as an extruded axis-aligned prism.
    """
    id: str
    footprint: BoundingBox2D
    height: float
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (x, y, z_base)
    material_id: str = "default_wall"
    enabled: bool = True

    def __post_init__(self):
        if self.height <= 0.0:
            raise ValueError(f"Building height must be > 0, got {self.height}")

    @property
    def xmin(self) -> float:
        return self.footprint.xmin + self.position[0]

    @property
    def xmax(self) -> float:
        return self.footprint.xmax + self.position[0]

    @property
    def ymin(self) -> float:
        return self.footprint.ymin + self.position[1]

    @property
    def ymax(self) -> float:
        return self.footprint.ymax + self.position[1]

    @property
    def zmin(self) -> float:
        return self.position[2]

    @property
    def zmax(self) -> float:
        return self.position[2] + self.height

    @property
    def bounds_3d(self) -> Tuple[float, float, float, float, float, float]:
        """Returns (xmin, xmax, ymin, ymax, zmin, zmax) in world coordinates."""
        return (self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)

    @property
    def footprint_area(self) -> float:
        return self.footprint.area

    @property
    def volume(self) -> float:
        return self.footprint.area * self.height
