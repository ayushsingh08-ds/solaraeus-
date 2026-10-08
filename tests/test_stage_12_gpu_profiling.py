"""
Unit tests for Stage 12: GPU Runtime, Memory, and Work Profiling.
"""

import json
from pathlib import Path
import pytest


@pytest.fixture
def stage_12_dir():
    p = Path(__file__).resolve().parent.parent / "results" / "stage_12_gpu_profiling"
    assert p.exists(), f"Stage 12 output directory {p} does not exist"
    return p


def test_stage_12_required_files_exist(stage_12_dir):
    required = [
        "gpu_benchmark_trials.csv",
        "gpu_runtime_summary.json",
        "gpu_memory_summary.json",
        "gpu_work_summary.json",
        "gpu_cpu_speedup_report.md",
        "gpu_profiling_environment.json",
        "stage_12_test_results.json"
    ]
    for fname in required:
        fpath = stage_12_dir / fname
        assert fpath.exists(), f"Missing required stage 12 file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_stage_12_test_suite_all_pass(stage_12_dir):
    data = json.loads((stage_12_dir / "stage_12_test_results.json").read_text(encoding="utf-8"))
    assert data["stage"] == 12
    assert data["overall_status"] == "PASS"
    assert data["tests_passed"] == 6
    assert data["tests_failed"] == 0
    assert data["success_token"] == "STAGE_12_GPU_RUNTIME_MEMORY_WORK_PROFILING_COMPLETE"
    for t in data["test_records"]:
        assert t["pass"] is True, f"Stage 12 subtest failed: {t['name']}"


def test_stage_12_work_reduction(stage_12_dir):
    work = json.loads((stage_12_dir / "gpu_work_summary.json").read_text(encoding="utf-8"))
    gpu_inc_work = work["work_allocation"]["GPU Incremental"]
    assert gpu_inc_work["reused_fraction"] > 0.99
    assert gpu_inc_work["ray_work_avoided_pct"] > 99.0


def test_stage_12_speedup_recorded(stage_12_dir):
    runtime = json.loads((stage_12_dir / "gpu_runtime_summary.json").read_text(encoding="utf-8"))
    speedups = runtime["effective_speedup_vs_cpu_full"]
    assert speedups["GPU Full"] > 1.0
    assert speedups["GPU Incremental"] > 1.0
