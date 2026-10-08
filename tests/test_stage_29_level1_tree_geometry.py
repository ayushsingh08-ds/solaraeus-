"""
Tests for SOLARAEUS Stage 29: Provisional Level 1 Tree Geometry Integration
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_29_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results" / "stage_29_level1_tree_geometry"


def test_stage_29_artifacts_exist(stage_29_dir):
    assert stage_29_dir.exists(), "Stage 29 directory missing"
    required = [
        "tree_geometry_schema.json",
        "approved_provisional_tree_geometry.json",
        "tree_geometry_scene_manifest.json",
        "tree_geometry_bounds_report.json",
        "tree_geometry_validation.json",
        "tree_geometry_limitations.md",
        "stage_29_test_results.json",
    ]
    for fname in required:
        assert (stage_29_dir / fname).exists(), f"Missing {fname}"
        assert (stage_29_dir / fname).stat().st_size > 0, f"Empty file: {fname}"


def test_stage_29_manifest_and_status(stage_29_dir):
    with open(stage_29_dir / "tree_geometry_scene_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_29_PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE"
    assert data["tree_geometry_status"] == "PROVISIONAL_PHOTO_ESTIMATED"
    assert data["field_validation_status"] == "DEFERRED"
    assert data["approved_for_sensitivity_testing"] is True
    assert data["approved_for_calibrated_claims"] is False
    assert len(data["core_tree_ids"]) == 6


def test_stage_29_six_core_trees(stage_29_dir):
    with open(stage_29_dir / "approved_provisional_tree_geometry.json", encoding="utf-8") as f:
        data = json.load(f)
    for state in ["CONSERVATIVE_SMALL", "NOMINAL_PROVISIONAL", "CONSERVATIVE_LARGE"]:
        assert state in data
        assert len(data[state]) == 6
        tree_ids = [t["tree_id"] for t in data[state]]
        assert set(tree_ids) == {"T08", "T09", "T10", "T11", "T12", "T13"}


def test_stage_29_test_results(stage_29_dir):
    with open(stage_29_dir / "stage_29_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_29_PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE"
    assert data["token"] == "STAGE_29_PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE"
    assert data["acceptance_criteria_met"] is True
