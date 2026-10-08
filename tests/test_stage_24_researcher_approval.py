"""
Tests for SOLARAEUS Stage 24: Researcher Approval Closure
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_24_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_24_researcher_approval"


def test_stage_24_artifacts_exist(stage_24_dir):
    assert stage_24_dir.exists()
    required = [
        "researcher_approval_final.json",
        "researcher_approval_final.md",
        "tree_promotion_decision.json",
        "terrain_promotion_decision.json",
        "approval_audit.json",
        "stage_24_test_results.json",
    ]
    for fname in required:
        assert (stage_24_dir / fname).exists(), f"Missing {fname}"


def test_stage_24_approved_status(stage_24_dir):
    with open(stage_24_dir / "researcher_approval_final.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_24_APPROVED"
    assert data["available_data_use_approved"] is True
    assert data["synthetic_terrain_testing_approved"] is True
    assert data["provisional_tree_geometry_sensitivity_approved"] is True
    assert data["canopy_sensitivity_analysis_approved"] is True
    assert data["field_validation_required_before_calibrated_claims"] is True
    assert data["field_validation_deferred"] is True
    assert data["fabdem_status"] == "REGIONAL_REFERENCE_ONLY"
    assert data["measured_street_scale_dtm_available"] is False
    assert data["tree_geometry_field_validated"] is False
    assert data["canopy_parameters_field_validated"] is False


def test_stage_24_promotion_blocked(stage_24_dir):
    with open(stage_24_dir / "tree_promotion_decision.json", encoding="utf-8") as f:
        tree_data = json.load(f)
    assert tree_data["data_promoted_to_processed"] is False
    assert tree_data["status"] == "APPROVED_FOR_SENSITIVITY_ONLY"

    with open(stage_24_dir / "terrain_promotion_decision.json", encoding="utf-8") as f:
        terrain_data = json.load(f)
    assert terrain_data["synthetic_terrain_approved_for_solver_mechanics"] is True
    assert terrain_data["real_world_terrain_claims_permitted"] is False
    assert terrain_data["fabdem_classification"] == "REGIONAL_REFERENCE_ONLY"
    assert terrain_data["street_scale_dtm_status"] == "MISSING"


def test_stage_24_audit_and_test_results(stage_24_dir):
    with open(stage_24_dir / "approval_audit.json", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["approved_decisions"] == 8
    assert audit["gate_status"] == "STAGE_24_APPROVED"

    with open(stage_24_dir / "stage_24_test_results.json", encoding="utf-8") as f:
        test_res = json.load(f)
    assert test_res["status"] == "STAGE_24_APPROVED"
    assert test_res["acceptance_criteria_met"] is True
