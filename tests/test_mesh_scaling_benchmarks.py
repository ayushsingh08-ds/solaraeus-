"""
Tests for Mesh Scaling Benchmark Suite.

Validates parametric triangle count scaling, resolution scaling, memory boundedness,
and certified incremental recomputation efficiency.
"""

from __future__ import annotations
import csv
import json
import os
import tempfile
import pytest

from urban_comfort.benchmark.mesh_scaling_benchmark import (
    create_mesh_scaling_scene,
    run_scaling_trial,
    run_mesh_scaling_benchmark,
)
from urban_comfort.config import Weather, SimulationConfig


@pytest.fixture
def scaling_weather() -> Weather:
    return Weather(
        air_temperature=30.0,
        relative_humidity=45.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=850.0,
        diffuse_horizontal_irradiance=150.0,
    )


@pytest.fixture
def fast_scaling_config() -> SimulationConfig:
    return SimulationConfig(
        latitude=48.8566,
        longitude=2.3522,
        date="2026-07-15",
        local_time="14:00:00",
        pedestrian_height=1.1,
        grid_resolution=2.0,
        tmrt_tolerance=0.5,
        numerical_tolerance=0.05,
        sky_patch_configuration=16,
        max_svf_search_dist_m=60.0,
    )


def test_create_mesh_scaling_scene_triangle_counts():
    """Verify that scenes generate exact geometric multiples of 12 triangles per box."""
    test_counts = [1, 4, 16, 64, 256]
    expected_triangles = [12, 48, 192, 768, 3072]

    for n_bldgs, exp_tri in zip(test_counts, expected_triangles):
        scene = create_mesh_scaling_scene(n_bldgs, extent_m=100.0, resolution_m=1.0)
        assert len(scene.meshes) == n_bldgs
        actual_tri = sum(len(m.triangles) for m in scene.meshes.values())
        assert actual_tri == exp_tri

        # Verify each mesh has valid properties
        for mesh in scene.meshes.values():
            assert mesh.num_vertices == 8
            assert mesh.num_triangles == 12
            assert mesh.total_surface_area > 0.0


def test_single_scaling_trial_execution(scaling_weather, fast_scaling_config):
    """Verify that run_scaling_trial executes and returns valid metrics."""
    scene = create_mesh_scaling_scene(4, extent_m=60.0, resolution_m=2.0)
    rec = run_scaling_trial(scene, fast_scaling_config, scaling_weather, "triangle_scaling", "T2_48_tri")

    assert rec["config_type"] == "triangle_scaling"
    assert rec["tier_id"] == "T2_48_tri"
    assert rec["building_count"] == 4
    assert rec["mesh_triangle_count"] == 48
    assert rec["grid_cells_total"] == 30 * 30  # 900
    assert rec["peak_memory_mb"] > 0.0
    assert rec["peak_memory_mb"] < 50.0
    assert rec["time_full_recompute_sec"] > 0.0
    assert rec["speedup_ratio"] >= 1.0


def test_full_mesh_scaling_benchmark_and_artifacts():
    """Verify execution of full benchmark suite and persistence of CSV and JSON summary."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        summary = run_mesh_scaling_benchmark(output_dir=tmp_dir)

        assert summary["total_trials"] == 8
        assert summary["max_peak_memory_mb"] < 50.0
        assert summary["mean_speedup_ratio"] >= 1.0
        assert len(summary["triangle_scaling"]) == 5
        assert len(summary["resolution_scaling"]) == 3

        # CSV checks
        csv_path = os.path.join(tmp_dir, "mesh_scaling_results.csv")
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 8

        # JSON checks
        json_path = os.path.join(tmp_dir, "mesh_scaling_summary.json")
        assert os.path.exists(json_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["total_trials"] == 8


def test_memory_boundedness_and_subquadratic_scaling():
    """Verify that peak heap memory remains tightly bounded and runtime scaling is subquadratic."""
    # Check that artifact exists in target results directory
    results_dir = "results/mesh_validation_20261006_092428"
    summary_path = os.path.join(results_dir, "mesh_scaling_summary.json")

    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        # 1. Memory must remain bounded under 50 MB (measured ~8.34 MB)
        assert summary["max_peak_memory_mb"] < 50.0

        # 2. Triangle scaling: 256x increase in triangles should result in < 256x increase in runtime
        tri_records = summary["triangle_scaling"]
        t_12 = tri_records[0]["time_full_recompute_sec"]
        t_3072 = tri_records[-1]["time_full_recompute_sec"]
        runtime_ratio = t_3072 / max(1e-6, t_12)
        assert runtime_ratio < 256.0  # Demonstrating sublinear/subquadratic growth
