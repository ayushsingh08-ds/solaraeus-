"""
Data utilities for CRS transformations, bounding boxes, and raster manipulation.
"""

from typing import Tuple
import pyproj
from shapely.ops import transform
from shapely.geometry import box, Polygon


def get_transformer(from_epsg: int, to_epsg: int) -> pyproj.Transformer:
    """Creates a pyproj Transformer between two EPSG codes."""
    return pyproj.Transformer.from_crs(f"EPSG:{from_epsg}", f"EPSG:{to_epsg}", always_xy=True)


def bbox_to_polygon(bbox_latlon: Tuple[float, float, float, float]) -> Polygon:
    """
    Converts (S, W, N, E) bounding box into a Shapely Polygon (EPSG:4326).
    """
    south, west, north, east = bbox_latlon
    return box(west, south, east, north)


def reproject_polygon(poly: Polygon, from_epsg: int = 4326, to_epsg: int = 32618) -> Polygon:
    """Reprojects a Shapely geometry from one EPSG to another."""
    transformer = get_transformer(from_epsg, to_epsg)
    return transform(transformer.transform, poly)
