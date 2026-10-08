"""
Pytest validation suite for Stage 22: Terrain-Aware CPU Reference Solver Extension.
"""

import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_22_dir = root_dir / "results" / "stage_22_cpu_terrain_extension"


def test_stage_22_artifacts_exist():
    assert stage_22_dir.exists(), "Stage 22 results directory missing!"
    required_files = [
        "terrain_cpu_api_manifest.json",
        "terrain_cpu_api.md",
        "terrain_scene_schema.json",
        "terrain_validation_report.json",
        "flat_ground_regression_report.json",
        "synthetic_terrain_test_report.json",
        "church_street_terrain_results.json",
        "terrain_cpu_certificates.json",
        "stage_22_test_results.json",
    ]
    for rf in required_files:
        f = stage_22_dir / rf
        assert f.exists(), f"Required Stage 22 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_22_flat_ground_exact_parity():
    reg_path = stage_22_dir / "flat_ground_regression_report.json"
    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["exact_bit_match_shadow"] is True
    assert data["exact_bit_match_svf"] is True
    assert data["exact_bit_match_tmrt"] is True
    assert data["exact_bit_match_utci"] is True
    assert data["status"] == "PASS_EXACT_EQUIVALENCE"


def test_stage_22_nine_certificates_pass():
    cert_path = stage_22_dir / "terrain_cpu_certificates.json"
    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cert_keys = [f"CERT_{i:02d}" for i in range(1, 10)]
    for ck in cert_keys:
        matching = [v for k, v in data.items() if k.startswith(ck)]
        assert len(matching) == 1, f"Missing certificate: {ck}"
        assert matching[0]["status"] == "PASSED", f"Certificate failed: {ck}"


def test_stage_22_synthetic_suite_pass():
    syn_path = stage_22_dir / "synthetic_terrain_test_report.json"
    with open(syn_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["verdict"] == "SYNTHETIC_SUITE_100_PERCENT_PASSED"
    assert len(data["synthetic_profiles_tested"]) >= 4
