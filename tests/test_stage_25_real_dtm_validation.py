"""
Tests for SOLARAEUS Stage 25: Real Street-Scale DTM Validation
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_25_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_25_real_dtm_validation"


def test_stage_25_artifacts_exist(stage_25_dir):
    assert stage_25_dir.exists()
    required = [
        "dtm_source_manifest.json",
        "dtm_quality_report.json",
        "dtm_crs_vertical_datum_report.json",
        "dtm_alignment_report.md",
        "dtm_accuracy_report.json",
        "dtm_promotion_decision.json",
        "stage_25_test_results.json",
        "dtm_validation_plots/stage_25_synthetic_profiles.png",
    ]
    for fname in required:
        assert (stage_25_dir / fname).exists(), f"Missing {fname}"


def test_stage_25_fabdem_protection(stage_25_dir):
    with open(stage_25_dir / "dtm_source_manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)
    fabdem = next(s for s in manifest["evaluated_sources"] if s["source_id"] == "SRC_FABDEM_V12")
    assert fabdem["classification"] == "REGIONAL_REFERENCE_ONLY"
    assert manifest["measured_street_scale_dtm_available"] is False
    assert manifest["classification"] == "SYNTHETIC_TERRAIN_ONLY"


def test_stage_25_promotion_decision(stage_25_dir):
    with open(stage_25_dir / "dtm_promotion_decision.json", encoding="utf-8") as f:
        decision = json.load(f)
    assert decision["promotion_to_measured_street_scale"] is False
    assert decision["classification"] == "SYNTHETIC_TERRAIN_ONLY"
    assert decision["real_world_terrain_claims_permitted"] is False
    assert decision["software_engine_testing_permitted"] is True
    assert decision["token"] == "STAGE_25_SYNTHETIC_TERRAIN_ONLY"


def test_stage_25_test_results(stage_25_dir):
    with open(stage_25_dir / "stage_25_test_results.json", encoding="utf-8") as f:
        res = json.load(f)
    assert res["status"] == "STAGE_25_SYNTHETIC_TERRAIN_ONLY"
    assert res["acceptance_criteria_met"] is True
