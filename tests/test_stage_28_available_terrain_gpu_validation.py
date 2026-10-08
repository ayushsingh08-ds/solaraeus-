"""
Tests for SOLARAEUS Stage 28: Available-Data Terrain GPU and Incremental Validation
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_28_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_28_available_terrain_gpu_validation"


def test_stage_28_artifacts_exist(stage_28_dir):
    assert stage_28_dir.exists(), "Stage 28 directory missing"
    required = [
        "available_terrain_gpu_manifest.json",
        "available_terrain_gpu_full_outputs.json",
        "available_terrain_gpu_incremental_outputs.json",
        "available_terrain_gpu_cpu_comparison.json",
        "available_terrain_gpu_incremental_comparison.json",
        "available_terrain_gpu_affected_region.json",
        "available_terrain_gpu_certificates.json",
        "available_terrain_gpu_runtime_metrics.json",
        "available_terrain_gpu_memory_metrics.json",
        "stage_28_test_results.json",
    ]
    for fname in required:
        assert (stage_28_dir / fname).exists(), f"Missing {fname}"
        assert (stage_28_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_28_manifest_and_labels(stage_28_dir):
    with open(stage_28_dir / "available_terrain_gpu_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"
    assert data["api_version"] == "2.1.0-gpu-terrain"
    assert data["real_world_street_scale_claim"] == "NOT_MEASURED_STREET_SCALE"
    assert data["token"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"


def test_stage_28_parity_and_incremental(stage_28_dir):
    with open(stage_28_dir / "available_terrain_gpu_cpu_comparison.json", encoding="utf-8") as f:
        cpu_comp = json.load(f)
    for profile, metrics in cpu_comp.items():
        assert metrics["exact_shadow_parity"] is True
        assert metrics["parity_within_tolerance"] is True

    with open(stage_28_dir / "available_terrain_gpu_incremental_comparison.json", encoding="utf-8") as f:
        inc_comp = json.load(f)
    assert inc_comp["error_within_certificate_bound"] is True
    assert inc_comp["certificate_bound_k"] == 0.0812


def test_stage_28_test_results(stage_28_dir):
    with open(stage_28_dir / "stage_28_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"
    assert data["token"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"
    assert data["acceptance_criteria_met"] is True
