"""
Unit tests for data models, geometric primitives, scene graph, and configurations.
"""

import os
import json
import pytest

from urban_comfort.config import (
    Material, Weather, SimulationConfig,
    DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.primitives import BoundingBox2D, Building
from urban_comfort.geometry.scene import (
    Scene, GroundPlane, PedestrianGridConfig,
    create_single_box_scene, create_canyon_scene, create_occlusion_scene
)


def test_bounding_box_2d():
    bbox = BoundingBox2D(xmin=10.0, xmax=30.0, ymin=20.0, ymax=50.0)
    assert bbox.width_x == 20.0
    assert bbox.width_y == 30.0
    assert bbox.area == 600.0
    assert bbox.contains(15.0, 25.0)
    assert not bbox.contains(5.0, 25.0)

    # Intersection
    overlapping = BoundingBox2D(xmin=25.0, xmax=40.0, ymin=30.0, ymax=60.0)
    disjoint = BoundingBox2D(xmin=100.0, xmax=120.0, ymin=100.0, ymax=120.0)
    assert bbox.intersects(overlapping)
    assert not bbox.intersects(disjoint)

    # Invalid bounds
    with pytest.raises(ValueError):
        BoundingBox2D(xmin=30.0, xmax=10.0, ymin=20.0, ymax=50.0)


def test_building_primitive():
    bbox = BoundingBox2D(xmin=10.0, xmax=20.0, ymin=10.0, ymax=20.0)
    bldg = Building(id="b1", footprint=bbox, height=15.0, position=(5.0, 5.0, 0.0))

    assert bldg.xmin == 15.0
    assert bldg.xmax == 25.0
    assert bldg.ymin == 15.0
    assert bldg.ymax == 25.0
    assert bldg.zmin == 0.0
    assert bldg.zmax == 15.0
    assert bldg.bounds_3d == (15.0, 25.0, 15.0, 25.0, 0.0, 15.0)
    assert bldg.footprint_area == 100.0
    assert bldg.volume == 1500.0

    # Negative or zero height rejection
    with pytest.raises(ValueError):
        Building(id="b_invalid", footprint=bbox, height=-5.0)
    with pytest.raises(ValueError):
        Building(id="b_zero", footprint=bbox, height=0.0)


def test_material_validation():
    m = Material(id="brick", albedo=0.3, emissivity=0.9, surface_temperature=300.0)
    assert m.is_opaque is True

    # Out of range albedo
    with pytest.raises(ValueError):
        Material(id="bad_albedo", albedo=1.5, emissivity=0.9, surface_temperature=300.0)

    # Out of range emissivity
    with pytest.raises(ValueError):
        Material(id="bad_emiss", albedo=0.5, emissivity=-0.1, surface_temperature=300.0)

    # Negative Kelvin
    with pytest.raises(ValueError):
        Material(id="bad_temp", albedo=0.5, emissivity=0.9, surface_temperature=-10.0)


def test_weather_and_config_validation():
    w = Weather(
        air_temperature=298.15,
        relative_humidity=50.0,
        wind_speed=2.5,
        wind_direction=180.0,
        direct_normal_irradiance=750.0,
        diffuse_horizontal_irradiance=150.0
    )
    assert w.air_temperature == 298.15

    with pytest.raises(ValueError):
        Weather(air_temperature=-5.0, relative_humidity=50.0, wind_speed=2.0,
                wind_direction=0.0, direct_normal_irradiance=0.0, diffuse_horizontal_irradiance=0.0)

    cfg = SimulationConfig(latitude=40.7128, longitude=-74.0060, grid_resolution=1.0)
    assert cfg.pedestrian_height == 1.1

    with pytest.raises(ValueError):
        SimulationConfig(latitude=120.0)


def test_scene_graph_and_serialization(tmp_path):
    scene = create_single_box_scene(extent_m=60.0, box_size=12.0, box_height=15.0)
    assert "bldg_center" in scene.buildings
    assert scene.pedestrian_grid.nx == 60
    assert scene.pedestrian_grid.ny == 60
    assert len(scene.get_active_buildings()) == 1

    # Add duplicate building ID
    with pytest.raises(ValueError):
        scene.add_building(Building(id="bldg_center", footprint=BoundingBox2D(0, 5, 0, 5), height=10))

    # Remove building
    removed = scene.remove_building("bldg_center")
    assert removed.id == "bldg_center"
    assert len(scene.get_active_buildings()) == 0

    # JSON Roundtrip
    scene2 = create_canyon_scene(extent_m=80.0)
    json_path = tmp_path / "canyon.json"
    scene2.save_json(str(json_path))

    loaded_scene = Scene.load_json(str(json_path))
    assert len(loaded_scene.buildings) == 2
    assert "bldg_north_row" in loaded_scene.buildings
    assert "bldg_south_row" in loaded_scene.buildings
    assert loaded_scene.pedestrian_grid.extent_x == 80.0


def test_baseline_scene_config_file():
    cfg_file = os.path.join(os.path.dirname(__file__), "..", "configs", "baseline_scene.json")
    assert os.path.exists(cfg_file), "configs/baseline_scene.json does not exist!"
    scene = Scene.load_json(cfg_file)
    assert "bldg_center" in scene.buildings
    b = scene.buildings["bldg_center"]
    assert b.height == 18.0
    assert b.footprint.width_x == 16.0
    assert b.footprint.width_y == 16.0
