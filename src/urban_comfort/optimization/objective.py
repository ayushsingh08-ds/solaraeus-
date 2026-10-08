"""
Thermal Comfort Objective Functions & Evaluation Metrics.

Computes multi-criteria microclimate performance objectives across evaluated pedestrian cells,
including mean UTCI, P90 thermal stress, peak temperature, comfort exceedances, and area penalties.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import numpy as np

from urban_comfort.reference.full_recompute import SimulationResult


@dataclass
class ComfortObjectiveConfig:
    """Configuration weights for scalar composite objective evaluation."""
    weight_mean_utci: float = 1.00
    weight_p90_utci: float = 0.50
    weight_max_utci: float = 0.00
    weight_mean_tmrt: float = 0.00
    weight_area_penalty: float = 0.005     # Penalty per square meter of shade panel
    comfort_threshold_utci: float = 32.0   # UTCI moderate heat stress threshold (degC)
    feasibility_penalty: float = 1000.0    # Penalty added for infeasible designs


@dataclass
class EvaluationMetrics:
    """Diagnostic thermal comfort and spatial performance metrics for a candidate."""
    mean_utci: float
    p90_utci: float
    max_utci: float
    min_utci: float
    mean_tmrt: float
    max_tmrt: float
    pct_improved_cells: float          # Percentage of evaluated cells where UTCI < baseline
    pct_comfortable_cells: float       # Percentage of cells with UTCI < comfort_threshold
    area_m2: float
    area_penalty: float
    objective_value: float
    delta_mean_utci: float             # candidate mean UTCI - baseline mean UTCI (negative is cooling)
    delta_mean_tmrt: float             # candidate mean Tmrt - baseline mean Tmrt
    evaluated_cells_count: int
    peak_local_tmrt_improvement: float = 0.0  # maximum local Tmrt drop across evaluated cells (K)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mean_utci_c": float(self.mean_utci),
            "p90_utci_c": float(self.p90_utci),
            "max_utci_c": float(self.max_utci),
            "min_utci_c": float(self.min_utci),
            "mean_tmrt_c": float(self.mean_tmrt),
            "max_tmrt_c": float(self.max_tmrt),
            "pct_improved_cells": float(self.pct_improved_cells),
            "pct_comfortable_cells": float(self.pct_comfortable_cells),
            "area_m2": float(self.area_m2),
            "area_penalty": float(self.area_penalty),
            "objective_value": float(self.objective_value),
            "delta_mean_utci_c": float(self.delta_mean_utci),
            "delta_mean_tmrt_c": float(self.delta_mean_tmrt),
            "peak_local_tmrt_improvement": float(self.peak_local_tmrt_improvement),
            "evaluated_cells_count": int(self.evaluated_cells_count),
        }


def compute_objective(sim_result: SimulationResult,
                      baseline_result: SimulationResult,
                      eval_mask: np.ndarray,
                      panel_area_m2: float,
                      config: Optional[ComfortObjectiveConfig] = None) -> EvaluationMetrics:
    """
    Computes objective metrics and scalar objective score over valid pedestrian evaluation cells.
    
    Args:
        sim_result: Output from candidate simulation.
        baseline_result: Baseline unshaded simulation reference.
        eval_mask: Boolean mask indicating pedestrian receptors to aggregate (e.g. corridor cells).
        panel_area_m2: Planar area of candidate shade canopy in square meters.
        config: Weighting and threshold configuration.
        
    Returns:
        EvaluationMetrics containing individual metrics and scalar objective_value.
    """
    if config is None:
        config = ComfortObjectiveConfig()

    cand_utci = sim_result.utci
    base_utci = baseline_result.utci
    cand_tmrt = sim_result.tmrt
    base_tmrt = baseline_result.tmrt

    # Mask valid finite evaluation cells
    valid_mask = eval_mask & np.isfinite(cand_utci) & np.isfinite(base_utci)
    cell_count = int(np.sum(valid_mask))

    if cell_count == 0:
        # Fallback for empty domain
        return EvaluationMetrics(
            mean_utci=99.0, p90_utci=99.0, max_utci=99.0, min_utci=99.0,
            mean_tmrt=99.0, max_tmrt=99.0, pct_improved_cells=0.0,
            pct_comfortable_cells=0.0, area_m2=panel_area_m2,
            area_penalty=0.0, objective_value=config.feasibility_penalty,
            delta_mean_utci=0.0, delta_mean_tmrt=0.0, evaluated_cells_count=0
        )

    eval_cand_utci = cand_utci[valid_mask]
    eval_base_utci = base_utci[valid_mask]
    eval_cand_tmrt = cand_tmrt[valid_mask]
    eval_base_tmrt = base_tmrt[valid_mask]

    mean_utci = float(np.mean(eval_cand_utci))
    p90_utci = float(np.percentile(eval_cand_utci, 90))
    max_utci = float(np.max(eval_cand_utci))
    min_utci = float(np.min(eval_cand_utci))

    mean_tmrt = float(np.mean(eval_cand_tmrt))
    max_tmrt = float(np.max(eval_cand_tmrt))

    # Improvement percentages
    diff_utci = eval_cand_utci - eval_base_utci
    improved_count = int(np.sum(diff_utci < -0.01))
    pct_improved = (improved_count / float(cell_count)) * 100.0

    comfortable_count = int(np.sum(eval_cand_utci < config.comfort_threshold_utci))
    pct_comfortable = (comfortable_count / float(cell_count)) * 100.0

    delta_mean_utci = mean_utci - float(np.mean(eval_base_utci))
    delta_mean_tmrt = mean_tmrt - float(np.mean(eval_base_tmrt))
    peak_local_tmrt_improvement = float(np.max(np.maximum(0.0, eval_base_tmrt - eval_cand_tmrt)))

    area_penalty = float(config.weight_area_penalty * panel_area_m2)

    # Scalar objective
    objective = (
        config.weight_mean_utci * mean_utci +
        config.weight_p90_utci * p90_utci +
        config.weight_max_utci * max_utci +
        config.weight_mean_tmrt * mean_tmrt +
        area_penalty
    )

    return EvaluationMetrics(
        mean_utci=mean_utci,
        p90_utci=p90_utci,
        max_utci=max_utci,
        min_utci=min_utci,
        mean_tmrt=mean_tmrt,
        max_tmrt=max_tmrt,
        pct_improved_cells=pct_improved,
        pct_comfortable_cells=pct_comfortable,
        area_m2=panel_area_m2,
        area_penalty=area_penalty,
        objective_value=objective,
        delta_mean_utci=delta_mean_utci,
        delta_mean_tmrt=delta_mean_tmrt,
        evaluated_cells_count=cell_count,
        peak_local_tmrt_improvement=peak_local_tmrt_improvement,
    )
