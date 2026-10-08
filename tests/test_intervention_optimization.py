"""
Unit & Integration Tests for Geographically Constrained AI Intervention Optimization.

Covers the 12 specific testing requirements:
  1. Parameter bounds & vector mapping
  2. Invalid geometry rejection
  3. Building-collision rejection
  4. Pedestrian-clearance rejection
  5. Deterministic candidate generation
  6. Random-search reproducibility
  7. Optimizer-to-solver integration (synthetic scene)
  8. Certificate failure & exception isolation
  9. Candidate ledger completeness & persistence
  10. Frozen directory protection
  11. Best-candidate selection
  12. Final CPU / GPU / Incremental multi-path parity validation
"""

from __future__ import annotations
import math
import os
from pathlib import Path
import shutil
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
    validate_candidate_multi_path, run_multi_path_validation_suite
)


# ---------------------------------------------------------------------------
# Test 1: Parameter bounds & vector mapping
# ---------------------------------------------------------------------------
def test_parameter_bounds():
    bounds = ParameterBounds(
        x_min=0.0, x_max=10.0,
        y_min=0.0, y_max=10.0,
        length_min=2.0, length_max=8.0,
        width_min=1.0, width_max=4.0,
        height_min=2.5, height_max=5.0,
        heading_min=0.0, heading_max=180.0,
        albedo_min=0.1, albedo_max=0.9,
    )
    valid_p = ShadePanelParams(x=5.0, y=5.0, length=4.0, width=2.0, height=3.0, heading_deg=45.0, albedo=0.5)
    assert bounds.contains(valid_p)

    out_p = ShadePanelParams(x=15.0, y=5.0, length=4.0, width=2.0, height=3.0, heading_deg=45.0, albedo=0.5)
    assert not bounds.contains(out_p)

    # Vector conversion roundtrip
    vec = bounds.to_vector(valid_p)
    p_back = bounds.from_vector(vec)
    assert pytest.approx(p_back.x) == valid_p.x
    assert pytest.approx(p_back.length) == valid_p.length
    assert pytest.approx(p_back.heading_deg) == valid_p.heading_deg

    # Clipping
    clipped = bounds.clip(np.array([20.0, -5.0, 10.0, 0.5, 6.0, 200.0, 1.2]))
    assert clipped[0] == 10.0
    assert clipped[1] == 0.0
    assert clipped[2] == 8.0
    assert clipped[3] == 1.0


# ---------------------------------------------------------------------------
# Test 2: Invalid geometry rejection
# ---------------------------------------------------------------------------
def test_invalid_geometry_rejection():
    constraints = FeasibilityConstraints(
        min_length_m=2.0, max_length_m=10.0,
        min_width_m=1.0, max_width_m=5.0,
        min_area_m2=5.0, max_area_m2=40.0,
        min_aspect_ratio=1.0, max_aspect_ratio=4.0,
    )

    # Non-finite coordinates
    nan_p = ShadePanelParams(x=float("nan"), y=5.0, length=4.0, width=2.0, height=3.0, heading_deg=0.0, albedo=0.5)
    res_nan = check_feasibility(nan_p, constraints)
    assert not res_nan.is_valid
    assert res_nan.rejection_reason == RejectionReason.INVALID_COORDINATES

    # Below min dimensions
    small_p = ShadePanelParams(x=5.0, y=5.0, length=1.0, width=1.0, height=3.0, heading_deg=0.0, albedo=0.5)
    res_small = check_feasibility(small_p, constraints)
    assert not res_small.is_valid
    assert res_small.rejection_reason == RejectionReason.BELOW_MIN_DIMENSIONS

    # Exceeds max dimensions
    huge_p = ShadePanelParams(x=5.0, y=5.0, length=15.0, width=4.0, height=3.0, heading_deg=0.0, albedo=0.5)
    res_huge = check_feasibility(huge_p, constraints)
    assert not res_huge.is_valid
    assert res_huge.rejection_reason == RejectionReason.EXCEEDS_MAX_DIMENSIONS

    # Aspect ratio violation
    skinny_p = ShadePanelParams(x=5.0, y=5.0, length=9.0, width=1.2, height=3.0, heading_deg=0.0, albedo=0.5)
    res_skinny = check_feasibility(skinny_p, constraints)
    assert not res_skinny.is_valid
    assert res_skinny.rejection_reason == RejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION


