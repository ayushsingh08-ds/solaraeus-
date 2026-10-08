"""
Tests for SOLARAEUS Stages 27 Through 38 Execution and Project Closure
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def results_dir():
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "results"


def test_stage_27_available_terrain_cpu_complete(results_dir):
    st27 = results_dir / "stage_27_available_terrain_cpu_validation"
    assert st27.exists()
    with open(st27 / "available_terrain_cpu_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_27_AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE"
    assert data["token"] == "STAGE_27_AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE"


def test_stage_28_available_terrain_gpu_complete(results_dir):
    st28 = results_dir / "stage_28_available_terrain_gpu_validation"
    assert st28.exists()
    with open(st28 / "available_terrain_gpu_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"
    assert data["token"] == "STAGE_28_AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE"


def test_stage_29_provisional_tree_geometry_complete(results_dir):
    st29 = results_dir / "stage_29_level1_tree_geometry"
    assert st29.exists()
    with open(st29 / "tree_geometry_scene_manifest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_29_PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE"
    assert data["token"] == "STAGE_29_PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE"
    assert data["approved_for_sensitivity_testing"] is True
    assert data["approved_for_calibrated_claims"] is False


def test_stages_30_to_36_complete(results_dir):
    expected_tokens = {
        30: "STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE",
        31: "STAGE_31_GPU_TREE_SHADOW_COMPLETE",
        32: "STAGE_32_TREE_AWARE_INCREMENTAL_COMPLETE",
        33: "STAGE_33_CANOPY_SENSITIVITY_COMPLETE",
        34: "STAGE_34_TERRAIN_TREE_PARITY_COMPLETE",
        35: "STAGE_35_PROVISIONAL_TERRAIN_TREE_OPTIMIZATION_COMPLETE",
        36: "STAGE_36_PROVISIONAL_TERRAIN_TREE_VALIDATION_COMPLETE",
    }
    for stage_num, expected_token in expected_tokens.items():
        stage_subdirs = [d for d in results_dir.glob(f"stage_{stage_num}_*") if not d.name.endswith(".json") and not d.name.endswith(".md")]
        assert len(stage_subdirs) >= 1, f"Missing directory for stage {stage_num}"
        s_dir = stage_subdirs[0]
        test_res_file = s_dir / f"stage_{stage_num}_test_results.json"
        assert test_res_file.exists(), f"Missing test results for stage {stage_num}"
        with open(test_res_file, encoding="utf-8") as f:
            tdata = json.load(f)
        assert tdata["status"] == expected_token


def test_stage_37_field_data_unavailable(results_dir):
    st37 = results_dir / "stage_37_field_comparison"
    assert st37.exists()
    with open(st37 / "calibration_status.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_37_FIELD_DATA_UNAVAILABLE"
    assert data["calibrated"] is False


def test_stage_38_final_publication_and_closure(results_dir):
    st38 = results_dir / "stage_38_final_publication"
    assert st38.exists()
    with open(st38 / "stage_38_test_results.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "STAGE_38_FINAL_PUBLICATION_AND_ARCHIVAL_COMPLETE"
    assert data["token"] == "STAGE_38_FINAL_PUBLICATION_AND_ARCHIVAL_COMPLETE"

    comp_status = results_dir / "FINAL_PROJECT_COMPLETION_STATUS.json"
    assert comp_status.exists()
    with open(comp_status, encoding="utf-8") as f:
        cdata = json.load(f)
    assert cdata["status"] == "SOLARAEUS_PROJECT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
