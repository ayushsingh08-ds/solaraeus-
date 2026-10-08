"""
Uncertainty-Aware Candidate Acquisition & Seed Generation for Two-Panel SOLARAEUS Optimization.

Generates initial seed portfolios using:
- Duplicated best single-panel designs with valid corridor offsets
- Cross-pairings of top historical single-panel candidates
- Feasible Latin Hypercube and uniform spatial pairs

Provides acquisition policies (Predicted-Best, High-Uncertainty, Boundary, Pareto, Exploration)
guided by the two-panel tabular surrogate model and strictly filtered through geographic feasibility.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from urban_comfort.optimization.parameters import ShadePanelParams
from urban_comfort.optimization.two_panel_parameters import TwoPanelParams, TwoPanelBounds
from urban_comfort.optimization.two_panel_feasibility import (
    TwoPanelConstraints,
    check_two_panel_feasibility,
    TwoPanelFeasibilityResult,
    TwoPanelRejectionReason,
)
from urban_comfort.optimization.two_panel_surrogate import (
    TwoPanelSurrogateModel,
    TwoPanelSurrogatePrediction,
)
from urban_comfort.optimization.two_panel_objective import compute_pareto_front


@dataclass
class TwoPanelAcquisitionConfig:
    """Configuration for two-panel candidate acquisition portfolio."""
    strategy: str = "portfolio"          # "portfolio", "predicted_best", "uncertainty", "random"
    pool_size: int = 1500                # Number of candidate samples screened per acquisition round
    kappa: float = 1.5                   # LCB exploration coefficient
    seed: int = 42
    min_diversity_dist: float = 0.05     # Minimum normalized Euclidean distance between batch candidates


def compute_normalized_two_panel_distance(p1: TwoPanelParams, p2: TwoPanelParams, bounds: TwoPanelBounds) -> float:
    """Computes normalized Euclidean distance between two 14-parameter candidate vectors."""
    v1 = p1.canonicalize().to_vector()
    v2 = p2.canonicalize().to_vector()
    pb = bounds.panel_bounds
    ranges = np.array([
        pb.x_max - pb.x_min, pb.y_max - pb.y_min, pb.length_max - pb.length_min, pb.width_max - pb.width_min,
        pb.height_max - pb.height_min, pb.heading_max - pb.heading_min, pb.albedo_max - pb.albedo_min,
        pb.x_max - pb.x_min, pb.y_max - pb.y_min, pb.length_max - pb.length_min, pb.width_max - pb.width_min,
        pb.height_max - pb.height_min, pb.heading_max - pb.heading_min, pb.albedo_max - pb.albedo_min,
    ], dtype=np.float64)
    diff_norm = (v1 - v2) / ranges
    return float(np.linalg.norm(diff_norm) / math.sqrt(len(ranges)))


def generate_two_panel_seeds(
    constraints: TwoPanelConstraints,
    bounds: TwoPanelBounds,
    n_seeds: int = 10,
    stage1_ledger_path: Optional[Path] = None,
    stage2_ledger_path: Optional[Path] = None,
    rng: Optional[np.random.Generator] = None,
) -> Tuple[List[TwoPanelParams], List[Dict[str, Any]]]:
    """
    Generates controlled initial two-panel seed candidates using:
    1. Duplicated best single-panel designs with valid separation.
    2. Pairings of top single-panel candidates from Stage 1 and Stage 2.
    3. Latin Hypercube feasible pairs.
    4. Random feasible pairs.

    Returns:
        (feasible_seeds, rejected_proposals)
    """
    if rng is None:
        rng = np.random.default_rng(42)

    feasible_seeds: List[TwoPanelParams] = []
    rejected_proposals: List[Dict[str, Any]] = []

    def _test_and_add(cand: TwoPanelParams, method: str) -> bool:
        c_can = cand.canonicalize()
        res = check_two_panel_feasibility(c_can, constraints)
        if res.is_valid:
            # Check diversity against already accepted seeds
            if all(compute_normalized_two_panel_distance(c_can, s, bounds) >= 0.04 for s in feasible_seeds):
                feasible_seeds.append(c_can)
                return True
        else:
            rejected_proposals.append({
                "method": method,
                "params": c_can.to_dict(),
                "rejection_reason": res.rejection_reason.value,
                "rejection_message": res.message,
                "details": res.details,
            })
        return False

    # 1. Duplicated Stage 2 Best Candidate (CAND_0063_SURR) with spatial offset along corridor
    # CAND_0063_SURR: x=122.120, y=65.789, L=3.48, W=2.95, h=2.99, heading=95.80, albedo=0.68
    best_s2 = ShadePanelParams(
        x=122.120, y=65.789, length=3.48, width=2.95, height=2.99, heading_deg=95.80, albedo=0.68
    )
    # Church Street corridor runs along heading ~102 deg. An offset of dx ~ 18m, dy ~ -3m stays inside corridor
    for dx, dy in [(18.0, -3.5), (15.0, -2.5), (22.0, -4.5)]:
        p2_offset = ShadePanelParams(
            x=best_s2.x + dx, y=best_s2.y + dy, length=best_s2.length, width=best_s2.width,
            height=best_s2.height, heading_deg=best_s2.heading_deg, albedo=best_s2.albedo
        )
        cand = TwoPanelParams.from_panels(best_s2, p2_offset)
        _test_and_add(cand, "seed_duplicated_best_offset")
        if len(feasible_seeds) >= 2:
            break

    # 2. Pairings of top single-panel designs from prior ledgers if provided
    top_singles: List[ShadePanelParams] = []
    for ledger_p in [stage2_ledger_path, stage1_ledger_path]:
        if ledger_p is not None and ledger_p.exists():
            try:
                data = json.loads(ledger_p.read_text(encoding="utf-8"))
                for entry in data:
                    if entry.get("is_feasible") and entry.get("params"):
                        p_d = entry["params"]
                        top_singles.append(ShadePanelParams.from_dict(p_d))
            except Exception:
                pass

    if len(top_singles) >= 2:
        for i in range(min(5, len(top_singles))):
            for j in range(i + 1, min(10, len(top_singles))):
                cand = TwoPanelParams.from_panels(top_singles[i], top_singles[j])
                _test_and_add(cand, "seed_top_single_pair")
                if len(feasible_seeds) >= 4:
                    break

    # 3. Latin Hypercube feasible pairs
    lhs_candidates = bounds.sample_lhs(n_samples=max(20, n_seeds * 5), rng=rng)
    for cand in lhs_candidates:
        _test_and_add(cand, "seed_lhs")
        if len(feasible_seeds) >= int(n_seeds * 0.7):
            break

    # 4. Uniform random space-filling feasible pairs
    attempts = 0
    while len(feasible_seeds) < n_seeds and attempts < 1000:
        attempts += 1
        cand = bounds.sample_uniform(rng)
        _test_and_add(cand, "seed_random")

    return feasible_seeds[:n_seeds], rejected_proposals


class TwoPanelAcquisitionEngine:
    """
    Proposes new two-panel intervention candidates using surrogate predictions,
    ensemble uncertainty, boundary exploration, and geometric feasibility filtering.
    """

    def __init__(self, config: Optional[TwoPanelAcquisitionConfig] = None):
        self.config = config or TwoPanelAcquisitionConfig()
        self.rng = np.random.default_rng(self.config.seed)

    def propose_batch(
        self,
        surrogate: TwoPanelSurrogateModel,
        constraints: TwoPanelConstraints,
        bounds: TwoPanelBounds,
        batch_size: int = 5,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[List[Tuple[TwoPanelParams, str, TwoPanelSurrogatePrediction]], List[Dict[str, Any]]]:
        """
        Proposes a diverse, uncertainty-aware batch of feasible two-panel candidates.

        Returns:
            proposals: List of (TwoPanelParams, acquisition_strategy_name, surrogate_prediction)
            rejected_in_screening: Machine-readable rejections encountered during candidate pool generation.
        """
        if rng is None:
            rng = self.rng

        # 1. Generate screening pool of candidate proposals
        pool: List[TwoPanelParams] = []
        rejected_in_screening: List[Dict[str, Any]] = []

        # Draw LHS and uniform candidates
        lhs_pool = bounds.sample_lhs(n_samples=self.config.pool_size // 2, rng=rng)
        uniform_pool = bounds.sample_uniform(rng, n_samples=self.config.pool_size // 2)

        for c in (lhs_pool + uniform_pool):
            c_can = c.canonicalize()
            res = check_two_panel_feasibility(c_can, constraints)
            if res.is_valid:
                pool.append(c_can)
            else:
                rejected_in_screening.append({
                    "params": c_can.to_dict(),
                    "rejection_reason": res.rejection_reason.value,
                    "rejection_message": res.message,
                    "details": res.details,
                })

        if not pool:
            # Fallback if pool is empty
            fallback = bounds.sample_uniform(rng)
            return [(fallback, "fallback_random", surrogate.predict(fallback))], rejected_in_screening

        # 2. Score pool candidates with surrogate model
        predictions = surrogate.predict_batch(pool)

        # 3. Portfolio selection across distinct exploration/exploitation objectives
        selected: List[Tuple[TwoPanelParams, str, TwoPanelSurrogatePrediction]] = []

        def _is_diverse(cand: TwoPanelParams) -> bool:
            return all(
                compute_normalized_two_panel_distance(cand, s[0], bounds) >= self.config.min_diversity_dist
                for s in selected
            )

        # Strategy A: Predicted-Best (Pure surrogate objective minimization)
        sorted_by_mean = sorted(range(len(pool)), key=lambda i: predictions[i].objective_mean)
        for idx in sorted_by_mean:
            cand = pool[idx]
            if _is_diverse(cand):
                selected.append((cand, "surrogate_predicted_best", predictions[idx]))
                break

        # Strategy B: Lower Confidence Bound (Exploitation + Moderate Uncertainty)
        # LCB = mean - kappa * std
        sorted_by_lcb = sorted(
            range(len(pool)),
            key=lambda i: predictions[i].objective_mean - self.config.kappa * predictions[i].objective_std
        )
        for idx in sorted_by_lcb:
            cand = pool[idx]
            if _is_diverse(cand):
                selected.append((cand, "surrogate_lcb", predictions[idx]))
                break

        # Strategy C: High Uncertainty (Pure epistemic exploration)
        sorted_by_unc = sorted(range(len(pool)), key=lambda i: predictions[i].objective_std, reverse=True)
        for idx in sorted_by_unc:
            cand = pool[idx]
            if _is_diverse(cand):
                selected.append((cand, "surrogate_high_uncertainty", predictions[idx]))
                break

        # Strategy D: Boundary Candidate (Separation distance near minimum threshold 2.0m - 2.5m)
        pool_with_sep = [
            (i, pool[i].separation_distance()) for i in range(len(pool))
            if constraints.min_panel_separation_m <= pool[i].separation_distance() <= constraints.min_panel_separation_m + 0.8
        ]
        if pool_with_sep:
            # Pick the lowest predicted objective among near-boundary candidates
            sorted_boundary = sorted(pool_with_sep, key=lambda item: predictions[item[0]].objective_mean)
            for idx, sep in sorted_boundary:
                cand = pool[idx]
                if _is_diverse(cand):
                    selected.append((cand, "boundary_separation", predictions[idx]))
                    break

        # Strategy E: Multi-Objective Pareto Candidate
        # Screen candidates that trade off high predicted thermal improvement vs lower total area
        pareto_cands_meta = []
        for i in range(len(pool)):
            pareto_cands_meta.append({
                "pool_idx": i,
                "thermal_improvement_utci_c": predictions[i].means.get("thermal_improvement_utci_c", 0.0),
                "total_area_m2": pool[i].total_area,
                "estimated_construction_cost_usd": 10000.0 + pool[i].total_area * 250.0,
            })
        pareto_front_items = compute_pareto_front(pareto_cands_meta)
        if pareto_front_items:
            for item in pareto_front_items:
                idx = item["pool_idx"]
                cand = pool[idx]
                if _is_diverse(cand):
                    selected.append((cand, "surrogate_pareto", predictions[idx]))
                    break

        # Fill remaining slots up to batch_size
        for idx in sorted_by_lcb:
            if len(selected) >= batch_size:
                break
            cand = pool[idx]
            if _is_diverse(cand):
                selected.append((cand, "surrogate_lcb_fill", predictions[idx]))

        return selected[:batch_size], rejected_in_screening
