"""
Pytest validation suite for Stage 17: Publication Review and Archival Release.
"""

import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_17_dir = root_dir / "results" / "stage_17_publication_review"


def test_stage_17_artifacts_exist():
    assert stage_17_dir.exists(), "Stage 17 results directory missing!"
    required_files = [
        "publication_claim_audit.json",
        "publication_provenance_audit.json",
        "publication_license_audit.json",
        "publication_figure_audit.json",
        "publication_table_audit.json",
        "publication_path_scrub_report.json",
        "publication_review_report.md",
        "archival_manifest.json",
        "stage_17_test_results.json",
    ]
    for rf in required_files:
        f = stage_17_dir / rf
        assert f.exists(), f"Required Stage 17 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_17_claims_audit():
    claim_path = stage_17_dir / "publication_claim_audit.json"
    with open(claim_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["audit_verdict"] == "ALL_CLAIMS_STRICTLY_TRACEABLE_AND_SUBSTANTIATED"
    assert data["unsubstantiated_claims"] == 0
    assert data["verified_claims"] > 0


def test_stage_17_path_scrubbing():
    scrub_path = stage_17_dir / "publication_path_scrub_report.json"
    with open(scrub_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_clean"] is True
    assert data["files_audited"] > 0


def test_stage_17_licensing_and_provenance():
    lic_path = stage_17_dir / "publication_license_audit.json"
    with open(lic_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "LICENSES_VERIFIED_AND_COMPLIANT"
    assert data["license_compatibility"] == "FULLY_COMPATIBLE"

    prov_path = stage_17_dir / "publication_provenance_audit.json"
    with open(prov_path, "r", encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["status"] == "PROVENANCE_FULLY_DOCUMENTED"


def test_stage_17_figures_and_tables_exist():
    fig_path = stage_17_dir / "publication_figure_audit.json"
    with open(fig_path, "r", encoding="utf-8") as f:
        figs = json.load(f)
    assert figs["valid_figures"] == figs["total_figures"]

    tab_path = stage_17_dir / "publication_table_audit.json"
    with open(tab_path, "r", encoding="utf-8") as f:
        tabs = json.load(f)
    assert tabs["valid_tables"] == tabs["total_tables"]


def test_stage_17_archival_manifest_no_autopublish():
    arch_path = stage_17_dir / "archival_manifest.json"
    with open(arch_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["auto_publish"] is False
    assert data["total_files"] > 0
    assert len(data["files"]) == data["total_files"]
