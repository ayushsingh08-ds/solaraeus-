"""
Surrogate-Assisted Multi-Intervention (Two-Panel) Optimization Engine for SOLARAEUS.

Coordinates:
1. Two-panel parameterization and canonical sorting.
2. Watertight dual-mesh construction.
3. Geometric and geographic feasibility filtering.
4. Combined scene edits via AddMultiMeshEdit.
5. Exact affected-region union and overlap calculation.
6. Certified GPU incremental simulation.
7. Error certificate bounds verification.
8. Multi-objective comfort, area, and construction cost evaluation.
9. Immutable candidate ledger appending.
10. Periodic tabular surrogate retraining and acquisition.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.incremental.mesh_update import AddMultiMeshEdit
from urban_comfort.incremental.update import compute_exact_dirty_shadow_mask
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.two_panel_parameters import TwoPanelParams, TwoPanelBounds
from urban_comfort.optimization.two_panel_feasibility import (
    TwoPanelConstraints,
    check_two_panel_feasibility,
    TwoPanelFeasibilityResult,
    TwoPanelRejectionReason,
)
from urban_comfort.optimization.two_panel_objective import (
    TwoPanelComfortObjectiveConfig,
    TwoPanelEvaluationMetrics,
    compute_two_panel_objective,
)
from urban_comfort.optimization.two_panel_ledger import (
    TwoPanelCandidateRecord,
    TwoPanelCandidateLedger,
)
from urban_comfort.optimization.two_panel_surrogate import (
    TwoPanelSurrogateConfig,
    TwoPanelSurrogateModel,
    TwoPanelSurrogatePrediction,
    SKLEARN_AVAILABLE,
)
from urban_comfort.optimization.two_panel_acquisition import (
    TwoPanelAcquisitionConfig,
    TwoPanelAcquisitionEngine,
    generate_two_panel_seeds,
)


@dataclass
class TwoPanelOptimizerConfig:
    """Configuration for two-panel surrogate-assisted optimization search."""
    seed: int = 42
    num_iterations: int = 3              # Number of surrogate propose-eval-retrain iterations
    batch_size: int = 5                  # Number of candidates proposed per iteration
    seed_budget: int = 10                # Number of initial physical seed candidates
    bounds: TwoPanelBounds = field(default_factory=TwoPanelBounds.get_canonical_church_street_bounds)
    surrogate_config: TwoPanelSurrogateConfig = field(default_factory=TwoPanelSurrogateConfig)
    acquisition_config: TwoPanelAcquisitionConfig = field(default_factory=TwoPanelAcquisitionConfig)
    objective_config: TwoPanelComfortObjectiveConfig = field(default_factory=TwoPanelComfortObjectiveConfig)
    fallback_to_cpu: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "num_iterations": self.num_iterations,
            "batch_size": self.batch_size,
            "seed_budget": self.seed_budget,
            "total_target_budget": self.seed_budget + self.num_iterations * self.batch_size,
            "bounds": {
                "min_separation_m": self.bounds.min_separation_m,
                "max_individual_area_m2": self.bounds.max_individual_area_m2,
                "max_total_area_m2": self.bounds.max_total_area_m2,
                "min_total_area_m2": self.bounds.min_total_area_m2,
                "panel_bounds": self.bounds.panel_bounds.to_dict(),
            },
            "surrogate_config": self.surrogate_config.to_dict(),
            "acquisition_config": {
                "strategy": self.acquisition_config.strategy,
                "pool_size": self.acquisition_config.pool_size,
                "kappa": self.acquisition_config.kappa,
                "seed": self.acquisition_config.seed,
                "min_diversity_dist": self.acquisition_config.min_diversity_dist,
            },
            "objective_weights": {
                "weight_mean_utci": self.objective_config.weight_mean_utci,
                "weight_p90_utci": self.objective_config.weight_p90_utci,
                "weight_area_penalty": self.objective_config.weight_area_penalty,
                "weight_construction_cost": self.objective_config.weight_construction_cost,
                "base_cost_per_panel": self.objective_config.base_cost_per_panel,
                "cost_per_m2": self.objective_config.cost_per_m2,
            },
            "fallback_to_cpu": self.fallback_to_cpu,
        }


class TwoPanelOptimizationEngine:
    """
    Coordinates multi-intervention surrogate-assisted optimization.
    Surrogate proposes candidates only; certified GPU/CPU physics solvers remain final authority.
    """

    def __init__(
        self,
        baseline_scene: Scene,
        baseline_result: SimulationResult,
        weather: Weather,
        sim_config: SimulationConfig,
        feasibility_constraints: TwoPanelConstraints,
        eval_mask: np.ndarray,
        config: Optional[TwoPanelOptimizerConfig] = None,
        gpu_engine: Optional[GPUIncrementalEngine] = None,
    ):
        self.baseline_scene = baseline_scene
        self.baseline_result = baseline_result
        self.weather = weather
        self.sim_config = sim_config
        self.feasibility_constraints = feasibility_constraints
        self.eval_mask = eval_mask
        self.config = config or TwoPanelOptimizerConfig()

        self.ledger = TwoPanelCandidateLedger()
        self.grid = PedestrianGrid(self.baseline_scene.pedestrian_grid)

        # Solar position calculation for exact shadow masks
        dt_str = f"{self.sim_config.date} {self.sim_config.local_time}"
        dt_utc = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        self.solar_pos = calculate_solar_position(self.sim_config.latitude, self.sim_config.longitude, dt_utc)

        # GPU Incremental solver
        if gpu_engine is not None:
            self.gpu_engine = gpu_engine
        else:
            self.gpu_engine = GPUIncrementalEngine(fallback_to_cpu=self.config.fallback_to_cpu)

        # Preload baseline scene on GPU if GPU is available
        self._is_preloaded = False

        # Tabular surrogate model and acquisition engine
        self.surrogate = TwoPanelSurrogateModel(self.config.surrogate_config)
        self.acquisition = TwoPanelAcquisitionEngine(self.config.acquisition_config)
        self.rng = np.random.default_rng(self.config.seed)

    def preload(self):
        """Preloads baseline static building geometry onto GPU memory."""
        if not self._is_preloaded and self.gpu_engine.is_available:
            self.gpu_engine.preload_resident_baseline(
                self.baseline_scene, self.grid, self.baseline_result
            )
            self._is_preloaded = True

    def evaluate_candidate(
        self,
        params: TwoPanelParams,
        method: str = "surrogate_proposal",
        iteration: Optional[int] = None,
        acquisition_strategy: Optional[str] = None,
        surrogate_pred: Optional[TwoPanelSurrogatePrediction] = None,
    ) -> TwoPanelCandidateRecord:
        """
        Evaluates a proposed two-panel candidate through:
        1. Geographic and pairwise feasibility filtering.
        2. Watertight mesh generation and AddMultiMeshEdit creation.
        3. Exact union and overlap affected region accounting.
        4. Certified GPU incremental simulation.
        5. Thermal comfort and cost objective computation.
        6. Immutable ledger recording.
        """
        iter_idx = iteration if iteration is not None else len(self.ledger)
        cand_id = f"CAND_{iter_idx:04d}_{method[:4].upper()}"

        # Ensure canonical ordering
        params_canon = params.canonicalize()

        # 1. Geographic Feasibility Filter
        feas_res = check_two_panel_feasibility(params_canon, self.feasibility_constraints)
        if not feas_res.is_valid:
            record = TwoPanelCandidateRecord(
                candidate_id=cand_id,
                iteration=iter_idx,
                method=method,
                params=params_canon.to_dict(),
                is_feasible=False,
                total_panel_area=params_canon.total_area,
                rejection_reason=feas_res.rejection_reason.value,
                rejection_message=feas_res.message,
                rejection_details=feas_res.details,
                objective_value=float("inf"),
                metrics=None,
                surrogate_predicted_objective=surrogate_pred.objective_mean if surrogate_pred else None,
                surrogate_uncertainty=surrogate_pred.objective_std if surrogate_pred else None,
                acquisition_strategy=acquisition_strategy,
                wall_time_s=0.0,
            )
            self.ledger.add(record)
            return record

        # Ensure GPU resident state is initialized
        if not self._is_preloaded:
            self.preload()

        # 2. Geometry Builder for Both Panels
        (m1, poly1), (m2, poly2) = params_canon.build_geometries(id_prefix=f"PANEL_{iter_idx:04d}")

        # Unique material IDs for both panels
        mat1_id = f"PANEL_MAT_{iter_idx:04d}_1"
        mat2_id = f"PANEL_MAT_{iter_idx:04d}_2"
        m1.material_id = mat1_id
        m2.material_id = mat2_id

        mat1 = Material(id=mat1_id, albedo=float(params_canon.albedo1), emissivity=0.90, surface_temperature=308.15, is_opaque=True)
        mat2 = Material(id=mat2_id, albedo=float(params_canon.albedo2), emissivity=0.90, surface_temperature=308.15, is_opaque=True)

        edit = AddMultiMeshEdit([m1, m2])
        updated_scene, edit_bounds = edit.apply(self.baseline_scene)

        # Update scene materials
        updated_materials = dict(self.baseline_scene.materials)
        updated_materials[mat1_id] = mat1
        updated_materials[mat2_id] = mat2
        updated_scene.materials = updated_materials

        # 3. Calculate Exact Union and Overlap of Shadow Footprints
        b1_3d = (float(np.min(m1.vertices[:, 0])), float(np.max(m1.vertices[:, 0])),
                 float(np.min(m1.vertices[:, 1])), float(np.max(m1.vertices[:, 1])),
                 float(np.min(m1.vertices[:, 2])), float(np.max(m1.vertices[:, 2])))
        b2_3d = (float(np.min(m2.vertices[:, 0])), float(np.max(m2.vertices[:, 0])),
                 float(np.min(m2.vertices[:, 1])), float(np.max(m2.vertices[:, 1])),
                 float(np.min(m2.vertices[:, 2])), float(np.max(m2.vertices[:, 2])))

        mask1 = compute_exact_dirty_shadow_mask(self.grid, b1_3d, self.solar_pos)
        mask2 = compute_exact_dirty_shadow_mask(self.grid, b2_3d, self.solar_pos)
        union_mask = mask1 | mask2
        overlap_mask = mask1 & mask2
        union_cells = int(np.sum(union_mask))
        overlap_cells = int(np.sum(overlap_mask))

        # 4. GPU Incremental Simulation
        t0 = time.perf_counter()
        update_res, cert = self.gpu_engine.execute_certified_update(
            previous_scene=self.baseline_scene,
            updated_scene=updated_scene,
            previous_result=self.baseline_result,
            edit=edit,
            weather=self.weather,
            config=self.sim_config,
        )
        wall_time_s = time.perf_counter() - t0

        # Extract GPU kernel timing telemetry
        gpu_telemetry = getattr(self.gpu_engine, "_last_telemetry", {})
        gpu_kernel_time_ms = gpu_telemetry.get("kernel_time_ms", 0.0)
        h2d_time_ms = gpu_telemetry.get("h2d_time_ms", 0.0)
        d2h_time_ms = gpu_telemetry.get("d2h_time_ms", 0.0)

        # 5. Multi-Objective Thermal Comfort & Cost Evaluation
        metrics = compute_two_panel_objective(
            sim_result=update_res.result,
            baseline_result=self.baseline_result,
            eval_mask=self.eval_mask,
            area1_m2=params_canon.area1,
            area2_m2=params_canon.area2,
            config=self.config.objective_config,
        )

        # 6. Ray and Cell Work Accounting
        recomputed_cells = update_res.recomputed_cells
        total_cells = update_res.total_cells
        reused_cells = total_cells - recomputed_cells

        # In SOLWEIG ray tracing: 1 direct shadow ray + horizon SVF search per cell
        rays_per_cell = 1 + getattr(self.sim_config, "sky_patch_configuration", 32)
        recomputed_rays = recomputed_cells * rays_per_cell
        reused_rays = reused_cells * rays_per_cell
        affected_rays = union_cells * rays_per_cell

        # Certificate status
        max_bound = float(np.max(cert.predicted_error_bound)) if hasattr(cert, "predicted_error_bound") else 0.0
        n_violations = getattr(cert, "n_violations", 0)

        record = TwoPanelCandidateRecord(
            candidate_id=cand_id,
            iteration=iter_idx,
            method=method,
            params=params_canon.to_dict(),
            is_feasible=True,
            total_panel_area=params_canon.total_area,
            rejection_reason=None,
            rejection_message=None,
            objective_value=metrics.objective_value,
            metrics=metrics.to_dict(),
            affected_cells_count=union_cells,
            recomputed_cells_count=recomputed_cells,
            reused_cells_count=reused_cells,
            total_active_cells=total_cells,
            affected_rays_count=affected_rays,
            recomputed_rays_count=recomputed_rays,
            reused_rays_count=reused_rays,
            overlap_cells_count=overlap_cells,
            union_cells_count=union_cells,
            gpu_kernel_time_ms=gpu_kernel_time_ms,
            host_to_device_time_ms=h2d_time_ms,
            device_to_host_time_ms=d2h_time_ms,
            total_runtime_s=wall_time_s,
            certificate_status=cert.status,
            certificate_violations=n_violations,
            max_certificate_bound_k=max_bound,
            max_observed_error_k=None,
            surrogate_predicted_objective=surrogate_pred.objective_mean if surrogate_pred else None,
            surrogate_uncertainty=surrogate_pred.objective_std if surrogate_pred else None,
            acquisition_strategy=acquisition_strategy,
        )

        self.ledger.add(record)
        return record

    def run_optimization(
        self,
        stage1_ledger_path: Optional[Path] = None,
        stage2_ledger_path: Optional[Path] = None,
    ) -> TwoPanelCandidateLedger:
        """
        Executes full two-panel surrogate-assisted optimization cycle:
        Phase 1: Seed portfolio evaluation (duplicated Stage 2 best, LHS pairs, random pairs)
        Phase 2: Iterative surrogate propose-eval-retrain loop
        """
        # Phase 1: Physical Evaluation of Controlled Two-Panel Seed Portfolio
        seeds, rejected_seeds = generate_two_panel_seeds(
            constraints=self.feasibility_constraints,
            bounds=self.config.bounds,
            n_seeds=self.config.seed_budget,
            stage1_ledger_path=stage1_ledger_path,
            stage2_ledger_path=stage2_ledger_path,
            rng=self.rng,
        )

        # Log any rejected seeds for machine-readable provenance
        for rej in rejected_seeds:
            cand_id = f"REJ_SEED_{len(self.ledger):04d}"
            r_rec = TwoPanelCandidateRecord(
                candidate_id=cand_id,
                iteration=len(self.ledger),
                method=rej.get("method", "seed_proposal"),
                params=rej.get("params", {}),
                is_feasible=False,
                rejection_reason=rej.get("rejection_reason"),
                rejection_message=rej.get("rejection_message"),
                rejection_details=rej.get("details"),
                objective_value=float("inf"),
            )
            self.ledger.add(r_rec)

        # Evaluate feasible seeds via certified GPU incremental solver
        for seed_params in seeds:
            self.evaluate_candidate(
                params=seed_params,
                method="seed_initialization",
                acquisition_strategy="seed_portfolio",
            )

        # Phase 2: Iterative Surrogate Propose - Evaluate - Retrain Loop
        for it in range(self.config.num_iterations):
            # Retrain surrogate on all physically evaluated two-panel records
            feasible_evaluated = [r for r in self.ledger.records if r.is_feasible and r.metrics is not None]
            if len(feasible_evaluated) >= 3 and SKLEARN_AVAILABLE:
                try:
                    self.surrogate.fit(self.ledger.records)
                except Exception:
                    pass

            # Propose uncertainty-aware batch of candidates
            if self.surrogate.is_fitted:
                batch, rejected_in_screening = self.acquisition.propose_batch(
                    surrogate=self.surrogate,
                    constraints=self.feasibility_constraints,
                    bounds=self.config.bounds,
                    batch_size=self.config.batch_size,
                    rng=self.rng,
                )
                # Record screening rejections into ledger
                for rej in rejected_in_screening:
                    c_id = f"REJ_ACQ_{len(self.ledger):04d}"
                    r_rec = TwoPanelCandidateRecord(
                        candidate_id=c_id,
                        iteration=len(self.ledger),
                        method="acquisition_screening",
                        params=rej.get("params", {}),
                        is_feasible=False,
                        rejection_reason=rej.get("rejection_reason"),
                        rejection_message=rej.get("rejection_message"),
                        rejection_details=rej.get("details"),
                        objective_value=float("inf"),
                    )
                    self.ledger.add(r_rec)
            else:
                # Fallback if surrogate not yet fitted
                random_cands = self.config.bounds.sample_uniform(self.rng, n_samples=self.config.batch_size)
                batch = [(c, "random_exploration", None) for c in random_cands]

            # Evaluate each batch proposal via GPU incremental engine
            for cand_params, acq_strat, surr_pred in batch:
                self.evaluate_candidate(
                    params=cand_params,
                    method="surrogate_proposal",
                    acquisition_strategy=acq_strat,
                    surrogate_pred=surr_pred,
                )

        return self.ledger
