"""
Tests for SOLARAEUS Stage 38: Final Publication, Archival Release, and Project Closure
"""

import csv
import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_38_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_38_final_publication"


def test_stage_38_all_16_artifacts_exist(stage_38_dir):
    assert stage_38_dir.exists(), "Stage 38 directory missing"
    required = [
        "final_methodology.md",
        "final_results_summary.md",
        "final_terrain_tree_results.md",
        "final_uncertainty_report.md",
        "final_field_comparison.md",
        "final_limitations.md",
        "final_reproducibility_guide.md",
        "final_data_and_code_availability.md",
        "final_license_and_provenance.md",
        "final_figure_manifest.json",
        "final_table_manifest.json",
        "final_archival_manifest.json",
        "final_project_status.json",
        "final_stage_status_matrix.csv",
        "final_protection_audit.json",
        "stage_38_test_results.json",
    ]
    for fname in required:
        fp = stage_38_dir / fname
        assert fp.exists(), f"Missing required Stage 38 artifact: {fname}"
        assert fp.stat().st_size > 0, f"Empty artifact: {fname}"


def test_stage_38_final_project_status(stage_38_dir):
    with open(stage_38_dir / "final_project_status.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "SOLARAEUS_PROJECT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
    assert data["stage_tokens"]["STAGE_38"] == "FINAL_PUBLICATION_STAGE_38_COMPLETE"
    assert "FIELD_CALIBRATION_NOT_PERFORMED" in data["field_observation_status"]
    assert "FIELD_DATA_UNAVAILABLE" in data["field_observation_status"]
    assert "MEASURED_STREET_SCALE_DTM_NOT_AVAILABLE" in data["terrain_data_status"]
    assert "FABDEM_REGIONAL_REFERENCE_ONLY" in data["terrain_data_status"]
    assert "TREE_GEOMETRY_PHOTO_ESTIMATED_ONLY" in data["tree_data_status"]


def test_stage_38_protection_audit(stage_38_dir):
    with open(stage_38_dir / "final_protection_audit.json", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["all_protected_files_intact"] is True
    assert audit["protected_file_count"] == 14


def test_stage_38_test_results(stage_38_dir):
    with open(stage_38_dir / "stage_38_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_38_FINAL_PUBLICATION_AND_ARCHIVAL_COMPLETE"
    assert data["token"] == "STAGE_38_FINAL_PUBLICATION_AND_ARCHIVAL_COMPLETE"
    assert data["acceptance_criteria_met"] is True
