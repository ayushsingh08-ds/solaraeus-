"""
Unit tests for Stage 10: Complete GPU Full-vs-CPU Validation.
"""

import json
from pathlib import Path
import pytest
import numpy as np


@pytest.fixture
def stage_10_dir():
    p = Path(__file__).resolve().parent.parent / "results" / "stage_10_gpu_full_cpu_validation"
    assert p.exists(), f"Stage 10 output directory {p} does not exist"
    return p


def test_stage_10_required_files_exist(stage_10_dir):
    required = [
        "cpu_gpu_full_comparison.json",
        "cpu_gpu_full_comparison.md",
        "gpu_full_validation_certificate.json",
        "gpu_full_runtime_metadata.json",
        "gpu_full_reproducibility_report.json",
        "stage_10_test_results.json",
        "gpu_full_arrays.npz"
    ]
    for fname in required:
        fpath = stage_10_dir / fname
        assert fpath.exists(), f"Missing required stage 10 file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_stage_10_test_suite_all_pass(stage_10_dir):
    data = json.loads((stage_10_dir / "stage_10_test_results.json").read_text(encoding="utf-8"))
    assert data["stage"] == 10
    assert data["overall_status"] == "PASS"
    assert data["tests_passed"] == 6
    assert data["tests_failed"] == 0
    assert data["success_token"] == "STAGE_10_GPU_FULL_VS_CPU_VALIDATION_COMPLETE"
    for t in data["test_records"]:
        assert t["pass"] is True, f"Stage 10 subtest failed: {t['name']}"


def test_stage_10_certificate_valid(stage_10_dir):
    cert = json.loads((stage_10_dir / "gpu_full_validation_certificate.json").read_text(encoding="utf-8"))
    assert cert["is_valid"] is True
    assert cert["token"] == "STAGE_10_GPU_FULL_VS_CPU_VALIDATION_COMPLETE"
    for field, diff in cert["field_discrepancies"].items():
        assert diff == 0, f"Discrepancies found in {field}: {diff}"


def test_stage_10_numerical_parity_tolerances(stage_10_dir):
    comp = json.loads((stage_10_dir / "cpu_gpu_full_comparison.json").read_text(encoding="utf-8"))
    assert comp["all_fields_passed"] is True
    fields = comp["field_comparisons"]
    assert fields["shadow_mask"]["differing_cells"] == 0
    assert fields["direct_irradiance"]["differing_cells"] == 0
    assert fields["svf"]["differing_cells"] == 0
    assert fields["shortwave_flux"]["differing_cells"] == 0
    assert fields["longwave_flux"]["differing_cells"] == 0
    assert fields["tmrt"]["differing_cells"] == 0
    assert fields["utci"]["differing_cells"] == 0


def test_stage_10_reproducibility(stage_10_dir):
    rep = json.loads((stage_10_dir / "gpu_full_reproducibility_report.json").read_text(encoding="utf-8"))
    assert rep["pass"] is True
    assert rep["inter_trial_shadow_differences"] == 0
    assert rep["inter_trial_svf_max_abs_diff"] == 0.0
    assert rep["inter_trial_tmrt_max_abs_diff_k"] == 0.0
