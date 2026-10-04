"""
Benchmark execution and verification harness for Certified Incremental SOLWEIG.
Compares full recomputation against certified incremental update,
verifies mathematical soundness (actual <= bound), and profiles speedup.
"""

from __future__ import annotations
from dataclasses import dataclass
import time
from typing import List, Dict, Any, Optional
import numpy as np

from solaraeus.core.geometry import UrbanGrid, GeometricEdit
from solaraeus.core.solweig import (
    ReferenceSOLWEIGSolver, WeatherParameters, SOLWEIGConfig, SOLWEIGState
)
from solaraeus.incremental.solver import IncrementalSOLWEIGSolver, IncrementalUpdateResult
from solaraeus.benchmark.adversarial import AdversarialCase


@dataclass
class VerificationRecord:
    """Detailed verification metrics for a single edit experiment."""
    case_name: str
    tolerance_k: float
    max_actual_error_k: float
    max_predicted_bound_k: float
    max_violation_k: float
    num_violations: int
    is_sound: bool
    is_within_tolerance: bool
    reused_fraction: float
    recomputed_cells: int
    total_cells: int
    time_full_sec: float
    time_cert_sec: float
    time_recompute_sec: float
    time_incremental_sec: float
    speedup: float

    # Spatial fields for visual/scientific inspection
    actual_error_map: np.ndarray
    predicted_bound_map: np.ndarray
    t_mrt_full: np.ndarray
    t_mrt_inc: np.ndarray


def run_experiment(initial_grid: UrbanGrid, edit: GeometricEdit,
                   weather: WeatherParameters, config: SOLWEIGConfig,
                   tolerance_k: float = 0.5, case_name: str = "custom_case") -> VerificationRecord:
    """
    Executes a complete verification cycle:
    1. Runs incremental solver with certificate generation and selective recomputation.
    2. Runs full solver from scratch on modified geometry.
    3. Computes exact pointwise error and verifies actual <= bound.
    4. Measures execution times and speedup.
    """
    # 1. Incremental Solver Run
    inc_solver = IncrementalSOLWEIGSolver(initial_grid, weather, config)
    inc_res = inc_solver.apply_edit(edit, tolerance_k=tolerance_k)

    # 2. Full Reference Solver Run on Modified Geometry
    ref_solver = ReferenceSOLWEIGSolver(weather, config)
    t0_full = time.perf_counter()
    full_state = ref_solver.solve(inc_res.grid)
    time_full = time.perf_counter() - t0_full

    # 3. Soundness & Error Analysis
    t_mrt_full = full_state.t_mrt
    t_mrt_inc = inc_res.state.t_mrt
    actual_error = np.abs(t_mrt_inc - t_mrt_full)
    predicted_bound = inc_res.certificate.error_bound

    # Pointwise soundness check: actual_error <= predicted_bound + numerical_slack
    # Numerical slack of 1e-10 accounts for floating point rounding in transcendentals
    slack = actual_error - predicted_bound
    violations = slack > 1e-10
    num_violations = int(np.sum(violations))
    max_violation = float(np.max(slack)) if num_violations > 0 else 0.0

    # User contract check on reused cells: actual_error <= tolerance_k
    reused_mask = ~inc_res.certificate.dirty_mask
    if np.any(reused_mask):
        reused_max_error = float(np.max(actual_error[reused_mask]))
        is_within_tolerance = reused_max_error <= (tolerance_k + 1e-10)
    else:
        reused_max_error = 0.0
        is_within_tolerance = True

    speedup = time_full / max(1e-6, inc_res.time_total_sec)

    return VerificationRecord(
        case_name=case_name,
        tolerance_k=tolerance_k,
        max_actual_error_k=float(np.max(actual_error)),
        max_predicted_bound_k=float(np.max(predicted_bound)),
        max_violation_k=max_violation,
        num_violations=num_violations,
        is_sound=(num_violations == 0),
        is_within_tolerance=is_within_tolerance,
        reused_fraction=inc_res.fraction_reused,
        recomputed_cells=inc_res.num_dirty_cells,
        total_cells=inc_res.total_cells,
        time_full_sec=time_full,
        time_cert_sec=inc_res.time_cert_sec,
        time_recompute_sec=inc_res.time_recompute_sec,
        time_incremental_sec=inc_res.time_total_sec,
        speedup=speedup,
        actual_error_map=actual_error,
        predicted_bound_map=predicted_bound,
        t_mrt_full=t_mrt_full,
        t_mrt_inc=t_mrt_inc
    )


def run_suite(suite: List[AdversarialCase],
              tolerances: List[float] = [0.1, 0.5, 1.0]) -> List[VerificationRecord]:
    """Runs a complete test suite across multiple tolerance thresholds."""
    results = []
    for case in suite:
        for tol in tolerances:
            rec = run_experiment(
                initial_grid=case.grid,
                edit=case.edit,
                weather=case.weather,
                config=case.config,
                tolerance_k=tol,
                case_name=case.name
            )
            results.append(rec)
    return results


def format_markdown_table(records: List[VerificationRecord]) -> str:
    """Formats verification records into a clean GitHub markdown table."""
    headers = [
        "Case", "Tol (K)", "Max Err (K)", "Max Bound (K)",
        "Sound?", "Reused %", "Full (s)", "Cert (ms)", "Recomp (s)", "Speedup"
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for r in records:
        sound_str = "PASS" if r.is_sound else f"FAIL ({r.num_violations})"
        lines.append(
            f"| `{r.case_name}` | {r.tolerance_k:.2f} | {r.max_actual_error_k:.4f} | "
            f"{r.max_predicted_bound_k:.4f} | **{sound_str}** | {r.reused_fraction * 100:.1f}% | "
            f"{r.time_full_sec:.3f} | {r.time_cert_sec * 1000:.1f} | "
            f"{r.time_recompute_sec:.3f} | **{r.speedup:.2f}x** |"
        )
    return "\n".join(lines)
