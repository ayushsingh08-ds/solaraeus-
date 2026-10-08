"""
Geographically Constrained AI Intervention Optimization Package for SOLARAEUS.

Provides parameterization, geographic feasibility validation, multi-criteria comfort objectives,
candidate ledgers, derivative-free search optimizers, surrogate modeling, uncertainty-aware acquisition,
and multi-path physical validation for single-panel and two-panel shade interventions.
"""

from __future__ import annotations

from urban_comfort.optimization.parameters import (
    ShadePanelParams, ParameterBounds, build_panel_geometry
)
from urban_comfort.optimization.feasibility import (
    RejectionReason, FeasibilityConstraints, FeasibilityResult, check_feasibility
)
from urban_comfort.optimization.objective import (
    ComfortObjectiveConfig, EvaluationMetrics, compute_objective
)
from urban_comfort.optimization.ledger import (
    CandidateRecord, CandidateLedger
)
from urban_comfort.optimization.optimizer import (
    OptimizationEngine, OptimizerConfig
)
from urban_comfort.optimization.validation import (
    validate_candidate_multi_path, MultiPathValidationSummary, run_multi_path_validation_suite
)
from urban_comfort.optimization.surrogate import (
    SurrogateConfig, SurrogatePrediction, SurrogateModel, FallbackSurrogateModel
)
from urban_comfort.optimization.acquisition import (
    AcquisitionConfig, CandidateAcquisitionEngine
)
from urban_comfort.optimization.surrogate_optimizer import (
    SurrogateOptimizerConfig, SurrogateOptimizationEngine
)

# Two-Panel Multi-Intervention Exports
from urban_comfort.optimization.two_panel_parameters import (
    TwoPanelParams, TwoPanelBounds
)
from urban_comfort.optimization.two_panel_feasibility import (
    TwoPanelRejectionReason, TwoPanelFeasibilityResult, TwoPanelConstraints, check_two_panel_feasibility
)
from urban_comfort.optimization.two_panel_objective import (
    TwoPanelComfortObjectiveConfig, TwoPanelEvaluationMetrics, compute_two_panel_objective, compute_pareto_front
)
from urban_comfort.optimization.two_panel_ledger import (
    TwoPanelCandidateRecord, TwoPanelCandidateLedger
)
from urban_comfort.optimization.two_panel_surrogate import (
    TWO_PANEL_FEATURE_NAMES, TWO_PANEL_DEFAULT_TARGETS, TwoPanelSurrogateConfig,
    TwoPanelSurrogatePrediction, extract_two_panel_features, extract_two_panel_targets,
    TwoPanelSurrogateModel
)
from urban_comfort.optimization.two_panel_acquisition import (
    TwoPanelAcquisitionConfig, TwoPanelAcquisitionEngine, generate_two_panel_seeds,
    compute_normalized_two_panel_distance
)
from urban_comfort.optimization.two_panel_optimizer import (
    TwoPanelOptimizerConfig, TwoPanelOptimizationEngine
)
from urban_comfort.optimization.two_panel_validation import (
    TwoPanelValidationReport, TwoPanelMultiPathSummary, validate_two_panel_multi_path
)

__all__ = [
    # Single-panel exports (protected regression path)
    "ShadePanelParams",
    "ParameterBounds",
    "build_panel_geometry",
    "RejectionReason",
    "FeasibilityConstraints",
    "FeasibilityResult",
    "check_feasibility",
    "ComfortObjectiveConfig",
    "EvaluationMetrics",
    "compute_objective",
    "CandidateRecord",
    "CandidateLedger",
    "OptimizationEngine",
    "OptimizerConfig",
    "validate_candidate_multi_path",
    "MultiPathValidationSummary",
    "run_multi_path_validation_suite",
    "SurrogateConfig",
    "SurrogatePrediction",
    "SurrogateModel",
    "FallbackSurrogateModel",
    "AcquisitionConfig",
    "CandidateAcquisitionEngine",
    "SurrogateOptimizerConfig",
    "SurrogateOptimizationEngine",
    # Two-panel exports
    "TwoPanelParams",
    "TwoPanelBounds",
    "TwoPanelRejectionReason",
    "TwoPanelFeasibilityResult",
    "TwoPanelConstraints",
    "check_two_panel_feasibility",
    "TwoPanelComfortObjectiveConfig",
    "TwoPanelEvaluationMetrics",
    "compute_two_panel_objective",
    "compute_pareto_front",
    "TwoPanelCandidateRecord",
    "TwoPanelCandidateLedger",
    "TWO_PANEL_FEATURE_NAMES",
    "TWO_PANEL_DEFAULT_TARGETS",
    "TwoPanelSurrogateConfig",
    "TwoPanelSurrogatePrediction",
    "extract_two_panel_features",
    "extract_two_panel_targets",
    "TwoPanelSurrogateModel",
    "TwoPanelAcquisitionConfig",
    "TwoPanelAcquisitionEngine",
    "generate_two_panel_seeds",
    "compute_normalized_two_panel_distance",
    "TwoPanelOptimizerConfig",
    "TwoPanelOptimizationEngine",
    "TwoPanelValidationReport",
    "TwoPanelMultiPathSummary",
    "validate_two_panel_multi_path",
    # Robustness and Sensitivity exports
    "WeatherScenario",
    "SolarTimestampScenario",
    "ObjectiveWeightScenario",
    "ConstraintSensitivityScenario",
    "RobustnessStudyConfig",
    "get_standard_weather_scenarios",
    "get_standard_solar_timestamps",
    "get_standard_objective_scenarios",
    "get_standard_constraint_scenarios",
    "recompute_score_under_scenario",
    "evaluate_candidate_at_condition",
]

from urban_comfort.optimization.robustness import (
    WeatherScenario,
    SolarTimestampScenario,
    ObjectiveWeightScenario,
    ConstraintSensitivityScenario,
    RobustnessStudyConfig,
    get_standard_weather_scenarios,
    get_standard_solar_timestamps,
    get_standard_objective_scenarios,
    get_standard_constraint_scenarios,
    recompute_score_under_scenario,
    evaluate_candidate_at_condition,
)
