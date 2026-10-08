"""
Pytest integration for Stage 14: Baseline Search and Constrained AI Optimizer.
"""

import json
from pathlib import Path
import pytest

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "stage_14_constrained_optimizer"


def test_stage_14_required_artifacts_exist():
    assert (RESULTS_DIR / "baseline_search_results.csv").is_file()
    assert (RESULTS_DIR / "optimizer_configuration.json").is_file()
    assert (RESULTS_DIR / "optimizer_candidate_history.csv").is_file()
    assert (RESULTS_DIR / "optimizer_best_candidates.csv").is_file()
    assert (RESULTS_DIR / "optimizer_checkpoint.json").is_file()
    assert (RESULTS_DIR / "optimizer_reproducibility.json").is_file()
    assert (RESULTS_DIR / "optimizer_constraint_report.json").is_file()
    assert (RESULTS_DIR / "optimizer_certificate_summary.json").is_file()
    assert (RESULTS_DIR / "stage_14_test_results.json").is_file()


def test_stage_14_test_suite_status():
    report = json.loads((RESULTS_DIR / "stage_14_test_results.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "PASS"
    assert report["total_tests"] == 9
    assert report["tests_passed"] == 9
    assert report["tests_failed"] == 0
    assert report["success_token"] == "STAGE_14_BASELINE_SEARCH_AND_CONSTRAINED_AI_OPTIMIZER_COMPLETE"


def test_stage_14_certificate_soundness():
    cert_summary = json.loads((RESULTS_DIR / "optimizer_certificate_summary.json").read_text(encoding="utf-8"))
    assert cert_summary["feasible_simulations_count"] > 0
    assert cert_summary["all_certified"] is True
    assert cert_summary["violation_count"] == 0
    assert cert_summary["soundness_rate_pct"] == 100.0


def test_stage_14_constraint_enforcement():
    constraint_report = json.loads((RESULTS_DIR / "optimizer_constraint_report.json").read_text(encoding="utf-8"))
    assert constraint_report["feasible_count"] > 0
    assert constraint_report["infeasible_count"] > 0
    assert "OUT_OF_BOUNDS" in constraint_report["rejection_reasons_breakdown"] or "BUILDING_COLLISION" in constraint_report["rejection_reasons_breakdown"]
