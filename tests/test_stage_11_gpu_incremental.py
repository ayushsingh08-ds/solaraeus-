"""
Unit tests for Stage 11: GPU Incremental Recomputation & Parity Validation.
"""

import json
from pathlib import Path
import pytest
import numpy as np


@pytest.fixture
def stage_11_dir():
    p = Path(__file__).resolve().parent.parent / "results" / "stage_11_gpu_incremental"
    assert p.exists(), f"Stage 11 output directory {p} does not exist"
    return p


def test_stage_11_required_files_exist(stage_11_dir):
    required = [
        "gpu_incremental_outputs.json",
        "gpu_incremental_affected_region.json",
        "gpu_incremental_reuse_metrics.json",
        "gpu_incremental_runtime_metrics.json",
        "gpu_incremental_cpu_comparison.json",
        "gpu_incremental_full_comparison.json",
        "gpu_incremental_certificate.json",
        "stage_11_test_results.json",
        "gpu_incremental_arrays.npz"
    ]
    for fname in required:
        fpath = stage_11_dir / fname
        assert fpath.exists(), f"Missing required stage 11 file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_stage_11_test_suite_all_pass(stage_11_dir):
    data = json.loads((stage_11_dir / "stage_11_test_results.json").read_text(encoding="utf-8"))
    assert data["stage"] == 11
    assert data["overall_status"] == "PASS"
    assert data["tests_passed"] == 8
    assert data["tests_failed"] == 0
    assert data["success_token"] == "STAGE_11_GPU_INCREMENTAL_RECOMPUTATION_COMPLETE"
    for t in data["test_records"]:
        assert t["pass"] is True, f"Stage 11 subtest failed: {t['name']}"


def test_stage_11_certificate_valid(stage_11_dir):
    cert = json.loads((stage_11_dir / "gpu_incremental_certificate.json").read_text(encoding="utf-8"))
    assert cert["is_valid"] is True
    assert cert["num_violations"] == 0
    assert cert["max_actual_error_on_reused_k"] <= cert["epsilon_target_k"]


def test_stage_11_reuse_metrics(stage_11_dir):
    reuse = json.loads((stage_11_dir / "gpu_incremental_reuse_metrics.json").read_text(encoding="utf-8"))
    assert reuse["cells"]["reused"] == 28048
    assert reuse["cells"]["recomputed"] == 72
    assert reuse["cells"]["total"] == 28120
    assert reuse["rays"]["ray_work_reduction_pct"] > 99.0


def test_stage_11_three_way_parity(stage_11_dir):
    cpu_comp = json.loads((stage_11_dir / "gpu_incremental_cpu_comparison.json").read_text(encoding="utf-8"))
    assert cpu_comp["all_tolerances_satisfied"] is True
    full_comp = json.loads((stage_11_dir / "gpu_incremental_full_comparison.json").read_text(encoding="utf-8"))
    assert full_comp["all_tolerances_satisfied"] is True
