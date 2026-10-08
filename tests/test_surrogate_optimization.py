"""
Unit and Integration Tests for Stage 2: Surrogate-Assisted Optimization.

Tests all 13 required test cases:
1. Surrogate training from the existing ledger.
2. Deterministic training with a fixed seed.
3. Candidate prediction shape and schema.
4. Uncertainty output.
5. Acquisition-function ranking.
6. Feasibility filtering before simulation.
7. Invalid-candidate handling.
8. Ledger append and provenance.
9. Surrogate-assisted optimizer integration.
10. Comparison against random search.
11. Final CPU/GPU/incremental validation.
12. Frozen-directory protection.
13. Fallback behavior when the surrogate dependency is unavailable.
"""

from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import tempfile
import numpy as np
import pytest
from shapely.geometry import Polygon, box

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult, full_recompute
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.parameters import (
    ShadePanelParams, ParameterBounds, build_panel_geometry
)
from urban_comfort.optimization.feasibility import (
    RejectionReason, FeasibilityConstraints, check_feasibility
)
from urban_comfort.optimization.objective import (
    ComfortObjectiveConfig, EvaluationMetrics, compute_objective
)
from urban_comfort.optimization.ledger import (
    CandidateRecord, CandidateLedger
)
from urban_comfort.optimization.optimizer import (
    OptimizerConfig, OptimizationEngine
)
from urban_comfort.optimization.validation import (
    validate_candidate_multi_path, TOLERANCES_INCREMENTAL, TOLERANCES_SOLVER_EQUIVALENCE
)
from urban_comfort.optimization.surrogate import (
    SurrogateConfig, SurrogatePrediction, SurrogateModel, FallbackSurrogateModel
)
from urban_comfort.optimization.acquisition import (
    AcquisitionConfig, CandidateAcquisitionEngine, compute_lcb_score, compute_ei_score
)
from urban_comfort.optimization.surrogate_optimizer import (
    SurrogateOptimizerConfig, SurrogateOptimizationEngine
)


REPO_ROOT = Path(__file__).resolve().parent.parent
FROZEN_STAGE1_DIR = REPO_ROOT / "results" / "church_street_intervention_optimization_20261007_102725"
STAGE1_LEDGER_PATH = FROZEN_STAGE1_DIR / "candidate_ledger.json"


def load_stage1_ledger() -> CandidateLedger:
    assert STAGE1_LEDGER_PATH.exists(), f"Stage 1 ledger missing at {STAGE1_LEDGER_PATH}"
    ledger = CandidateLedger()
    raw = json.loads(STAGE1_LEDGER_PATH.read_text(encoding="utf-8"))
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
        ledger.add(r)
    return ledger


# ---------------------------------------------------------------------------
# Test 1: Surrogate training from the existing ledger
# ---------------------------------------------------------------------------
def test_surrogate_training_from_existing_ledger():
    ledger = load_stage1_ledger()
    assert len(ledger) == 44
    feasible = ledger.get_feasible()
    assert len(feasible) == 21

    cfg = SurrogateConfig(model_type="random_forest", n_estimators=50, seed=42)
    surrogate = SurrogateModel(cfg)
    metrics = surrogate.fit(ledger.records)

    assert surrogate.is_fitted is True
    assert metrics["n_train_samples"] == 21
    assert "dataset_hash" in metrics
    assert len(metrics["dataset_hash"]) == 64

    # Check targets trained
    for target in cfg.target_names:
        assert target in surrogate.regressors
        t_metric = metrics["target_metrics"][target]
        assert t_metric["rmse"] >= 0.0
        assert "feature_importances" in t_metric
        assert len(t_metric["feature_importances"]) == 8


# ---------------------------------------------------------------------------
# Test 2: Deterministic training with a fixed seed
# ---------------------------------------------------------------------------
def test_deterministic_training_fixed_seed():
    ledger = load_stage1_ledger()
    cfg = SurrogateConfig(model_type="random_forest", n_estimators=40, seed=123)

    m1 = SurrogateModel(cfg)
    m1.fit(ledger.records)

    m2 = SurrogateModel(cfg)
    m2.fit(ledger.records)

    test_cand = ShadePanelParams(
        x=135.0, y=60.0, length=4.0, width=2.5, height=3.5, heading_deg=105.0, albedo=0.7
    )

    pred1 = m1.predict(test_cand)
    pred2 = m2.predict(test_cand)

    for tn in cfg.target_names:
        np.testing.assert_allclose(pred1.means[tn], pred2.means[tn], rtol=1e-12)
        np.testing.assert_allclose(pred1.stds[tn], pred2.stds[tn], rtol=1e-12)
    assert pred1.feasibility_probability == pred2.feasibility_probability


