"""
Tests for SOLARAEUS Stage 35: Terrain/Tree Intervention Optimization
"""

import csv
import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_35_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_35_terrain_tree_optimization"


def test_stage_35_artifacts_exist(stage_35_dir):
    assert stage_35_dir.exists(), "Stage 35 directory missing"
    required = [
        "terrain_tree_baseline_search.csv",
        "terrain_tree_optimizer_config.json",
        "terrain_tree_candidate_history.csv",
        "terrain_tree_best_candidates.csv",
        "terrain_tree_constraints.json",
        "terrain_tree_certificates.json",
        "terrain_tree_reproducibility.json",
        "terrain_tree_sensitivity_summary.md",
        "stage_35_test_results.json",
    ]
    for fname in required:
        assert (stage_35_dir / fname).exists(), f"Missing {fname}"
        assert (stage_35_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_35_candidate_history_labels(stage_35_dir):
    with open(stage_35_dir / "terrain_tree_candidate_history.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 10
    for r in rows:
        assert r["terrain_status"] == "SYNTHETIC_TERRAIN_ONLY"
        assert r["tree_status"] == "PROVISIONAL_PHOTO_ESTIMATED"
        assert r["canopy_status"] == "LITERATURE_ASSUMED_OR_SENSITIVITY_ONLY"
        assert r["ranking_status"] == "NON_AUTHORITATIVE"


def test_stage_35_test_results(stage_35_dir):
    with open(stage_35_dir / "stage_35_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_35_PROVISIONAL_TERRAIN_TREE_OPTIMIZATION_COMPLETE"
    assert data["token"] == "STAGE_35_PROVISIONAL_TERRAIN_TREE_OPTIMIZATION_COMPLETE"
    assert data["acceptance_criteria_met"] is True