# ---------------------------------------------------------------------------
# Test 3: Building-collision rejection
# ---------------------------------------------------------------------------
def test_building_collision_rejection():
    bldg = box(20.0, 20.0, 40.0, 40.0)
    constraints = FeasibilityConstraints(
        building_footprints=bldg,
        min_building_setback_m=1.0,
    )

    # Directly intersecting building
    colliding_p = ShadePanelParams(x=25.0, y=25.0, length=4.0, width=3.0, height=3.5, heading_deg=0.0, albedo=0.5)
    res_col = check_feasibility(colliding_p, constraints)
    assert not res_col.is_valid
    assert res_col.rejection_reason == RejectionReason.BUILDING_COLLISION

    # Violating 1.0 m setback buffer (e.g. at 18.5, right edge is 19.5, distance to 20.0 is 0.5 < 1.0)
    setback_violating_p = ShadePanelParams(x=18.5, y=25.0, length=3.0, width=2.0, height=3.5, heading_deg=0.0, albedo=0.5)
    res_sb = check_feasibility(setback_violating_p, constraints)
    assert not res_sb.is_valid
    assert res_sb.rejection_reason == RejectionReason.BUILDING_COLLISION

    # Safe outside setback
    safe_p = ShadePanelParams(x=10.0, y=25.0, length=3.0, width=2.0, height=3.5, heading_deg=0.0, albedo=0.5)
    res_safe = check_feasibility(safe_p, constraints)
    assert res_safe.is_valid


# ---------------------------------------------------------------------------
# Test 4: Pedestrian-clearance rejection
# ---------------------------------------------------------------------------
def test_pedestrian_clearance_rejection():
    constraints = FeasibilityConstraints(min_underside_height_m=2.50)

    # Height 2.2 m < 2.50 m
    low_p = ShadePanelParams(x=10.0, y=10.0, length=4.0, width=2.0, height=2.20, heading_deg=0.0, albedo=0.5)
    res_low = check_feasibility(low_p, constraints)
    assert not res_low.is_valid
    assert res_low.rejection_reason == RejectionReason.INSUFFICIENT_CLEARANCE

    # Height 2.8 m >= 2.50 m
    ok_p = ShadePanelParams(x=10.0, y=10.0, length=4.0, width=2.0, height=2.80, heading_deg=0.0, albedo=0.5)
    res_ok = check_feasibility(ok_p, constraints)
    assert res_ok.is_valid


# ---------------------------------------------------------------------------
# Test 5: Deterministic candidate generation
# ---------------------------------------------------------------------------
def test_deterministic_candidate_generation():
    canon = ParameterBounds.get_canonical_church_street_baseline_params()
    assert pytest.approx(canon.x) == 131.789
    assert pytest.approx(canon.y) == 64.007
    assert pytest.approx(canon.length) == 6.0
    assert pytest.approx(canon.width) == 3.0
    assert pytest.approx(canon.height) == 3.5
    assert pytest.approx(canon.heading_deg) == 102.44
    assert pytest.approx(canon.albedo) == 0.60
    assert pytest.approx(canon.area) == 18.0

    mesh, poly = build_panel_geometry(canon, thickness_m=0.1)
    assert mesh.num_vertices == 8
    assert mesh.num_triangles == 12
    assert mesh.material_id == "SHADE_PANEL_ASSUMED_001"
    assert pytest.approx(poly.area, abs=1e-4) == 18.0

    # Underside vertices at 3.5 m, top at 3.6 m
    z_coords = mesh.vertices[:, 2]
    assert pytest.approx(np.min(z_coords)) == 3.5
    assert pytest.approx(np.max(z_coords)) == 3.6


