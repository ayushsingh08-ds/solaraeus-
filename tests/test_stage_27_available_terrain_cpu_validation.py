"""
Tests for SOLARAEUS Stage 27: Available-Data Terrain CPU Validation
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_27_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_27_available_terrain_cpu_validation"


def test_stage_27_artifacts_exist(stage_27_dir):
    assert stage_27_dir.exists(), "Stage 27 directory missing"
    required = [
        "available_terrain_cpu_manifest.json",
        "available_terrain_cpu_outputs.json",
        "available_terrain_cpu_comparison.json",
        "available_terrain_cpu_certificates.json",
        "available_terrain_cpu_limitations.md",
        "stage_27_test_results.json",
    ]
    for fname in required:
        assert (stage_27_dir / fname).exists(), f"Missing {fname}"
        assert (stage_27_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_27_manifest_and_labels(stage_27_dir):
    with open(stage_27_dir / "available_terrain_cpu_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_27_AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE"
    assert data["api_version"] == "2.1.0-cpu-terrain"
    assert data["street_scale_claim"] == "NOT_MEASURED_STREET_SCALE"
    for profile in data["profiles_tested"]:
        assert profile["label"] in ("SYNTHETIC_TERRAIN_TEST", "REGIONAL_REFERENCE_TEST")


def test_stage_27_flat_ground_parity(stage_27_dir):
    with open(stage_27_dir / "available_terrain_cpu_comparison.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["flat_ground_exact_match"] is True
    assert data["flat_ground_parity_diff_k"] < 1e-12


def test_stage_27_test_results(stage_27_dir):
    with open(stage_27_dir / "stage_27_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_27_AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE"
    assert data["token"] == "STAGE_27_AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE"
    assert data["acceptance_criteria_met"] is True
