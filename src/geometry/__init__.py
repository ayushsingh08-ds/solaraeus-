"""
Geometry construction subpackage for Solaraeus.
Handles 2.5D DSM raster validation, 3D building mesh extrusion, and pedestrian query grids.
"""

from . import dsm, meshes, pedestrian_grid

__all__ = ["dsm", "meshes", "pedestrian_grid"]
