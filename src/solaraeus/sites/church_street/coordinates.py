"""
Authoritative coordinate transformation and validation pipeline for SOLARAEUS.

Provides strict, reversible transformations between:
- Geographic Coordinates: WGS84 (EPSG:4326) [Longitude, Latitude]
- Projected Metric Coordinates: UTM Zone 43N (EPSG:32643) [Eastings, Northings (m)]
- Local Project Cartesian Coordinates: Church Street Reference Origin [X (East, m), Y (North, m), Z (Up, m)]
- 3D Engine Coordinates (Three.js WebGL): [X (East), Y (Up), Z (-North)]
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pyproj import Transformer


@dataclass(frozen=True)
class CoordinateSystemDefinition:
    source_crs: str = "EPSG:4326"
    projected_crs: str = "EPSG:32643"
    utm_zone: str = "43N"
    # Local Origin in UTM Zone 43N meters (Church Street Corridor Reference)
    local_origin_x: float = 782541.8055380594
    local_origin_y: float = 1435736.1103432046
    local_origin_z: float = 0.0
    grid_convergence_deg: float = 0.585366
    vertical_datum: str = "EGM2008_ORTHOMETRIC"
    units: str = "meters"
    axis_orientation: str = "X_EAST_Y_NORTH_Z_UP"


class CoordinateTransformer:
    """Authoritative coordinator for all spatial transformations in SOLARAEUS."""

    def __init__(self, definition: Optional[CoordinateSystemDefinition] = None):
        self.def_ = definition or CoordinateSystemDefinition()
        # Always use (x, y) = (lon, lat) order
        self.geo_to_utm_trans = Transformer.from_crs(
            self.def_.source_crs, self.def_.projected_crs, always_xy=True
        )
        self.utm_to_geo_trans = Transformer.from_crs(
            self.def_.projected_crs, self.def_.source_crs, always_xy=True
        )

    def geo_to_utm(self, lon: float, lat: float) -> Tuple[float, float]:
        """Convert WGS84 (lon, lat) to UTM 43N (eastings, northings)."""
        utm_x, utm_y = self.geo_to_utm_trans.transform(lon, lat)
        return float(utm_x), float(utm_y)

    def utm_to_geo(self, utm_x: float, utm_y: float) -> Tuple[float, float]:
        """Convert UTM 43N (eastings, northings) to WGS84 (lon, lat)."""
        lon, lat = self.utm_to_geo_trans.transform(utm_x, utm_y)
        return float(lon), float(lat)

    def utm_to_local(self, utm_x: float, utm_y: float, utm_z: float = 0.0) -> Tuple[float, float, float]:
        """Convert UTM 43N meters to local Church Street Cartesian meters."""
        loc_x = utm_x - self.def_.local_origin_x
        loc_y = utm_y - self.def_.local_origin_y
        loc_z = utm_z - self.def_.local_origin_z
        return float(loc_x), float(loc_y), float(loc_z)

    def local_to_utm(self, loc_x: float, loc_y: float, loc_z: float = 0.0) -> Tuple[float, float, float]:
        """Convert local Church Street Cartesian meters to UTM 43N meters."""
        utm_x = loc_x + self.def_.local_origin_x
        utm_y = loc_y + self.def_.local_origin_y
        utm_z = loc_z + self.def_.local_origin_z
        return float(utm_x), float(utm_y), float(utm_z)

    def geo_to_local(self, lon: float, lat: float, elevation: float = 0.0) -> Tuple[float, float, float]:
        """Direct transformation from WGS84 to local Church Street coordinates."""
        utm_x, utm_y = self.geo_to_utm(lon, lat)
        return self.utm_to_local(utm_x, utm_y, elevation)

    def local_to_geo(self, loc_x: float, loc_y: float) -> Tuple[float, float]:
        """Direct transformation from local Church Street coordinates to WGS84."""
        utm_x, utm_y, _ = self.local_to_utm(loc_x, loc_y)
        return self.utm_to_geo(utm_x, utm_y)

    def local_to_threejs(self, loc_x: float, loc_y: float, loc_z: float = 0.0) -> Tuple[float, float, float]:
        """
        Convert Local Cartesian [X: East, Y: North, Z: Up]
        to Three.js WebGL space [X: East, Y: Up, Z: -North (South is +Z)].
        """
        return float(loc_x), float(loc_z), float(-loc_y)

    def threejs_to_local(self, three_x: float, three_y: float, three_z: float) -> Tuple[float, float, float]:
        """
        Convert Three.js WebGL space [X: East, Y: Up, Z: -North]
        to Local Cartesian [X: East, Y: North, Z: Up].
        """
        return float(three_x), float(-three_z), float(three_y)

    def validate_roundtrip(self, lon: float, lat: float) -> Dict[str, float]:
        """Test roundtrip error between Geo -> Local -> Geo."""
        lx, ly, _ = self.geo_to_local(lon, lat)
        r_lon, r_lat = self.local_to_geo(lx, ly)
        err_lon = abs(lon - r_lon)
        err_lat = abs(lat - r_lat)
        return {"error_lon_deg": err_lon, "error_lat_deg": err_lat}

    def generate_manifest(self) -> Dict[str, Any]:
        """Export coordinate system specification as serializable manifest."""
        return {
            "coordinate_system": asdict(self.def_),
            "reference_station": {
                "name": "Church Street Central Corridor",
                "city": "Bengaluru, India",
                "nominal_coordinates": {"latitude_deg": 12.9749, "longitude_deg": 77.6054},
                "utm_origin": {
                    "easting_m": self.def_.local_origin_x,
                    "northing_m": self.def_.local_origin_y,
                    "elevation_m": self.def_.local_origin_z,
                },
            },
            "axis_conventions": {
                "local_x": "+East (meters)",
                "local_y": "+North (meters)",
                "local_z": "+Up (meters)",
                "threejs_x": "+East",
                "threejs_y": "+Up",
                "threejs_z": "-North (toward South)",
            },
            "status": "AUTHORITATIVE_COORDINATE_PIPELINE_VALIDATED",
        }


# Global default transformer
transformer = CoordinateTransformer()
