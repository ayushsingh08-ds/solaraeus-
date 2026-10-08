"""
Robustness and Sensitivity Analysis Suite for Two-Panel Interventions in SOLARAEUS.

Provides comprehensive multi-dimensional sensitivity evaluations:
1. Random-Seed Robustness (Seeds 7, 42, 12345).
2. Increased Evaluation Budgets (Original 25, Medium 50, Extended 100).
3. Weather Sensitivity (Air Temperature, Humidity, Wind Speed, DNI, DHI).
4. Solar-Timestep Sensitivity (09:00, 11:00, 13:00, 15:00).
5. Objective-Weight Sensitivity (Comfort-Focused, Balanced, Cost-Focused, Coverage-Focused).
6. Constraint Sensitivity (Separation, Setback, Area Limit, Underside Clearance).
7. Cross-Intervention Comparison (No-Intervention, Single-Panel, Two-Panel Nominals & Robust Bests).
8. Multi-Path Physical Solver Validation (CPU Full, GPU Full, GPU Incremental).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from typing import Dict, Any, List, Optional, Tuple, Sequence
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult, full_recompute
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.incremental.mesh_update import AddMultiMeshEdit
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
    compute_pareto_front,
)
from urban_comfort.optimization.two_panel_ledger import (
    TwoPanelCandidateRecord,
    TwoPanelCandidateLedger,
)
from urban_comfort.optimization.two_panel_optimizer import (
    TwoPanelOptimizerConfig,
    TwoPanelOptimizationEngine,
)
from urban_comfort.optimization.two_panel_validation import (
    validate_two_panel_multi_path,
    TwoPanelValidationReport,
)


@dataclass
class WeatherScenario:
    """Weather perturbation scenario."""
    name: str
    description: str
    weather: Weather

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "air_temperature_k": self.weather.air_temperature,
            "relative_humidity_pct": self.weather.relative_humidity,
            "wind_speed_m_s": self.weather.wind_speed,
            "direct_normal_irradiance_w_m2": self.weather.direct_normal_irradiance,
            "diffuse_horizontal_irradiance_w_m2": self.weather.diffuse_horizontal_irradiance,
        }


@dataclass
class SolarTimestampScenario:
    """Solar timestamp scenario for cross-solar-path evaluation."""
    name: str
    description: str
    local_time: str
    date: str = "2024-04-15"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "local_time": self.local_time,
            "date": self.date,
        }


@dataclass
class ObjectiveWeightScenario:
    """Alternative objective weighting scenario."""
    name: str
    description: str
    config: TwoPanelComfortObjectiveConfig
    coverage_bonus_weight: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "weight_mean_utci": self.config.weight_mean_utci,
            "weight_p90_utci": self.config.weight_p90_utci,
            "weight_max_utci": self.config.weight_max_utci,
            "weight_mean_tmrt": self.config.weight_mean_tmrt,
            "weight_area_penalty": self.config.weight_area_penalty,
            "weight_construction_cost": self.config.weight_construction_cost,
            "coverage_bonus_weight": self.coverage_bonus_weight,
            "base_cost_per_panel": self.config.base_cost_per_panel,
            "cost_per_m2": self.config.cost_per_m2,
        }


@dataclass
class ConstraintSensitivityScenario:
    """Perturbed constraint specification to evaluate design volume change."""
    name: str
    description: str
    min_panel_separation_m: float
    min_building_setback_m: float
    max_total_area_m2: float
    min_underside_height_m: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "min_panel_separation_m": self.min_panel_separation_m,
            "min_building_setback_m": self.min_building_setback_m,
            "max_total_area_m2": self.max_total_area_m2,
            "min_underside_height_m": self.min_underside_height_m,
        }


@dataclass
class RobustnessStudyConfig:
    """Global configuration for the two-panel robustness and sensitivity study."""
    seeds: List[int] = field(default_factory=lambda: [7, 42, 12345])
    budgets: List[int] = field(default_factory=lambda: [25, 50, 100])
    nominal_seed: int = 42
    nominal_budget: int = 25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seeds": self.seeds,
            "budgets": self.budgets,
            "nominal_seed": self.nominal_seed,
            "nominal_budget": self.nominal_budget,
        }


def get_standard_weather_scenarios(nominal_weather: Weather) -> Dict[str, WeatherScenario]:
    """Returns standardized weather perturbation scenarios."""
    return {
        "nominal": WeatherScenario(
            name="nominal",
            description="Nominal Church Street summer conditions (35°C, 19.7% RH, 1.5 m/s wind, 728.3 W/m² DNI)",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature,
                relative_humidity=nominal_weather.relative_humidity,
                wind_speed=nominal_weather.wind_speed,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=nominal_weather.direct_normal_irradiance,
                diffuse_horizontal_irradiance=nominal_weather.diffuse_horizontal_irradiance,
            ),
        ),
        "hotter_air": WeatherScenario(
            name="hotter_air",
            description="Extreme heatwave scenario: Air temperature elevated by +4.0 K (39.0°C / 312.15 K)",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature + 4.0,
                relative_humidity=nominal_weather.relative_humidity,
                wind_speed=nominal_weather.wind_speed,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=nominal_weather.direct_normal_irradiance,
                diffuse_horizontal_irradiance=nominal_weather.diffuse_horizontal_irradiance,
            ),
        ),
        "higher_humidity": WeatherScenario(
            name="higher_humidity",
            description="Monsoon/pre-monsoon humidity spike: Relative humidity increased to 55.0%",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature,
                relative_humidity=55.0,
                wind_speed=nominal_weather.wind_speed,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=nominal_weather.direct_normal_irradiance,
                diffuse_horizontal_irradiance=nominal_weather.diffuse_horizontal_irradiance,
            ),
        ),
        "lower_wind": WeatherScenario(
            name="lower_wind",
            description="Stagnant urban canyon air: Wind speed decreased to 0.5 m/s",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature,
                relative_humidity=nominal_weather.relative_humidity,
                wind_speed=0.5,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=nominal_weather.direct_normal_irradiance,
                diffuse_horizontal_irradiance=nominal_weather.diffuse_horizontal_irradiance,
            ),
        ),
        "lower_direct": WeatherScenario(
            name="lower_direct",
            description="Hazy/overcast skies: Direct normal irradiance reduced to 500.0 W/m²",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature,
                relative_humidity=nominal_weather.relative_humidity,
                wind_speed=nominal_weather.wind_speed,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=500.0,
                diffuse_horizontal_irradiance=nominal_weather.diffuse_horizontal_irradiance,
            ),
        ),
        "higher_diffuse": WeatherScenario(
            name="higher_diffuse",
            description="Atmospheric aerosol scattering: Diffuse horizontal irradiance elevated to 300.0 W/m²",
            weather=Weather(
                air_temperature=nominal_weather.air_temperature,
                relative_humidity=nominal_weather.relative_humidity,
                wind_speed=nominal_weather.wind_speed,
                wind_direction=nominal_weather.wind_direction,
                direct_normal_irradiance=nominal_weather.direct_normal_irradiance,
                diffuse_horizontal_irradiance=300.0,
            ),
        ),
    }


def get_standard_solar_timestamps() -> List[SolarTimestampScenario]:
    """Returns standardized solar timestamps for diurnal path sensitivity."""
    return [
        SolarTimestampScenario(name="09:00", description="Morning oblique sun (Nominal optimization timestamp)", local_time="09:00:00"),
        SolarTimestampScenario(name="11:00", description="Late morning high sun", local_time="11:00:00"),
        SolarTimestampScenario(name="13:00", description="Near solar noon peak zenith", local_time="13:00:00"),
        SolarTimestampScenario(name="15:00", description="Mid afternoon western sun", local_time="15:00:00"),
    ]


def get_standard_objective_scenarios() -> Dict[str, ObjectiveWeightScenario]:
    """Returns standardized objective configurations for preference sensitivity."""
    return {
        "balanced": ObjectiveWeightScenario(
            name="balanced",
            description="Nominal balanced comfort and cost objective",
            config=TwoPanelComfortObjectiveConfig(
                weight_mean_utci=1.00,
                weight_p90_utci=0.50,
                weight_max_utci=0.00,
                weight_mean_tmrt=0.00,
                weight_area_penalty=0.005,
                weight_construction_cost=0.0001,
                base_cost_per_panel=5000.0,
                cost_per_m2=250.0,
            ),
            coverage_bonus_weight=0.0,
        ),
        "comfort_focused": ObjectiveWeightScenario(
            name="comfort_focused",
            description="Aggressive pedestrian cooling prioritization with negligible cost sensitivity",
            config=TwoPanelComfortObjectiveConfig(
                weight_mean_utci=2.00,
                weight_p90_utci=1.00,
                weight_max_utci=0.00,
                weight_mean_tmrt=0.00,
                weight_area_penalty=0.001,
                weight_construction_cost=0.0000,
                base_cost_per_panel=5000.0,
                cost_per_m2=250.0,
            ),
            coverage_bonus_weight=0.0,
        ),
        "cost_focused": ObjectiveWeightScenario(
            name="cost_focused",
            description="Strict budget minimization with heavy panel area and staging cost penalties",
            config=TwoPanelComfortObjectiveConfig(
                weight_mean_utci=0.50,
                weight_p90_utci=0.20,
                weight_max_utci=0.00,
                weight_mean_tmrt=0.00,
                weight_area_penalty=0.020,
                weight_construction_cost=0.0005,
                base_cost_per_panel=5000.0,
                cost_per_m2=250.0,
            ),
            coverage_bonus_weight=0.0,
        ),
        "coverage_focused": ObjectiveWeightScenario(
            name="coverage_focused",
            description="Maximizing pedestrian footprint coverage and percentage of cells cooled",
            config=TwoPanelComfortObjectiveConfig(
                weight_mean_utci=0.80,
                weight_p90_utci=0.40,
                weight_max_utci=0.00,
                weight_mean_tmrt=0.00,
                weight_area_penalty=0.002,
                weight_construction_cost=0.00005,
                base_cost_per_panel=5000.0,
                cost_per_m2=250.0,
            ),
            coverage_bonus_weight=0.10,  # Penalizes lack of coverage
        ),
    }


def get_standard_constraint_scenarios() -> Dict[str, ConstraintSensitivityScenario]:
    """Returns standardized constraint scenarios for feasibility boundary sensitivity."""
    return {
        "nominal": ConstraintSensitivityScenario(
            name="nominal",
            description="Nominal Stage 3 feasibility constraints",
            min_panel_separation_m=2.0,
            min_building_setback_m=0.50,
            max_total_area_m2=60.0,
            min_underside_height_m=2.50,
        ),
        "relaxed_separation": ConstraintSensitivityScenario(
            name="relaxed_separation",
            description="Relaxed minimum separation (1.0 m) permitting closer panel spacing",
            min_panel_separation_m=1.0,
            min_building_setback_m=0.50,
            max_total_area_m2=60.0,
            min_underside_height_m=2.50,
        ),
        "strict_separation": ConstraintSensitivityScenario(
            name="strict_separation",
            description="Strict minimum separation (4.0 m) requiring wider panel dispersion",
            min_panel_separation_m=4.0,
            min_building_setback_m=0.50,
            max_total_area_m2=60.0,
            min_underside_height_m=2.50,
        ),
        "strict_setback": ConstraintSensitivityScenario(
            name="strict_setback",
            description="Strict building setback (1.0 m) requiring greater buffer from facade walls",
            min_panel_separation_m=2.0,
            min_building_setback_m=1.00,
            max_total_area_m2=60.0,
            min_underside_height_m=2.50,
        ),
        "relaxed_setback": ConstraintSensitivityScenario(
            name="relaxed_setback",
            description="Relaxed building setback (0.25 m) allowing panels closer to facades",
            min_panel_separation_m=2.0,
            min_building_setback_m=0.25,
            max_total_area_m2=60.0,
            min_underside_height_m=2.50,
        ),
        "tight_area": ConstraintSensitivityScenario(
            name="tight_area",
            description="Reduced canopy area budget (max 40.0 m²)",
            min_panel_separation_m=2.0,
            min_building_setback_m=0.50,
            max_total_area_m2=40.0,
            min_underside_height_m=2.50,
        ),
        "expanded_area": ConstraintSensitivityScenario(
            name="expanded_area",
            description="Expanded canopy area budget (max 80.0 m²)",
            min_panel_separation_m=2.0,
            min_building_setback_m=0.50,
            max_total_area_m2=80.0,
            min_underside_height_m=2.50,
        ),
        "higher_clearance": ConstraintSensitivityScenario(
            name="higher_clearance",
            description="Elevated clearance requirement (underside height >= 3.0 m)",
            min_panel_separation_m=2.0,
            min_building_setback_m=0.50,
            max_total_area_m2=60.0,
            min_underside_height_m=3.00,
        ),
    }


def recompute_score_under_scenario(
    record: TwoPanelCandidateRecord,
    scenario: ObjectiveWeightScenario,
) -> float:
    """Recomputes composite objective score for an evaluated record under alternative weights."""
    if not record.is_feasible or record.metrics is None:
        return float("inf")
    m = record.metrics
    mean_utci = float(m.get("mean_utci_c", 0.0))
    p90_utci = float(m.get("p90_utci_c", 0.0))
    max_utci = float(m.get("max_utci_c", 0.0))
    mean_tmrt = float(m.get("mean_tmrt_c", 0.0))
    pct_improved = float(m.get("percentage_cells_improved_pct", 0.0))
    tot_area = float(record.total_panel_area or 0.0)
    cost = float(m.get("estimated_construction_cost_usd", 0.0))

    cfg = scenario.config
    score = (
        cfg.weight_mean_utci * mean_utci
        + cfg.weight_p90_utci * p90_utci
        + cfg.weight_max_utci * max_utci
        + cfg.weight_mean_tmrt * mean_tmrt
        + cfg.weight_area_penalty * tot_area
        + cfg.weight_construction_cost * cost
    )
    if scenario.coverage_bonus_weight > 0:
        # Subtract coverage reward: higher coverage reduces score
        score -= scenario.coverage_bonus_weight * (pct_improved / 10.0)

    return float(score)


def evaluate_candidate_at_condition(
    params: TwoPanelParams,
    scene: Scene,
    baseline_result: SimulationResult,
    weather: Weather,
    config: SimulationConfig,
    eval_mask: np.ndarray,
    obj_config: TwoPanelComfortObjectiveConfig,
    gpu_engine: GPUIncrementalEngine,
) -> Tuple[SimulationResult, TwoPanelEvaluationMetrics, Dict[str, Any]]:
    """
    Evaluates a two-panel candidate under specific weather or solar conditions.
    Returns (updated_result, metrics, telemetry).
    """
    params_canon = params.canonicalize()
    (m1, _), (m2, _) = params_canon.build_geometries(id_prefix="EVAL")
    m1.material_id = "PANEL_MAT_1"
    m2.material_id = "PANEL_MAT_2"
    mat1 = Material(id="PANEL_MAT_1", albedo=float(params_canon.albedo1), emissivity=0.90, surface_temperature=weather.air_temperature, is_opaque=True)
    mat2 = Material(id="PANEL_MAT_2", albedo=float(params_canon.albedo2), emissivity=0.90, surface_temperature=weather.air_temperature, is_opaque=True)

    edit = AddMultiMeshEdit([m1, m2])
    up_scene, _ = edit.apply(scene)
    up_materials = dict(scene.materials)
    up_materials["PANEL_MAT_1"] = mat1
    up_materials["PANEL_MAT_2"] = mat2
    up_scene.materials = up_materials

    t0 = time.perf_counter()
    up_res, cert = gpu_engine.execute_certified_update(
        previous_scene=scene,
        updated_scene=up_scene,
        previous_result=baseline_result,
        edit=edit,
        weather=weather,
        config=config,
    )
    wall_s = time.perf_counter() - t0

    metrics = compute_two_panel_objective(
        sim_result=up_res.result,
        baseline_result=baseline_result,
        eval_mask=eval_mask,
        area1_m2=params_canon.area1,
        area2_m2=params_canon.area2,
        config=obj_config,
    )

    telemetry = {
        "wall_time_s": wall_s,
        "recomputed_cells": up_res.recomputed_cells,
        "total_cells": up_res.total_cells,
        "reused_fraction_pct": ((up_res.total_cells - up_res.recomputed_cells) / max(1, up_res.total_cells)) * 100.0,
        "cert_status": cert.status,
        "cert_violations": getattr(cert, "n_violations", 0),
        "max_predicted_bound_k": float(np.max(cert.predicted_error_bound)) if hasattr(cert, "predicted_error_bound") else 0.0,
    }

    return up_res.result, metrics, telemetry
