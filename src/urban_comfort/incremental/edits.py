"""Geometric edit types: the *what changed* half of the incremental API.

An edit is a small, serializable description of a change to a `Scene`.  Each
edit knows how to apply itself and how to report the 3-D volume of space whose
geometry changed, which is what the affected-region and certificate code needs
in order to bound the error.  `incremental/certificate.py` depends on this
module and this module depends on nothing in `incremental/`, which is what
keeps the certificate path free of import cycles.

Split out of `incremental/update.py` during the cycle break; the class bodies
are byte-identical to the originals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from urban_comfort.geometry.primitives import Building
from urban_comfort.geometry.scene import Scene


@dataclass
class GeometricEdit:
    """Base class for geometric building edits."""

    edit_type: str

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        """Applies edit to scene and returns (new_scene, modified_volume_bounds_3d)."""
        raise NotImplementedError


@dataclass
class AddBuildingEdit(GeometricEdit):
    building: Building

    def __init__(self, building: Building):
        super().__init__(edit_type="building_added")
        self.building = building

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        new_scene.add_building(self.building)
        return new_scene, self.building.bounds_3d


@dataclass
class RemoveBuildingEdit(GeometricEdit):
    building_id: str

    def __init__(self, building_id: str):
        super().__init__(edit_type="building_removed")
        self.building_id = building_id

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        removed = new_scene.remove_building(self.building_id)
        return new_scene, removed.bounds_3d


@dataclass
class ChangeHeightEdit(GeometricEdit):
    building_id: str
    new_height: float

    def __init__(self, building_id: str, new_height: float):
        super().__init__(edit_type="building_height_changed")
        self.building_id = building_id
        self.new_height = new_height

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        bldg = new_scene.buildings[self.building_id]
        old_bounds = bldg.bounds_3d
        bldg.height = self.new_height
        new_bounds = bldg.bounds_3d

        # The differential volume of geometry changed is between min(old_h, new_h) and max(old_h, new_h)
        diff_bounds = (
            min(old_bounds[0], new_bounds[0]),
            max(old_bounds[1], new_bounds[1]),
            min(old_bounds[2], new_bounds[2]),
            max(old_bounds[3], new_bounds[3]),
            min(old_bounds[5], new_bounds[5]),
            max(old_bounds[5], new_bounds[5]),
        )
        return new_scene, diff_bounds


@dataclass
class MoveBuildingEdit(GeometricEdit):
    building_id: str
    shift_x: float
    shift_y: float

    def __init__(self, building_id: str, shift_x: float, shift_y: float):
        super().__init__(edit_type="building_moved")
        self.building_id = building_id
        self.shift_x = shift_x
        self.shift_y = shift_y

    def apply(self, scene: Scene) -> Tuple[Scene, Tuple[float, float, float, float, float, float]]:
        new_scene = Scene.from_dict(scene.to_dict())
        bldg = new_scene.buildings[self.building_id]
        old_bounds = bldg.bounds_3d

        old_pos = bldg.position
        bldg.position = (old_pos[0] + self.shift_x, old_pos[1] + self.shift_y, old_pos[2])
        new_bounds = bldg.bounds_3d

        union_bounds = (
            min(old_bounds[0], new_bounds[0]),
            max(old_bounds[1], new_bounds[1]),
            min(old_bounds[2], new_bounds[2]),
            max(old_bounds[3], new_bounds[3]),
            min(old_bounds[4], new_bounds[4]),
            max(old_bounds[5], new_bounds[5]),
        )
        return new_scene, union_bounds
