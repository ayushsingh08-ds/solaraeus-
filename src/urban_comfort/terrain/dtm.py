"""
Digital Terrain Model (DTM) representations and spatial interpolation utilities.
Part of SOLARAEUS 2.1.0-cpu-terrain extension.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any
import numpy as np

from urban_comfort.geometry.primitives import BoundingBox2D


@dataclass
class TerrainGrid:
    """
    Regular raster representation of digital terrain elevation.
    Coordinate conventions:
      - X corresponds to Easting (metres)
      - Y corresponds to Northing (metres)
      - Z corresponds to Elevation above datum (metres)
    """
    elevation: np.ndarray                      # 2D array [ny, nx] in float64
    bounds: BoundingBox2D                      # Spatial extents [xmin, xmax, ymin, ymax]
    crs: str = "EPSG:32643"                    # Coordinate Reference System
    vertical_datum: str = "MSL"                # Vertical datum (Orthometric)
    nodata_value: float = -9999.0              # Explicit NoData sentinel
    nodata_mask: Optional[np.ndarray] = None   # Boolean mask [ny, nx] where True = NoData / Invalid

    def __post_init__(self):
        self.elevation = np.asarray(self.elevation, dtype=np.float64)
        if self.elevation.ndim != 2:
            raise ValueError(f"Elevation array must be 2D, got shape {self.elevation.shape}")
        
        # Build nodata mask
        is_nodata_val = np.isclose(self.elevation, self.nodata_value)
        is_nan = np.isnan(self.elevation)
        auto_mask = is_nodata_val | is_nan
        if self.nodata_mask is None:
            self.nodata_mask = auto_mask
        else:
            self.nodata_mask = np.asarray(self.nodata_mask, dtype=bool) | auto_mask

        self.ny, self.nx = self.elevation.shape
        self.dx = (self.bounds.xmax - self.bounds.xmin) / max(1, self.nx - 1)
        self.dy = (self.bounds.ymax - self.bounds.ymin) / max(1, self.ny - 1)

    @classmethod
    def create_flat(cls, bounds: BoundingBox2D, elevation_val: float = 0.0,
                    nx: int = 100, ny: int = 100, crs: str = "EPSG:32643") -> "TerrainGrid":
        """Creates a perfectly flat planar terrain."""
        elev = np.full((ny, nx), elevation_val, dtype=np.float64)
        return cls(elevation=elev, bounds=bounds, crs=crs)

    @classmethod
    def create_inclined(cls, bounds: BoundingBox2D, base_elevation: float = 0.0,
                        slope_x: float = 0.03, slope_y: float = 0.0,
                        nx: int = 100, ny: int = 100, crs: str = "EPSG:32643") -> "TerrainGrid":
        """Creates a planar inclined slope: z(x, y) = base_elev + slope_x*(x - xmin) + slope_y*(y - ymin)."""
        x = np.linspace(bounds.xmin, bounds.xmax, nx)
        y = np.linspace(bounds.ymin, bounds.ymax, ny)
        X, Y = np.meshgrid(x, y)
        elev = base_elevation + slope_x * (X - bounds.xmin) + slope_y * (Y - bounds.ymin)
        return cls(elevation=elev, bounds=bounds, crs=crs)

    @classmethod
    def create_stepped(cls, bounds: BoundingBox2D, step_x: float, step_height_m: float = 0.15,
                       nx: int = 100, ny: int = 100, crs: str = "EPSG:32643") -> "TerrainGrid":
        """Creates a stepped terrace representing a curb or plinth."""
        x = np.linspace(bounds.xmin, bounds.xmax, nx)
        y = np.linspace(bounds.ymin, bounds.ymax, ny)
        X, Y = np.meshgrid(x, y)
        elev = np.where(X >= step_x, step_height_m, 0.0).astype(np.float64)
        return cls(elevation=elev, bounds=bounds, crs=crs)

    @classmethod
    def create_with_nodata(cls, bounds: BoundingBox2D, hole_bounds: BoundingBox2D,
                           nx: int = 100, ny: int = 100, crs: str = "EPSG:32643") -> "TerrainGrid":
        """Creates a flat terrain with an internal NoData hole for robust boundary testing."""
        grid = cls.create_flat(bounds, elevation_val=10.0, nx=nx, ny=ny, crs=crs)
        x = np.linspace(bounds.xmin, bounds.xmax, nx)
        y = np.linspace(bounds.ymin, bounds.ymax, ny)
        X, Y = np.meshgrid(x, y)
        in_hole = (X >= hole_bounds.xmin) & (X <= hole_bounds.xmax) & (Y >= hole_bounds.ymin) & (Y <= hole_bounds.ymax)
        grid.elevation[in_hole] = grid.nodata_value
        grid.nodata_mask[in_hole] = True
        return grid

    def sample_elevation(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Bilinearly samples elevation at continuous world coordinates (x, y).
        Returns:
            elevation: sampled z elevation array (np.nan where out-of-bounds or nodata)
            valid_mask: boolean mask indicating valid points
        """
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)

        in_bounds = (
            (x_arr >= self.bounds.xmin) & (x_arr <= self.bounds.xmax) &
            (y_arr >= self.bounds.ymin) & (y_arr <= self.bounds.ymax)
        )

        # Normalized coordinates [0, nx-1] and [0, ny-1]
        gx = np.clip((x_arr - self.bounds.xmin) / max(1e-9, self.dx), 0, self.nx - 1)
        gy = np.clip((y_arr - self.bounds.ymin) / max(1e-9, self.dy), 0, self.ny - 1)

        ix0 = np.floor(gx).astype(np.int64)
        iy0 = np.floor(gy).astype(np.int64)
        ix1 = np.clip(ix0 + 1, 0, self.nx - 1)
        iy1 = np.clip(iy0 + 1, 0, self.ny - 1)

        wx = gx - ix0
        wy = gy - iy0

        z00 = self.elevation[iy0, ix0]
        z10 = self.elevation[iy0, ix1]
        z01 = self.elevation[iy1, ix0]
        z11 = self.elevation[iy1, ix1]

        m00 = self.nodata_mask[iy0, ix0]
        m10 = self.nodata_mask[iy0, ix1]
        m01 = self.nodata_mask[iy1, ix0]
        m11 = self.nodata_mask[iy1, ix1]
        any_nodata = m00 | m10 | m01 | m11

        z_interp = (
            (1.0 - wx) * (1.0 - wy) * z00 +
            wx * (1.0 - wy) * z10 +
            (1.0 - wx) * wy * z01 +
            wx * wy * z11
        )

        valid_mask = in_bounds & (~any_nodata)
        z_out = np.where(valid_mask, z_interp, np.nan)
        return z_out, valid_mask

    def compute_surface_normals(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Computes 3D unit surface normals (nx, ny, nz) using Horn's central differences.
        """
        dz_dx = np.gradient(self.elevation, self.dx, axis=1)
        dz_dy = np.gradient(self.elevation, self.dy, axis=0)
        
        # Upward surface normal (-dz/dx, -dz/dy, 1.0) normalized
        nx = -dz_dx
        ny = -dz_dy
        nz = np.ones_like(dz_dx)
        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        return nx / norm, ny / norm, nz / norm
