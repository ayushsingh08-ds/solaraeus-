"""
Uncertainty-Aware Candidate Acquisition Engine for SOLARAEUS.

Provides acquisition policies (LCB, Expected Improvement, High-Uncertainty,
Boundary Exploration, and Pareto Frontiers) for surrogate-assisted optimization.
Strictly filters all proposed candidates through geographic feasibility before evaluation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np
from scipy.stats import norm

from urban_comfort.optimization.parameters import ShadePanelParams, ParameterBounds
from urban_comfort.optimization.feasibility import FeasibilityConstraints, check_feasibility, RejectionReason
from urban_comfort.optimization.surrogate import SurrogateModel, SurrogatePrediction, FallbackSurrogateModel


@dataclass
class AcquisitionConfig:
    """Configuration for candidate acquisition policies."""
    strategy: str = "hybrid"             # "hybrid", "lcb", "ei", "uncertainty"
    kappa: float = 2.0                   # Lower Confidence Bound exploration weight
    xi: float = 0.01                     # Expected Improvement exploration margin
    pool_size: int = 1000                # Number of candidate samples drawn per acquisition round
    seed: int = 42
    min_diversity_dist: float = 0.03     # Minimum normalized Euclidean distance between batch candidates


def compute_lcb_score(mu: np.ndarray, sigma: np.ndarray, kappa: float = 2.0) -> np.ndarray:
    """
    Computes Lower Confidence Bound score for minimization.
    
    Since we minimize objective f(x), the LCB is:
      LCB(x) = mu(x) - kappa * sigma(x)
    To formulate as an acquisition value to maximize (higher is better):
      alpha_lcb(x) = -LCB(x) = kappa * sigma(x) - mu(x)
    """
    return kappa * sigma - mu


def compute_ei_score(mu: np.ndarray, sigma: np.ndarray, y_best: float, xi: float = 0.01) -> np.ndarray:
    """
    Closed-form Expected Improvement for minimization:
      EI(x) = (y_best - mu(x) - xi) * Phi(Z) + sigma(x) * phi(Z)
    """
    ei = np.zeros_like(mu)
    sigma_safe = np.maximum(sigma, 1e-9)
    diff = y_best - mu - xi
    z = diff / sigma_safe

    # Gaussian CDF and PDF
    phi_z = norm.cdf(z)
    pdf_z = norm.pdf(z)

    # Where uncertainty is non-negligible
    mask = sigma > 1e-6
    ei[mask] = diff[mask] * phi_z[mask] + sigma[mask] * pdf_z[mask]
    # Where uncertainty is zero, deterministic positive improvement
    ei[~mask] = np.maximum(0.0, diff[~mask])
    return np.maximum(0.0, ei)


def compute_normalized_distance(p1: ShadePanelParams, p2: ShadePanelParams, bounds: ParameterBounds) -> float:
    """Computes normalized Euclidean distance between two candidate parameter vectors in [0, 1]^d."""
    ranges = np.array([
        bounds.x_max - bounds.x_min,
        bounds.y_max - bounds.y_min,
        bounds.length_max - bounds.length_min,
        bounds.width_max - bounds.width_min,
        bounds.height_max - bounds.height_min,
        bounds.heading_max - bounds.heading_min,
        bounds.albedo_max - bounds.albedo_min,
    ], dtype=np.float64)
    v1 = bounds.to_vector(p1)
    v2 = bounds.to_vector(p2)
    diff_norm = (v1 - v2) / ranges
    return float(np.linalg.norm(diff_norm) / math.sqrt(len(ranges)))


class CandidateAcquisitionEngine:
    """
    Proposes new intervention candidates using surrogate predictions,
    uncertainty estimates, and geometric feasibility filtering.
    """

    def __init__(self, config: Optional[AcquisitionConfig] = None):
        self.config = config or AcquisitionConfig()
        self.rng = np.random.default_rng(self.config.seed)

    def propose_batch(
        self,
        surrogate: SurrogateModel | FallbackSurrogateModel,
        constraints: FeasibilityConstraints,
        bounds: ParameterBounds,
        current_best_objective: float,
        batch_size: int = 5,
        rng: Optional[np.random.Generator] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates and selects an acquisition batch of geographically feasible candidates.
        
        Returns:
            Tuple of:
              - proposed_candidates: List of dicts with params, tag, prediction, scores
              - pool_diagnostics: Dict with pool size, feasible count, rejected breakdown
        """
        gen = rng or self.rng

        # 1. Generate candidate pool (mix of LHS and uniform samples)
        n_lhs = self.config.pool_size // 2
        n_uniform = self.config.pool_size - n_lhs

        pool_lhs = bounds.sample_lhs(n_lhs, gen)
        pool_uniform = bounds.sample_uniform(gen, n_uniform)
        raw_pool = pool_lhs + pool_uniform

        # 2. Strict Geographic Feasibility Filtering BEFORE simulation
        feasible_pool: List[ShadePanelParams] = []
        rejected_counts: Dict[str, int] = {}
        rejected_details: List[Dict[str, Any]] = []

        for p in raw_pool:
            res = check_feasibility(p, constraints)
            if res.is_valid:
                feasible_pool.append(p)
            else:
                reason = res.rejection_reason.value
                rejected_counts[reason] = rejected_counts.get(reason, 0) + 1
                if len(rejected_details) < 100:
                    rejected_details.append({
                        "params": p.to_dict(),
                        "reason": reason,
                        "message": res.message,
                    })

        if not feasible_pool:
            raise RuntimeError(
                f"Candidate acquisition pool of {self.config.pool_size} generated 0 feasible candidates. "
                "Check parameter bounds and corridor constraints."
            )

        # 3. Surrogate Predictions on Feasible Pool
        predictions = surrogate.predict_batch(feasible_pool)

        # 4. Compute Acquisition Values
        mu_obj = np.array([pred.objective_mean for pred in predictions], dtype=np.float64)
        sigma_obj = np.array([pred.objective_std for pred in predictions], dtype=np.float64)
        mu_utci = np.array([pred.means.get("mean_utci_c", 36.5) for pred in predictions], dtype=np.float64)
        areas = np.array([p.area for p in feasible_pool], dtype=np.float64)

        lcb_scores = compute_lcb_score(mu_obj, sigma_obj, kappa=self.config.kappa)
        ei_scores = compute_ei_score(mu_obj, sigma_obj, y_best=current_best_objective, xi=self.config.xi)
        unc_scores = sigma_obj.copy()

        # Boundary distance score: candidate closeness to parameter bounds
        boundary_closeness = np.zeros(len(feasible_pool), dtype=np.float64)
        for i, p in enumerate(feasible_pool):
            v = bounds.to_vector(p)
            mins = np.array([bounds.x_min, bounds.y_min, bounds.length_min, bounds.width_min, bounds.height_min, bounds.heading_min, bounds.albedo_min])
            maxs = np.array([bounds.x_max, bounds.y_max, bounds.length_max, bounds.width_max, bounds.height_max, bounds.heading_max, bounds.albedo_max])
            norm_dist_to_edges = np.minimum((v - mins) / (maxs - mins), (maxs - v) / (maxs - mins))
            boundary_closeness[i] = float(np.min(norm_dist_to_edges))

        # 5. Pareto Front Identification (Mean UTCI vs Area)
        is_pareto = np.ones(len(feasible_pool), dtype=bool)
        for i in range(len(feasible_pool)):
            u_i = mu_utci[i]
            a_i = areas[i]
            for j in range(len(feasible_pool)):
                if i == j:
                    continue
                if (mu_utci[j] <= u_i and areas[j] <= a_i) and (mu_utci[j] < u_i or areas[j] < a_i):
                    is_pareto[i] = False
                    break

        pareto_indices = np.where(is_pareto)[0]

        # 6. Portfolio Selection Strategy
        selected_candidates: List[Dict[str, Any]] = []
        selected_params: List[ShadePanelParams] = []

        def is_diverse(candidate: ShadePanelParams) -> bool:
            for sp in selected_params:
                if compute_normalized_distance(candidate, sp, bounds) < self.config.min_diversity_dist:
                    return False
            return True

        if self.config.strategy == "hybrid":
            # Target portfolio breakdown:
            # Role 1: Best Predicted Candidate (Max EI or Max LCB)
            ei_ranked = np.argsort(-ei_scores)
            for idx in ei_ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": "surrogate_best_ei",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                    break

            # Role 2: Maximum Uncertainty (Exploration)
            unc_ranked = np.argsort(-unc_scores)
            for idx in unc_ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": "surrogate_high_uncertainty",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                    break

            # Role 3: Boundary Candidate (Closest to geometric bounds)
            bound_ranked = np.argsort(boundary_closeness) # closest to bound edge first
            for idx in bound_ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": "surrogate_boundary",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                            "boundary_distance": float(boundary_closeness[idx]),
                        },
                    })
                    break

            # Role 4: Pareto Front Candidate
            if len(pareto_indices) > 0:
                # Rank pareto candidates by LCB
                pareto_lcb = lcb_scores[pareto_indices]
                sorted_pareto = pareto_indices[np.argsort(-pareto_lcb)]
                for idx in sorted_pareto:
                    cand = feasible_pool[idx]
                    if is_diverse(cand):
                        selected_params.append(cand)
                        selected_candidates.append({
                            "params": cand,
                            "role": "surrogate_pareto",
                            "prediction": predictions[idx],
                            "acquisition_scores": {
                                "ei": float(ei_scores[idx]),
                                "lcb": float(lcb_scores[idx]),
                                "uncertainty": float(unc_scores[idx]),
                            },
                        })
                        break

            # Role 5: Random Feasible Exploration
            perm = gen.permutation(len(feasible_pool))
            for idx in perm:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": "surrogate_random_exploration",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                    break

        elif self.config.strategy == "lcb":
            ranked = np.argsort(-lcb_scores)
            for idx in ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": f"surrogate_lcb_rank_{len(selected_candidates)+1}",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                if len(selected_candidates) >= batch_size:
                    break

        elif self.config.strategy == "ei":
            ranked = np.argsort(-ei_scores)
            for idx in ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": f"surrogate_ei_rank_{len(selected_candidates)+1}",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                if len(selected_candidates) >= batch_size:
                    break

        else: # uncertainty
            ranked = np.argsort(-unc_scores)
            for idx in ranked:
                cand = feasible_pool[idx]
                if is_diverse(cand):
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": f"surrogate_unc_rank_{len(selected_candidates)+1}",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                if len(selected_candidates) >= batch_size:
                    break

        # Fill remaining slots up to batch_size if needed
        if len(selected_candidates) < batch_size:
            lcb_ranked = np.argsort(-lcb_scores)
            for idx in lcb_ranked:
                cand = feasible_pool[idx]
                if cand not in selected_params:
                    selected_params.append(cand)
                    selected_candidates.append({
                        "params": cand,
                        "role": f"surrogate_fill_{len(selected_candidates)+1}",
                        "prediction": predictions[idx],
                        "acquisition_scores": {
                            "ei": float(ei_scores[idx]),
                            "lcb": float(lcb_scores[idx]),
                            "uncertainty": float(unc_scores[idx]),
                        },
                    })
                if len(selected_candidates) >= batch_size:
                    break

        pool_diagnostics = {
            "pool_size": self.config.pool_size,
            "feasible_count": len(feasible_pool),
            "rejected_count": len(raw_pool) - len(feasible_pool),
            "feasible_fraction_pct": round(len(feasible_pool) / len(raw_pool) * 100.0, 2),
            "rejected_breakdown": rejected_counts,
            "pareto_pool_count": len(pareto_indices),
            "rejected_sample_details": rejected_details[:20],
        }

        return selected_candidates[:batch_size], pool_diagnostics