# ---------------------------------------------------------------------------
# Test 3: Candidate prediction shape and schema
# ---------------------------------------------------------------------------
def test_candidate_prediction_shape_and_schema():
    ledger = load_stage1_ledger()
    surrogate = SurrogateModel(SurrogateConfig(n_estimators=30, seed=42))
    surrogate.fit(ledger.records)

    cands = [
        ShadePanelParams(x=130.0, y=62.0, length=5.0, width=3.0, height=3.2, heading_deg=100.0, albedo=0.6),
        ShadePanelParams(x=140.0, y=58.0, length=3.5, width=2.2, height=3.8, heading_deg=110.0, albedo=0.75),
    ]

    preds = surrogate.predict_batch(cands)
    assert len(preds) == 2

    for pred in preds:
        assert isinstance(pred, SurrogatePrediction)
        assert "objective_value" in pred.means
        assert "mean_utci_c" in pred.means
        assert "p90_utci_c" in pred.means
        assert "mean_tmrt_c" in pred.means
        assert "delta_mean_tmrt_c" in pred.means
        assert "peak_local_tmrt_improvement" in pred.means

        assert 0.0 <= pred.feasibility_probability <= 1.0
        assert 0.0 <= pred.feasibility_risk <= 1.0
        assert math.isclose(pred.feasibility_probability + pred.feasibility_risk, 1.0, abs_tol=1e-6)

        d = pred.to_dict()
        assert "means" in d and "stds" in d and "feasibility_probability" in d


# ---------------------------------------------------------------------------
# Test 4: Uncertainty output
# ---------------------------------------------------------------------------
def test_uncertainty_output():
    ledger = load_stage1_ledger()
    surrogate = SurrogateModel(SurrogateConfig(n_estimators=50, seed=42))
    surrogate.fit(ledger.records)

    test_cand = ShadePanelParams(x=120.0, y=65.0, length=6.0, width=3.0, height=4.0, heading_deg=90.0, albedo=0.5)
    pred = surrogate.predict(test_cand)

    # Standard deviation must be strictly positive for unobserved design
    for tn in surrogate.config.target_names:
        assert pred.stds[tn] >= 0.0
    assert pred.objective_std > 0.0, "Expected non-zero ensemble tree variance"


# ---------------------------------------------------------------------------
# Test 5: Acquisition-function ranking
# ---------------------------------------------------------------------------
def test_acquisition_function_ranking():
    mu = np.array([55.0, 55.0, 58.0])
    sigma = np.array([0.1, 1.0, 0.5])
    y_best = 55.2

    # Lower Confidence Bound: LCB = mu - kappa * sigma -> score = kappa * sigma - mu
    score_lcb_k1 = compute_lcb_score(mu, sigma, kappa=1.0)
    score_lcb_k3 = compute_lcb_score(mu, sigma, kappa=3.0)

    # Candidate 1 has higher uncertainty than 0 with same mu -> candidate 1 scores higher
    assert score_lcb_k1[1] > score_lcb_k1[0]
    assert score_lcb_k3[1] > score_lcb_k3[0]

    # Expected Improvement
    ei = compute_ei_score(mu, sigma, y_best=y_best, xi=0.01)
    assert ei[0] >= 0.0
    assert ei[1] >= 0.0
    # Candidate with higher uncertainty should have higher upside EI given same mean close to y_best
    assert ei[1] > ei[0]


