"""
Urban Optimization & Surrogate-Assisted Active Learning Package (SOLARAEUS Stage 6).
"""

from __future__ import annotations

from solaraeus.optimizer.problem import (
    CanopySpec, OptimizationBounds, EvaluationRecord, UrbanOptimizationProblem
)
from solaraeus.optimizer.algorithms import (
    OptimizationResult,
    RandomSearchOptimizer,
    DirectSearchOptimizer,
    SurrogateOnlyOptimizer,
    ActiveLearningSurrogateOptimizer,
    run_tiny_exhaustive_benchmark
)

__all__ = [
    "CanopySpec",
    "OptimizationBounds",
    "EvaluationRecord",
    "UrbanOptimizationProblem",
    "OptimizationResult",
    "RandomSearchOptimizer",
    "DirectSearchOptimizer",
    "SurrogateOnlyOptimizer",
    "ActiveLearningSurrogateOptimizer",
    "run_tiny_exhaustive_benchmark"
]
