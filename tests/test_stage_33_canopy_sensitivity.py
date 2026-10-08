"""
Tests for SOLARAEUS Stage 33: Canopy-Parameter Sensitivity Analysis
"""

import csv
import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_33_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_33_canopy_sensitivity"


def test_stage_33_artifacts_exist(stage_33_dir):
    assert stage_33_dir.exists(), "Stage 33 directory missing"
    required = [
        "canopy_parameter_manifest.json",
        "canopy_parameter_ranges.csv",
        "canopy_sensitivity_results.csv",
        "species_sensitivity_report.md",
        "canopy_uncertainty_report.json",
        "canopy_assumption_limits.md",
        "stage_33_test_results.json",
    ]
    for fname in required:
        assert (stage_33_dir / fname).exists(), f"Missing {fname}"
        assert (stage_33_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_33_manifest_and_labels(stage_33_dir):
    with open(stage_33_dir / "canopy_parameter_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_33_CANOPY_SENSITIVITY_COMPLETE"
    assert data["canopy_validation_status"] == "CANOPY_PARAMETERS_NOT_FIELD_VALIDATED"
    assert data["calibration_claim"] == "CANOPY_LEVEL_2_CALIBRATION_NOT_CLAIMED"
    assert data["token"] == "STAGE_33_CANOPY_SENSITIVITY_COMPLETE"


def test_stage_33_sensitivity_results(stage_33_dir):
    with open(stage_33_dir / "canopy_sensitivity_results.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 6
    regimes = [r["regime"] for r in rows]
    assert "opaque_canopy" in regimes
    assert "sparse_canopy" in regimes


def test_stage_33_test_results(stage_33_dir):
    with open(stage_33_dir / "stage_33_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_33_CANOPY_SENSITIVITY_COMPLETE"
    assert data["token"] == "STAGE_33_CANOPY_SENSITIVITY_COMPLETE"
    assert data["acceptance_criteria_met"] is True
