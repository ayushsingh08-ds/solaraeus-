"""
Scene graph and synthetic urban scene generators.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import json

from urban_comfort.config import (
    Material, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.mesh import TriangleMesh


@dataclass
class GroundPlane:
    """Flat horizontal ground surface at z = 0.0."""
    z_elevation: float = 0.0
    material_id: str = "default_ground"


@dataclass
class PedestrianGridConfig:
    """2D domain extent and sampling resolution for the pedestrian calculation plane."""
    extent_x: float = 80.0       # Domain width in meters
    extent_y: float = 80.0       # Domain length in meters
    origin_x: float = 0.0        # Southwest corner X coordinate
    origin_y: float = 0.0        # Southwest corner Y coordinate
    resolution: float = 1.0      # Cell spacing dx (m)
    pedestrian_height: float = 1.1 # z height above terrain (m)

    @property
    def nx(self) -> int:
        return int(round(self.extent_x / self.resolution))

    @property
    def ny(self) -> int:
        return int(round(self.extent_y / self.resolution))

    @property
    def total_cells(self) -> int:
        return self.nx * self.ny


@dataclass
class Scene:
    """Complete urban scene representation."""
    buildings: Dict[str, Building] = field(default_factory=dict)
    meshes: Dict[str, TriangleMesh] = field(default_factory=dict)
    ground: GroundPlane = field(default_factory=GroundPlane)
    pedestrian_grid: PedestrianGridConfig = field(default_factory=PedestrianGridConfig)
    materials: Dict[str, Material] = field(default_factory=dict)
    coordinate_system: str = "EPSG:32633_LOCAL"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure default materials exist
        if "default_wall" not in self.materials:
            self.materials["default_wall"] = DEFAULT_WALL_MATERIAL
        if "default_ground" not in self.materials:
            self.materials["default_ground"] = DEFAULT_GROUND_MATERIAL

    def add_building(self, building: Building):
        if building.id in self.buildings:
            raise ValueError(f"Building ID '{building.id}' already exists in scene.")
        self.buildings[building.id] = building

    def remove_building(self, building_id: str) -> Building:
        if building_id not in self.buildings:
            raise KeyError(f"Building ID '{building_id}' not found in scene.")
        return self.buildings.pop(building_id)

    def get_active_buildings(self) -> List[Building]:
        return [b for b in self.buildings.values() if b.enabled]

    def add_mesh(self, mesh: TriangleMesh):
        if mesh.id in self.meshes:
            raise ValueError(f"Mesh ID '{mesh.id}' already exists in scene.")
        self.meshes[mesh.id] = mesh

    def remove_mesh(self, mesh_id: str) -> TriangleMesh:
        if mesh_id not in self.meshes:
            raise KeyError(f"Mesh ID '{mesh_id}' not found in scene.")
        return self.meshes.pop(mesh_id)

    def get_active_meshes(self) -> List[TriangleMesh]:
        return [m for m in self.meshes.values() if m.enabled]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes scene to a JSON-compatible dictionary."""
        return {
            "coordinate_system": self.coordinate_system,
            "metadata": self.metadata,
            "ground": {
                "z_elevation": self.ground.z_elevation,
                "material_id": self.ground.material_id
            },
            "pedestrian_grid": {
                "extent_x": self.pedestrian_grid.extent_x,
                "extent_y": self.pedestrian_grid.extent_y,
                "origin_x": self.pedestrian_grid.origin_x,
                "origin_y": self.pedestrian_grid.origin_y,
                "resolution": self.pedestrian_grid.resolution,
                "pedestrian_height": self.pedestrian_grid.pedestrian_height
            },
            "materials": {
                m_id: {
                    "id": m.id,
                    "albedo": m.albedo,
                    "emissivity": m.emissivity,
                    "surface_temperature": m.surface_temperature,
                    "is_opaque": m.is_opaque
                }
                for m_id, m in self.materials.items()
            },
            "buildings": [
                {
                    "id": b.id,
                    "footprint": {
                        "xmin": b.footprint.xmin,
                        "xmax": b.footprint.xmax,
                        "ymin": b.footprint.ymin,
                        "ymax": b.footprint.ymax
                    },
                    "height": b.height,
                    "position": list(b.position),
                    "material_id": b.material_id,
                    "enabled": b.enabled
                }
                for b in self.buildings.values()
            ],
            "meshes": [
                m.to_dict()
                for m in self.meshes.values()
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Scene:
        """Constructs a Scene from a serialized dictionary."""
        materials = {
            m_id: Material(
                id=m_data["id"],
                albedo=m_data["albedo"],
                emissivity=m_data["emissivity"],
                surface_temperature=m_data["surface_temperature"],
                is_opaque=m_data.get("is_opaque", True)
            )
            for m_id, m_data in data.get("materials", {}).items()
        }

        ground_data = data.get("ground", {})
        ground = GroundPlane(
            z_elevation=ground_data.get("z_elevation", 0.0),
            material_id=ground_data.get("material_id", "default_ground")
        )

        grid_data = data.get("pedestrian_grid", {})
        ped_grid = PedestrianGridConfig(
            extent_x=grid_data.get("extent_x", 80.0),
            extent_y=grid_data.get("extent_y", 80.0),
            origin_x=grid_data.get("origin_x", 0.0),
            origin_y=grid_data.get("origin_y", 0.0),
            resolution=grid_data.get("resolution", 1.0),
            pedestrian_height=grid_data.get("pedestrian_height", 1.1)
        )

        buildings = {}
        for b_data in data.get("buildings", []):
            fp_data = b_data["footprint"]
            footprint = BoundingBox2D(
                xmin=fp_data["xmin"],
                xmax=fp_data["xmax"],
                ymin=fp_data["ymin"],
                ymax=fp_data["ymax"]
            )
            b = Building(
                id=b_data["id"],
                footprint=footprint,
                height=b_data["height"],
                position=tuple(b_data.get("position", (0.0, 0.0, 0.0))),
                material_id=b_data.get("material_id", "default_wall"),
                enabled=b_data.get("enabled", True)
            )
            buildings[b.id] = b

        meshes = {}
        for m_data in data.get("meshes", []):
            m = TriangleMesh.from_dict(m_data)
            meshes[m.id] = m

        return cls(
            buildings=buildings,
            meshes=meshes,
            ground=ground,
            pedestrian_grid=ped_grid,
            materials=materials,
            coordinate_system=data.get("coordinate_system", "EPSG:32633_LOCAL"),
            metadata=data.get("metadata", {})
        )

    def save_json(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, file_path: str) -> Scene:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


# Canonical Synthetic Scene Generators
def create_single_box_scene(extent_m: float = 80.0, box_size: float = 16.0,
                            box_height: float = 18.0) -> Scene:
    """Creates a canonical flat scene with one centered rectangular building."""
    center = extent_m / 2.0
    half_size = box_size / 2.0
    footprint = BoundingBox2D(
        xmin=center - half_size,
        xmax=center + half_size,
        ymin=center - half_size,
        ymax=center + half_size
    )
    building = Building(id="bldg_center", footprint=footprint, height=box_height)
    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=extent_m, extent_y=extent_m))
    scene.add_building(building)
    scene.metadata["generator"] = "create_single_box_scene"
    return scene