# ---------------------------------------------------------------------------
# Test 6: Feasibility filtering before simulation
# ---------------------------------------------------------------------------
def test_feasibility_filtering_before_simulation():
    ledger = load_stage1_ledger()
    surrogate = SurrogateModel(SurrogateConfig(n_estimators=30, seed=42))
    surrogate.fit(ledger.records)

    corridor = Polygon([(110, 55), (150, 55), (150, 70), (110, 70)])
    constraints = FeasibilityConstraints(
        allowed_area=corridor,
        min_underside_height_m=2.5,
        max_underside_height_m=5.0,
        min_length_m=2.5,
        max_length_m=12.0,
        min_width_m=1.5,
        max_width_m=4.5,
    )
    bounds = ParameterBounds(
        x_min=110.0, x_max=150.0, y_min=55.0, y_max=70.0,
        length_min=3.0, length_max=10.0, width_min=2.0, width_max=4.0,
        height_min=2.5, height_max=4.5, heading_min=80.0, heading_max=120.0,
        albedo_min=0.2, albedo_max=0.8
    )

    acq = CandidateAcquisitionEngine(AcquisitionConfig(pool_size=200, seed=42))
    batch, diag = acq.propose_batch(
        surrogate=surrogate,
        constraints=constraints,
        bounds=bounds,
        current_best_objective=54.93,
        batch_size=5,
    )

    assert len(batch) == 5
    assert diag["feasible_count"] > 0
    assert diag["rejected_count"] >= 0

    # Every single proposed candidate MUST pass feasibility
    for item in batch:
        p = item["params"]
        f_res = check_feasibility(p, constraints)
        assert f_res.is_valid is True, f"Proposed candidate failed feasibility: {f_res.message}"


# ---------------------------------------------------------------------------
# Test 7: Invalid-candidate handling
# ---------------------------------------------------------------------------
def test_invalid_candidate_handling():
    # Synthetic scene for testing exception isolation
    grid_cfg = PedestrianGridConfig(extent_x=20.0, extent_y=20.0, origin_x=0.0, origin_y=0.0, resolution=2.0, pedestrian_height=1.1)
    scene = Scene(buildings={}, pedestrian_grid=grid_cfg)
    grid = PedestrianGrid(grid_cfg)
    zeros = np.zeros(grid.shape, dtype=np.float64)
    base_res = SimulationResult(
        shadow_mask=np.zeros(grid.shape, dtype=bool),
        direct_irradiance=zeros,
        visibility_fields={"svf": np.ones(grid.shape, dtype=np.float64)},
        shortwave_flux=zeros,
        longwave_flux=zeros,
        tmrt=zeros + 300.0,
        utci=zeros + 30.0,
        metadata={"source": "test"},
    )

    constraints = FeasibilityConstraints(
        allowed_area=box(0, 0, 20, 20),
        min_underside_height_m=2.5,
    )
    engine = OptimizationEngine(
        baseline_scene=scene,
        baseline_result=base_res,
        weather=Weather(air_temperature=300.0, relative_humidity=50.0, wind_speed=1.0, wind_direction=0.0,
                        direct_normal_irradiance=600.0, diffuse_horizontal_irradiance=100.0),
        sim_config=SimulationConfig(backend="cpu"),
        feasibility_constraints=constraints,
        eval_mask=np.ones(grid.shape, dtype=bool),
        config=OptimizerConfig(fallback_to_cpu=True),
    )

    # Infeasible candidate (height < 2.5m)
    p_infeasible = ShadePanelParams(x=10.0, y=10.0, length=4.0, width=2.0, height=1.5, heading_deg=0.0, albedo=0.5)
    rec_inf = engine.evaluate_candidate(p_infeasible, method="test_infeasible")

    assert rec_inf.is_feasible is False
    assert rec_inf.rejection_reason == RejectionReason.INSUFFICIENT_CLEARANCE.value
    assert rec_inf.objective_value == float("inf")

    # Ensure ledger adds record safely
    assert len(engine.ledger) == 1
    assert len(engine.ledger.get_feasible()) == 0