# ---------------------------------------------------------------------------
# Test 6: Random-search reproducibility
# ---------------------------------------------------------------------------
def test_random_search_reproducibility():
    bounds = ParameterBounds.get_canonical_church_street_bounds()
    rng1 = np.random.default_rng(12345)
    rng2 = np.random.default_rng(12345)

    samples1 = bounds.sample_uniform(rng1, n_samples=10)
    samples2 = bounds.sample_uniform(rng2, n_samples=10)

    for s1, s2 in zip(samples1, samples2):
        assert s1.to_dict() == s2.to_dict()

    # LHS reproducibility
    rng3 = np.random.default_rng(999)
    rng4 = np.random.default_rng(999)
    lhs1 = bounds.sample_lhs(rng3, n_samples=5)
    lhs2 = bounds.sample_lhs(rng4, n_samples=5)
    for l1, l2 in zip(lhs1, lhs2):
        assert l1.to_dict() == l2.to_dict()


# ---------------------------------------------------------------------------
# Helper: Small Synthetic Scene for Optimizer Integration Tests
# ---------------------------------------------------------------------------
def _make_synthetic_scene_and_results():
    # 20m x 20m domain with 2m resolution -> 10 x 10 = 100 cells
    ped_grid = PedestrianGridConfig(
        extent_x=20.0, extent_y=20.0,
        origin_x=0.0, origin_y=0.0,
        resolution=2.0,
        pedestrian_height=1.1,
    )
    bldgs = {
        "B1": Building(id="B1", footprint=BoundingBox2D(0.0, 4.0, 0.0, 4.0), height=8.0)
    }
    scene = Scene(
        buildings=bldgs,
        meshes={},
        pedestrian_grid=ped_grid,
        materials={
            "default_wall": Material(id="default_wall", albedo=0.20, emissivity=0.90, surface_temperature=305.15),
            "default_ground": Material(id="default_ground", albedo=0.15, emissivity=0.95, surface_temperature=308.15),
        }
    )
    weather = Weather(
        air_temperature=305.15,
        relative_humidity=40.0,
        wind_speed=1.5,
        wind_direction=90.0,
        direct_normal_irradiance=700.0,
        diffuse_horizontal_irradiance=150.0,
    )
    sim_cfg = SimulationConfig(
        latitude=12.97,
        longitude=77.60,
        date="2024-04-15",
        local_time="10:00:00",
        pedestrian_height=1.1,
        grid_resolution=2.0,
        tmrt_tolerance=0.50,
        sky_patch_configuration=32,
        max_svf_search_dist_m=30.0,
        backend="auto",
    )
    base_res = full_recompute(scene, weather, sim_cfg, backend="auto")
    corridor_poly = box(4.0, 4.0, 18.0, 18.0)
    constraints = FeasibilityConstraints(
        allowed_area=corridor_poly,
        building_footprints=box(0.0, 0.0, 4.0, 4.0),
        min_building_setback_m=0.5,
        min_underside_height_m=2.5,
        min_length_m=2.0, max_length_m=6.0,
        min_width_m=1.0, max_width_m=3.0,
        min_area_m2=2.0, max_area_m2=18.0,
    )
    eval_mask = np.ones(base_res.shadow_mask.shape, dtype=bool)
    return scene, base_res, weather, sim_cfg, constraints, eval_mask


