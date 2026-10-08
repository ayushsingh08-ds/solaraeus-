"""
Tests for SOLARAEUS Stage 34: Terrain/Tree Parity and Certificate Validation
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_34_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_34_terrain_tree_validation"


def test_stage_34_artifacts_exist(stage_34_dir):
    assert stage_34_dir.exists(), "Stage 34 directory missing"
    required = [
        "terrain_tree_cpu_gpu_comparison.json",
        "terrain_tree_incremental_comparison.json",
        "terrain_tree_certificate_audit.json",
        "terrain_tree_runtime_report.json",
        "terrain_tree_memory_report.json",
        "terrain_tree_validation_report.md",
        "terrain_tree_limitations.md",
        "stage_34_test_results.json",
    ]
    for fname in required:
        assert (stage_34_dir / fname).exists(), f"Missing {fname}"
        assert (stage_34_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_34_parity_and_certificates(stage_34_dir):
    with open(stage_34_dir / "terrain_tree_cpu_gpu_comparison.json", encoding="utf-8") as f:
        comp = json.load(f)
    for cname, m in comp.items():
        assert m["exact_shadow_parity"] is True
        assert m["thermal_parity_passed"] is True

    with open(stage_34_dir / "terrain_tree_certificate_audit.json", encoding="utf-8") as f:
        certs = json.load(f)
    assert len(certs) == 5
    for c_id, val in certs.items():
        assert "PASSED" in val


def test_stage_34_test_results(stage_34_dir):
    with open(stage_34_dir / "stage_34_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_34_TERRAIN_TREE_PARITY_COMPLETE"
    assert data["token"] == "STAGE_34_TERRAIN_TREE_PARITY_COMPLETE"
    assert data["acceptance_criteria_met"] is True
