"""
Unit tests for dependency graph traversal, hashing, and cache maintenance.
"""

import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import create_single_box_scene
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.dependency_graph import (
    DependencyGraph, FIELD_SHADOW, FIELD_SVF, FIELD_SHORTWAVE,
    FIELD_LONGWAVE, FIELD_TMRT, FIELD_UTCI, INPUT_GEOMETRY, INPUT_WIND, INPUT_ALBEDO
)
from urban_comfort.incremental.cache import (
    SimulationCache, compute_scene_hash, compute_weather_hash, compute_config_hash
)


def test_hash_determinism_and_sensitivity():
    scene1 = create_single_box_scene(extent_m=60.0, box_size=15.0, box_height=18.0)
    scene2 = create_single_box_scene(extent_m=60.0, box_size=15.0, box_height=18.0)
    scene3 = create_single_box_scene(extent_m=60.0, box_size=15.0, box_height=22.0)  # Different height

    hash1 = compute_scene_hash(scene1)
    hash2 = compute_scene_hash(scene2)
    hash3 = compute_scene_hash(scene3)

    assert hash1 == hash2, "Identical scenes must produce identical SHA-256 hashes"
    assert hash1 != hash3, "Scenes with different building heights must produce distinct hashes"

    weather1 = Weather(300.0, 50.0, 2.0, 180.0, 700.0, 150.0)
    weather2 = Weather(300.0, 50.0, 4.0, 180.0, 700.0, 150.0)  # Different wind
    assert compute_weather_hash(weather1) != compute_weather_hash(weather2)


def test_dependency_graph_building_geometry_invalidation():
    graph = DependencyGraph()
    invalidated = graph.get_invalidated_fields([INPUT_GEOMETRY])

    # Geometry modification invalidates the entire thermal radiation and comfort chain
    assert FIELD_SHADOW in invalidated
    assert FIELD_SVF in invalidated
    assert FIELD_SHORTWAVE in invalidated
    assert FIELD_LONGWAVE in invalidated
    assert FIELD_TMRT in invalidated
    assert FIELD_UTCI in invalidated


def test_dependency_graph_wind_invalidation():
    graph = DependencyGraph()
    invalidated = graph.get_invalidated_fields([INPUT_WIND])

    # Wind speed change only invalidates UTCI; radiation fields remain untouched!
    assert invalidated == {FIELD_UTCI}


def test_dependency_graph_albedo_invalidation():
    graph = DependencyGraph()
    invalidated = graph.get_invalidated_fields([INPUT_ALBEDO])

    # Albedo affects shortwave, Tmrt, and UTCI, but does NOT invalidate geometric shadows or SVF
    assert FIELD_SHORTWAVE in invalidated
    assert FIELD_TMRT in invalidated
    assert FIELD_UTCI in invalidated

    assert FIELD_SHADOW not in invalidated
    assert FIELD_SVF not in invalidated
    assert FIELD_LONGWAVE not in invalidated


def test_upstream_dependencies():
    graph = DependencyGraph()
    upstream_tmrt = graph.get_upstream_dependencies(FIELD_TMRT)

    assert FIELD_SHORTWAVE in upstream_tmrt
    assert FIELD_LONGWAVE in upstream_tmrt
    assert FIELD_SHADOW in upstream_tmrt
    assert FIELD_SVF in upstream_tmrt
    assert INPUT_GEOMETRY in upstream_tmrt


def test_simulation_cache_populate_and_invalidation():
    scene = create_single_box_scene(extent_m=40.0)
    weather = Weather(300.15, 50.0, 2.0, 180.0, 700.0, 150.0)
    config = SimulationConfig(sky_patch_configuration=16)

    result = full_recompute(scene, weather, config)
    cache = SimulationCache()
    cache.populate(scene, weather, config, result)

    # Initial state: all fields populated and 100% valid
    assert cache.scene_hash is not None
    assert cache.metadata[FIELD_TMRT].is_fully_valid is True
    assert cache.metadata[FIELD_TMRT].valid_fraction == 1.0

    # Invalidate a candidate spatial patch (10x10 cells in center)
    dirty_mask = np.zeros(scene.pedestrian_grid.ny, dtype=bool)
    dirty_mask = np.zeros((scene.pedestrian_grid.ny, scene.pedestrian_grid.nx), dtype=bool)
    dirty_mask[15:25, 15:25] = True

    graph = DependencyGraph()
    inval_fields = graph.get_invalidated_for_edit("building_height_changed")
    cache.invalidate_fields(inval_fields, dirty_spatial_mask=dirty_mask)

    # Tmrt metadata should now show partially valid mask
    meta_tmrt = cache.metadata[FIELD_TMRT]
    assert meta_tmrt.is_fully_valid is False
    assert meta_tmrt.valid_mask[0, 0] is True or meta_tmrt.valid_mask[0, 0] == 1
    assert meta_tmrt.valid_mask[20, 20] is False or meta_tmrt.valid_mask[20, 20] == 0
