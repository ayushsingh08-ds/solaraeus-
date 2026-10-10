"""
Geographically Constrained AI Intervention Optimization Package for SOLARAEUS.

Provides parameterization, geographic feasibility validation, multi-criteria comfort objectives,
candidate ledgers, derivative-free search optimizers, surrogate modeling, uncertainty-aware acquisition,
and multi-path physical validation for single-panel and dual-panel shade interventions.
"""

from __future__ import annotations

from solaraeus.placement.parameters import (
    ShadePanelParams, ParameterBounds, build_panel_geometry
)
from solaraeus.placement.feasibility import (
    RejectionReason, FeasibilityConstraints, FeasibilityResult, check_feasibility
)
from solaraeus.placement.objective import (
    ComfortObjectiveConfig, EvaluationMetrics, compute_objective
)
from solaraeus.placement.evaluation_ledger import (
    CandidateRecord, CandidateLedger
)
from solaraeus.placement.placement_solver import (
    PlacementSolverEngine, PlacementSolverConfig
)
from solaraeus.placement.candidate_validation import (
    validate_candidate_multi_path, MultiPathValidationSummary, run_multi_path_validation_suite
)
from solaraeus.placement.surrogate_model import (
    SurrogateConfig, SurrogatePrediction, SurrogateModel, FallbackSurrogateModel
)
from solaraeus.placement.acquisition import (
    AcquisitionConfig, CandidateAcquisitionEngine
)
from solaraeus.placement.surrogate_placement_solver import (
    SurrogatePlacementSolverConfig, SurrogatePlacementSolverEngine
)

# Dual-Panel Multi-Intervention Exports
from solaraeus.placement.dual_panel_parameters import (
    DualPanelParams, DualPanelBounds
)
from solaraeus.placement.dual_panel_feasibility import (
    DualPanelRejectionReason, DualPanelFeasibilityResult, DualPanelConstraints, check_dual_panel_feasibility
)
from solaraeus.placement.dual_panel_objective import (
    DualPanelComfortObjectiveConfig, DualPanelEvaluationMetrics, compute_dual_panel_objective, compute_pareto_front
)
from solaraeus.placement.dual_panel_evaluation_ledger import (
    DualPanelCandidateRecord, DualPanelCandidateLedger
)
from solaraeus.placement.dual_panel_surrogate_model import (
    DUAL_PANEL_FEATURE_NAMES, DUAL_PANEL_DEFAULT_TARGETS, DualPanelSurrogateConfig,
    DualPanelSurrogatePrediction, extract_dual_panel_features, extract_dual_panel_targets,
    DualPanelSurrogateModel
)
from solaraeus.placement.dual_panel_acquisition import (
    DualPanelAcquisitionConfig, DualPanelAcquisitionEngine, generate_dual_panel_seeds,
    compute_normalized_dual_panel_distance
)
from solaraeus.placement.dual_panel_placement_solver import (
    DualPanelPlacementSolverConfig, DualPanelPlacementSolverEngine
)
from solaraeus.placement.dual_panel_candidate_validation import (
    DualPanelValidationReport, DualPanelMultiPathSummary, validate_dual_panel_multi_path
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
    "PlacementSolverEngine",
    "PlacementSolverConfig",
    "validate_candidate_multi_path",
    "MultiPathValidationSummary",
    "run_multi_path_validation_suite",
    "SurrogateConfig",
    "SurrogatePrediction",
    "SurrogateModel",
    "FallbackSurrogateModel",
    "AcquisitionConfig",
    "CandidateAcquisitionEngine",
    "SurrogatePlacementSolverConfig",
    "SurrogatePlacementSolverEngine",
    # Dual-panel exports
    "DualPanelParams",
    "DualPanelBounds",
    "DualPanelRejectionReason",
    "DualPanelFeasibilityResult",
    "DualPanelConstraints",
    "check_dual_panel_feasibility",
    "DualPanelComfortObjectiveConfig",
    "DualPanelEvaluationMetrics",
    "compute_dual_panel_objective",
    "compute_pareto_front",
    "DualPanelCandidateRecord",
    "DualPanelCandidateLedger",
    "DUAL_PANEL_FEATURE_NAMES",
    "DUAL_PANEL_DEFAULT_TARGETS",
    "DualPanelSurrogateConfig",
    "DualPanelSurrogatePrediction",
    "extract_dual_panel_features",
    "extract_dual_panel_targets",
    "DualPanelSurrogateModel",
    "DualPanelAcquisitionConfig",
    "DualPanelAcquisitionEngine",
    "generate_dual_panel_seeds",
    "compute_normalized_dual_panel_distance",
    "DualPanelPlacementSolverConfig",
    "DualPanelPlacementSolverEngine",
    "DualPanelValidationReport",
    "DualPanelMultiPathSummary",
    "validate_dual_panel_multi_path",
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

from solaraeus.placement.robustness import (
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