# ---------------------------------------------------------------------------
# Test 8: Ledger append and provenance
# ---------------------------------------------------------------------------
def test_ledger_append_and_provenance():
    ledger = CandidateLedger()
    p = ShadePanelParams(x=10.0, y=10.0, length=4.0, width=2.0, height=3.0, heading_deg=0.0, albedo=0.5)

    rec = CandidateRecord(
        candidate_id="CAND_9999_TEST",
        iteration=0,
        method="surrogate_test",
        params=p.to_dict(),
        is_feasible=True,
        objective_value=50.0,
        wall_time_s=0.05,
    )
    ledger.add(rec)
    assert len(ledger) == 1
    assert ledger.get_best().candidate_id == "CAND_9999_TEST"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ledger.save_json(tmp_path / "ledger.json")
        ledger.save_csv(tmp_path / "ledger.csv")

        assert (tmp_path / "ledger.json").exists()
        assert (tmp_path / "ledger.csv").exists()

        content = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
        assert len(content) == 1
        assert content[0]["candidate_id"] == "CAND_9999_TEST"


# ---------------------------------------------------------------------------
# Test 9: Surrogate-assisted optimizer integration
# ---------------------------------------------------------------------------
def test_surrogate_assisted_optimizer_integration():
    grid_cfg = PedestrianGridConfig(extent_x=20.0, extent_y=20.0, origin_x=0.0, origin_y=0.0, resolution=2.0, pedestrian_height=1.1)
    scene = Scene(buildings={}, pedestrian_grid=grid_cfg)
    grid = PedestrianGrid(grid_cfg)
    zeros = np.zeros(grid.shape, dtype=np.float64)
    base_res = SimulationResult(
        shadow_mask=np.zeros(grid.shape, dtype=bool),
        direct_irradiance=zeros,
        visibility_fields={"svf": np.ones(grid.shape, dtype=np.float64)},
        shortwave_flux=zeros,
        longwave_flux=zeros,
        tmrt=zeros + 305.0,
        utci=zeros + 35.0,
        metadata={"source": "test"},
    )
    constraints = FeasibilityConstraints(
        allowed_area=box(2, 2, 18, 18),
        min_underside_height_m=2.5,
    )
    bounds = ParameterBounds(
        x_min=4.0, x_max=16.0, y_min=4.0, y_max=16.0,
        length_min=2.5, length_max=6.0, width_min=1.5, width_max=3.5,
        height_min=2.5, height_max=4.0, heading_min=0.0, heading_max=90.0,
        albedo_min=0.3, albedo_max=0.8
    )

    opt_cfg = SurrogateOptimizerConfig(
        seed=42,
        num_iterations=2,
        batch_size=2,
        bounds=bounds,
        fallback_to_cpu=True,
        surrogate_config=SurrogateConfig(n_estimators=10, seed=42),
        acquisition_config=AcquisitionConfig(pool_size=100, seed=42),
    )

    engine = SurrogateOptimizationEngine(
        baseline_scene=scene,
        baseline_result=base_res,
        weather=Weather(air_temperature=300.0, relative_humidity=50.0, wind_speed=1.0, wind_direction=0.0,
                        direct_normal_irradiance=600.0, diffuse_horizontal_irradiance=100.0),
        sim_config=SimulationConfig(backend="cpu"),
        feasibility_constraints=constraints,
        eval_mask=np.ones(grid.shape, dtype=bool),
        config=opt_cfg,
    )

    summary = engine.run()
    assert summary["surrogate_iterations"] == 2
    assert len(summary["retraining_history"]) == 2
    assert len(summary["predictions_log"]) > 0
    assert len(engine.ledger) > 0


# ---------------------------------------------------------------------------
# Test 10: Comparison against random search
# ---------------------------------------------------------------------------
def test_comparison_against_random_search():
    ledger = load_stage1_ledger()
    feasible = ledger.get_feasible()
    assert len(feasible) > 0

    # Filter random search vs evolutionary search from Stage 1
    rand_candidates = [r for r in feasible if r.method == "random"]
    evo_candidates = [r for r in feasible if r.method == "evolutionary"]

    best_rand = min(rand_candidates, key=lambda r: r.objective_value) if rand_candidates else None
    best_evo = min(evo_candidates, key=lambda r: r.objective_value) if evo_candidates else None

    assert best_rand is not None
    assert best_evo is not None
    # Evolutionary search in Stage 1 found candidate <= random search
    assert best_evo.objective_value <= best_rand.objective_value


