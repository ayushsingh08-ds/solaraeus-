"""
Thermal Comfort Multi-Objective Formulation for Two-Panel Interventions.

Computes multi-criteria microclimate performance objectives across evaluated pedestrian cells,
including mean UTCI, P90 thermal stress, peak temperature, comfort exceedances, total panel area,
estimated construction cost, and Pareto front identification across thermal improvement, area, and cost.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np

from urban_comfort.reference.full_recompute import SimulationResult


@dataclass
class TwoPanelComfortObjectiveConfig:
    """Configuration weights and costs for two-panel composite objective evaluation."""
    weight_mean_utci: float = 1.00
    weight_p90_utci: float = 0.50
    weight_max_utci: float = 0.00
    weight_mean_tmrt: float = 0.00
    weight_area_penalty: float = 0.005          # Penalty per square meter of shade panel
    weight_construction_cost: float = 0.0001    # Penalty per dollar of construction cost
    base_cost_per_panel: float = 5000.0         # Base foundation & installation cost per panel ($)
    cost_per_m2: float = 250.0                  # Material and structural framing cost per m2 ($)
    comfort_threshold_utci: float = 32.0        # UTCI moderate heat stress threshold (degC)
    feasibility_penalty: float = 1000.0         # Penalty added for infeasible designs
    obstruction_penalty: float = 0.0            # Penalty for pedestrian corridor narrowing


@dataclass
class TwoPanelEvaluationMetrics:
    """Comprehensive diagnostic thermal comfort and spatial performance metrics for two-panel candidate."""
    mean_utci: float
    p90_utci: float
    max_utci: float
    min_utci: float
    mean_tmrt: float
    max_tmrt: float
    pct_improved_cells: float           # Percentage of evaluated cells where UTCI < baseline
    pct_comfortable_cells: float        # Percentage of cells with UTCI < comfort_threshold
    area1_m2: float
    area2_m2: float
    total_area_m2: float
    area_penalty: float
    estimated_construction_cost: float  # Total estimated construction cost ($)
    construction_cost_penalty: float
    obstruction_penalty: float
    objective_value: float
    delta_mean_utci: float              # candidate mean UTCI - baseline mean UTCI (negative is cooling)
    delta_mean_tmrt: float              # candidate mean Tmrt - baseline mean Tmrt (negative is cooling)
    thermal_improvement_utci: float     # baseline mean UTCI - candidate mean UTCI (positive is improvement)
    peak_local_tmrt_improvement: float  # maximum local Tmrt drop across evaluated cells (K)
    evaluated_cells_count: int

    @property
    def mean_utci_c(self) -> float:
        return self.mean_utci

    @property
    def p90_utci_c(self) -> float:
        return self.p90_utci

    @property
    def max_utci_c(self) -> float:
        return self.max_utci

    @property
    def mean_tmrt_c(self) -> float:
        return self.mean_tmrt

    @property
    def delta_mean_utci_c(self) -> float:
        return self.delta_mean_utci

    @property
    def delta_mean_tmrt_c(self) -> float:
        return self.delta_mean_tmrt

    @property
    def peak_local_tmrt_improvement_k(self) -> float:
        return self.peak_local_tmrt_improvement

    @property
    def percentage_cells_improved_pct(self) -> float:
        return self.pct_improved_cells

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
            "area1_m2": float(self.area1_m2),
            "area2_m2": float(self.area2_m2),
            "total_area_m2": float(self.total_area_m2),
            "area_penalty": float(self.area_penalty),
            "estimated_construction_cost_usd": float(self.estimated_construction_cost),
            "construction_cost_penalty": float(self.construction_cost_penalty),
            "obstruction_penalty": float(self.obstruction_penalty),
            "objective_value": float(self.objective_value),
            "delta_mean_utci_c": float(self.delta_mean_utci),
            "delta_mean_tmrt_c": float(self.delta_mean_tmrt),
            "thermal_improvement_utci_c": float(self.thermal_improvement_utci),
            "peak_local_tmrt_improvement_k": float(self.peak_local_tmrt_improvement),
            "evaluated_cells_count": int(self.evaluated_cells_count),
        }


def compute_two_panel_objective(sim_result: SimulationResult,
                                baseline_result: SimulationResult,
                                eval_mask: np.ndarray,
                                area1_m2: float,
                                area2_m2: float,
                                config: Optional[TwoPanelComfortObjectiveConfig] = None,
                                obstruction_penalty: float = 0.0) -> TwoPanelEvaluationMetrics:
    """
    Computes objective metrics and composite scalar score over valid pedestrian evaluation cells.
    """
    if config is None:
        config = TwoPanelComfortObjectiveConfig()

    cand_utci = sim_result.utci
    base_utci = baseline_result.utci
    cand_tmrt = sim_result.tmrt
    base_tmrt = baseline_result.tmrt

    # Mask valid finite evaluation cells
    valid_mask = eval_mask & np.isfinite(cand_utci) & np.isfinite(base_utci)
    cell_count = int(np.sum(valid_mask))

    total_area_m2 = area1_m2 + area2_m2
    est_cost = 2.0 * config.base_cost_per_panel + total_area_m2 * config.cost_per_m2
    cost_penalty = float(config.weight_construction_cost * est_cost)
    area_penalty = float(config.weight_area_penalty * total_area_m2)

    if cell_count == 0:
        return TwoPanelEvaluationMetrics(
            mean_utci=99.0, p90_utci=99.0, max_utci=99.0, min_utci=99.0,
            mean_tmrt=99.0, max_tmrt=99.0,
            pct_improved_cells=0.0, pct_comfortable_cells=0.0,
            area1_m2=area1_m2, area2_m2=area2_m2, total_area_m2=total_area_m2,
            area_penalty=area_penalty,
            estimated_construction_cost=est_cost,
            construction_cost_penalty=cost_penalty,
            obstruction_penalty=obstruction_penalty,
            objective_value=999.0,
            delta_mean_utci=0.0, delta_mean_tmrt=0.0,
            thermal_improvement_utci=0.0,
            peak_local_tmrt_improvement=0.0,
            evaluated_cells_count=0,
        )

    cand_utci_vals = cand_utci[valid_mask]
    base_utci_vals = base_utci[valid_mask]
    cand_tmrt_vals = cand_tmrt[valid_mask]
    base_tmrt_vals = base_tmrt[valid_mask]

    mean_utci = float(np.mean(cand_utci_vals))
    p90_utci = float(np.percentile(cand_utci_vals, 90.0))
    max_utci = float(np.max(cand_utci_vals))
    min_utci = float(np.min(cand_utci_vals))

    mean_tmrt = float(np.mean(cand_tmrt_vals))
    max_tmrt = float(np.max(cand_tmrt_vals))

    base_mean_utci = float(np.mean(base_utci_vals))
    base_mean_tmrt = float(np.mean(base_tmrt_vals))

    delta_mean_utci = mean_utci - base_mean_utci
    delta_mean_tmrt = mean_tmrt - base_mean_tmrt
    thermal_improvement_utci = base_mean_utci - mean_utci

    improved_cells = np.sum(cand_utci_vals < (base_utci_vals - 1e-3))
    pct_improved = float((improved_cells / cell_count) * 100.0)

    comfortable_cells = np.sum(cand_utci_vals < config.comfort_threshold_utci)
    pct_comfortable = float((comfortable_cells / cell_count) * 100.0)

    local_tmrt_improvement = base_tmrt_vals - cand_tmrt_vals
    peak_local_tmrt = float(np.max(local_tmrt_improvement)) if len(local_tmrt_improvement) > 0 else 0.0

    # Composite scalar objective:
    # minimize: mean_UTCI + 0.5 * P90_UTCI + area_penalty + construction_cost_penalty + obstruction_penalty
    obj_val = (
        config.weight_mean_utci * mean_utci
        + config.weight_p90_utci * p90_utci
        + config.weight_max_utci * max_utci
        + config.weight_mean_tmrt * mean_tmrt
        + area_penalty
        + cost_penalty
        + obstruction_penalty
    )

    return TwoPanelEvaluationMetrics(
        mean_utci=mean_utci,
        p90_utci=p90_utci,
        max_utci=max_utci,
        min_utci=min_utci,
        mean_tmrt=mean_tmrt,
        max_tmrt=max_tmrt,
        pct_improved_cells=pct_improved,
        pct_comfortable_cells=pct_comfortable,
        area1_m2=area1_m2,
        area2_m2=area2_m2,
        total_area_m2=total_area_m2,
        area_penalty=area_penalty,
        estimated_construction_cost=est_cost,
        construction_cost_penalty=cost_penalty,
        obstruction_penalty=obstruction_penalty,
        objective_value=obj_val,
        delta_mean_utci=delta_mean_utci,
        delta_mean_tmrt=delta_mean_tmrt,
        thermal_improvement_utci=thermal_improvement_utci,
        peak_local_tmrt_improvement=peak_local_tmrt,
        evaluated_cells_count=cell_count,
    )


def _extract_pareto_triplet(cand: Any) -> Tuple[float, float, float]:
    if isinstance(cand, dict):
        t = cand.get("thermal_improvement_utci_c", cand.get("delta_mean_utci_c", 0.0))
        a = cand.get("total_area_m2", cand.get("total_panel_area", 0.0))
        c = cand.get("estimated_construction_cost_usd", 0.0)
        return float(t), float(a), float(c)
    m = getattr(cand, "metrics", None) or {}
    t = m.get("thermal_improvement_utci_c", m.get("delta_mean_utci_c", 0.0))
    a = getattr(cand, "total_panel_area", 0.0)
    c = m.get("estimated_construction_cost_usd", 0.0)
    return float(t), float(a), float(c)


def compute_pareto_front(candidates: Sequence[Any]) -> List[Any]:
    """
    Identifies non-dominated Pareto candidates optimizing:
    1. Thermal improvement (maximize thermal_improvement_utci_c)
    2. Total panel area (minimize total_area_m2)
    3. Estimated construction cost (minimize estimated_construction_cost_usd)

    Accepts either dictionaries or TwoPanelCandidateRecord objects.
    """
    if not candidates:
        return []

    # Filter only feasible if objects
    filtered = [
        c for c in candidates
        if (isinstance(c, dict) and c.get("is_feasible", True))
        or (not isinstance(c, dict) and getattr(c, "is_feasible", True) and getattr(c, "metrics", None) is not None)
    ]
    if not filtered:
        return []

    pareto_set: List[Any] = []

    for i, cand_a in enumerate(filtered):
        is_dominated = False
        t_a, a_a, c_a = _extract_pareto_triplet(cand_a)

        for j, cand_b in enumerate(filtered):
            if i == j:
                continue
            t_b, a_b, c_b = _extract_pareto_triplet(cand_b)

            better_or_equal = (t_b >= t_a - 1e-5) and (a_b <= a_a + 1e-5) and (c_b <= c_a + 1e-5)
            strictly_better = (t_b > t_a + 1e-5) or (a_b < a_a - 1e-5) or (c_b < c_a - 1e-5)

            if better_or_equal and strictly_better:
                is_dominated = True
                break

        if not is_dominated:
            pareto_set.append(cand_a)

    return pareto_set
