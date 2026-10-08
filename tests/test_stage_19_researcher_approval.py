"""
Pytest validation suite for Stage 19: Researcher Approval of Terrain and Tree Data.
"""

import csv
import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_19_dir = root_dir / "results" / "stage_19_researcher_approval"


def test_stage_19_artifacts_exist():
    assert stage_19_dir.exists(), "Stage 19 results directory missing!"
    required_files = [
        "researcher_approval_schema.json",
        "researcher_approval_form.md",
        "researcher_decision_matrix.csv",
        "terrain_tree_promotion_decision.json",
        "approval_status.json",
        "stage_19_test_results.json",
    ]
    for rf in required_files:
        f = stage_19_dir / rf
        assert f.exists(), f"Required Stage 19 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_19_approval_pending_status():
    status_path = stage_19_dir / "approval_status.json"
    with open(status_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_status"] == "STAGE_19_HUMAN_APPROVAL_PENDING"
    assert data["human_approval_present"] is False
    assert data["data_promotion_blocked"] is True
    assert data["real_world_solver_integration_blocked"] is True
    assert data["token"] == "STAGE_19_HUMAN_APPROVAL_PENDING"


def test_stage_19_promotion_decision_blocked():
    dec_path = stage_19_dir / "terrain_tree_promotion_decision.json"
    with open(dec_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["tree_data_promoted"] is False
    assert data["terrain_data_promoted"] is False
    assert data["fabdem_classification"] == "REGIONAL_REFERENCE_ONLY"
    assert data["promotion_authorized"] is False
    assert data["solver_integration_permitted"] is False


def test_stage_19_decision_matrix_all_pending():
    csv_path = stage_19_dir / "researcher_decision_matrix.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 19
    for r in rows:
        assert r["current_status"] == "PENDING"
        assert r["reviewer_name"] == "Unassigned"
