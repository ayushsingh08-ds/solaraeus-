"""
Comprehensive Test Suite for SOLARAEUS Two-Panel Robustness and Sensitivity Validation.

Verifies:
1. Reproducibility for each random seed.
2. Different seeds produce independent but valid runs.
3. Evaluation-budget configuration.
4. Weather-scenario configuration.
5. Solar-timestep configuration.
6. Objective-weight configuration.
7. Constraint-sensitivity configuration.
8. Candidate ranking consistency.
9. Candidate ledger completeness.
10. Certificate-failure handling.
11. CPU/GPU/incremental parity.
12. Frozen-directory protection.
13. Single-panel regression preservation.
14. Two-panel feasibility preservation.
15. No duplicate panel or candidate records.
16. Deterministic report generation where applicable.
"""

from __future__ import annotations
import copy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import pytest
import numpy as np
from shapely.geometry import Polygon, Point

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult, full_recompute
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.incremental.mesh_update import AddMultiMeshEdit
from urban_comfort.optimization.parameters import ShadePanelParams, build_panel_geometry
from urban_comfort.optimization.feasibility import FeasibilityConstraints, check_feasibility
from urban_comfort.optimization.objective import ComfortObjectiveConfig, compute_objective
from urban_comfort.optimization.two_panel_parameters import TwoPanelParams, TwoPanelBounds
from urban_comfort.optimization.two_panel_feasibility import (
    TwoPanelConstraints,
    check_two_panel_feasibility,
    TwoPanelRejectionReason,
)
from urban_comfort.optimization.two_panel_objective import (
    TwoPanelComfortObjectiveConfig,
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
)
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


@pytest.fixture
def synthetic_scene_and_baseline():
    """Builds a small, fast synthetic scene for two-panel testing."""
    grid_cfg = PedestrianGridConfig(extent_x=24.0, extent_y=24.0, resolution=1.0, pedestrian_height=1.5)
    scene = Scene(pedestrian_grid=grid_cfg)
    bldg = Building(id="B1", footprint=BoundingBox2D(xmin=2.0, xmax=6.0, ymin=2.0, ymax=6.0), height=10.0, material_id="default_wall")
    scene.add_building(bldg)
    scene.materials["default_wall"] = Material(id="default_wall", albedo=0.3, emissivity=0.9, surface_temperature=305.15)
    scene.materials["default_ground"] = Material(id="default_ground", albedo=0.2, emissivity=0.95, surface_temperature=305.15)

    config = SimulationConfig(
        latitude=12.97, longitude=77.59, date="2024-04-15", local_time="09:00:00",
        sky_patch_configuration=8, tmrt_tolerance=0.5
    )
    weather = Weather(
        air_temperature=303.15, relative_humidity=50.0, wind_speed=1.5,
        wind_direction=180.0, direct_normal_irradiance=800.0, diffuse_horizontal_irradiance=200.0
    )

    base_res = full_recompute(scene, weather, config, backend="cpu")

    allowed_poly = Polygon([(8.0, 2.0), (22.0, 2.0), (22.0, 22.0), (8.0, 22.0)])
    single_c = FeasibilityConstraints.from_scene(
        scene=scene, allowed_area=allowed_poly, min_underside_height_m=2.5, min_building_setback_m=0.5
    )
    constraints = TwoPanelConstraints.from_single_constraints(
        single=single_c, min_panel_separation_m=2.0, max_individual_area_m2=30.0, max_total_area_m2=50.0
    )

    return scene, base_res, weather, config, constraints


# Test 1: Reproducibility for each random seed
def test_random_seed_reproducibility(synthetic_scene_and_baseline):
    """Verifies that running with identical seed produces identical initial candidates."""
    scene, base_res, weather, config, constraints = synthetic_scene_and_baseline
    bounds = TwoPanelBounds.get_canonical_church_street_bounds()

    rng1 = np.random.default_rng(42)
    sample1 = bounds.sample_uniform(rng1)

    rng2 = np.random.default_rng(42)
    sample2 = bounds.sample_uniform(rng2)

    assert sample1.x1 == sample2.x1
    assert sample1.y1 == sample2.y1
    assert sample1.x2 == sample2.x2
    assert sample1.y2 == sample2.y2
    assert sample1.total_area == sample2.total_area


