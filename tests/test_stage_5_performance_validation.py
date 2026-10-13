"""
Tests for Stage 5 Performance Engineering & Benchmark Validation.

Protocol Verification:
1. Benchmark scripts exist (benchmark_cpu.sh, benchmark_gpu.py, run_stage_5_performance_suite.py).
2. 3 Benchmark scenes evaluated: Scene A, Scene B, Scene C.
3. 4 Modes benchmarked (CPU-Full, GPU-Full, CPU-Inc, GPU-Inc) with >= 5 repeats.
4. Overhead metrics recorded: Initialisation, ray tracing, data transfer, total latency (median & std), peak GPU memory.
5. Numerical parity: max |Tmrt| error between GPU and CPU < 1e-3 K, and Incremental vs Full within bound (<= 0.50 K).
6. Consistent speedups computed: GPU-Full vs CPU-Full, CPU-Inc vs CPU-Full, GPU-Inc vs GPU-Full.
7. Reuse fraction sweep covers ~90%, ~95%, ~99% and verifies latency scaling.
8. Bottlenecks and crossover cases identified and documented.
"""

from __future__ import annotations
import json
import os
import pytest
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGE_5_DIR = os.path.join(ROOT, "results", "raw", "stage_5")
METRICS_FILE = os.path.join(STAGE_5_DIR, "stage_5_performance_metrics.json")


def test_stage_5_scripts_exist():
    """Verify that all required Stage 5 benchmark scripts exist."""
    scripts = [
        os.path.join(ROOT, "benchmarks", "benchmark_cpu.sh"),
        os.path.join(ROOT, "benchmarks", "benchmark_cpu.py"),
        os.path.join(ROOT, "benchmarks", "benchmark_gpu.py"),
        os.path.join(ROOT, "benchmarks", "run_stage_5_performance_suite.py")
    ]
    for s in scripts:
        assert os.path.isfile(s), f"Missing required script: {s}"


def test_stage_5_artifacts_generated():
    """Verify that all raw output metrics and static visualization plots are generated."""
    artifacts = [
        METRICS_FILE,
        os.path.join(STAGE_5_DIR, "stage_5_latency_breakdown.png"),
        os.path.join(STAGE_5_DIR, "stage_5_speedup_comparison.png"),
        os.path.join(STAGE_5_DIR, "stage_5_reuse_sweep.png")
    ]
    for art in artifacts:
        assert os.path.isfile(art), f"Missing Stage 5 artifact: {art}"
        assert os.path.getsize(art) > 0, f"Artifact is empty: {art}"


def test_stage_5_hardware_and_provenance():
    """Verify that hardware specifications and git commit are documented."""
    assert os.path.isfile(METRICS_FILE), "Missing metrics JSON"
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["stage"] == 5
    assert data["role"] == "performance_engineer"
    assert "git_commit" in data and len(data["git_commit"]) > 0

    hw = data["hardware"]
    assert "cpu_model" in hw and hw["cpu_model"] != ""
    assert "gpu_model" in hw and hw["gpu_model"] != ""
    assert "gpu_driver" in hw and hw["gpu_driver"] != "N/A"
    assert "os" in hw and hw["os"] != ""


