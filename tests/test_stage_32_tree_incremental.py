"""
Tests for SOLARAEUS Stage 32: Tree-Aware Incremental Recomputation
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_32_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_32_tree_incremental"


def test_stage_32_artifacts_exist(stage_32_dir):
    assert stage_32_dir.exists(), "Stage 32 directory missing"
    required = [
        "tree_incremental_cpu_outputs.json",
        "tree_incremental_gpu_outputs.json",
        "tree_incremental_affected_region.json",
        "tree_incremental_reuse_metrics.json",
        "tree_incremental_cpu_comparison.json",
        "tree_incremental_gpu_comparison.json",
        "tree_incremental_certificates.json",
        "tree_incremental_limitations.md",
        "stage_32_test_results.json",
    ]
    for fname in required:
        assert (stage_32_dir / fname).exists(), f"Missing {fname}"
        assert (stage_32_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_32_parity_and_reuse(stage_32_dir):
    with open(stage_32_dir / "tree_incremental_cpu_comparison.json", encoding="utf-8") as f:
        cpu_comp = json.load(f)
    for scenario, res in cpu_comp.items():
        assert res["within_tolerance"] is True

    with open(stage_32_dir / "tree_incremental_gpu_comparison.json", encoding="utf-8") as f:
        gpu_comp = json.load(f)
    for scenario, res in gpu_comp.items():
        assert res["within_tolerance"] is True

    with open(stage_32_dir / "tree_incremental_reuse_metrics.json", encoding="utf-8") as f:
        reuse = json.load(f)
    for scenario, res in reuse.items():
        assert res["reused_cells"] > 0
        assert res["reuse_efficiency_pct"] > 0.0


def test_stage_32_test_results(stage_32_dir):
    with open(stage_32_dir / "stage_32_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_32_TREE_AWARE_INCREMENTAL_COMPLETE"
    assert data["token"] == "STAGE_32_TREE_AWARE_INCREMENTAL_COMPLETE"
    assert data["acceptance_criteria_met"] is True
