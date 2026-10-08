"""
Surrogate-Assisted Geographically Constrained Intervention Optimizer.

Coordinates iterative surrogate training, uncertainty-aware acquisition,
geographic feasibility filtering, resident GPU incremental evaluation,
certificate validation, and immutable ledger recording.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.parameters import ShadePanelParams, ParameterBounds, build_panel_geometry
from urban_comfort.optimization.feasibility import FeasibilityConstraints, check_feasibility, RejectionReason
from urban_comfort.optimization.objective import ComfortObjectiveConfig, EvaluationMetrics, compute_objective
from urban_comfort.optimization.ledger import CandidateRecord, CandidateLedger
from urban_comfort.optimization.optimizer import OptimizationEngine, OptimizerConfig
from urban_comfort.optimization.surrogate import (
    SurrogateConfig, SurrogateModel, SurrogatePrediction, FallbackSurrogateModel, SKLEARN_AVAILABLE
)
from urban_comfort.optimization.acquisition import AcquisitionConfig, CandidateAcquisitionEngine


@dataclass
class SurrogateOptimizerConfig:
    """Configuration for surrogate-assisted optimization search."""
    seed: int = 42
    num_iterations: int = 4              # Number of surrogate propose-eval-retrain iterations
    batch_size: int = 5                  # Number of candidates proposed per iteration (total budget = num_iterations * batch_size)
    bounds: ParameterBounds = field(default_factory=ParameterBounds.get_canonical_church_street_bounds)
    surrogate_config: SurrogateConfig = field(default_factory=SurrogateConfig)
    acquisition_config: AcquisitionConfig = field(default_factory=AcquisitionConfig)
    objective_config: ComfortObjectiveConfig = field(default_factory=ComfortObjectiveConfig)
    fallback_to_cpu: bool = False
    use_fallback_surrogate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "num_iterations": self.num_iterations,
            "batch_size": self.batch_size,
            "total_budget": self.num_iterations * self.batch_size,
            "surrogate_config": self.surrogate_config.to_dict(),
            "acquisition_config": {
                "strategy": self.acquisition_config.strategy,
                "kappa": self.acquisition_config.kappa,
                "xi": self.acquisition_config.xi,
                "pool_size": self.acquisition_config.pool_size,
                "seed": self.acquisition_config.seed,
            },
            "bounds": self.bounds.to_dict(),
            "objective_weights": {
                "weight_mean_utci": self.objective_config.weight_mean_utci,
                "weight_p90_utci": self.objective_config.weight_p90_utci,
                "weight_area_penalty": self.objective_config.weight_area_penalty,
            },
            "fallback_to_cpu": self.fallback_to_cpu,
        }


class SurrogateOptimizationEngine:
    """
    Surrogate-assisted optimization engine with physics-in-the-loop GPU incremental evaluation.
    
    The surrogate is an acceleration mechanism that proposes candidates only.
    The certified GPU incremental solver remains the sole physics authority.
    """

    def __init__(
        self,
        baseline_scene: Scene,
        baseline_result: SimulationResult,
        weather: Weather,
        sim_config: SimulationConfig,
        feasibility_constraints: FeasibilityConstraints,
        eval_mask: np.ndarray,
        config: Optional[SurrogateOptimizerConfig] = None,
        gpu_engine: Optional[GPUIncrementalEngine] = None,
    ):
        self.baseline_scene = baseline_scene
        self.baseline_result = baseline_result
        self.weather = weather
        self.sim_config = sim_config
        self.feasibility_constraints = feasibility_constraints
        self.eval_mask = eval_mask
        self.config = config or SurrogateOptimizerConfig()

        # Optimizer configuration for physics evaluation
        base_opt_config = OptimizerConfig(
            seed=self.config.seed,
            bounds=self.config.bounds,
            objective_config=self.config.objective_config,
            fallback_to_cpu=self.config.fallback_to_cpu,
        )
        self.opt_engine = OptimizationEngine(
            baseline_scene=baseline_scene,
            baseline_result=baseline_result,
            weather=weather,
            sim_config=sim_config,
            feasibility_constraints=feasibility_constraints,
            eval_mask=eval_mask,
            config=base_opt_config,
            gpu_engine=gpu_engine,
        )

        # Initialize surrogate model
        if self.config.use_fallback_surrogate or not SKLEARN_AVAILABLE:
            self.surrogate = FallbackSurrogateModel(self.config.surrogate_config)
        else:
            self.surrogate = SurrogateModel(self.config.surrogate_config)

        # Acquisition engine
        self.acquisition_engine = CandidateAcquisitionEngine(self.config.acquisition_config)

        # Tracking state
        self.retraining_history: List[Dict[str, Any]] = []
        self.acquisition_history: List[Dict[str, Any]] = []
        self.surrogate_predictions_log: List[Dict[str, Any]] = []
        self.surrogate_evaluated_records: List[CandidateRecord] = []
        self.initial_dataset_size: int = 0
        self.initial_dataset_hash: str = ""

    @property
    def ledger(self) -> CandidateLedger:
        return self.opt_engine.ledger

    def preload(self) -> float:
        """Preloads resident baseline to GPU."""
        return self.opt_engine.preload()

    def load_initial_dataset(self, ledger_or_path: CandidateLedger | Path | str | List[CandidateRecord]):
        """
        Loads pre-existing candidate ledger (e.g. Stage 1 results) as initial training dataset.
        """
        records: List[CandidateRecord] = []
        if isinstance(ledger_or_path, CandidateLedger):
            records = list(ledger_or_path.records)
        elif isinstance(ledger_or_path, (str, Path)):
            p = Path(ledger_or_path)
            raw = json.loads(p.read_text(encoding="utf-8"))
            for item in raw:
                r = CandidateRecord(
                    candidate_id=item["candidate_id"],
                    iteration=item["iteration"],
                    method=item["method"],
                    params=item["params"],
                    is_feasible=item["is_feasible"],
                    rejection_reason=item.get("rejection_reason"),
                    rejection_message=item.get("rejection_message"),
                    objective_value=float(item["objective_value"]) if item.get("objective_value") is not None else float("inf"),
                    metrics=item.get("metrics"),
                    gpu_metrics=item.get("gpu_metrics"),
                    certificate_status=item.get("certificate_status"),
                    certificate_violations=item.get("certificate_violations"),
                    max_predicted_bound_k=item.get("max_predicted_bound_k"),
                    wall_time_s=float(item.get("wall_time_s", 0.0)),
                )
                records.append(r)
        elif isinstance(ledger_or_path, list):
            records = list(ledger_or_path)

        for rec in records:
            self.opt_engine.ledger.add(rec)

        self.initial_dataset_size = len(records)
        data_rep = json.dumps([{"id": r.candidate_id, "obj": r.objective_value} for r in records], sort_keys=True)
        self.initial_dataset_hash = hashlib.sha256(data_rep.encode("utf-8")).hexdigest()

    def run(self) -> Dict[str, Any]:
        """
        Executes surrogate-assisted optimization loop:
          For iter in 1..num_iterations:
            1. Retrain surrogate on accumulated feasible ledger records
            2. Propose acquisition batch with uncertainty awareness
            3. Verify geographic feasibility
            4. Execute resident GPU incremental physics simulation
            5. Verify certificate and record metrics to ledger
        """
        t0_total = time.perf_counter()

        # Ensure GPU resident baseline is preloaded
        self.preload()

        # If no dataset was pre-loaded, evaluate deterministic baseline as seed
        if len(self.opt_engine.ledger) == 0:
            rec_det = self.opt_engine.run_deterministic_baseline()
            # Also sample a few uniform random to bootstrap surrogate
            for _ in range(4):
                p_rand = self.config.bounds.sample_uniform(self.opt_engine.rng)
                self.opt_engine.evaluate_candidate(p_rand, method="bootstrap_random")

        # Iterative surrogate loop
        for iter_idx in range(1, self.config.num_iterations + 1):
            t_iter_start = time.perf_counter()

            # 1. Retrain surrogate
            t0_train = time.perf_counter()
            train_metrics = self.surrogate.fit(self.opt_engine.ledger.records)
            train_time_s = time.perf_counter() - t0_train

            # Current best observed feasible candidate
            best_cand = self.opt_engine.ledger.get_best()
            current_best_obj = best_cand.objective_value if best_cand else 100.0

            # 2. Candidate Acquisition
            t0_acq = time.perf_counter()
            proposed_batch, pool_diag = self.acquisition_engine.propose_batch(
                surrogate=self.surrogate,
                constraints=self.feasibility_constraints,
                bounds=self.config.bounds,
                current_best_objective=current_best_obj,
                batch_size=self.config.batch_size,
            )
            acq_time_s = time.perf_counter() - t0_acq

            # Log retraining event
            self.retraining_history.append({
                "iteration": iter_idx,
                "train_samples_feasible": train_metrics["n_train_samples"],
                "total_ledger_records": len(self.opt_engine.ledger),
                "train_time_s": round(train_time_s, 4),
                "acq_time_s": round(acq_time_s, 4),
                "dataset_hash": self.surrogate.training_dataset_hash,
                "target_metrics": train_metrics.get("target_metrics", {}),
                "pool_feasible_fraction_pct": pool_diag["feasible_fraction_pct"],
                "current_best_objective": round(current_best_obj, 4),
            })

            # 3. Physical Evaluation of Proposed Batch
            for cand_info in proposed_batch:
                params: ShadePanelParams = cand_info["params"]
                role: str = cand_info["role"]
                prediction: SurrogatePrediction = cand_info["prediction"]
                scores: Dict[str, float] = cand_info["acquisition_scores"]

                global_iter = len(self.opt_engine.ledger)

                # Geographic feasibility check
                feas_check = check_feasibility(params, self.feasibility_constraints)
                if not feas_check.is_valid:
                    # Infeasible candidate: record to ledger, do not evaluate physics
                    rec = self.opt_engine.evaluate_candidate(
                        params, method=f"{role}", iteration=global_iter
                    )
                    self.surrogate_predictions_log.append({
                        "candidate_id": rec.candidate_id,
                        "iteration": global_iter,
                        "role": role,
                        "params": params.to_dict(),
                        "is_feasible": False,
                        "rejection_reason": rec.rejection_reason,
                        "predicted_objective": prediction.objective_mean,
                        "predicted_std": prediction.objective_std,
                        "observed_objective": None,
                        "error": None,
                    })
                    continue

                # Feasible candidate: evaluate with certified GPU incremental solver
                rec = self.opt_engine.evaluate_candidate(
                    params, method=f"{role}", iteration=global_iter
                )
                self.surrogate_evaluated_records.append(rec)

                # Prediction audit
                obs_obj = rec.objective_value
                pred_obj = prediction.objective_mean
                pred_std = prediction.objective_std
                err_obj = obs_obj - pred_obj if math.isfinite(obs_obj) else None

                self.surrogate_predictions_log.append({
                    "candidate_id": rec.candidate_id,
                    "iteration": global_iter,
                    "role": role,
                    "params": params.to_dict(),
                    "is_feasible": rec.is_feasible,
                    "rejection_reason": rec.rejection_reason,
                    "predicted_objective": pred_obj,
                    "predicted_std": pred_std,
                    "predicted_means": prediction.means,
                    "predicted_stds": prediction.stds,
                    "observed_objective": obs_obj if math.isfinite(obs_obj) else None,
                    "observed_mean_utci": rec.metrics.get("mean_utci_c") if rec.metrics else None,
                    "observed_mean_tmrt": rec.metrics.get("mean_tmrt_c") if rec.metrics else None,
                    "error_objective": err_obj,
                    "z_score": (err_obj / pred_std) if (err_obj is not None and pred_std > 1e-6) else 0.0,
                    "acquisition_scores": scores,
                    "gpu_kernel_time_ms": rec.gpu_metrics.get("gpu_kernel_time_ms") if rec.gpu_metrics else None,
                    "reused_fraction_pct": rec.gpu_metrics.get("reused_fraction_pct") if rec.gpu_metrics else None,
                    "certificate_violations": rec.certificate_violations,
                })

                self.acquisition_history.append({
                    "surrogate_iteration": iter_idx,
                    "candidate_id": rec.candidate_id,
                    "role": role,
                    "objective_value": obs_obj,
                    "predicted_objective": pred_obj,
                    "predicted_std": pred_std,
                    "scores": scores,
                })

        total_wall_s = time.perf_counter() - t0_total

        return {
            "total_wall_time_s": round(total_wall_s, 2),
            "surrogate_iterations": self.config.num_iterations,
            "candidates_proposed": len(self.surrogate_predictions_log),
            "candidates_evaluated_physics": len(self.surrogate_evaluated_records),
            "total_ledger_records": len(self.opt_engine.ledger),
            "best_candidate": self.opt_engine.ledger.get_best().to_dict() if self.opt_engine.ledger.get_best() else None,
            "retraining_history": self.retraining_history,
            "predictions_log": self.surrogate_predictions_log,
        }
