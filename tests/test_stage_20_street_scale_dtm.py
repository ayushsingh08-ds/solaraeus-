"""
Pytest validation suite for Stage 20: Street-Scale DTM Acquisition or Validation.
"""

import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_20_dir = root_dir / "results" / "stage_20_street_scale_dtm"


def test_stage_20_artifacts_exist():
    assert stage_20_dir.exists(), "Stage 20 results directory missing!"
    required_files = [
        "dtm_source_manifest.json",
        "dtm_quality_report.json",
        "dtm_crs_vertical_datum_report.json",
        "dtm_alignment_report.md",
        "dtm_accuracy_report.json",
        "dtm_validation_plots/synthetic_terrain_profiles.png",
        "dtm_promotion_decision.json",
        "stage_20_test_results.json",
    ]
    for rf in required_files:
        f = stage_20_dir / rf
        assert f.exists(), f"Required Stage 20 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_20_source_manifest_synthetic_only():
    man_path = stage_20_dir / "dtm_source_manifest.json"
    with open(man_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["measured_street_scale_survey_available"] is False
    assert data["selected_development_track"] == "SYNTHETIC_TERRAIN_ONLY"


def test_stage_20_fabdem_regional_only():
    qual_path = stage_20_dir / "dtm_quality_report.json"
    with open(qual_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["fabdem_quality"]["quality_verdict"] == "FAIL_FOR_MICROSCALE_SIMULATION"
    assert data["synthetic_terrain_quality"]["quality_verdict"] == "PASS_FOR_NUMERICAL_SOLVER_VERIFICATION"


def test_stage_20_promotion_decision():
    dec_path = stage_20_dir / "dtm_promotion_decision.json"
    with open(dec_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["measured_dtm_promoted"] is False
    assert data["fabdem_promoted_as_street_dtm"] is False
    assert data["synthetic_terrain_approved_for_software_testing"] is True
    assert data["real_world_terrain_claims_permitted"] is False
    assert data["token"] == "STAGE_20_SYNTHETIC_TERRAIN_ONLY"