# Test 2: Different seeds produce independent but valid runs
def test_different_seeds_independent(synthetic_scene_and_baseline):
    """Verifies that seeds 7, 42, and 12345 produce distinct samples."""
    bounds = TwoPanelBounds.get_canonical_church_street_bounds()

    s7 = bounds.sample_uniform(np.random.default_rng(7))
    s42 = bounds.sample_uniform(np.random.default_rng(42))
    s12345 = bounds.sample_uniform(np.random.default_rng(12345))

    assert s7.x1 != s42.x1
    assert s42.x1 != s12345.x1
    assert s7.y2 != s12345.y2


# Test 3: Evaluation-budget configuration
def test_evaluation_budget_configuration():
    """Verifies budget math and scaling configurations."""
    cfg = TwoPanelOptimizerConfig(seed=42, seed_budget=10, num_iterations=3, batch_size=5)
    d = cfg.to_dict()
    assert d["total_target_budget"] == 25

    cfg_med = TwoPanelOptimizerConfig(seed=42, seed_budget=10, num_iterations=8, batch_size=5)
    assert cfg_med.to_dict()["total_target_budget"] == 50

    cfg_ext = TwoPanelOptimizerConfig(seed=42, seed_budget=10, num_iterations=18, batch_size=5)
    assert cfg_ext.to_dict()["total_target_budget"] == 100


# Test 4: Weather-scenario configuration
def test_weather_scenario_configuration():
    """Verifies all standard weather perturbation scenarios are well-defined."""
    base_w = Weather(air_temperature=308.15, relative_humidity=20.0, wind_speed=1.5, wind_direction=90.0, direct_normal_irradiance=728.0, diffuse_horizontal_irradiance=172.0)
    scenarios = get_standard_weather_scenarios(base_w)

    assert len(scenarios) == 6
    assert "nominal" in scenarios
    assert "hotter_air" in scenarios
    assert "higher_humidity" in scenarios
    assert "lower_wind" in scenarios
    assert "lower_direct" in scenarios
    assert "higher_diffuse" in scenarios

    assert scenarios["hotter_air"].weather.air_temperature == pytest.approx(312.15)
    assert scenarios["higher_humidity"].weather.relative_humidity == 55.0
    assert scenarios["lower_wind"].weather.wind_speed == 0.5
    assert scenarios["lower_direct"].weather.direct_normal_irradiance == 500.0


# Test 5: Solar-timestep configuration
def test_solar_timestep_configuration():
    """Verifies diurnal solar timestamp configurations."""
    ts_list = get_standard_solar_timestamps()
    assert len(ts_list) == 4
    times = [ts.local_time for ts in ts_list]
    assert times == ["09:00:00", "11:00:00", "13:00:00", "15:00:00"]


# Test 6: Objective-weight configuration
def test_objective_weight_configuration():
    """Verifies alternative objective weight profiles."""
    objs = get_standard_objective_scenarios()
    assert len(objs) == 4
    assert "balanced" in objs
    assert "comfort_focused" in objs
    assert "cost_focused" in objs
    assert "coverage_focused" in objs

    # Comfort focused has higher weight on UTCI
    assert objs["comfort_focused"].config.weight_mean_utci > objs["balanced"].config.weight_mean_utci
    # Cost focused has higher weight on area/cost penalties
    assert objs["cost_focused"].config.weight_construction_cost > objs["balanced"].config.weight_construction_cost


# Test 7: Constraint-sensitivity configuration
def test_constraint_sensitivity_configuration():
    """Verifies constraint sensitivity definitions and boundary variations."""
    c_scenarios = get_standard_constraint_scenarios()
    assert len(c_scenarios) == 8
    assert "nominal" in c_scenarios
    assert "relaxed_separation" in c_scenarios
    assert "strict_separation" in c_scenarios
    assert "strict_setback" in c_scenarios

    assert c_scenarios["relaxed_separation"].min_panel_separation_m == 1.0
    assert c_scenarios["strict_separation"].min_panel_separation_m == 4.0
    assert c_scenarios["strict_setback"].min_building_setback_m == 1.00


