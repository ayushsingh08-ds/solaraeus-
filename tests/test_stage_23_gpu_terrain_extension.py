"""
Pytest validation suite for Stage 23: Terrain-Aware GPU and Incremental Extension.
"""

import json
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
stage_23_dir = root_dir / "results" / "stage_23_gpu_terrain_extension"


def test_stage_23_artifacts_exist():
    assert stage_23_dir.exists(), "Stage 23 results directory missing!"
    required_files = [
        "terrain_gpu_backend_manifest.json",
        "terrain_gpu_full_outputs.json",
        "terrain_gpu_incremental_outputs.json",
        "terrain_gpu_cpu_comparison.json",
        "terrain_gpu_incremental_comparison.json",
        "terrain_gpu_affected_region.json",
        "terrain_gpu_runtime_metrics.json",
        "terrain_gpu_memory_metrics.json",
        "terrain_gpu_certificates.json",
        "stage_23_test_results.json",
    ]
    for rf in required_files:
        f = stage_23_dir / rf
        assert f.exists(), f"Required Stage 23 artifact missing: {rf}"
        assert f.stat().st_size > 0, f"Artifact empty: {rf}"


def test_stage_23_cpu_gpu_parity():
    comp_path = stage_23_dir / "terrain_gpu_cpu_comparison.json"
    with open(comp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["flat_ground_parity"]["exact_bit_match"] is True
    assert data["synthetic_incline_parity"]["parity_status"] == "EXACT_PARITY_PASSED"


def test_stage_23_incremental_comparison():
    inc_path = stage_23_dir / "terrain_gpu_incremental_comparison.json"
    with open(inc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    comp = data["gpu_incremental_vs_full"]
    assert comp["parity_status"] == "WITHIN_CERTIFIED_TOLERANCE"
    assert comp["max_abs_error_tmrt_k"] <= comp["certified_bound_k"]


def test_stage_23_gpu_certificates():
    cert_path = stage_23_dir / "terrain_gpu_certificates.json"
    with open(cert_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 5
    for k, v in data.items():
        if isinstance(v, dict) and "status" in v:
            assert v["status"] == "PASSED", f"GPU certificate failed: {k}"
