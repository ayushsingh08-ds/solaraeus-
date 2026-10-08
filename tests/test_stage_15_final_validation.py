"""
Pytest integration for Stage 15: Final Candidate Validation & Uncertainty Analysis.
"""

import json
from pathlib import Path
import pytest

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "stage_15_final_validation"


def test_stage_15_required_artifacts_exist():
    assert (RESULTS_DIR / "final_candidate_validation.json").is_file()
    assert (RESULTS_DIR / "final_candidate_validation.md").is_file()
    assert (RESULTS_DIR / "final_candidate_certificates.json").is_file()
    assert (RESULTS_DIR / "final_candidate_parity_report.json").is_file()
    assert (RESULTS_DIR / "final_candidate_uncertainty.csv").is_file()
    assert (RESULTS_DIR / "final_candidate_sensitivity.csv").is_file()
    assert (RESULTS_DIR / "final_candidate_constraint_report.json").is_file()
    assert (RESULTS_DIR / "final_candidate_reproducibility.json").is_file()
    assert (RESULTS_DIR / "stage_15_test_results.json").is_file()


def test_stage_15_test_suite_status():
    report = json.loads((RESULTS_DIR / "stage_15_test_results.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "PASS"
    assert report["total_tests"] == 9
    assert report["tests_passed"] == 9
    assert report["tests_failed"] == 0
    assert report["success_token"] == "STAGE_15_FINAL_CANDIDATE_VALIDATION_AND_UNCERTAINTY_COMPLETE"


def test_stage_15_multi_path_parity():
    parities = json.loads((RESULTS_DIR / "final_candidate_parity_report.json").read_text(encoding="utf-8"))
    assert len(parities) >= 3
    for p in parities:
        assert p["cpu_full_vs_gpu_full"]["pass"] is True
        assert p["cpu_full_vs_gpu_full"]["max_tmrt_error_k"] < 1e-9
        assert p["gpu_inc_vs_gpu_full"]["pass"] is True
        assert p["gpu_inc_vs_gpu_full"]["max_tmrt_error_k"] <= 0.50
        assert p["cpu_full_vs_gpu_inc"]["pass"] is True


def test_stage_15_certificates_and_constraints():
    certs = json.loads((RESULTS_DIR / "final_candidate_certificates.json").read_text(encoding="utf-8"))
    for c in certs:
        assert c["is_certified"] is True
        assert c["violations_count"] == 0
        assert c["bound_valid"] is True

    constraints = json.loads((RESULTS_DIR / "final_candidate_constraint_report.json").read_text(encoding="utf-8"))
    for c in constraints:
        assert c["is_feasible"] is True
        assert c["minimum_constraint_margin"] >= 0.0
        assert c["maximum_constraint_violation"] == 0.0
