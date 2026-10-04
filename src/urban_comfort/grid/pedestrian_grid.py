"""
Pedestrian calculation grid representation and spatial coordinate mapping.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

from urban_comfort.geometry.scene import PedestrianGridConfig


class PedestrianGrid:
    """
    Structured regular pedestrian calculation grid.
    Receptors are situated at ground-relative pedestrian height (z_ped = 1.1m).
    """

    def __init__(self, config: PedestrianGridConfig):
        self.config = config
        self.nx = config.nx
        self.ny = config.ny
        self.dx = config.resolution
        self.z_ped = config.pedestrian_height
        self.origin_x = config.origin_x
        self.origin_y = config.origin_y

        # 1D coordinate vectors representing cell centers
        self.x_coords = self.origin_x + (np.arange(self.nx, dtype=np.float64) + 0.5) * self.dx
        self.y_coords = self.origin_y + (np.arange(self.ny, dtype=np.float64) + 0.5) * self.dx

        # 2D coordinate meshgrids
        self.X, self.Y = np.meshgrid(self.x_coords, self.y_coords)
        self.Z = np.full_like(self.X, self.z_ped)

    @property
    def shape(self) -> Tuple[int, int]:
        """Returns (ny, nx) shape of the grid."""
        return (self.ny, self.nx)

    @property
    def total_cells(self) -> int:
        return self.ny * self.nx

    def linear_to_2d(self, linear_idx: int) -> Tuple[int, int]:
        """Maps 1D flat cell index to 2D matrix indices (iy, ix)."""
        if not (0 <= linear_idx < self.total_cells):
            raise IndexError(f"Linear index {linear_idx} out of range [0, {self.total_cells}).")
        iy = linear_idx // self.nx
        ix = linear_idx % self.nx
        return (iy, ix)

    def coords_2d_to_linear(self, iy: int, ix: int) -> int:
        """Maps 2D matrix indices (iy, ix) to 1D flat cell index."""
        if not (0 <= iy < self.ny and 0 <= ix < self.nx):
            raise IndexError(f"Coordinates ({iy}, {ix}) out of range (ny={self.ny}, nx={self.nx}).")
        return iy * self.nx + ix

    def world_to_cell(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        """Maps continuous world-space coordinates (x, y) to discrete grid indices (iy, ix)."""
        ix = int(np.floor((x - self.origin_x) / self.dx))
        iy = int(np.floor((y - self.origin_y) / self.dx))
        if 0 <= ix < self.nx and 0 <= iy < self.ny:
            return (iy, ix)
        return None

    def cell_to_world(self, iy: int, ix: int) -> Tuple[float, float, float]:
        """Returns world-space (x, y, z) center coordinate of cell (iy, ix)."""
        if not (0 <= iy < self.ny and 0 <= ix < self.nx):
            raise IndexError(f"Cell indices ({iy}, {ix}) out of grid boundaries.")
        return (float(self.x_coords[ix]), float(self.y_coords[iy]), float(self.z_ped))

    def bounding_box_slices(self, xmin: float, xmax: float,
                            ymin: float, ymax: float) -> Tuple[slice, slice]:
        """
        Computes clamped index slices (slice_y, slice_x) covering a world-space bounding box.
        """
        ix_min = max(0, int(np.floor((xmin - self.origin_x) / self.dx)))
        ix_max = min(self.nx - 1, int(np.floor((xmax - self.origin_x) / self.dx)))
        iy_min = max(0, int(np.floor((ymin - self.origin_y) / self.dx)))
        iy_max = min(self.ny - 1, int(np.floor((ymax - self.origin_y) / self.dx)))

        return (slice(iy_min, iy_max + 1), slice(ix_min, ix_max + 1))

    def get_flat_points(self) -> np.ndarray:
        """Returns array of shape (N_cells, 3) containing all (x, y, z) receptor points."""
        return np.column_stack([self.X.ravel(), self.Y.ravel(), self.Z.ravel()])