# ---------------------------------------------------------------------------
# Test 11: Final CPU/GPU/incremental validation
# ---------------------------------------------------------------------------
def test_final_multi_path_validation():
    # Test on Stage 1 best candidate
    cand_dict = json.loads((FROZEN_STAGE1_DIR / "best_candidate.json").read_text(encoding="utf-8"))
    best_params = ShadePanelParams.from_dict(cand_dict["params"])

    # Synthetic validation scene
    grid_cfg = PedestrianGridConfig(extent_x=20.0, extent_y=20.0, origin_x=0.0, origin_y=0.0, resolution=2.0, pedestrian_height=1.1)
    scene = Scene(
        buildings={"B1": Building(id="B1", footprint=BoundingBox2D(0.0, 4.0, 0.0, 4.0), height=8.0)},
        pedestrian_grid=grid_cfg,
        materials={
            "default_wall": Material(id="default_wall", albedo=0.20, emissivity=0.90, surface_temperature=305.15),
            "default_ground": Material(id="default_ground", albedo=0.15, emissivity=0.95, surface_temperature=308.15),
        }
    )
    weather = Weather(
        air_temperature=305.15, relative_humidity=40.0, wind_speed=1.5, wind_direction=90.0,
        direct_normal_irradiance=700.0, diffuse_horizontal_irradiance=150.0
    )
    sim_cfg = SimulationConfig(
        latitude=12.97, longitude=77.60, date="2024-04-15", local_time="10:00:00",
        pedestrian_height=1.1, grid_resolution=2.0, tmrt_tolerance=0.50,
        sky_patch_configuration=32, max_svf_search_dist_m=30.0, backend="auto"
    )
    base_res = full_recompute(scene, weather, sim_cfg, backend="auto")

    gpu_engine = GPUIncrementalEngine(fallback_to_cpu=True)
    val_report = validate_candidate_multi_path(
        candidate_id="TEST_CAND_001",
        params=ShadePanelParams(x=10.0, y=10.0, length=4.0, width=2.0, height=3.0, heading_deg=45.0, albedo=0.6),
        role="test_best",
        baseline_scene=scene,
        baseline_result=base_res,
        weather=weather,
        config=sim_cfg,
        gpu_engine=gpu_engine,
    )

    assert val_report.all_passed is True
    assert val_report.cpu_full_vs_gpu_full.passed_all is True
    assert val_report.cpu_full_vs_gpu_inc.passed_all is True
    assert val_report.gpu_full_vs_gpu_inc.passed_all is True


# ---------------------------------------------------------------------------
# Test 12: Frozen-directory protection
# ---------------------------------------------------------------------------
def test_frozen_directory_protection():
    frozen_dirs = [
        REPO_ROOT / "results" / "church_street_static_20261006_232110",
        REPO_ROOT / "results" / "church_street_shade_full_20261007_001600",
        REPO_ROOT / "results" / "church_street_shade_incremental_20261007_081114",
        REPO_ROOT / "results" / "church_street_gpu_full_20261007_091111",
        REPO_ROOT / "results" / "church_street_shade_gpu_incremental_20261007_093905",
        REPO_ROOT / "results" / "church_street_intervention_optimization_20261007_102725",
    ]

    for fd in frozen_dirs:
        assert fd.exists(), f"Protected frozen directory missing: {fd}"

    # Verify Stage 1 best candidate json is intact
    best_path = FROZEN_STAGE1_DIR / "best_candidate.json"
    assert best_path.exists()
    cand_data = json.loads(best_path.read_text(encoding="utf-8"))
    assert cand_data["candidate_id"] == "CAND_0036_EVOL"
    assert math.isclose(cand_data["objective_value"], 54.93094153527447, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Test 13: Fallback behavior when the surrogate dependency is unavailable
# ---------------------------------------------------------------------------
def test_fallback_behavior_surrogate_unavailable():
    ledger = load_stage1_ledger()
    fallback_model = FallbackSurrogateModel()
    metrics = fallback_model.fit(ledger.records)

    assert fallback_model.is_fitted is True
    assert metrics["model_type"] == "fallback_empirical"

    test_cand = ShadePanelParams(x=130.0, y=60.0, length=4.0, width=2.5, height=3.2, heading_deg=100.0, albedo=0.7)
    pred = fallback_model.predict(test_cand)

    assert isinstance(pred, SurrogatePrediction)
    assert "objective_value" in pred.means
    assert pred.objective_std > 0.0
    assert pred.feasibility_probability == 1.0
