"""
General coordinate transformation system for SOLARAEUS.

Provides strict, reversible transformations between:
- Geographic Coordinates: WGS84 (EPSG:4326) [Longitude, Latitude]
- Projected Metric Coordinates (UTM or local National Grids)
- Local Project Cartesian Coordinates [X (East, m), Y (North, m), Z (Up, m)]
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple
import numpy as np
from pyproj import Transformer


@dataclass(frozen=True)
class CoordinateSystemDefinition:
    source_crs: str = "EPSG:4326"
    projected_crs: str = "EPSG:25833"  # Default Berlin ETRS89 / UTM zone 33N
    utm_zone: str = "33N"
    local_origin_x: float = 389000.0
    local_origin_y: float = 5819000.0
    local_origin_z: float = 0.0
    grid_convergence_deg: float = 0.0
    vertical_datum: str = "DHHN2016"
    units: str = "meters"
    axis_orientation: str = "X_EAST_Y_NORTH_Z_UP"


class CoordinateTransformer:
    """General coordinator for spatial transformations in SOLARAEUS."""

    def __init__(self, definition: Optional[CoordinateSystemDefinition] = None):
        self.def_ = definition or CoordinateSystemDefinition()
        self.geo_to_utm_trans = Transformer.from_crs(
            self.def_.source_crs, self.def_.projected_crs, always_xy=True
        )
        self.utm_to_geo_trans = Transformer.from_crs(
            self.def_.projected_crs, self.def_.source_crs, always_xy=True
        )

    def geo_to_utm(self, lon: float, lat: float) -> Tuple[float, float]:
        """Convert WGS84 (lon, lat) to projected metric coordinates."""
        utm_x, utm_y = self.geo_to_utm_trans.transform(lon, lat)
        return float(utm_x), float(utm_y)

    def utm_to_geo(self, utm_x: float, utm_y: float) -> Tuple[float, float]:
        """Convert projected metric coordinates to WGS84 (lon, lat)."""
        lon, lat = self.utm_to_geo_trans.transform(utm_x, utm_y)
        return float(lon), float(lat)

    def utm_to_local(self, utm_x: float, utm_y: float, utm_z: float = 0.0) -> Tuple[float, float, float]:
        """Convert projected meters to local Cartesian meters."""
        loc_x = utm_x - self.def_.local_origin_x
        loc_y = utm_y - self.def_.local_origin_y
        loc_z = utm_z - self.def_.local_origin_z
        return float(loc_x), float(loc_y), float(loc_z)

    def local_to_utm(self, loc_x: float, loc_y: float, loc_z: float = 0.0) -> Tuple[float, float, float]:
        """Convert local Cartesian meters to projected meters."""
        utm_x = loc_x + self.def_.local_origin_x
        utm_y = loc_y + self.def_.local_origin_y
        utm_z = loc_z + self.def_.local_origin_z
        return float(utm_x), float(utm_y), float(utm_z)

    def geo_to_local(self, lon: float, lat: float, elevation: float = 0.0) -> Tuple[float, float, float]:
        """Direct transformation from WGS84 to local Cartesian coordinates."""
        utm_x, utm_y = self.geo_to_utm(lon, lat)
        return self.utm_to_local(utm_x, utm_y, elevation)

    def local_to_geo(self, loc_x: float, loc_y: float) -> Tuple[float, float]:
        """Direct transformation from local Cartesian coordinates to WGS84."""
        utm_x, utm_y, _ = self.local_to_utm(loc_x, loc_y)
        return self.utm_to_geo(utm_x, utm_y)


# Global default transformer
transformer = CoordinateTransformer()
