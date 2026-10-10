"""
Geographically Constrained AI Intervention Optimization Package for SOLARAEUS.

Provides parameterization, geographic feasibility validation, multi-criteria comfort objectives,
candidate ledgers, derivative-free search optimizers, surrogate modeling, uncertainty-aware acquisition,
and multi-path physical validation for single-panel and two-panel shade interventions.
"""

from __future__ import annotations

from urban_comfort.optimization.acquisition import AcquisitionConfig, CandidateAcquisitionEngine
from urban_comfort.optimization.feasibility import (
    FeasibilityConstraints,
    FeasibilityResult,
    RejectionReason,
    check_feasibility,
)
from urban_comfort.optimization.ledger import CandidateLedger, CandidateRecord
from urban_comfort.optimization.objective import (
    ComfortObjectiveConfig,
    EvaluationMetrics,
    compute_objective,
)
from urban_comfort.optimization.optimizer import OptimizationEngine, OptimizerConfig
from urban_comfort.optimization.parameters import (
    ParameterBounds,
    ShadePanelParams,
    build_panel_geometry,
)
from urban_comfort.optimization.surrogate import (
    FallbackSurrogateModel,
    SurrogateConfig,
    SurrogateModel,
    SurrogatePrediction,
)
from urban_comfort.optimization.surrogate_optimizer import (
    SurrogateOptimizationEngine,
    SurrogateOptimizerConfig,
)
from urban_comfort.optimization.two_panel_acquisition import (
    TwoPanelAcquisitionConfig,
    TwoPanelAcquisitionEngine,
    compute_normalized_two_panel_distance,
    generate_two_panel_seeds,
)
from urban_comfort.optimization.two_panel_feasibility import (
    TwoPanelConstraints,
    TwoPanelFeasibilityResult,
    TwoPanelRejectionReason,
    check_two_panel_feasibility,
)
from urban_comfort.optimization.two_panel_ledger import (
    TwoPanelCandidateLedger,
    TwoPanelCandidateRecord,
)
from urban_comfort.optimization.two_panel_objective import (
    TwoPanelComfortObjectiveConfig,
    TwoPanelEvaluationMetrics,
    compute_pareto_front,
    compute_two_panel_objective,
)
from urban_comfort.optimization.two_panel_optimizer import (
    TwoPanelOptimizationEngine,
    TwoPanelOptimizerConfig,
)

# Two-Panel Multi-Intervention Exports
from urban_comfort.optimization.two_panel_parameters import TwoPanelBounds, TwoPanelParams
from urban_comfort.optimization.two_panel_surrogate import (
    TWO_PANEL_DEFAULT_TARGETS,
    TWO_PANEL_FEATURE_NAMES,
    TwoPanelSurrogateConfig,
    TwoPanelSurrogateModel,
    TwoPanelSurrogatePrediction,
    extract_two_panel_features,
    extract_two_panel_targets,
)
from urban_comfort.optimization.two_panel_validation import (
    TwoPanelMultiPathSummary,
    TwoPanelValidationReport,
    validate_two_panel_multi_path,
)
from urban_comfort.optimization.validation import (
    MultiPathValidationSummary,
    run_multi_path_validation_suite,
    validate_candidate_multi_path,
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
    ConstraintSensitivityScenario,
    ObjectiveWeightScenario,
    RobustnessStudyConfig,
    SolarTimestampScenario,
    WeatherScenario,
    evaluate_candidate_at_condition,
    get_standard_constraint_scenarios,
    get_standard_objective_scenarios,
    get_standard_solar_timestamps,
    get_standard_weather_scenarios,
    recompute_score_under_scenario,
)
