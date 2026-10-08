"""
Intervention Optimizer Engine.

Orchestrates derivative-free candidate generation, geographic feasibility filtering,
physics-in-the-loop GPU incremental evaluation, certificate verification, and candidate recording.
Supports deterministic baseline, uniform random search, Latin-Hypercube Sampling (LHS),
and constrained differential evolution.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult
from urban_comfort.incremental.mesh_update import AddMeshEdit
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.parameters import ShadePanelParams, ParameterBounds, build_panel_geometry
from urban_comfort.optimization.feasibility import FeasibilityConstraints, check_feasibility, RejectionReason
from urban_comfort.optimization.objective import ComfortObjectiveConfig, EvaluationMetrics, compute_objective
from urban_comfort.optimization.ledger import CandidateRecord, CandidateLedger


@dataclass
class OptimizerConfig:
    """Configuration for intervention optimization search."""
    seed: int = 42
    budget_random: int = 25
    budget_lhs: int = 10
    budget_evolutionary: int = 15
    population_size: int = 10
    mutation_factor: float = 0.5
    crossover_prob: float = 0.7
    max_total_evaluations: int = 75
    bounds: ParameterBounds = field(default_factory=ParameterBounds.get_canonical_church_street_bounds)
    objective_config: ComfortObjectiveConfig = field(default_factory=ComfortObjectiveConfig)
    fallback_to_cpu: bool = False


class OptimizationEngine:
    """
    Main physics-in-the-loop optimization coordinator.
    Ensures that only geographically feasible candidates are simulated using
    the resident GPU incremental solver.
    """

    def __init__(
        self,
        baseline_scene: Scene,
        baseline_result: SimulationResult,
        weather: Weather,
        sim_config: SimulationConfig,
        feasibility_constraints: FeasibilityConstraints,
        eval_mask: np.ndarray,
        config: Optional[OptimizerConfig] = None,
        gpu_engine: Optional[GPUIncrementalEngine] = None,
    ):
        self.baseline_scene = baseline_scene
        self.baseline_result = baseline_result
        self.weather = weather
        self.sim_config = sim_config
        self.feasibility_constraints = feasibility_constraints
        self.eval_mask = eval_mask
        self.config = config or OptimizerConfig()
        self.ledger = CandidateLedger()

        self.gpu_engine = gpu_engine or GPUIncrementalEngine(fallback_to_cpu=self.config.fallback_to_cpu)
        self.grid = PedestrianGrid(baseline_scene.pedestrian_grid)
        self._is_preloaded: bool = False
        self.rng = np.random.default_rng(self.config.seed)

    def preload(self) -> float:
        """Preloads baseline static geometry and physical fields into GPU memory once."""
        if self._is_preloaded:
            return 0.0
        t0 = time.perf_counter()
        if self.gpu_engine.is_available:
            self.gpu_engine.preload_resident_baseline(self.baseline_scene, self.grid, self.baseline_result)
        self._is_preloaded = True
        return time.perf_counter() - t0

    def evaluate_candidate(
        self,
        params: ShadePanelParams,
        method: str = "unknown",
        iteration: Optional[int] = None,
    ) -> CandidateRecord:
        """
        Full evaluation pipeline for a proposed intervention candidate:
        1. Validate geographic feasibility (reject before simulation if invalid).
        2. If feasible, construct 3D geometry and apply as scene edit.
        3. Execute certified GPU incremental simulation.
        4. Verify certificate guarantees.
        5. Compute thermal comfort objective and diagnostic metrics.
        6. Append candidate record to ledger.
        """
        iter_idx = iteration if iteration is not None else len(self.ledger)
        cand_id = f"CAND_{iter_idx:04d}_{method[:4].upper()}"

        # 1. Geographic Feasibility Filter
        feas_res = check_feasibility(params, self.feasibility_constraints)
        if not feas_res.is_valid:
            record = CandidateRecord(
                candidate_id=cand_id,
                iteration=iter_idx,
                method=method,
                params=params.to_dict(),
                is_feasible=False,
                rejection_reason=feas_res.rejection_reason.value,
                rejection_message=feas_res.message,
                objective_value=float("inf"),
                metrics=None,
                gpu_metrics=None,
                certificate_status=None,
                certificate_violations=None,
                max_predicted_bound_k=None,
                wall_time_s=0.0,
            )
            self.ledger.add(record)
            return record

        # Ensure GPU resident static baseline is loaded
        if not self._is_preloaded:
            self.preload()

        # 2. Geometry Builder
        mesh, poly = build_panel_geometry(params, mesh_id=f"PANEL_{iter_idx:04d}")
        edit = AddMeshEdit(mesh)
        updated_scene, edit_bounds = edit.apply(self.baseline_scene)

        # Assign intervention material
        mat_panel = Material(
            id="SHADE_PANEL_ASSUMED_001",
            albedo=float(params.albedo),
            emissivity=0.90,
            surface_temperature=308.15,
            is_opaque=True,
        )
        materials_updated = dict(self.baseline_scene.materials)
        materials_updated["SHADE_PANEL_ASSUMED_001"] = mat_panel
        updated_scene.materials = materials_updated

        # 3. GPU Incremental Simulation with robust error isolation
        t0 = time.perf_counter()
        try:
            update_res, cert = self.gpu_engine.execute_certified_update(
                previous_scene=self.baseline_scene,
                updated_scene=updated_scene,
                previous_result=self.baseline_result,
                edit=edit,
                weather=self.weather,
                config=self.sim_config,
            )
            wall_time_s = time.perf_counter() - t0
            sim_success = True
        except Exception as exc:
            wall_time_s = time.perf_counter() - t0
            sim_success = False
            err_msg = str(exc)

        if not sim_success:
            record = CandidateRecord(
                candidate_id=cand_id,
                iteration=iter_idx,
                method=method,
                params=params.to_dict(),
                is_feasible=False,
                rejection_reason="SIMULATION_ERROR",
                rejection_message=f"Incremental physics evaluation failed: {err_msg}",
                objective_value=float("inf"),
                metrics=None,
                gpu_metrics=None,
                certificate_status="ERROR",
                certificate_violations=None,
                max_predicted_bound_k=None,
                wall_time_s=wall_time_s,
            )
            self.ledger.add(record)
            return record

        # 4. Certificate Verification
        cert_status = cert.status
        cert_violations = 0 if cert.is_certified else int(getattr(cert, "violations_count", 1))
        max_bound_k = float(np.max(cert.predicted_error_bound))

        # 5. Objective & Metric Computation
        metrics = compute_objective(
            sim_result=update_res.result,
            baseline_result=self.baseline_result,
            eval_mask=self.eval_mask,
            panel_area_m2=params.area,
            config=self.config.objective_config,
        )

        # 6. GPU Performance Metrics Extraction
        total_cells = update_res.total_cells
        recomputed_cells = update_res.recomputed_cells
        reused_cells = total_cells - recomputed_cells
        reused_pct = update_res.reused_fraction * 100.0
        num_rays_per_cell = 1 + self.sim_config.sky_patch_configuration
        recomputed_rays = recomputed_cells * num_rays_per_cell
        reused_rays = reused_cells * num_rays_per_cell
        ray_reduction_pct = (reused_rays / (total_cells * num_rays_per_cell) * 100.0) if total_cells > 0 else 0.0

        last_m = self.gpu_engine.last_metrics
        kernel_ms = last_m.gpu_kernel_time_ms if last_m else (update_res.time_selective_recompute_sec * 1000.0)
        h2d_ms = getattr(last_m, "host_to_device_time_ms", 0.0) if last_m else 0.0
        d2h_ms = getattr(last_m, "device_to_host_time_ms", 0.0) if last_m else 0.0

        gpu_metrics_dict = {
            "total_cells": total_cells,
            "recomputed_cells": recomputed_cells,
            "reused_cells": reused_cells,
            "reused_fraction_pct": round(reused_pct, 4),
            "recomputed_rays": recomputed_rays,
            "reused_rays": reused_rays,
            "ray_work_reduction_pct": round(ray_reduction_pct, 4),
            "gpu_kernel_time_ms": round(kernel_ms, 3),
            "h2d_transfer_time_ms": round(h2d_ms, 3),
            "d2h_transfer_time_ms": round(d2h_ms, 3),
            "incremental_wall_time_s": round(update_res.time_incremental_sec, 4),
        }

        record = CandidateRecord(
            candidate_id=cand_id,
            iteration=iter_idx,
            method=method,
            params=params.to_dict(),
            is_feasible=True,
            rejection_reason=None,
            rejection_message=None,
            objective_value=metrics.objective_value,
            metrics=metrics.to_dict(),
            gpu_metrics=gpu_metrics_dict,
            certificate_status=cert_status,
            certificate_violations=cert_violations,
            max_predicted_bound_k=round(max_bound_k, 6),
            wall_time_s=round(wall_time_s, 4),
        )
        self.ledger.add(record)
        return record

    def run_deterministic_baseline(self) -> CandidateRecord:
        """Evaluates canonical CANOPY_001 / BLR_SHADE_001 reference candidate."""
        canon_params = ParameterBounds.get_canonical_church_street_baseline_params()
        return self.evaluate_candidate(canon_params, method="deterministic_baseline")

    def run_random_search(self, n_samples: int) -> List[CandidateRecord]:
        """Runs uniform random sampling within configured bounds."""
        candidates = self.config.bounds.sample_uniform(self.rng, n_samples=n_samples)
        records = []
        for cand in candidates:
            if len(self.ledger) >= self.config.max_total_evaluations:
                break
            records.append(self.evaluate_candidate(cand, method="random"))
        return records

    def run_lhs_search(self, n_samples: int) -> List[CandidateRecord]:
        """Runs Latin-Hypercube sampling within configured bounds."""
        candidates = self.config.bounds.sample_lhs(self.rng, n_samples=n_samples)
        records = []
        for cand in candidates:
            if len(self.ledger) >= self.config.max_total_evaluations:
                break
            records.append(self.evaluate_candidate(cand, method="lhs"))
        return records

    def run_evolutionary_search(
        self,
        generations: int,
        pop_size: int,
        mutation_factor: Optional[float] = None,
        crossover_prob: Optional[float] = None,
    ) -> List[CandidateRecord]:
        """
        Constrained Differential Evolution over continuous parameter space.
        Uses feasible candidates discovered so far as initial seed population.
        """
        F = mutation_factor if mutation_factor is not None else self.config.mutation_factor
        CR = crossover_prob if crossover_prob is not None else self.config.crossover_prob
        records: List[CandidateRecord] = []

        feasible_seeds = self.ledger.get_feasible()
        # Ensure we have at least 4 feasible seeds for DE mutation
        while len(feasible_seeds) < max(4, min(pop_size, 8)):
            if len(self.ledger) >= self.config.max_total_evaluations:
                break
            sample = self.config.bounds.sample_uniform(self.rng, n_samples=1)[0]
            rec = self.evaluate_candidate(sample, method="evolutionary_init")
            records.append(rec)
            feasible_seeds = self.ledger.get_feasible()

        if len(feasible_seeds) < 2:
            return records

        # Initialize population
        best_seeds = sorted(feasible_seeds, key=lambda r: r.objective_value)[:pop_size]
        population: List[Tuple[np.ndarray, float]] = [
            (self.config.bounds.to_vector(ShadePanelParams.from_dict(r.params)), r.objective_value)
            for r in best_seeds
        ]

        bounds = self.config.bounds
        n_dim = 7

        for gen in range(generations):
            if len(self.ledger) >= self.config.max_total_evaluations:
                break

            for i in range(len(population)):
                if len(self.ledger) >= self.config.max_total_evaluations:
                    break

                target_vec, target_obj = population[i]

                # Select 3 distinct random candidates (or as many as available)
                idxs = [idx for idx in range(len(population)) if idx != i]
                if len(idxs) < 3:
                    # Fallback to Gaussian perturbation of best
                    best_vec = population[0][0]
                    donor_vec = best_vec + self.rng.normal(0, 0.05, size=n_dim) * (
                        np.array([bounds.x_max - bounds.x_min, bounds.y_max - bounds.y_min,
                                  bounds.length_max - bounds.length_min, bounds.width_max - bounds.width_min,
                                  bounds.height_max - bounds.height_min, bounds.heading_max - bounds.heading_min,
                                  bounds.albedo_max - bounds.albedo_min])
                    )
                else:
                    r1, r2, r3 = self.rng.choice(idxs, size=3, replace=False)
                    v_r1 = population[r1][0]
                    v_r2 = population[r2][0]
                    v_r3 = population[r3][0]
                    donor_vec = v_r1 + F * (v_r2 - v_r3)

                # Binomial crossover
                trial_vec = target_vec.copy()
                rand_dim = self.rng.integers(0, n_dim)
                for d in range(n_dim):
                    if d == rand_dim or self.rng.random() < CR:
                        trial_vec[d] = donor_vec[d]

                # Clip to parameter bounds
                clipped_vec = bounds.clip(trial_vec)
                child_params = bounds.from_vector(clipped_vec)

                # Evaluate trial candidate
                rec = self.evaluate_candidate(child_params, method="evolutionary")
                records.append(rec)

                # Selection: replace in population if feasible and improved
                if rec.is_feasible and rec.objective_value < target_obj:
                    population[i] = (clipped_vec, rec.objective_value)
                    # Keep population sorted by objective
                    population.sort(key=lambda item: item[1])

        return records

    def run_full_optimization(
        self,
        budget_random: Optional[int] = None,
        budget_lhs: Optional[int] = None,
        budget_evolutionary: Optional[int] = None,
    ) -> CandidateLedger:
        """
        Executes complete multi-phase search:
        Phase 1: Deterministic baseline
        Phase 2: Uniform random search
        Phase 3: Latin-Hypercube Sampling
        Phase 4: Constrained Differential Evolution
        """
        b_rand = budget_random if budget_random is not None else self.config.budget_random
        b_lhs = budget_lhs if budget_lhs is not None else self.config.budget_lhs
        b_evo = budget_evolutionary if budget_evolutionary is not None else self.config.budget_evolutionary

        # Phase 1: Baseline
        self.run_deterministic_baseline()

        # Phase 2: Random
        if b_rand > 0:
            self.run_random_search(n_samples=b_rand)

        # Phase 3: LHS
        if b_lhs > 0:
            self.run_lhs_search(n_samples=b_lhs)

        # Phase 4: Evolutionary
        if b_evo > 0:
            generations = max(1, b_evo // self.config.population_size)
            self.run_evolutionary_search(generations=generations, pop_size=self.config.population_size)

        return self.ledger