def create_canyon_scene(extent_m: float = 80.0, canyon_width: float = 16.0,
                        building_height: float = 20.0) -> Scene:
    """Creates an urban canyon with two parallel rows of buildings along East-West."""
    center_y = extent_m / 2.0
    half_canyon = canyon_width / 2.0

    # North building row
    bldg_north = Building(
        id="bldg_north_row",
        footprint=BoundingBox2D(xmin=10.0, xmax=extent_m - 10.0,
                                ymin=center_y + half_canyon, ymax=center_y + half_canyon + 15.0),
        height=building_height
    )
    # South building row
    bldg_south = Building(
        id="bldg_south_row",
        footprint=BoundingBox2D(xmin=10.0, xmax=extent_m - 10.0,
                                ymin=center_y - half_canyon - 15.0, ymax=center_y - half_canyon),
        height=building_height
    )

    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=extent_m, extent_y=extent_m))
    scene.add_building(bldg_north)
    scene.add_building(bldg_south)
    scene.metadata["generator"] = "create_canyon_scene"
    return scene


def create_occlusion_scene(extent_m: float = 80.0) -> Scene:
    """
    Creates an occlusion test scene with an aligned tall background building
    and a shorter foreground building.
    """
    center_x = extent_m / 2.0
    # Tall background building (North, height 26m)
    bldg_rear = Building(
        id="bldg_rear_tall",
        footprint=BoundingBox2D(xmin=center_x - 8.0, xmax=center_x + 8.0, ymin=45.0, ymax=55.0),
        height=26.0
    )
    # Shorter foreground building (South, height 12m)
    bldg_front = Building(
        id="bldg_front_short",
        footprint=BoundingBox2D(xmin=center_x - 8.0, xmax=center_x + 8.0, ymin=25.0, ymax=35.0),
        height=12.0
    )

    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=extent_m, extent_y=extent_m))
    scene.add_building(bldg_rear)
    scene.add_building(bldg_front)
    scene.metadata["generator"] = "create_occlusion_scene"
    return scene