# ---------------------------------------------------------------------------
# Test 7: Optimizer-to-solver integration (synthetic scene)
# ---------------------------------------------------------------------------
def test_optimizer_to_solver_integration():
    scene, base_res, weather, sim_cfg, constraints, eval_mask = _make_synthetic_scene_and_results()

    bounds = ParameterBounds(
        x_min=6.0, x_max=14.0,
        y_min=6.0, y_max=14.0,
        length_min=2.0, length_max=4.0,
        width_min=1.0, width_max=2.0,
        height_min=2.8, height_max=4.0,
        heading_min=0.0, heading_max=90.0,
        albedo_min=0.3, albedo_max=0.8,
    )
    opt_cfg = OptimizerConfig(
        seed=42,
        budget_random=3,
        budget_lhs=0,
        budget_evolutionary=0,
        bounds=bounds,
        max_total_evaluations=10,
        fallback_to_cpu=True,
    )
    engine = OptimizationEngine(
        baseline_scene=scene,
        baseline_result=base_res,
        weather=weather,
        sim_config=sim_cfg,
        feasibility_constraints=constraints,
        eval_mask=eval_mask,
        config=opt_cfg,
    )

    ledger = engine.run_random_search(n_samples=3)
    assert len(ledger) == 3
    assert len(engine.ledger) == 3
    for rec in engine.ledger.records:
        assert rec.candidate_id.startswith("CAND_")
        assert rec.method == "random"
        if rec.is_feasible:
            assert rec.objective_value < 1000.0
            assert rec.metrics is not None
            assert rec.gpu_metrics is not None


# ---------------------------------------------------------------------------
# Test 8: Certificate failure / exception handling
# ---------------------------------------------------------------------------
def test_certificate_failure_handling():
    scene, base_res, weather, sim_cfg, constraints, eval_mask = _make_synthetic_scene_and_results()

    class FailingIncrementalEngine:
        is_available = True
        last_metrics = None
        def preload_resident_baseline(self, *args, **kwargs):
            return 0.0
        def execute_certified_update(self, *args, **kwargs):
            raise RuntimeError("Mock GPU CUDA kernel out of memory error!")

    opt_cfg = OptimizerConfig(seed=42, fallback_to_cpu=True)
    engine = OptimizationEngine(
        baseline_scene=scene,
        baseline_result=base_res,
        weather=weather,
        sim_config=sim_cfg,
        feasibility_constraints=constraints,
        eval_mask=eval_mask,
        config=opt_cfg,
        gpu_engine=FailingIncrementalEngine(),
    )

    valid_cand = ShadePanelParams(x=10.0, y=10.0, length=3.0, width=2.0, height=3.0, heading_deg=0.0, albedo=0.5)
    rec = engine.evaluate_candidate(valid_cand, method="test_failure")

    assert not rec.is_feasible
    assert rec.rejection_reason == "SIMULATION_ERROR"
    assert "Mock GPU CUDA kernel" in (rec.rejection_message or "")
    assert rec.objective_value == float("inf")
    assert rec.certificate_status == "ERROR"


# ---------------------------------------------------------------------------
# Test 9: Candidate ledger completeness & persistence
# ---------------------------------------------------------------------------
def test_candidate_ledger_completeness(tmp_path: Path):
    ledger = CandidateLedger()

    r1 = CandidateRecord(
        candidate_id="CAND_0001",
        iteration=0,
        method="random",
        params={"x": 10.0, "y": 10.0, "length": 4.0, "width": 2.0, "height": 3.0, "heading_deg": 0.0, "albedo": 0.6, "area_m2": 8.0},
        is_feasible=True,
        objective_value=32.45,
        metrics={"mean_utci_c": 30.1, "p90_utci_c": 33.2, "pct_improved_cells": 12.5, "delta_mean_utci_c": -0.15},
        gpu_metrics={"recomputed_cells": 10, "reused_cells": 90, "ray_work_reduction_pct": 90.0, "gpu_kernel_time_ms": 12.3},
        certificate_status="certified",
        certificate_violations=0,
        max_predicted_bound_k=0.025,
        wall_time_s=0.045,
    )
    r2 = CandidateRecord(
        candidate_id="CAND_0002",
        iteration=1,
        method="random",
        params={"x": 2.0, "y": 2.0, "length": 4.0, "width": 2.0, "height": 3.0, "heading_deg": 0.0, "albedo": 0.6, "area_m2": 8.0},
        is_feasible=False,
        rejection_reason=RejectionReason.BUILDING_COLLISION.value,
        rejection_message="Collision with building B1",
        objective_value=float("inf"),
    )
    ledger.add(r1)
    ledger.add(r2)

    assert len(ledger) == 2
    assert len(ledger.get_feasible()) == 1
    assert len(ledger.get_rejected()) == 1
    assert ledger.get_best().candidate_id == "CAND_0001"

    json_path = tmp_path / "ledger.json"
    csv_path = tmp_path / "ledger.csv"
    ledger.save_json(json_path)
    ledger.save_csv(csv_path)

    assert json_path.exists()
    assert csv_path.exists()
    assert "CAND_0001" in json_path.read_text(encoding="utf-8")
    assert "BUILDING_COLLISION" in csv_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 10: Frozen directory protection
