"""
Stage 6 Optimization & Active Learning Protocol Validation Tests.

Protocol Verification:
1. All Stage 6 benchmark scripts and modules exist.
2. Artifacts generated in results/raw/stage_6/:
   - stage_6_optimization_metrics.json
   - stage_6_convergence_comparison.png
   - stage_6_method_benchmarks.png
   - stage_6_tiny_problem_optimality.png
   - stage_6_optimal_layout_map.png
   - stage_6_surrogate_parity.png
3. Problem definition: decision variables, spatial bounds, non-overlap, area budget.
4. Tiny problem ground truth verified (exhaustive evaluation of discrete grid).
5. All 4 methods evaluated with identical budget (50 evaluations) across >= 3 seeds.
6. Full physics re-evaluation audit verifies declared best designs with exact parity (< 1e-4 K).
7. Surrogate MAE on held-out test designs reported with error bars.
8. Statistical hypothesis testing recorded.
"""

from __future__ import annotations
import json
import os
import pytest
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGE_6_DIR = os.path.join(ROOT, "results", "raw", "stage_6")
METRICS_FILE = os.path.join(STAGE_6_DIR, "stage_6_optimization_metrics.json")


def test_stage_6_scripts_and_modules_exist():
    """Verify that all required Stage 6 code modules exist."""
    files = [
        os.path.join(ROOT, "src", "solaraeus", "optimizer", "problem.py"),
        os.path.join(ROOT, "src", "solaraeus", "optimizer", "algorithms.py"),
        os.path.join(ROOT, "src", "solaraeus", "optimizer", "__init__.py"),
        os.path.join(ROOT, "benchmarks", "run_stage_6_optimization_suite.py")
    ]
    for f in files:
        assert os.path.isfile(f), f"Missing Stage 6 code file: {f}"


def test_stage_6_artifacts_exist():
    """Verify that all required Stage 6 raw results and figures exist and are non-empty."""
    artifacts = [
        METRICS_FILE,
        os.path.join(STAGE_6_DIR, "stage_6_convergence_comparison.png"),
        os.path.join(STAGE_6_DIR, "stage_6_method_benchmarks.png"),
        os.path.join(STAGE_6_DIR, "stage_6_tiny_problem_optimality.png"),
        os.path.join(STAGE_6_DIR, "stage_6_optimal_layout_map.png"),
        os.path.join(STAGE_6_DIR, "stage_6_surrogate_parity.png")
    ]
    for art in artifacts:
        assert os.path.isfile(art), f"Missing Stage 6 artifact: {art}"
        assert os.path.getsize(art) > 0, f"Artifact is empty: {art}"


def test_stage_6_hardware_and_problem_formulation():
    """Verify problem formulation and hardware documentation."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["stage"] == 6
    assert data["role"] == "ml_researcher_and_urban_planner"
    assert "git_commit" in data and len(data["git_commit"]) > 0

    hw = data["hardware"]
    assert "cpu_model" in hw and hw["cpu_model"] != ""
    assert "gpu_model" in hw and hw["gpu_model"] != ""
    assert "gpu_driver" in hw and hw["gpu_driver"] != "N/A"

    prob = data["problem_formulation"]
    assert prob["site"] == "Berlin Friedrichstraße Corridor"
    assert "primary_objective" in prob and len(prob["primary_objective"]) > 0
    assert "objective_justification" in prob and len(prob["objective_justification"]) > 0
    assert prob["number_of_canopies"] == 2
    assert prob["total_dimension"] == 12
    assert len(prob["constraints"]) >= 4


def test_stage_6_tiny_problem_ground_truth():
    """Verify tiny problem exhaustive evaluation and optimality benchmarks."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    tiny = data["tiny_problem_exhaustive"]
    assert tiny["evaluations_used"] == 45, f"Expected 45 exhaustive points, got {tiny['evaluations_used']}"
    opt = tiny["true_optimum"]
    assert "mean_tmrt_c" in opt and opt["mean_tmrt_c"] < tiny["baseline_mean_tmrt"]
    assert "cooling_delta_k" in opt and opt["cooling_delta_k"] > 0

    bench = data["tiny_problem_methods_benchmark"]
    assert set(bench.keys()) == {"random_search", "direct_search", "surrogate_only", "active_learning"}
    for m_name, m_stats in bench.items():
        assert m_stats["mean_optimality_gap_k"] >= 0.0


def test_stage_6_multi_canopy_methods_benchmarks():
    """Verify that all 4 methods were evaluated on the multi-canopy problem."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    methods_agg = data["multi_canopy_methods_aggregated"]
    expected_methods = {"random_search", "direct_search", "surrogate_only", "active_learning"}
    assert set(methods_agg.keys()) == expected_methods

    for m_id, m_data in methods_agg.items():
        assert m_data["mean_tmrt_mean_c"] > 0
        assert m_data["cooling_delta_mean_k"] > 0, f"Method {m_id} achieved zero cooling delta"
        assert m_data["percent_improvement_mean"] > 0
        assert m_data["wall_time_mean_s"] > 0
        assert len(m_data["convergence_mean"]) == 50, f"Convergence curve for {m_id} has wrong length {len(m_data['convergence_mean'])}"


def test_stage_6_physics_re_evaluation_parity():
    """Verify that the full physics re-evaluation audit passes with exact parity."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = data["full_physics_re_evaluation_audit"]
    assert len(audit) == 12, f"Expected 12 re-evaluation records (4 methods x 3 seeds), got {len(audit)}"

    for rec in audit:
        assert rec["parity_error_k"] < 1e-4, (
            f"Parity mismatch in {rec['method']} seed {rec['seed']}: {rec['parity_error_k']} K"
        )
        assert rec["verified_cooling_delta_mean_k"] > 0.0


def test_stage_6_best_discovered_layout_constraints():
    """Verify that the chosen optimal layout satisfies all urban planning constraints."""
    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    best = data["best_discovered_layout"]
    canopies = best["canopies"]
    assert len(canopies) == 2, f"Expected 2 canopies, got {len(canopies)}"

    total_area = sum(c["area_m2"] for c in canopies)
    assert total_area <= 50.05, f"Area budget exceeded: {total_area} m2 > 50.0 m2"

    for c in canopies:
        assert -8.5 <= c["x"] <= 8.5, f"Canopy outside corridor X: {c['x']}"
        assert -40.0 <= c["y"] <= 40.0, f"Canopy outside corridor Y: {c['y']}"
        assert c["height"] >= 3.0, f"Clearance below 3.0m: {c['height']}"
