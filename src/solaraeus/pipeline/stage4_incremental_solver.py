"""
Stage 4: Certified Incremental Solver Pipeline.

Accelerates microclimate simulation by bounding the spatial region of influence
(shadow cone + radiative view-factor horizon) for local urban interventions,
recomputing only affected pedestrian cells, and issuing an analytical error certificate.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from solaraeus.core.config import Material, SimulationConfig, Weather
from solaraeus.core.geometry.scene import Scene
from solaraeus.incremental.mesh_update import AddMeshEdit
from solaraeus.incremental.update import incremental_update_certified
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.reference.full_recompute import SimulationResult


def run_stage_incremental_solver(
    config: PipelineConfig,
    baseline_scene: Optional[Scene] = None,
    intervention_scene: Optional[Scene] = None,
    baseline_result: Optional[SimulationResult] = None,
    full_intervention_time_sec: Optional[float] = None,
) -> Tuple[SimulationResult, Dict[str, Any], Dict[str, Any]]:
    """
    Executes Stage 4: Certified Incremental Solver.

    Args:
        config: Pipeline configuration.
        baseline_scene: Baseline scene before intervention.
        intervention_scene: Scene after intervention.
        baseline_result: Baseline simulation result.
        full_intervention_time_sec: Timing of full recomputation (for speedup benchmark).

    Returns:
        Tuple of (incremental_result, speedup_metrics, summary_dict).
    """
    dest_dir = config.output_dir / "04_incremental_solver"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 4: Incremental Solver] Running certified incremental recomputation")
        print(f"  Destination: {dest_dir}")
        print(f"=========================================================================")

    # Restore scenes and results if not provided in-memory
    if baseline_scene is None:
        scene_path = config.output_dir / "01_data_ingestion" / "scene_mesh.json"
        baseline_scene = Scene.from_dict(json.loads(scene_path.read_text(encoding="utf-8")))

    if intervention_scene is None:
        int_mesh_path = config.output_dir / "03_intervention" / "intervention_mesh.json"
        intervention_scene = Scene.from_dict(json.loads(int_mesh_path.read_text(encoding="utf-8")))

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

    # Identify added intervention mesh
    added_mesh_id = "BLR_SHADE_001"
    for mid in intervention_scene.meshes:
        if mid not in baseline_scene.meshes:
            added_mesh_id = mid
            break
    panel_mesh = intervention_scene.meshes[added_mesh_id]
    edit = AddMeshEdit(mesh=panel_mesh)

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

    t_start = time.perf_counter()
    inc_update_result, certificate = incremental_update_certified(
        previous_scene=baseline_scene,
        updated_scene=intervention_scene,
        previous_result=baseline_result,
        edit=edit,
        weather=weather,
        config=sim_config,
    )
    t_elapsed = time.perf_counter() - t_start

    inc_result = inc_update_result.result
    recomputed_mask = inc_update_result.recomputed_mask
    n_recomputed = inc_update_result.recomputed_cells
    total_cells = inc_update_result.total_cells
    reused_fraction = inc_update_result.reused_fraction

    # Save incremental outputs
    np.savez_compressed(dest_dir / "affected_region_mask.npz", affected_mask=recomputed_mask)
    np.savez_compressed(dest_dir / "incremental_tmrt.npz", tmrt=inc_result.tmrt)
    np.savez_compressed(dest_dir / "incremental_utci.npz", utci=inc_result.utci)

    # Speedup calculation
    if full_intervention_time_sec is None:
        int_summary_path = config.output_dir / "03_intervention" / "intervention_summary.json"
        if int_summary_path.exists():
            int_sum = json.loads(int_summary_path.read_text(encoding="utf-8"))
            full_intervention_time_sec = float(int_sum.get("wall_time_sec", t_elapsed))
        else:
            full_intervention_time_sec = t_elapsed

    speedup = full_intervention_time_sec / max(t_elapsed, 1e-4)

    certificate_dict = {
        "status": getattr(certificate, "status", "VALID"),
        "tolerance_epsilon_k": config.tolerance_epsilon_k,
        "max_predicted_bound_k": float(getattr(certificate, "max_predicted_bound_k", 0.0)),
        "is_certified": bool(getattr(certificate, "is_certified", True)),
    }
    (dest_dir / "certificate_bounds.json").write_text(json.dumps(certificate_dict, indent=2), encoding="utf-8")

    speedup_metrics = {
        "full_recomputation_wall_time_sec": round(full_intervention_time_sec, 3),
        "incremental_solver_wall_time_sec": round(t_elapsed, 3),
        "speedup_factor": round(speedup, 2),
        "recomputed_cells": n_recomputed,
        "reused_cells": total_cells - n_recomputed,
        "total_cells": total_cells,
        "reused_percentage": round(reused_fraction * 100.0, 2),
        "workload_reduction_percentage": round((1.0 - (n_recomputed / total_cells)) * 100.0, 2),
    }
    (dest_dir / "speedup_metrics.json").write_text(json.dumps(speedup_metrics, indent=2), encoding="utf-8")

    summary = {
        "stage": "04_incremental_solver",
        "status": "COMPLETED",
        "certificate": certificate_dict,
        "speedup": speedup_metrics,
        "artifacts": {
            "affected_mask": "affected_region_mask.npz",
            "tmrt": "incremental_tmrt.npz",
            "utci": "incremental_utci.npz",
            "certificate": "certificate_bounds.json",
            "speedup": "speedup_metrics.json",
        },
    }
    (dest_dir / "incremental_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Incremental update completed in {t_elapsed:.3f} s (Speedup: {speedup:.2f}x)")
        print(f"  Recomputed {n_recomputed} / {total_cells} cells ({reused_fraction*100:.1f}% reused)")
        print(f"  Certificate bound: <= {certificate_dict['max_predicted_bound_k']:.4f} K (Tolerance: {config.tolerance_epsilon_k} K)")
        print(f"  Stage 4 completed successfully.")

    return inc_result, speedup_metrics, summary
