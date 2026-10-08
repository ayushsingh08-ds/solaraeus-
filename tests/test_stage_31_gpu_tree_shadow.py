"""
Tests for SOLARAEUS Stage 31: GPU Tree-Shadow Backend
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_31_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_31_gpu_tree_shadow"


def test_stage_31_artifacts_exist(stage_31_dir):
    assert stage_31_dir.exists(), "Stage 31 directory missing"
    required = [
        "gpu_tree_backend_manifest.json",
        "gpu_tree_full_outputs.json",
        "gpu_tree_cpu_comparison.json",
        "gpu_tree_certificates.json",
        "gpu_tree_runtime_metrics.json",
        "gpu_tree_memory_metrics.json",
        "gpu_tree_limitations.md",
        "stage_31_test_results.json",
    ]
    for fname in required:
        assert (stage_31_dir / fname).exists(), f"Missing {fname}"
        assert (stage_31_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_31_manifest_and_labels(stage_31_dir):
    with open(stage_31_dir / "gpu_tree_backend_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_31_GPU_TREE_SHADOW_COMPLETE"
    assert data["api_version"] == "2.2.0-gpu-tree"
    assert data["classification"] == "PROVISIONAL_TREE_GEOMETRY"
    assert data["token"] == "STAGE_31_GPU_TREE_SHADOW_COMPLETE"


def test_stage_31_cpu_gpu_parity(stage_31_dir):
    with open(stage_31_dir / "gpu_tree_cpu_comparison.json", encoding="utf-8") as f:
        comp = json.load(f)
    for case_name, metrics in comp.items():
        assert metrics["exact_shadow_parity"] is True
        assert metrics["parity_within_tolerance"] is True


def test_stage_31_test_results(stage_31_dir):
    with open(stage_31_dir / "stage_31_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_31_GPU_TREE_SHADOW_COMPLETE"
    assert data["token"] == "STAGE_31_GPU_TREE_SHADOW_COMPLETE"
    assert data["acceptance_criteria_met"] is True
