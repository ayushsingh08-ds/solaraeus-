"""
Terrain-aware scene representations for SOLARAEUS 2.1.0-cpu-terrain extension.
Maintains 100% backward compatibility with flat-ground Scene when terrain is None.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene
from urban_comfort.terrain.dtm import TerrainGrid


@dataclass
class TerrainAwareScene:
    """
    Extends Scene with an optional TerrainGrid.
    Preserves all building, ground, and grid definitions from the base Scene.
    """
    base_scene: Scene
    terrain: Optional[TerrainGrid] = None
    terrain_version: str = "2.1.0-cpu-terrain"

    @property
    def buildings(self) -> List[Building]:
        return self.base_scene.buildings

    @property
    def materials(self) -> Dict[str, Any]:
        return self.base_scene.materials

    @property
    def pedestrian_grid(self) -> Any:
        return self.base_scene.pedestrian_grid

    def get_active_buildings(self) -> List[Building]:
        return self.base_scene.get_active_buildings()

    def has_terrain(self) -> bool:
        return self.terrain is not None

    def get_receptor_elevations(self, x: np.ndarray, y: np.ndarray,
                               pedestrian_height_m: float = 1.1) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes 3D receptor elevations Z_rec(x, y) = Z_terrain(x, y) + pedestrian_height_m.
        If terrain is None, returns pedestrian_height_m (flat ground).
        Returns:
            z_rec: array of 3D receptor heights
            valid_mask: boolean mask (True where terrain is valid and not NoData)
        """
        if self.terrain is None:
            z_rec = np.full_like(x, pedestrian_height_m, dtype=np.float64)
            valid_mask = np.ones_like(x, dtype=bool)
            return z_rec, valid_mask

        z_ground, valid_mask = self.terrain.sample_elevation(x, y)
        z_rec = np.where(valid_mask, z_ground + pedestrian_height_m, np.nan)
        return z_rec, valid_mask

    def validate_panel_clearance(self, panel_building: Building, min_clearance_m: float = 2.5) -> bool:
        """
        Validates panel underside clearance above local terrain.
        """
        if self.terrain is None:
            return panel_building.zmin >= min_clearance_m

        # Sample terrain under panel footprint corners
        xs = np.array([panel_building.xmin, panel_building.xmax, panel_building.xmin, panel_building.xmax])
        ys = np.array([panel_building.ymin, panel_building.ymin, panel_building.ymax, panel_building.ymax])
        z_ground, valid = self.terrain.sample_elevation(xs, ys)
        if not np.all(valid):
            return False
        max_ground = float(np.max(z_ground))
        clearance = float(panel_building.zmin - max_ground)
        return bool(clearance >= min_clearance_m)

    def validate_building_intersection(self, building: Building) -> bool:
        """
        Verifies building rests cleanly on or penetrates terrain without floating.
        """
        if self.terrain is None:
            return bool(building.zmin <= 0.0)

        xs = np.array([building.xmin, building.xmax, building.xmin, building.xmax])
        ys = np.array([building.ymin, building.ymin, building.ymax, building.ymax])
        z_ground, valid = self.terrain.sample_elevation(xs, ys)
        if not np.all(valid):
            return False
        # Building base should anchor at or below local ground minimum
        min_ground = float(np.min(z_ground))
        return bool(building.zmin <= min_ground + 1e-3)