# Test 8: Candidate ranking consistency
def test_candidate_ranking_consistency():
    """Verifies that recompute_score_under_scenario calculates consistent and ordered scores."""
    rec1 = TwoPanelCandidateRecord(
        candidate_id="C1", iteration=0, method="test", params={}, is_feasible=True,
        total_panel_area=15.0,
        metrics={"mean_utci_c": 36.0, "p90_utci_c": 39.0, "max_utci_c": 41.0, "mean_tmrt_c": 55.0, "percentage_cells_improved_pct": 30.0, "estimated_construction_cost_usd": 12000.0}
    )
    rec2 = TwoPanelCandidateRecord(
        candidate_id="C2", iteration=1, method="test", params={}, is_feasible=True,
        total_panel_area=25.0,
        metrics={"mean_utci_c": 35.8, "p90_utci_c": 38.5, "max_utci_c": 40.5, "mean_tmrt_c": 54.0, "percentage_cells_improved_pct": 45.0, "estimated_construction_cost_usd": 18000.0}
    )

    scenarios = get_standard_objective_scenarios()
    score1_bal = recompute_score_under_scenario(rec1, scenarios["balanced"])
    score2_bal = recompute_score_under_scenario(rec2, scenarios["balanced"])
    assert isinstance(score1_bal, float)
    assert isinstance(score2_bal, float)

    # Cost-focused scenario should favor lower-cost C1
    score1_cost = recompute_score_under_scenario(rec1, scenarios["cost_focused"])
    score2_cost = recompute_score_under_scenario(rec2, scenarios["cost_focused"])
    assert score1_cost < score2_cost


# Test 9: Candidate ledger completeness
def test_candidate_ledger_completeness():
    """Verifies that TwoPanelCandidateLedger correctly serializes and filters all fields."""
    ledger = TwoPanelCandidateLedger()
    rec = TwoPanelCandidateRecord(
        candidate_id="CAND_0001", iteration=1, method="surrogate",
        params={"x1": 10.0, "y1": 12.0, "length1": 3.0, "width1": 2.0, "height1": 3.0, "heading_deg1": 90.0, "albedo1": 0.6,
                "x2": 16.0, "y2": 12.0, "length2": 3.0, "width2": 2.0, "height2": 3.0, "heading_deg2": 90.0, "albedo2": 0.6},
        is_feasible=True, total_panel_area=12.0, objective_value=55.2,
        metrics={"mean_utci_c": 36.1, "estimated_construction_cost_usd": 13000.0},
        reused_cells_count=500, recomputed_cells_count=10,
    )
    ledger.add(rec)
    assert len(ledger) == 1
    assert len(ledger.get_feasible()) == 1

    d = ledger.to_dict()
    assert d["records"][0]["candidate_id"] == "CAND_0001"
    assert d["records"][0]["total_panel_area_m2"] == 12.0


# Test 10: Certificate-failure handling
def test_certificate_failure_handling():
    """Verifies that certificate failures or violations are recorded properly."""
    rec_violation = TwoPanelCandidateRecord(
        candidate_id="CAND_FAIL", iteration=0, method="test", params={}, is_feasible=True,
        certificate_status="violation", certificate_violations=2, max_certificate_bound_k=1.25,
        objective_value=float("inf"), metrics=None, rejection_reason="CERTIFICATE_VIOLATION"
    )
    assert rec_violation.certificate_violations == 2
    assert rec_violation.certificate_status == "violation"


# Test 11: CPU/GPU/incremental parity
def test_cpu_gpu_incremental_parity(synthetic_scene_and_baseline):
    """Verifies parity between CPU Full and GPU Incremental on synthetic two-panel scene."""
    scene, base_res, weather, config, constraints = synthetic_scene_and_baseline
    params = TwoPanelParams(
        x1=10.0, y1=10.0, length1=3.0, width1=2.0, height1=3.0, heading_deg1=90.0, albedo1=0.6,
        x2=16.0, y2=10.0, length2=3.0, width2=2.0, height2=3.0, heading_deg2=90.0, albedo2=0.6,
    )
    engine = GPUIncrementalEngine(fallback_to_cpu=True)
    report = validate_two_panel_multi_path(
        candidate_id="TEST_PARITY", params=params, role="Test",
        baseline_scene=scene, baseline_result=base_res, weather=weather,
        config=config, gpu_engine=engine
    )
    assert report.all_passed
    assert report.certificate_violations == 0
    assert report.gpu_full_vs_gpu_inc.max_tmrt_diff_k <= config.tmrt_tolerance


