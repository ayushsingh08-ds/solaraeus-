"""
Geometric representation and editing operations for 2.5D urban heightfield models.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np


@dataclass
class EditBoundingBox:
    """Bounding box and physical dimensions of an urban geometry modification."""
    xmin: int
    xmax: int
    ymin: int
    ymax: int
    h_before_max: float
    h_after_max: float
    delta_h_max: float
    footprint_area: float  # In m^2
    width_m: float  # Characteristic spatial width in m

    @property
    def x_slice(self) -> slice:
        return slice(self.xmin, self.xmax + 1)

    @property
    def y_slice(self) -> slice:
        return slice(self.ymin, self.ymax + 1)


class UrbanGrid:
    """
    Represents a 2.5D urban heightfield (Digital Surface Model).
    Pedestrian calculation height is at ground level + z_ped (default 1.1m).
    """

    def __init__(self, heights: np.ndarray, dx: float = 1.0, z_ped: float = 1.1):
        self.heights = np.asarray(heights, dtype=np.float64).copy()
        self.dx = float(dx)
        self.z_ped = float(z_ped)
        self.ny, self.nx = self.heights.shape

    def copy(self) -> "UrbanGrid":
        return UrbanGrid(self.heights.copy(), self.dx, self.z_ped)

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.ny, self.nx)

    @property
    def building_mask(self) -> np.ndarray:
        """Boolean mask where height exceeds threshold indicating a building."""
        return self.heights > 0.5

    def ground_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns physical coordinates (X, Y) in meters for all grid cell centers."""
        x = np.arange(self.nx, dtype=np.float64) * self.dx
        y = np.arange(self.ny, dtype=np.float64) * self.dx
        return np.meshgrid(x, y)

    def apply_edit(self, edit: "GeometricEdit") -> Tuple["UrbanGrid", EditBoundingBox]:
        """Applies a geometric edit and returns the modified grid and edit bounding box."""
        new_grid = self.copy()
        bbox = edit.apply(new_grid, self)
        return new_grid, bbox


class GeometricEdit:
    """Base class for atomic urban geometry edits."""

    def apply(self, target_grid: UrbanGrid, reference_grid: UrbanGrid) -> EditBoundingBox:
        raise NotImplementedError


class AddBuilding(GeometricEdit):
    """Adds a rectangular building with specified height."""

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int, height: float):
        self.xmin = max(0, int(xmin))
        self.xmax = int(xmax)
        self.ymin = max(0, int(ymin))
        self.ymax = int(ymax)
        self.height = float(height)

    def apply(self, target_grid: UrbanGrid, reference_grid: UrbanGrid) -> EditBoundingBox:
        self.xmax = min(target_grid.nx - 1, self.xmax)
        self.ymax = min(target_grid.ny - 1, self.ymax)

        h_before = reference_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1]
        h_before_max = float(np.max(h_before)) if h_before.size > 0 else 0.0

        target_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1] = self.height
        delta_h_max = max(0.0, self.height - h_before_max)

        width_m = max((self.xmax - self.xmin + 1) * target_grid.dx,
                      (self.ymax - self.ymin + 1) * target_grid.dx)
        area_m2 = (self.xmax - self.xmin + 1) * (self.ymax - self.ymin + 1) * (target_grid.dx ** 2)

        return EditBoundingBox(
            xmin=self.xmin, xmax=self.xmax,
            ymin=self.ymin, ymax=self.ymax,
            h_before_max=h_before_max,
            h_after_max=self.height,
            delta_h_max=delta_h_max,
            footprint_area=area_m2,
            width_m=width_m
        )


class RemoveBuilding(GeometricEdit):
    """Removes a building footprint, resetting height to ground (0.0)."""

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int):
        self.xmin = max(0, int(xmin))
        self.xmax = int(xmax)
        self.ymin = max(0, int(ymin))
        self.ymax = int(ymax)

    def apply(self, target_grid: UrbanGrid, reference_grid: UrbanGrid) -> EditBoundingBox:
        self.xmax = min(target_grid.nx - 1, self.xmax)
        self.ymax = min(target_grid.ny - 1, self.ymax)

        h_before = reference_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1]
        h_before_max = float(np.max(h_before)) if h_before.size > 0 else 0.0

        target_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1] = 0.0
        delta_h_max = h_before_max

        width_m = max((self.xmax - self.xmin + 1) * target_grid.dx,
                      (self.ymax - self.ymin + 1) * target_grid.dx)
        area_m2 = (self.xmax - self.xmin + 1) * (self.ymax - self.ymin + 1) * (target_grid.dx ** 2)

        return EditBoundingBox(
            xmin=self.xmin, xmax=self.xmax,
            ymin=self.ymin, ymax=self.ymax,
            h_before_max=h_before_max,
            h_after_max=0.0,
            delta_h_max=delta_h_max,
            footprint_area=area_m2,
            width_m=width_m
        )


