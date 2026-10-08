"""
Pytest integration for Stage 13: Geographic Feasibility & Intervention Parameterization.
"""

import json
from pathlib import Path
import pytest
from urban_comfort.optimization.parameters import ShadePanelParams
from urban_comfort.optimization.feasibility import (
    FeasibilityConstraints, check_feasibility, RejectionReason
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "stage_13_geographic_feasibility"


def test_stage_13_required_artifacts_exist():
    assert (RESULTS_DIR / "intervention_parameter_schema.json").is_file()
    assert (RESULTS_DIR / "feasibility_rules.json").is_file()
    assert (RESULTS_DIR / "candidate_feasibility_report.json").is_file()
    assert (RESULTS_DIR / "feasible_candidate_catalog.csv").is_file()
    assert (RESULTS_DIR / "infeasible_candidate_catalog.csv").is_file()
    assert (RESULTS_DIR / "stage_13_test_results.json").is_file()
    assert (RESULTS_DIR / "feasibility_plots" / "candidate_feasibility_screening.png").is_file()


def test_stage_13_test_suite_status():
    report = json.loads((RESULTS_DIR / "stage_13_test_results.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "PASS"
    assert report["total_tests"] == 9
    assert report["tests_passed"] == 9
    assert report["tests_failed"] == 0
    assert report["success_token"] == "STAGE_13_GEOGRAPHIC_FEASIBILITY_AND_PARAMETERIZATION_COMPLETE"


def test_stage_13_candidate_screening_metrics():
    report = json.loads((RESULTS_DIR / "candidate_feasibility_report.json").read_text(encoding="utf-8"))
    assert report["total_screened"] >= 100
    assert report["feasible_count"] > 0
    assert report["infeasible_count"] > 0
    assert report["canonical_benchmark_panel_status"] == "FEASIBLE"
    assert "BUILDING_COLLISION" in report["rejection_breakdown"]
    assert "OUT_OF_BOUNDS" in report["rejection_breakdown"]