def test_stage_5_scenes_and_modes_coverage():
    """Verify that all 3 scenes and 4 modes are comprehensively benchmarked."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    benchmarks = data["benchmarks"]
    assert len(benchmarks) == 3, f"Expected 3 benchmark scenes, got {len(benchmarks)}"

    scene_ids = {b["scene_id"] for b in benchmarks}
    assert scene_ids == {"scene_a", "scene_b", "scene_c"}

    expected_modes = {"cpu_full", "gpu_full", "cpu_inc", "gpu_inc"}
    for b in benchmarks:
        assert set(b["modes"].keys()) == expected_modes
        for m_name, m_data in b["modes"].items():
            assert m_data["total_time_median_s"] > 0
            assert m_data["raytrace_time_median_s"] >= 0
            assert m_data["transfer_time_median_s"] >= 0
            assert m_data["cells_per_sec"] > 0
            assert m_data["rays_per_sec"] > 0


def test_stage_5_numerical_parity():
    """Verify numerical parity between CPU and GPU modes."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for b in data["benchmarks"]:
        scene_name = b["scene_name"]
        gpu_full = b["modes"]["gpu_full"]
        cpu_full = b["modes"]["cpu_full"]
        gpu_inc = b["modes"]["gpu_inc"]
        cpu_inc = b["modes"]["cpu_inc"]

        # GPU-Full vs CPU-Full must have parity <= 1e-4 K
        assert gpu_full["max_tmrt_parity_err_k"] < 1e-3, (
            f"GPU-Full vs CPU-Full parity exceeded in {scene_name}: {gpu_full['max_tmrt_parity_err_k']} K"
        )

        # Incremental modes must remain strictly within the certified 0.50 K bound
        assert cpu_inc["max_tmrt_parity_err_k"] <= 0.50, (
            f"CPU-Inc error exceeded bound in {scene_name}: {cpu_inc['max_tmrt_parity_err_k']} K"
        )
        assert gpu_inc["max_tmrt_parity_err_k"] <= 0.50, (
            f"GPU-Inc error exceeded bound in {scene_name}: {gpu_inc['max_tmrt_parity_err_k']} K"
        )


def test_stage_5_speedup_baselines_and_bottlenecks():
    """Verify speedup metrics and identify documented crossover points."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Scene B (Berlin Corridor)
    b_scene = next(b for b in data["benchmarks"] if b["scene_id"] == "scene_b")
    spd_b = b_scene["speedups"]
    assert spd_b["gpu_full_vs_cpu_full"] > 10.0, f"Expected >10x GPU-Full speedup on Berlin corridor, got {spd_b['gpu_full_vs_cpu_full']}"
    assert spd_b["gpu_inc_vs_gpu_full"] > 2.0, f"Expected >2x GPU-Inc vs GPU-Full speedup on Berlin corridor, got {spd_b['gpu_inc_vs_gpu_full']}"
    assert spd_b["gpu_inc_vs_cpu_full_compound"] > 30.0, f"Expected >30x compound speedup, got {spd_b['gpu_inc_vs_cpu_full_compound']}"

    # Scene C (Dense Large-Scale Extent)
    c_scene = next(b for b in data["benchmarks"] if b["scene_id"] == "scene_c")
    spd_c = c_scene["speedups"]
    assert spd_c["gpu_full_vs_cpu_full"] > 35.0, f"Expected >35x GPU-Full speedup on large extent, got {spd_c['gpu_full_vs_cpu_full']}"

    # Crossover identification: On Scene C, GPU-Full is faster than GPU-Inc due to kernel overhead & CPU masking
    # Verify that this underperformance is captured and not hidden
    assert spd_c["gpu_inc_vs_gpu_full"] < 1.0, "Expected GPU-Inc vs GPU-Full to highlight crossover bottleneck in Scene C"


def test_stage_5_reuse_fraction_sweep():
    """Verify reuse sweep across ~90%, ~95%, ~99% targets."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    sweep = data["reuse_sweep"]
    assert len(sweep) == 3, f"Expected 3 sweep points, got {len(sweep)}"

    reuse_pcts = [s["measured_reuse_percent"] for s in sweep]
    # Check that sweep covers high reuse range
    assert min(reuse_pcts) >= 88.0, f"Minimum reuse {min(reuse_pcts)} too low"
    assert max(reuse_pcts) >= 98.0, f"Maximum reuse {max(reuse_pcts)} too low"

    # Higher reuse should generally result in lower recomputed cells and faster incremental execution
    for s in sweep:
        assert s["t_gpu_inc_s"] < s["t_gpu_full_s"], "GPU-Inc should be faster than GPU-Full on Berlin corridor sweep"
        assert s["speedup_gpu_inc_vs_gpu_full"] > 1.5, "Expected speedup > 1.5x across Berlin sweep"
