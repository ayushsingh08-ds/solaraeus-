"""
Pytest integration for Stage 16: Additional-Area Testing and Publication Package.
"""

import json
from pathlib import Path
import pytest

AREAS_DIR = Path(__file__).resolve().parent.parent / "results" / "stage_16_additional_areas"
PUB_DIR = Path(__file__).resolve().parent.parent / "results" / "stage_16_publication_package"


def test_stage_16_additional_areas_artifacts_exist():
    assert (AREAS_DIR / "area_catalog.json").is_file()
    assert (AREAS_DIR / "area_input_validation_report.json").is_file()
    assert (AREAS_DIR / "cross_area_summary.csv").is_file()
    assert (AREAS_DIR / "cross_area_limitations.md").is_file()
    assert (AREAS_DIR / "stage_16_test_results.json").is_file()
    assert (AREAS_DIR / "area_baseline_results" / "brigade_road_baseline.json").is_file()
    assert (AREAS_DIR / "area_intervention_results" / "brigade_road_intervention.json").is_file()
    assert (AREAS_DIR / "area_parity_reports" / "brigade_road_parity.json").is_file()
    assert (AREAS_DIR / "area_certificate_reports" / "brigade_road_certificate.json").is_file()


def test_stage_16_publication_package_artifacts_exist():
    assert (PUB_DIR / "publication_methodology.md").is_file()
    assert (PUB_DIR / "publication_results_summary.md").is_file()
    assert (PUB_DIR / "publication_limitations.md").is_file()
    assert (PUB_DIR / "reproducibility_guide.md").is_file()
    assert (PUB_DIR / "data_and_code_availability.md").is_file()
    assert (PUB_DIR / "license_and_provenance.md").is_file()
    assert (PUB_DIR / "figure_manifest.json").is_file()
    assert (PUB_DIR / "table_manifest.json").is_file()
    assert (PUB_DIR / "final_project_status.json").is_file()
    assert (PUB_DIR / "stage_16_test_results.json").is_file()


def test_stage_16_test_suite_status():
    report = json.loads((PUB_DIR / "stage_16_test_results.json").read_text(encoding="utf-8"))
    assert report["overall_status"] == "PASS"
    assert report["total_tests"] == 9
    assert report["tests_passed"] == 9
    assert report["tests_failed"] == 0
    assert report["success_token"] == "STAGE_16_ADDITIONAL_AREA_TESTING_AND_PUBLICATION_COMPLETE"


def test_stage_16_final_status_and_readiness():
    final_status = json.loads((PUB_DIR / "final_project_status.json").read_text(encoding="utf-8"))
    assert final_status["publication_readiness"] == "PUBLICATION_READY"
    assert len(final_status["stages_completed"]) == 16
    assert final_status["protection_audit"]["frozen_baseline_intact"] is True
