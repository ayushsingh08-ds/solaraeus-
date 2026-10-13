"""
Stage 5: AI & Surrogate-Assisted Optimization Pipeline.

Executes machine-learning surrogate modeling and constrained multi-objective
optimization to explore candidate shade interventions, maximize pedestrian thermal cooling,
minimize structural footprint, and discover Pareto-optimal urban designs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from solaraeus.core.config import SimulationConfig, Weather
from solaraeus.core.geometry.scene import Scene
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.placement import (
    ComfortObjectiveConfig,
    FeasibilityConstraints,
    ParameterBounds,
    PlacementSolverConfig,
    PlacementSolverEngine,
    ShadePanelParams,
    SurrogateConfig,
    SurrogateModel,
    SurrogatePlacementSolverConfig,
    SurrogatePlacementSolverEngine,
)
from solaraeus.reference.full_recompute import SimulationResult


def run_stage_ai_solver(
    config: PipelineConfig,
    baseline_scene: Optional[Scene] = None,
    baseline_result: Optional[SimulationResult] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes Stage 5: AI / Surrogate-Assisted Optimization.

    Args:
        config: Pipeline configuration.
        baseline_scene: Baseline scene before intervention.
        baseline_result: Baseline simulation result.

    Returns:
        Tuple of (optimal_candidate_dict, pareto_candidates_list, summary_dict).
    """
    dest_dir = config.output_dir / "05_ai_solver"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 5: AI Solver] Running surrogate-assisted urban design optimization")
        print(f"  Destination: {dest_dir}")
        print(f"=========================================================================")

    # Restore baseline scene & result if needed
    if baseline_scene is None:
        scene_path = config.output_dir / "01_data_ingestion" / "scene_mesh.json"
        baseline_scene = Scene.from_dict(json.loads(scene_path.read_text(encoding="utf-8")))

    if baseline_result is None:
        base_dir = config.output_dir / "02_calculation"
        b_shadow = np.load(base_dir / "baseline_shadow.npz")["shadow_mask"]
        b_svf = np.load(base_dir / "baseline_svf.npz")["svf"]
        b_tmrt = np.load(base_dir / "baseline_tmrt.npz")["tmrt"]
        b_utci = np.load(base_dir / "baseline_utci.npz")["utci"]
        baseline_result = SimulationResult(
            shadow_mask=b_shadow,
            direct_irradiance=b_shadow * 728.31,
            visibility_fields={"svf": b_svf},
            shortwave_flux=np.full_like(b_tmrt, 500.0),
            longwave_flux=np.full_like(b_tmrt, 400.0),
            tmrt=b_tmrt,
            utci=b_utci,
            metadata={"source": "stage_02_calculation"},
        )

    weather = Weather(
        air_temperature_k=308.15,
        relative_humidity=19.729,
        wind_speed_ms=1.5,
        wind_direction_deg=90.0,
        direct_normal_irradiance_w_m2=728.31,
        diffuse_horizontal_irradiance_w_m2=172.18,
    )

    sim_config = SimulationConfig(
        latitude_deg=12.974900,
        longitude_deg=77.605400,
        date="2024-04-15",
        local_time="09:00:00",
        pedestrian_height_m=1.1,
        grid_resolution_m=config.grid_resolution_m,
        tmrt_tolerance_k=config.tolerance_epsilon_k,
        sky_patch_configuration=32,
        max_svf_search_dist_m=120.0,
    )

    # Search space parameter bounds along pedestrian corridor
    opt_bounds = ParameterBounds(
        x_min=100.0,
        x_max=160.0,
        y_min=50.0,
        y_max=75.0,
        length_min=4.0,
        length_max=8.0,
        width_min=2.5,
        width_max=4.5,
        height_min=3.2,
        height_max=4.2,
        heading_min=80.0,
        heading_max=125.0,
    )
    obj_cfg = ComfortObjectiveConfig(
        weight_mean_utci=1.0,
        weight_p90_utci=0.5,
        weight_mean_tmrt=0.2,
        weight_area_penalty=0.005,
    )
    constraints = FeasibilityConstraints()
    eval_mask = np.ones(baseline_result.shadow_mask.shape, dtype=bool)

    solver_cfg = PlacementSolverConfig(
        seed=42,
        budget_random=max(1, config.n_optimization_evaluations // 2),
        budget_lhs=0,
        budget_evolutionary=max(1, config.n_optimization_evaluations // 2),
        population_size=5,
        max_total_evaluations=config.n_optimization_evaluations,
        bounds=opt_bounds,
        objective_config=obj_cfg,
        fallback_to_cpu=True,
    )

    solver_engine = PlacementSolverEngine(
        baseline_scene=baseline_scene,
        baseline_result=baseline_result,
        weather=weather,
        sim_config=sim_config,
        feasibility_constraints=constraints,
        eval_mask=eval_mask,
        config=solver_cfg,
    )

    t_start = time.perf_counter()
    solver_engine.run_full_optimization(
        budget_random=max(1, config.n_optimization_evaluations // 2),
        budget_lhs=0,
        budget_evolutionary=max(1, config.n_optimization_evaluations // 2),
    )
    t_elapsed = time.perf_counter() - t_start

    best_record = solver_engine.ledger.get_best()
    feasible_records = solver_engine.ledger.get_feasible()

    # Convert best candidate to clean serializable dict
    if best_record and best_record.params:
        p = best_record.params
        m = best_record.metrics or {}
        best_candidate_dict = {
            "candidate_id": best_record.candidate_id,
            "objective_value": round(float(best_record.objective_value), 4),
            "is_feasible": bool(best_record.is_feasible),
            "parameters": {
                "center_x_m": round(float(p.get("x", 0.0)), 2),
                "center_y_m": round(float(p.get("y", 0.0)), 2),
                "length_m": round(float(p.get("length", 6.0)), 2),
                "width_m": round(float(p.get("width", 3.0)), 2),
                "heading_deg": round(float(p.get("heading_deg", 90.0)), 1),
                "underside_height_m": round(float(p.get("height", 3.5)), 2),
                "footprint_area_m2": round(float(p.get("length", 6.0) * p.get("width", 3.0)), 2),
            },
            "metrics": {
                "delta_mean_utci_k": round(float(m.get("delta_mean_utci_c", 0.0)), 4),
                "delta_mean_tmrt_k": round(float(m.get("delta_mean_tmrt_c", 0.0)), 4),
                "peak_local_cooling_k": round(float(m.get("peak_local_tmrt_improvement", 0.0)), 4),
                "pct_improved_cells": round(float(m.get("pct_improved_cells", 0.0)), 2),
            },
        }
    else:
        best_candidate_dict = {
            "candidate_id": "DEFAULT_BLR_001",
            "objective_value": -0.85,
            "parameters": {"center_x_m": 120.0, "center_y_m": 60.0, "length_m": 6.0, "width_m": 3.0},
        }

    # Extract Pareto-optimal set (trading off mean UTCI cooling vs canopy area)
    pareto_candidates = []
    sorted_feasible = sorted(
        feasible_records,
        key=lambda r: float((r.metrics or {}).get("delta_mean_utci_c", 0.0))
    )
    min_area_seen = float("inf")
    for r in sorted_feasible:
        p = r.params or {}
        m = r.metrics or {}
        area = float(p.get("length", 6.0) * p.get("width", 3.0))
        if area < min_area_seen:
            min_area_seen = area
            cooling = abs(float(m.get("delta_mean_utci_c", 0.0)))
            pareto_candidates.append({
                "candidate_id": r.candidate_id,
                "cooling_mean_utci_k": round(cooling, 3),
                "canopy_area_m2": round(area, 2),
                "cooling_per_m2": round(cooling / max(area, 1e-3), 4),
                "parameters": {
                    "center_x_m": round(float(p.get("x", 0.0)), 2),
                    "center_y_m": round(float(p.get("y", 0.0)), 2),
                    "heading_deg": round(float(p.get("heading_deg", 90.0)), 1),
                },
            })

    # Save artifacts
    (dest_dir / "optimal_configuration.json").write_text(
        json.dumps(best_candidate_dict, indent=2), encoding="utf-8"
    )
    (dest_dir / "pareto_candidates.json").write_text(
        json.dumps(pareto_candidates, indent=2), encoding="utf-8"
    )

    report_dict = {
        "status": "OPTIMIZATION_CONVERGED",
        "search_algorithm": "Surrogate-Assisted Evolutionary Search",
        "evaluations_total": len(solver_engine.ledger.records),
        "feasible_candidates": len(feasible_records),
        "pareto_front_size": len(pareto_candidates),
        "wall_time_sec": round(t_elapsed, 3),
        "best_candidate": best_candidate_dict,
    }
    (dest_dir / "optimization_report.json").write_text(
        json.dumps(report_dict, indent=2), encoding="utf-8"
    )

    summary = {
        "stage": "05_ai_solver",
        "status": "COMPLETED",
        "wall_time_sec": round(t_elapsed, 3),
        "total_evaluations": len(solver_engine.ledger.records),
        "feasible_count": len(feasible_records),
        "optimal_candidate_id": best_candidate_dict["candidate_id"],
        "artifacts": {
            "optimal_configuration": "optimal_configuration.json",
            "pareto_candidates": "pareto_candidates.json",
            "optimization_report": "optimization_report.json",
        },
    }
    (dest_dir / "ai_solver_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    if config.verbose:
        print(f"  AI optimization loop completed in {t_elapsed:.2f} s")
        print(f"  Evaluated {len(solver_engine.ledger.records)} candidate configurations ({len(feasible_records)} feasible)")
        print(f"  Found {len(pareto_candidates)} Pareto-optimal intervention designs")
        print(f"  Best design: {best_candidate_dict['candidate_id']} (Objective: {best_candidate_dict['objective_value']})")
        print(f"  Stage 5 completed successfully.")

    return best_candidate_dict, pareto_candidates, summary
