"""
Pytest validation suite for Stage 21: Field Validation of Tree Dimensions and Existence.
"""

import csv
import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_21_dir = root_dir / "results" / "stage_21_field_tree_validation"


def test_stage_21_artifacts_exist():
    assert stage_21_dir.exists(), "Stage 21 results directory missing!"
    required_files = [
        "field_observation_schema.json",
        "core_tree_field_validation.csv",
        "context_tree_field_validation.csv",
        "tree_geometry_validation_report.md",
        "tree_existence_validation.json",
        "tree_measurement_uncertainty.csv",
        "field_photo_manifest.json",
        "stage_21_test_results.json",
    ]
    for rf in required_files:
        f = stage_21_dir / rf
        assert f.exists(), f"Required Stage 21 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_21_core_trees_photo_estimated():
    csv_path = stage_21_dir / "core_tree_field_validation.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 6
    expected_ids = {"T08", "T09", "T10", "T11", "T12", "T13"}
    found_ids = {r["tree_id"] for r in rows}
    assert found_ids == expected_ids
    for r in rows:
        assert r["measurement_status"] == "PHOTO_ESTIMATED_ONLY"
        assert r["existence_status"] == "UNCERTAIN_HISTORICAL_PHOTO_ONLY"


def test_stage_21_existence_pending():
    ex_path = stage_21_dir / "tree_existence_validation.json"
    with open(ex_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["current_existence_verified_in_field"] is False
    assert data["status"] == "STAGE_21_FIELD_VALIDATION_PENDING"


def test_stage_21_uncertainty_documented():
    unc_path = stage_21_dir / "tree_measurement_uncertainty.csv"
    with open(unc_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 6
    for r in rows:
        assert "±" in r["height_uncertainty_m"]