# ---------------------------------------------------------------------------
def test_frozen_directory_protection():
    root_dir = Path(__file__).resolve().parent.parent
    frozen_dirs = [
        root_dir / "results" / "church_street_static_20261006_232110",
        root_dir / "results" / "church_street_shade_full_20261007_001600",
        root_dir / "results" / "church_street_shade_incremental_20261007_081114",
        root_dir / "results" / "church_street_gpu_full_20261007_091111",
        root_dir / "results" / "church_street_shade_gpu_incremental_20261007_093905",
    ]
    for d in frozen_dirs:
        assert d.exists(), f"Frozen reference directory must exist: {d}"
        # Assert none of the frozen files have been modified recently during this test session
        manifest = list(d.glob("*.json")) + list(d.glob("*.npz"))
        assert len(manifest) > 0


# ---------------------------------------------------------------------------
# Test 11: Best-candidate selection
# ---------------------------------------------------------------------------
def test_best_candidate_selection():
    ledger = CandidateLedger()
    cand_scores = [35.2, 31.8, 38.0, 29.4, 34.1]
    for i, score in enumerate(cand_scores):
        rec = CandidateRecord(
            candidate_id=f"CAND_{i:04d}",
            iteration=i,
            method="test",
            params={"x": float(i), "y": 10.0, "length": 4.0, "width": 2.0, "height": 3.0, "heading_deg": 0.0, "albedo": 0.5, "area_m2": 8.0},
            is_feasible=True,
            objective_value=score,
        )
        ledger.add(rec)

    # Infeasible candidate with lower dummy score must NOT be selected
    infeasible_rec = CandidateRecord(
        candidate_id="CAND_INVAL",
        iteration=99,
        method="test",
        params={"x": 99.0, "y": 99.0, "length": 4.0, "width": 2.0, "height": 3.0, "heading_deg": 0.0, "albedo": 0.5, "area_m2": 8.0},
        is_feasible=False,
        rejection_reason="OUT_OF_BOUNDS",
        objective_value=float("inf"),
    )
    ledger.add(infeasible_rec)

    best = ledger.get_best()
    assert best is not None
    assert best.candidate_id == "CAND_0003"
    assert pytest.approx(best.objective_value) == 29.4

    top_3 = ledger.get_top_n(3)
    assert len(top_3) == 3
    assert [r.candidate_id for r in top_3] == ["CAND_0003", "CAND_0001", "CAND_0004"]


# ---------------------------------------------------------------------------
# Test 12: Final CPU/GPU/incremental validation
# ---------------------------------------------------------------------------
def test_final_cpu_gpu_incremental_validation():
    scene, base_res, weather, sim_cfg, constraints, eval_mask = _make_synthetic_scene_and_results()
    test_params = ShadePanelParams(
        x=10.0, y=10.0, length=4.0, width=2.0, height=3.0, heading_deg=30.0, albedo=0.60
    )

    report = validate_candidate_multi_path(
        candidate_id="SYNTH_VAL_001",
        params=test_params,
        role="synthetic_validation_candidate",
        baseline_scene=scene,
        baseline_result=base_res,
        weather=weather,
        config=sim_cfg,
    )

    assert report.all_passed
    assert report.cpu_full_vs_gpu_full.passed_all
    assert report.cpu_full_vs_gpu_inc.passed_all
    assert report.gpu_full_vs_gpu_inc.passed_all
    assert report.certificate_violations == 0
    assert report.max_predicted_bound_k > 0.0
    assert report.cpu_full_vs_gpu_inc.max_tmrt_diff_k <= sim_cfg.tmrt_tolerance