class ChangeHeight(GeometricEdit):
    """Changes building height within a footprint."""

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int, new_height: float):
        self.xmin = max(0, int(xmin))
        self.xmax = int(xmax)
        self.ymin = max(0, int(ymin))
        self.ymax = int(ymax)
        self.new_height = float(new_height)

    def apply(self, target_grid: UrbanGrid, reference_grid: UrbanGrid) -> EditBoundingBox:
        self.xmax = min(target_grid.nx - 1, self.xmax)
        self.ymax = min(target_grid.ny - 1, self.ymax)

        h_before = reference_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1]
        h_before_max = float(np.max(h_before)) if h_before.size > 0 else 0.0

        target_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1] = self.new_height
        delta_h_max = abs(self.new_height - h_before_max)

        width_m = max((self.xmax - self.xmin + 1) * target_grid.dx,
                      (self.ymax - self.ymin + 1) * target_grid.dx)
        area_m2 = (self.xmax - self.xmin + 1) * (self.ymax - self.ymin + 1) * (target_grid.dx ** 2)

        return EditBoundingBox(
            xmin=self.xmin, xmax=self.xmax,
            ymin=self.ymin, ymax=self.ymax,
            h_before_max=h_before_max,
            h_after_max=self.new_height,
            delta_h_max=delta_h_max,
            footprint_area=area_m2,
            width_m=width_m
        )


class MoveBuilding(GeometricEdit):
    """Moves a building from (xmin, xmax, ymin, ymax) by (shift_x, shift_y) cells."""

    def __init__(self, xmin: int, xmax: int, ymin: int, ymax: int, shift_x: int, shift_y: int):
        self.xmin = int(xmin)
        self.xmax = int(xmax)
        self.ymin = int(ymin)
        self.ymax = int(ymax)
        self.shift_x = int(shift_x)
        self.shift_y = int(shift_y)

    def apply(self, target_grid: UrbanGrid, reference_grid: UrbanGrid) -> EditBoundingBox:
        source_h = reference_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1].copy()
        h_max = float(np.max(source_h)) if source_h.size > 0 else 0.0

        # Erase source
        target_grid.heights[self.ymin:self.ymax + 1, self.xmin:self.xmax + 1] = 0.0

        # Place at destination
        dst_xmin = max(0, min(target_grid.nx - 1, self.xmin + self.shift_x))
        dst_xmax = max(0, min(target_grid.nx - 1, self.xmax + self.shift_x))
        dst_ymin = max(0, min(target_grid.ny - 1, self.ymin + self.shift_y))
        dst_ymax = max(0, min(target_grid.ny - 1, self.ymax + self.shift_y))

        # Size of valid placed slice
        src_w = min(source_h.shape[1], dst_xmax - dst_xmin + 1)
        src_h_len = min(source_h.shape[0], dst_ymax - dst_ymin + 1)
        target_grid.heights[dst_ymin:dst_ymin + src_h_len, dst_xmin:dst_xmin + src_w] = source_h[:src_h_len, :src_w]

        # Encompassing bounding box covering both source and destination
        union_xmin = min(self.xmin, dst_xmin)
        union_xmax = max(self.xmax, dst_xmax)
        union_ymin = min(self.ymin, dst_ymin)
        union_ymax = max(self.ymax, dst_ymax)

        width_m = max((union_xmax - union_xmin + 1) * target_grid.dx,
                      (union_ymax - union_ymin + 1) * target_grid.dx)
        area_m2 = (union_xmax - union_xmin + 1) * (union_ymax - union_ymin + 1) * (target_grid.dx ** 2)

        return EditBoundingBox(
            xmin=union_xmin, xmax=union_xmax,
            ymin=union_ymin, ymax=union_ymax,
            h_before_max=h_max,
            h_after_max=h_max,
            delta_h_max=h_max,
            footprint_area=area_m2,
            width_m=width_m
        )
