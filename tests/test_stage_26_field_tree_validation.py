"""
Tests for SOLARAEUS Stage 26: Field Validation of Trees
"""

import csv
import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_26_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_26_field_tree_validation"


def test_stage_26_artifacts_exist(stage_26_dir):
    assert stage_26_dir.exists()
    required = [
        "field_observation_schema.json",
        "core_tree_field_validation.csv",
        "context_tree_field_validation.csv",
        "tree_existence_validation.json",
        "tree_geometry_measurements.csv",
        "tree_measurement_uncertainty.csv",
        "field_photo_manifest.json",
        "field_validation_report.md",
        "stage_26_test_results.json",
    ]
    for fname in required:
        assert (stage_26_dir / fname).exists(), f"Missing {fname}"


def test_stage_26_core_trees_non_fabrication(stage_26_dir):
    with open(stage_26_dir / "core_tree_field_validation.csv", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 6
    for row in reader:
        assert row["current_existence"] == "CURRENT_EXISTENCE_UNCERTAIN"
        assert row["field_height_m"] == "MISSING_FIELD_OBSERVATION"
        assert row["field_height_m"] != "0"
        assert row["field_height_m"] != "0.0"
        assert row["approval_status"] == "PENDING"


def test_stage_26_existence_status(stage_26_dir):
    def_file = stage_26_dir / "stage_26_deferred_status.json"
    if def_file.exists():
        with open(def_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "STAGE_26_FIELD_VALIDATION_DEFERRED"
        assert data["tree_geometry_status"] == "PHOTO_ESTIMATED_ONLY"
        assert data["current_tree_existence_status"] == "UNCERTAIN"
        assert data["field_measurements_available"] is False
    else:
        with open(stage_26_dir / "tree_existence_validation.json", encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] in ("STAGE_26_FIELD_VALIDATION_PENDING", "STAGE_26_FIELD_VALIDATION_DEFERRED")
        assert data["classification"] == "PHOTO_ESTIMATED_ONLY"
        assert data["calibrated_geometry_claims_permitted"] is False


def test_stage_26_test_results(stage_26_dir):
    with open(stage_26_dir / "stage_26_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] in ("STAGE_26_FIELD_VALIDATION_DEFERRED", "STAGE_26_FIELD_VALIDATION_PENDING")
    assert data["acceptance_criteria_met"] is True
