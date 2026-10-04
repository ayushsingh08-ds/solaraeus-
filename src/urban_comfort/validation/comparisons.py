"""
Numerical comparison tools and pointwise error metrics between microclimate simulation results.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np

from urban_comfort.reference.full_recompute import SimulationResult


@dataclass
class ComparisonMetrics:
    """Detailed error norms and statistical exceedance metrics for a spatial field."""
    field_name: str
    max_absolute_error: float     # L-infinity norm: max |actual - expected|
    mean_absolute_error: float    # L1 norm: mean |actual - expected|
    root_mean_squared_error: float# L2 norm: sqrt(mean((actual - expected)^2))
    tolerance: float              # Evaluated threshold epsilon
    exceedance_count: int         # Number of grid cells where error > tolerance
    exceedance_fraction: float    # Fraction of grid cells where error > tolerance
    total_cells: int
    is_within_tolerance: bool     # True if max_absolute_error <= tolerance
    error_map: np.ndarray         # Shape (ny, nx) pointwise absolute error map


def compare_arrays(actual: np.ndarray, expected: np.ndarray,
                   field_name: str, tolerance: float = 1e-6) -> ComparisonMetrics:
    """
    Computes rigorous error norms between two 2D numpy arrays.
    """
    if actual.shape != expected.shape:
        raise ValueError(
            f"Shape mismatch for field '{field_name}': actual {actual.shape} vs expected {expected.shape}"
        )

    error_map = np.abs(actual - expected)
    total_cells = error_map.size

    max_err = float(np.max(error_map)) if total_cells > 0 else 0.0
    mae = float(np.mean(error_map)) if total_cells > 0 else 0.0
    rmse = float(np.sqrt(np.mean(error_map ** 2))) if total_cells > 0 else 0.0

    # Exceedance check (accounting for floating point precision)
    slack = error_map - tolerance
    exceedance_mask = slack > 1e-10
    exceedance_count = int(np.sum(exceedance_mask))
    exceedance_fraction = exceedance_count / float(total_cells) if total_cells > 0 else 0.0
    is_within_tolerance = (exceedance_count == 0)

    return ComparisonMetrics(
        field_name=field_name,
        max_absolute_error=max_err,
        mean_absolute_error=mae,
        root_mean_squared_error=rmse,
        tolerance=tolerance,
        exceedance_count=exceedance_count,
        exceedance_fraction=exceedance_fraction,
        total_cells=total_cells,
        is_within_tolerance=is_within_tolerance,
        error_map=error_map
    )


def compare_results(result_test: SimulationResult, result_ref: SimulationResult,
                    tmrt_tolerance: float = 0.5,
                    numerical_tolerance: float = 1e-6) -> Dict[str, ComparisonMetrics]:
    """
    Compares all microclimatic fields of two SimulationResult objects.
    """
    comparisons = {}

    comparisons["shadow_mask"] = compare_arrays(
        result_test.shadow_mask, result_ref.shadow_mask,
        field_name="shadow_mask", tolerance=numerical_tolerance
    )
    comparisons["direct_irradiance"] = compare_arrays(
        result_test.direct_irradiance, result_ref.direct_irradiance,
        field_name="direct_irradiance", tolerance=0.1
    )
    comparisons["svf"] = compare_arrays(
        result_test.svf, result_ref.svf,
        field_name="svf", tolerance=1e-3
    )
    comparisons["shortwave_flux"] = compare_arrays(
        result_test.shortwave_flux, result_ref.shortwave_flux,
        field_name="shortwave_flux", tolerance=0.1
    )
    comparisons["longwave_flux"] = compare_arrays(
        result_test.longwave_flux, result_ref.longwave_flux,
        field_name="longwave_flux", tolerance=0.1
    )
    comparisons["tmrt"] = compare_arrays(
        result_test.tmrt, result_ref.tmrt,
        field_name="tmrt", tolerance=tmrt_tolerance
    )
    comparisons["utci"] = compare_arrays(
        result_test.utci, result_ref.utci,
        field_name="utci", tolerance=tmrt_tolerance
    )

    return comparisons


def format_comparison_summary(comparisons: Dict[str, ComparisonMetrics]) -> str:
    """Formats comparison metrics into a structured markdown report."""
    headers = ["Field", "Max Error", "MAE", "RMSE", "Tol", "Exceed %", "Pass?"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for name, m in comparisons.items():
        pass_str = "PASS" if m.is_within_tolerance else f"FAIL ({m.exceedance_count})"
        lines.append(
            f"| `{name}` | {m.max_absolute_error:.4e} | {m.mean_absolute_error:.4e} | "
            f"{m.root_mean_squared_error:.4e} | {m.tolerance:.2e} | "
            f"{m.exceedance_fraction * 100:.2f}% | **{pass_str}** |"
        )
    return "\n".join(lines)
