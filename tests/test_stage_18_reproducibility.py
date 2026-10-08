"""
Pytest validation suite for Stage 18: Clean-Environment Reproducibility Verification.
"""

import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_18_dir = root_dir / "results" / "stage_18_reproducibility"


def test_stage_18_artifacts_exist():
    assert stage_18_dir.exists(), "Stage 18 results directory missing!"
    required_files = [
        "environment_manifest.json",
        "reproduction_commands.md",
        "reproduction_results.json",
        "reproduction_checksum_comparison.json",
        "reproduction_runtime_report.md",
        "reproduction_failure_log.json",
        "stage_18_test_results.json",
    ]
    for rf in required_files:
        f = stage_18_dir / rf
        assert f.exists(), f"Required Stage 18 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_18_environment_manifest():
    env_path = stage_18_dir / "environment_manifest.json"
    with open(env_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "operating_system" in data
    assert "python_version" in data
    assert "hardware" in data
    assert data["random_seed"] == 42


def test_stage_18_reproduction_results():
    rep_path = stage_18_dir / "reproduction_results.json"
    with open(rep_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["overall_status"] == "ALL_TARGETS_SUCCESSFULLY_REPRODUCED"
    assert data["failed_reproductions"] == 0
    assert data["total_targets_reproduced"] >= 9


def test_stage_18_failure_log_empty():
    fail_path = stage_18_dir / "reproduction_failure_log.json"
    with open(fail_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["failures_detected"] == 0
    assert data["status"] == "ZERO_FAILURES"


def test_stage_18_checksums_match():
    chk_path = stage_18_dir / "reproduction_checksum_comparison.json"
    with open(chk_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "ALL_CHECKSUMS_VERIFIED"
    assert data["exact_matches"] == data["total_checksums_evaluated"]
