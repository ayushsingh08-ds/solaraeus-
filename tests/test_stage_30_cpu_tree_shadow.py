"""
Tests for SOLARAEUS Stage 30: CPU Tree-Shadow Reference Solver
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_30_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_30_cpu_tree_shadow"


def test_stage_30_artifacts_exist(stage_30_dir):
    assert stage_30_dir.exists(), "Stage 30 directory missing"
    required = [
        "cpu_tree_reference_api.md",
        "cpu_tree_geometry_manifest.json",
        "cpu_tree_shadow_outputs.json",
        "cpu_tree_synthetic_tests.json",
        "cpu_tree_certificates.json",
        "cpu_tree_flat_ground_regression.json",
        "cpu_tree_available_terrain_regression.json",
        "cpu_tree_limitations.md",
        "stage_30_test_results.json",
    ]
    for fname in required:
        assert (stage_30_dir / fname).exists(), f"Missing {fname}"
        assert (stage_30_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_30_manifest_and_labels(stage_30_dir):
    with open(stage_30_dir / "cpu_tree_geometry_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE"
    assert data["api_version"] == "2.2.0-cpu-tree"
    assert data["classification"] == "PROVISIONAL_TREE_GEOMETRY"
    assert data["field_validation"] == "NOT_FIELD_VALIDATED"
    assert data["usage_scope"] == "SENSITIVITY_USE_ONLY"


def test_stage_30_flat_ground_regression(stage_30_dir):
    with open(stage_30_dir / "cpu_tree_flat_ground_regression.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["empty_tree_exact_shadow_match"] is True
    assert data["empty_tree_exact_tmrt_match"] is True
    assert data["status"] == "PASS_EXACT_EQUIVALENCE"


def test_stage_30_test_results(stage_30_dir):
    with open(stage_30_dir / "stage_30_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE"
    assert data["token"] == "STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE"
    assert data["acceptance_criteria_met"] is True
