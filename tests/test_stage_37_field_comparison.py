"""
Tests for SOLARAEUS Stage 37: Field Comparison and Calibration Assessment
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_37_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_37_field_comparison"


def test_stage_37_artifacts_exist(stage_37_dir):
    assert stage_37_dir.exists(), "Stage 37 directory missing"
    required = [
        "field_model_comparison.csv",
        "field_model_error_report.json",
        "calibration_status.json",
        "observation_provenance.json",
        "calibration_limitations.md",
        "stage_37_test_results.json",
    ]
    for fname in required:
        assert (stage_37_dir / fname).exists(), f"Missing {fname}"
        assert (stage_37_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_37_calibration_status(stage_37_dir):
    with open(stage_37_dir / "calibration_status.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_37_FIELD_DATA_UNAVAILABLE"
    assert data["calibrated"] is False
    assert data["token"] == "STAGE_37_FIELD_DATA_UNAVAILABLE"


def test_stage_37_test_results(stage_37_dir):
    with open(stage_37_dir / "stage_37_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_37_FIELD_DATA_UNAVAILABLE"
    assert data["token"] == "STAGE_37_FIELD_DATA_UNAVAILABLE"
    assert data["acceptance_criteria_met"] is True
