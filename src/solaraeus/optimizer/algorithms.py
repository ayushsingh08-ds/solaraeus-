"""
Stage 6: Optimization Algorithms for Urban Microclimate Optimization.

Implements:
1. Random Search (Baseline)
2. Direct Search without Surrogate (Genetic Algorithm with BLX-alpha & Elitism)
3. Surrogate-Only (Static Offline Gaussian Process with 49-sample DoE + 1 final verification)
4. Proposed Surrogate + Active Learning (Bayesian Optimization via GP-LCB Acquisition)
5. Exhaustive Search (Ground Truth Optimizer for Tiny Benchmark Problem)
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional, Callable

import numpy as np
from scipy.optimize import minimize, differential_evolution
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.metrics import mean_absolute_error

from solaraeus.optimizer.problem import UrbanOptimizationProblem, EvaluationRecord, CanopySpec


@dataclass
class OptimizationResult:
    """Standardized result envelope for an optimization run."""
    method_name: str
    seed: int
    evaluations_used: int
    best_candidate_vector: np.ndarray
    best_canopy_specs: List[CanopySpec]
    best_objective_value: float          # Primary objective: Mean Tmrt in Celsius
    best_record: EvaluationRecord
    convergence_history: List[float]     # Best-so-far objective at each evaluation (length = budget)
    all_evaluations: List[EvaluationRecord]
    wall_time_s: float
    held_out_mae_k: Optional[float] = None # Surrogate MAE on test designs if applicable
    surrogate_model: Optional[Any] = None

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method_name,
            "seed": self.seed,
            "evaluations_used": self.evaluations_used,
            "best_mean_tmrt_c": round(self.best_record.mean_tmrt_c, 4),
            "best_p90_tmrt_c": round(self.best_record.p90_tmrt_c, 4),
            "best_max_tmrt_c": round(self.best_record.max_tmrt_c, 4),
            "best_mean_utci_c": round(self.best_record.mean_utci_c, 4),
            "cooling_delta_mean_k": round(self.best_record.cooling_delta_mean_k, 4),
            "cooling_delta_p90_k": round(self.best_record.cooling_delta_p90_k, 4),
            "percent_improvement": round((self.best_record.cooling_delta_mean_k / self.best_record.mean_tmrt_c) * 100.0, 2),
            "wall_time_s": round(self.wall_time_s, 2),
            "held_out_mae_k": round(self.held_out_mae_k, 4) if self.held_out_mae_k is not None else None,
        }


def sample_feasible_candidate(problem: UrbanOptimizationProblem,
                             rng: np.random.Generator,
                             max_attempts: int = 100) -> np.ndarray:
    """Samples a uniformly distributed candidate vector that satisfies geometric feasibility."""
    lb, ub = problem.get_parameter_bounds()
    for _ in range(max_attempts):
        cand = rng.uniform(lb, ub)
        specs = problem.vector_to_specs(cand)
        is_feas, _, _ = problem.check_feasibility(specs)
        if is_feas:
            return cand
    # Fallback to random within bounds
    return rng.uniform(lb, ub)


def latin_hypercube_sampling(n_samples: int,
                            lb: np.ndarray,
                            ub: np.ndarray,
                            rng: np.random.Generator) -> np.ndarray:
    """Generates space-filling Latin Hypercube Samples in [lb, ub]^D."""
    d = len(lb)
    result = np.empty((n_samples, d), dtype=np.float64)
    for j in range(d):
        perm = rng.permutation(n_samples)
        intervals = (perm + rng.uniform(0.0, 1.0, size=n_samples)) / n_samples
        result[:, j] = lb[j] + intervals * (ub[j] - lb[j])
    return result


# ==============================================================================
# Method 1: Random Search
# ==============================================================================

class RandomSearchOptimizer:
    """Uniform random search over the constrained decision space."""

    def __init__(self, problem: UrbanOptimizationProblem, budget: int = 50, seed: int = 42):
        self.problem = problem
        self.budget = budget
        self.seed = seed

    def run(self) -> OptimizationResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        convergence = []
        best_obj = float("inf")
        best_rec = None
        best_cand = None

        for i in range(self.budget):
            cand = sample_feasible_candidate(self.problem, rng)
            obj, rec = self.problem.evaluate(cand)

            if obj < best_obj and rec.is_feasible:
                best_obj = obj
                best_rec = rec
                best_cand = cand

            convergence.append(best_obj if best_obj < float("inf") else obj)

        wall_time = time.perf_counter() - t0
        return OptimizationResult(
            method_name="random_search",
            seed=self.seed,
            evaluations_used=self.budget,
            best_candidate_vector=best_cand if best_cand is not None else self.problem.evaluations[0].params_vector,
            best_canopy_specs=self.problem.vector_to_specs(best_cand) if best_cand is not None else [],
            best_objective_value=best_obj,
            best_record=best_rec if best_rec is not None else self.problem.evaluations[0],
            convergence_history=convergence,
            all_evaluations=self.problem.evaluations[-self.budget:],
            wall_time_s=wall_time
        )


# ==============================================================================
# Method 2: Direct Search without Surrogate (Genetic Algorithm)
# ==============================================================================

class DirectSearchOptimizer:
    """
    Direct derivative-free evolutionary algorithm (Genetic Algorithm).
    Uses tournament selection, BLX-alpha crossover, polynomial mutation, and elitism.
    Evaluates every candidate directly on the physics simulation without a surrogate.
    """

    def __init__(self, problem: UrbanOptimizationProblem, budget: int = 50, seed: int = 42,
                 pop_size: int = 10):
        self.problem = problem
        self.budget = budget
        self.seed = seed
        self.pop_size = pop_size
        self.generations = budget // pop_size

    def run(self) -> OptimizationResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        lb, ub = problem_lb, problem_ub = self.problem.get_parameter_bounds()

        convergence = []
        best_obj = float("inf")
        best_rec = None
        best_cand = None

        # 1. Initialize Population
        population: List[np.ndarray] = []
        fitnesses: List[float] = []
        records: List[EvaluationRecord] = []

        for _ in range(self.pop_size):
            ind = sample_feasible_candidate(self.problem, rng)
            obj, rec = self.problem.evaluate(ind)
            population.append(ind)
            fitnesses.append(obj)
            records.append(rec)

            if obj < best_obj and rec.is_feasible:
                best_obj = obj
                best_rec = rec
                best_cand = ind
            convergence.append(best_obj if best_obj < float("inf") else obj)

        # 2. Evolutionary Generations until exact budget is reached
        evals_done = len(population)
        while evals_done < self.budget:
            sorted_indices = np.argsort(fitnesses)
            new_population = [population[i] for i in sorted_indices[:2]]
            new_fitnesses = [fitnesses[i] for i in sorted_indices[:2]]

            while len(new_population) < self.pop_size and evals_done < self.budget:
                p1_idx = min(rng.choice(len(population), size=2, replace=False), key=lambda x: fitnesses[x])
                p2_idx = min(rng.choice(len(population), size=2, replace=False), key=lambda x: fitnesses[x])
                p1 = population[p1_idx]
                p2 = population[p2_idx]

                alpha = 0.3
                c_min = np.minimum(p1, p2)
                c_max = np.maximum(p1, p2)
                range_c = c_max - c_min
                child = rng.uniform(c_min - alpha * range_c, c_max + alpha * range_c)

                mut_mask = rng.uniform(0.0, 1.0, size=len(child)) < 0.20
                mut_perturb = rng.normal(0.0, 0.1 * (ub - lb), size=len(child))
                child[mut_mask] += mut_perturb[mut_mask]
                child = np.clip(child, lb, ub)

                obj, rec = self.problem.evaluate(child)
                evals_done += 1
                new_population.append(child)
                new_fitnesses.append(obj)

                if obj < best_obj and rec.is_feasible:
                    best_obj = obj
                    best_rec = rec
                    best_cand = child
                convergence.append(best_obj if best_obj < float("inf") else obj)

            population = new_population
            fitnesses = new_fitnesses

        wall_time = time.perf_counter() - t0
        return OptimizationResult(
            method_name="direct_search",
            seed=self.seed,
            evaluations_used=self.budget,
            best_candidate_vector=best_cand if best_cand is not None else population[0],
            best_canopy_specs=self.problem.vector_to_specs(best_cand) if best_cand is not None else [],
            best_objective_value=best_obj,
            best_record=best_rec if best_rec is not None else records[0],
            convergence_history=convergence,
            all_evaluations=self.problem.evaluations[-self.budget:],
            wall_time_s=wall_time
        )


# ==============================================================================
# Method 3: Surrogate-Only (Static Offline ML)
# ==============================================================================

class SurrogateOnlyOptimizer:
    """
    Static offline surrogate-assisted optimization.
    Evaluates 49 initial samples (DoE), trains a Gaussian Process surrogate once,
    optimizes the surrogate extensively (2,000 queries, 0 physics cost),
    and executes the 50th physics evaluation to verify the surrogate optimum.
    """

    def __init__(self, problem: UrbanOptimizationProblem, budget: int = 50, seed: int = 42,
                 test_set_X: Optional[np.ndarray] = None, test_set_y: Optional[np.ndarray] = None):
        self.problem = problem
        self.budget = budget
        self.seed = seed
        self.test_set_X = test_set_X
        self.test_set_y = test_set_y

    def run(self) -> OptimizationResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        lb, ub = self.problem.get_parameter_bounds()

        doe_samples = self.budget - 1  # 49 training evaluations
        convergence = []
        best_obj = float("inf")
        best_rec = None
        best_cand = None

        X_train: List[np.ndarray] = []
        y_train: List[float] = []

        # 1. DoE Phase (Latin Hypercube Sampling)
        lhs = latin_hypercube_sampling(doe_samples, lb, ub, rng)
        for i in range(doe_samples):
            cand = lhs[i]
            obj, rec = self.problem.evaluate(cand)
            X_train.append(cand)
            y_train.append(obj)

            if obj < best_obj and rec.is_feasible:
                best_obj = obj
                best_rec = rec
                best_cand = cand
            convergence.append(best_obj if best_obj < float("inf") else obj)

        # 2. Fit Gaussian Process Surrogate Model
        X_arr = np.array(X_train)
        y_arr = np.array(y_train)

        # Matérn 5/2 kernel with automatic relevance determination (ARD)
        kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(length_scale=np.ones(len(lb)), nu=2.5) + WhiteKernel(noise_level=0.01)
        gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=5, random_state=self.seed)
        gp.fit(X_arr, y_arr)

        # Held-out Test MAE if test set provided
        held_out_mae = None
        if self.test_set_X is not None and self.test_set_y is not None:
            pred_y = gp.predict(self.test_set_X)
            held_out_mae = float(mean_absolute_error(self.test_set_y, pred_y))

        # 3. Optimize Surrogate Model Extensively (Differential Evolution, zero physics cost)
        def surrogate_obj(x: np.ndarray) -> float:
            specs = self.problem.vector_to_specs(x)
            is_feas, _, pen = self.problem.check_feasibility(specs)
            mu = float(gp.predict(x.reshape(1, -1))[0])
            return mu + (pen * 10.0 if not is_feas else 0.0)

        bounds_de = list(zip(lb, ub))
        de_res = differential_evolution(
            surrogate_obj,
            bounds=bounds_de,
            maxiter=40,
            popsize=15,
            seed=self.seed,
            polish=True
        )
        surr_best_cand = np.clip(de_res.x, lb, ub)

        # 4. Final Physics Verification Evaluation (50th simulation)
        final_obj, final_rec = self.problem.evaluate(surr_best_cand)
        if final_obj < best_obj and final_rec.is_feasible:
            best_obj = final_obj
            best_rec = final_rec
            best_cand = surr_best_cand
        convergence.append(best_obj if best_obj < float("inf") else final_obj)

        wall_time = time.perf_counter() - t0
        return OptimizationResult(
            method_name="surrogate_only",
            seed=self.seed,
            evaluations_used=self.budget,
            best_candidate_vector=best_cand if best_cand is not None else surr_best_cand,
            best_canopy_specs=self.problem.vector_to_specs(best_cand) if best_cand is not None else [],
            best_objective_value=best_obj,
            best_record=best_rec if best_rec is not None else final_rec,
            convergence_history=convergence,
            all_evaluations=self.problem.evaluations[-self.budget:],
            wall_time_s=wall_time,
            held_out_mae_k=held_out_mae,
            surrogate_model=gp
        )


# ==============================================================================
# Method 4: Proposed Surrogate + Active Learning (Bayesian Optimization)
# ==============================================================================

class ActiveLearningSurrogateOptimizer:
    """
    Proposed iterative active learning & Bayesian Optimization pipeline.
    Warmup with 15 Latin Hypercube samples, then iteratively updates Gaussian Process
    and queries candidates via Lower Confidence Bound (LCB) acquisition function:
        alpha_LCB(x) = mu(x) - kappa * sigma(x) + penalty(x)
    for the remaining 35 iterations.
    """

    def __init__(self, problem: UrbanOptimizationProblem, budget: int = 50, seed: int = 42,
                 warmup_samples: int = 15, kappa: float = 1.96,
                 test_set_X: Optional[np.ndarray] = None, test_set_y: Optional[np.ndarray] = None):
        self.problem = problem
        self.budget = budget
        self.seed = seed
        self.warmup_samples = warmup_samples
        self.kappa = kappa
        self.test_set_X = test_set_X
        self.test_set_y = test_set_y

    def run(self) -> OptimizationResult:
        t0 = time.perf_counter()
        rng = np.random.default_rng(self.seed)
        lb, ub = self.problem.get_parameter_bounds()

        convergence = []
        best_obj = float("inf")
        best_rec = None
        best_cand = None

        X_obs: List[np.ndarray] = []
        y_obs: List[float] = []

        # 1. Warm-up Phase (15 Latin Hypercube Samples)
        lhs = latin_hypercube_sampling(self.warmup_samples, lb, ub, rng)
        for i in range(self.warmup_samples):
            cand = lhs[i]
            obj, rec = self.problem.evaluate(cand)
            X_obs.append(cand)
            y_obs.append(obj)

            if obj < best_obj and rec.is_feasible:
                best_obj = obj
                best_rec = rec
                best_cand = cand
            convergence.append(best_obj if best_obj < float("inf") else obj)

        # 2. Iterative Active Learning Phase (35 Iterations)
        gp = None
        for step in range(self.warmup_samples, self.budget):
            X_arr = np.array(X_obs)
            y_arr = np.array(y_obs)

            # Fit GP surrogate
            kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(length_scale=np.ones(len(lb)), nu=2.5) + WhiteKernel(noise_level=0.01)
            gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, n_restarts_optimizer=2, random_state=self.seed + step)
            gp.fit(X_arr, y_arr)

            # Define GP-LCB Acquisition Function
            # We want to MINIMIZE mean Tmrt, so lower bound = mu - kappa * sigma
            def acquisition_func(x: np.ndarray) -> float:
                mu, sigma = gp.predict(x.reshape(1, -1), return_std=True)
                lcb = float(mu[0] - self.kappa * sigma[0])
                specs = self.problem.vector_to_specs(x)
                is_feas, _, pen = self.problem.check_feasibility(specs)
                return lcb + (pen * 15.0 if not is_feas else 0.0)

            # Multi-start local optimization of acquisition function
            best_acq_val = float("inf")
            best_acq_cand = None

            # Generate 25 candidate restarts (mix of random and best-so-far perturbations)
            restarts = [rng.uniform(lb, ub) for _ in range(20)]
            if best_cand is not None:
                for _ in range(5):
                    jitter = rng.normal(0.0, 0.05 * (ub - lb))
                    restarts.append(np.clip(best_cand + jitter, lb, ub))

            for r_cand in restarts:
                res = minimize(
                    acquisition_func,
                    x0=r_cand,
                    bounds=list(zip(lb, ub)),
                    method="L-BFGS-B",
                    options={"maxiter": 30}
                )
                if res.fun < best_acq_val:
                    best_acq_val = res.fun
                    best_acq_cand = res.x

            selected_cand = np.clip(best_acq_cand, lb, ub)

            # Evaluate selected candidate with physics simulation
            obj, rec = self.problem.evaluate(selected_cand)
            X_obs.append(selected_cand)
            y_obs.append(obj)

            if obj < best_obj and rec.is_feasible:
                best_obj = obj
                best_rec = rec
                best_cand = selected_cand
            convergence.append(best_obj if best_obj < float("inf") else obj)

        # Held-out Test MAE of final GP model
        held_out_mae = None
        if gp is not None and self.test_set_X is not None and self.test_set_y is not None:
            pred_y = gp.predict(self.test_set_X)
            held_out_mae = float(mean_absolute_error(self.test_set_y, pred_y))

        wall_time = time.perf_counter() - t0
        return OptimizationResult(
            method_name="active_learning",
            seed=self.seed,
            evaluations_used=self.budget,
            best_candidate_vector=best_cand if best_cand is not None else X_obs[0],
            best_canopy_specs=self.problem.vector_to_specs(best_cand) if best_cand is not None else [],
            best_objective_value=best_obj,
            best_record=best_rec if best_rec is not None else self.problem.evaluations[0],
            convergence_history=convergence,
            all_evaluations=self.problem.evaluations[-self.budget:],
            wall_time_s=wall_time,
            held_out_mae_k=held_out_mae,
            surrogate_model=gp
        )


# ==============================================================================
# Method 5: Exhaustive Search for Tiny Benchmark Problem
# ==============================================================================

def run_tiny_exhaustive_benchmark(backend: str = "gpu") -> Dict[str, Any]:
    """
    Solves the tiny single-canopy problem exhaustively across a fine candidate grid.
    Provides the ground truth global optimum for comparing sample efficiency.
    """
    print("\n" + "=" * 80)
    print("SOLVING TINY PROBLEM VIA EXHAUSTIVE DISCRETE SEARCH")
    print("=" * 80)

    problem = UrbanOptimizationProblem(num_canopies=1, backend=backend)

    # Fixed single canopy dimensions: 6.0m x 4.0m, height 3.5m, heading 0 deg
    canopy_len = 6.0
    canopy_wid = 4.0
    canopy_ht = 3.5
    canopy_heading = 0.0

    # 45 discrete coordinate candidates (5 across corridor, 9 along corridor)
    xs = [-4.0, -2.0, 0.0, 2.0, 4.0]
    ys = [-30.0, -22.5, -15.0, -7.5, 0.0, 7.5, 15.0, 22.5, 30.0]

    grid_results = []
    t0 = time.perf_counter()

    for y in ys:
        row = []
        for x in xs:
            vec = np.array([x, y, canopy_len, canopy_wid, canopy_heading, canopy_ht], dtype=np.float64)
            obj, rec = problem.evaluate(vec)
            row.append({
                "x": x,
                "y": y,
                "mean_tmrt_c": rec.mean_tmrt_c,
                "p90_tmrt_c": rec.p90_tmrt_c,
                "cooling_delta_k": rec.cooling_delta_mean_k
            })
            print(f"  Pos (x={x:+4.1f}, y={y:+5.1f}) -> Mean Tmrt: {rec.mean_tmrt_c:.4f} C (Delta-Tmrt: {rec.cooling_delta_mean_k:+.4f} K)")
        grid_results.append(row)

    total_evals = len(xs) * len(ys)
    wall_time = time.perf_counter() - t0

    # Find true global optimum
    all_points = [pt for row in grid_results for pt in row]
    true_opt = min(all_points, key=lambda p: p["mean_tmrt_c"])

    print(f"\nTRUE GLOBAL OPTIMUM IDENTIFIED:")
    print(f"  Optimal Position: x={true_opt['x']:.1f} m, y={true_opt['y']:.1f} m")
    print(f"  Minimum Mean Tmrt: {true_opt['mean_tmrt_c']:.4f} C")
    print(f"  Maximum Cooling Delta: {true_opt['cooling_delta_k']:.4f} K")
    print(f"  Evaluations: {total_evals} | Wall time: {wall_time:.2f} s")

    return {
        "xs": xs,
        "ys": ys,
        "grid_results": grid_results,
        "true_optimum": true_opt,
        "baseline_mean_tmrt": problem.baseline_mean_tmrt,
        "evaluations_used": total_evals,
        "wall_time_s": wall_time
    }