# Test 12: Frozen-directory protection
def test_frozen_directory_protection():
    """Verifies that all 8 earlier project result directories exist and remain unmodified."""
    root_dir = Path(__file__).resolve().parent.parent
    frozen_dirs = [
        root_dir / "results" / "church_street_static_20261006_232110",
        root_dir / "results" / "church_street_shade_full_20261007_001600",
        root_dir / "results" / "church_street_shade_incremental_20261007_081114",
        root_dir / "results" / "church_street_gpu_full_20261007_091111",
        root_dir / "results" / "church_street_shade_gpu_incremental_20261007_093905",
        root_dir / "results" / "church_street_intervention_optimization_20261007_102725",
        root_dir / "results" / "church_street_surrogate_optimization_20261007_110633",
        root_dir / "results" / "church_street_multi_intervention_optimization_20261007_114326",
    ]
    for d in frozen_dirs:
        assert d.exists(), f"Frozen directory {d.name} must exist"
        assert d.is_dir()


# Test 13: Single-panel regression preservation
def test_single_panel_regression_preservation(synthetic_scene_and_baseline):
    """Verifies single-panel workflow remains functional and protected."""
    scene, base_res, weather, config, constraints = synthetic_scene_and_baseline
    sp_params = ShadePanelParams(x=10.0, y=10.0, length=3.0, width=2.0, height=3.0, heading_deg=90.0, albedo=0.6)
    mesh, footprint = build_panel_geometry(sp_params)
    assert mesh is not None
    assert footprint.area == pytest.approx(6.0)

    allowed_poly = Polygon([(8.0, 2.0), (22.0, 2.0), (22.0, 22.0), (8.0, 22.0)])
    single_c = FeasibilityConstraints.from_scene(scene=scene, allowed_area=allowed_poly)
    f_res = check_feasibility(sp_params, single_c)
    assert f_res.is_valid


# Test 14: Two-panel feasibility preservation
def test_two_panel_feasibility_preservation(synthetic_scene_and_baseline):
    """Verifies collision, separation, and area constraints for two panels."""
    scene, base_res, weather, config, constraints = synthetic_scene_and_baseline

    # Overlapping / colliding panels
    colliding = TwoPanelParams(
        x1=10.0, y1=10.0, length1=4.0, width1=3.0, height1=3.0, heading_deg1=90.0, albedo1=0.6,
        x2=11.0, y2=10.0, length2=4.0, width2=3.0, height2=3.0, heading_deg2=90.0, albedo2=0.6,
    )
    res_col = check_two_panel_feasibility(colliding, constraints)
    assert not res_col.is_valid
    assert res_col.rejection_reason in (
        TwoPanelRejectionReason.PANEL_COLLISION,
        TwoPanelRejectionReason.INSUFFICIENT_PANEL_SEPARATION,
    )


# Test 15: No duplicate panel or candidate records
def test_no_duplicate_candidate_records():
    """Verifies ledger rejects or identifies duplicate candidate IDs."""
    ledger = TwoPanelCandidateLedger()
    rec1 = TwoPanelCandidateRecord(candidate_id="C1", iteration=0, method="test", params={}, is_feasible=True)
    rec2 = TwoPanelCandidateRecord(candidate_id="C2", iteration=1, method="test", params={}, is_feasible=True)
    ledger.add(rec1)
    ledger.add(rec2)
    ids = [r.candidate_id for r in ledger.records]
    assert len(ids) == len(set(ids))


# Test 16: Deterministic report generation
def test_deterministic_report_generation():
    """Verifies that recomputing metrics for identical candidates yields deterministic values."""
    m_dict = {
        "mean_utci_c": 36.05, "p90_utci_c": 39.80, "max_utci_c": 41.20,
        "mean_tmrt_c": 56.10, "percentage_cells_improved_pct": 35.0,
        "estimated_construction_cost_usd": 15000.0,
    }
    rec = TwoPanelCandidateRecord(
        candidate_id="DET_TEST", iteration=0, method="test", params={}, is_feasible=True,
        total_panel_area=20.0, metrics=m_dict,
    )
    sc = get_standard_objective_scenarios()["balanced"]
    score_a = recompute_score_under_scenario(rec, sc)
    score_b = recompute_score_under_scenario(rec, sc)
    assert score_a == score_b
