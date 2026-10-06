"""
Tests for Comparative AABB vs Mesh Benchmarking Suite.

Validates parity, biometeorological fidelity, and execution metrics between
Axis-Aligned Bounding Box (AABB) and equivalent triangular-mesh representations.
"""

from __future__ import annotations
import csv
import json
import os
import tempfile
import numpy as np
import pytest

from urban_comfort.benchmark.aabb_vs_mesh_benchmark import (
    get_canonical_benchmark_scenes,
    build_scene_pair,
    run_single_comparison,
    run_aabb_vs_mesh_benchmark,
)
from urban_comfort.config import Weather, SimulationConfig


@pytest.fixture
def standard_weather() -> Weather:
    return Weather(
        air_temperature=30.0,
        relative_humidity=45.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=850.0,
        diffuse_horizontal_irradiance=150.0,
    )


@pytest.fixture
def standard_config() -> SimulationConfig:
    return SimulationConfig(
        latitude=48.8566,
        longitude=2.3522,
        date="2026-07-15",
        local_time="14:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        tmrt_tolerance=0.5,
        numerical_tolerance=0.05,
        sky_patch_configuration=16,
        max_svf_search_dist_m=100.0,
    )


def test_canonical_benchmark_scene_definitions():
    """Verify that all 4 canonical benchmark scenes are properly defined."""
    scenes = get_canonical_benchmark_scenes()
    assert len(scenes) == 4
    scene_ids = [s.scene_id for s in scenes]
    assert scene_ids == ["isolated_building", "urban_canyon", "enclosed_courtyard", "dense_3x3_grid"]

    expected_bldg_counts = [1, 2, 4, 9]
    for s, exp_b in zip(scenes, expected_bldg_counts):
        assert len(s.buildings) == exp_b


def test_scene_pair_construction():
    """Verify conversion of benchmark scene definition to AABB Scene and Mesh Scene."""
    scenes = get_canonical_benchmark_scenes()
    sc_iso = scenes[0]
    scene_aabb, scene_mesh = build_scene_pair(sc_iso, resolution_m=1.0, pedestrian_height_m=1.1)

    assert len(scene_aabb.buildings) == 1
    assert len(scene_mesh.meshes) == 1
    mesh = list(scene_mesh.meshes.values())[0]
    assert mesh.num_vertices == 8
    assert mesh.num_triangles == 12
    # 20x20x25m box: 2*(400 + 500 + 500) = 2800 m^2
    assert pytest.approx(mesh.total_surface_area) == 2800.0


def test_single_scene_comparison_metrics(standard_weather, standard_config):
    """Verify that run_single_comparison computes all required physical and timing metrics."""
    scenes = get_canonical_benchmark_scenes()
    sc_iso = scenes[0]

    result = run_single_comparison(sc_iso, standard_weather, standard_config)

    assert result["scene_id"] == "isolated_building"
    assert result["aabb_building_count"] == 1
    assert result["mesh_triangle_count"] == 12

    # Direct shadow parity
    assert result["shadow_iou"] >= 0.999
    assert result["shadow_mismatch_cells"] == 0

    # SVF fidelity
    assert result["svf_mae"] < 0.005
    assert result["svf_max_diff"] < 0.01

    # Tmrt fidelity
    assert result["tmrt_mae_k"] < 0.05
    assert result["tmrt_max_diff_k"] < 0.15

    # UTCI category agreement
    assert result["utci_category_agreement"] >= 0.999

    # Runtime & overhead
    assert result["runtime_aabb_sec"] > 0.0
    assert result["runtime_mesh_sec"] > 0.0
    assert result["overhead_ratio"] > 0.0


def test_full_benchmark_execution_and_artifacts():
    """Verify execution of full benchmark suite and persistence of CSV and JSON summary."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        summary = run_aabb_vs_mesh_benchmark(output_dir=tmp_dir)

        assert summary["total_scenes"] == 4
        assert summary["min_shadow_iou"] >= 0.999
        assert summary["total_shadow_mismatches"] == 0
        assert summary["max_svf_mae"] < 0.005
        assert summary["max_tmrt_mae_k"] < 0.05
        assert summary["min_utci_agreement"] >= 0.999

        csv_path = os.path.join(tmp_dir, "aabb_vs_mesh_comparison.csv")
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 4

        json_path = os.path.join(tmp_dir, "aabb_vs_mesh_summary.json")
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["total_scenes"] == 4
            assert len(data["results"]) == 4


def test_mesh_watertightness_and_triangle_multiples():
    """Verify that all canonical scenes produce valid box meshes with 8 vertices and 12 triangles per box."""
    scenes = get_canonical_benchmark_scenes()
    for sc in scenes:
        _, scene_mesh = build_scene_pair(sc)
        for mesh in scene_mesh.meshes.values():
            assert mesh.num_vertices == 8
            assert mesh.num_triangles == 12
            assert mesh.total_surface_area > 0.0
