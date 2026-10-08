"""
Tests for SOLARAEUS Stage 36: Final Provisional Terrain/Tree Candidate Validation
"""

import csv
import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_36_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_36_final_terrain_tree_validation"


def test_stage_36_artifacts_exist(stage_36_dir):
    assert stage_36_dir.exists(), "Stage 36 directory missing"
    required = [
        "final_terrain_tree_candidate_validation.json",
        "final_terrain_tree_candidate_report.md",
        "final_terrain_tree_certificates.json",
        "final_terrain_tree_parity.json",
        "final_terrain_tree_sensitivity.csv",
        "final_terrain_tree_uncertainty.csv",
        "final_terrain_tree_reproducibility.json",
        "final_terrain_tree_limitations.md",
        "stage_36_test_results.json",
    ]
    for fname in required:
        assert (stage_36_dir / fname).exists(), f"Missing {fname}"
        assert (stage_36_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_36_uncertainty_and_stability(stage_36_dir):
    with open(stage_36_dir / "final_terrain_tree_uncertainty.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 4
    for r in rows:
        assert r["ranking_overlap_detected"] == "True"
        assert r["definitive_ranking_permitted"] == "False"


def test_stage_36_test_results(stage_36_dir):
    with open(stage_36_dir / "stage_36_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_36_PROVISIONAL_TERRAIN_TREE_VALIDATION_COMPLETE"
    assert data["token"] == "STAGE_36_PROVISIONAL_TERRAIN_TREE_VALIDATION_COMPLETE"
    assert data["acceptance_criteria_met"] is True
