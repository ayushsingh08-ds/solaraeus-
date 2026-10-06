"""
Mesh Certificate Audit Module for SOLARAEUS.

Executes an independent audit of the certified incremental recomputation framework
across controlled triangular-mesh scenarios, verifying pointwise error bounding,
mathematical soundness, user tolerance compliance, and recomputation efficiency.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.mesh import (
    TriangleMesh,
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_overhang_mesh,
    create_l_shaped_mesh
)
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.mesh_update import (
    AddMeshEdit, RemoveMeshEdit, ReplaceMeshEdit, MoveMeshEdit, ChangeMeshHeightEdit
)
from urban_comfort.incremental.update import incremental_update_certified
from urban_comfort.benchmark.independent_audit import audit_certificate_independently


@dataclass
class MeshAuditScenario:
    scenario_id: str
    typology: str
    description: str
    setup_fn: Any  # Callable returning (scene_base, edit)


def _scenario_01_rotated_box() -> Tuple[Scene, AddMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    mesh = create_rotated_box_mesh("rot_box", center_x=45.0, center_y=50.0,
                                   width_x=16.0, width_y=16.0, height=18.0, angle_deg=45.0)
    edit = AddMeshEdit(mesh)
    return scene, edit, grid_cfg


def _scenario_02_pitched_roof() -> Tuple[Scene, AddMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    # 1 existing box building
    b1 = create_box_mesh("b1", 20.0, 35.0, 20.0, 35.0, 0.0, 14.0)
    scene.add_mesh(b1)
    # Add pitched roof building
    mesh = create_pitched_roof_mesh("pitched_bldg", xmin=60.0, xmax=80.0, ymin=40.0, ymax=60.0,
                                    eave_height=10.0, ridge_height=20.0, ridge_orientation="x")
    edit = AddMeshEdit(mesh)
    return scene, edit, grid_cfg


def _scenario_03_overhang_canopy() -> Tuple[Scene, AddMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    mesh = create_overhang_mesh("oh_canopy", xmin=35.0, xmax=55.0, ymin=30.0, ymax=45.0,
                                base_height=16.0, overhang_depth=12.0, overhang_direction="north")
    edit = AddMeshEdit(mesh)
    return scene, edit, grid_cfg


def _scenario_04_flat_to_pitched_replacement() -> Tuple[Scene, ReplaceMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    flat_mesh = create_box_mesh("b_replace", 40.0, 60.0, 40.0, 60.0, 0.0, 12.0)
    scene.add_mesh(flat_mesh)
    pitched_mesh = create_pitched_roof_mesh("b_replace", 40.0, 60.0, 40.0, 60.0,
                                            eave_height=12.0, ridge_height=22.0, ridge_orientation="y")
    edit = ReplaceMeshEdit("b_replace", pitched_mesh)
    return scene, edit, grid_cfg


def _scenario_05_rotated_prism_translation() -> Tuple[Scene, MoveMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    rot_mesh = create_rotated_box_mesh("rot_move", center_x=30.0, center_y=30.0,
                                       width_x=12.0, width_y=12.0, height=14.0, angle_deg=30.0)
    scene.add_mesh(rot_mesh)
    edit = MoveMeshEdit("rot_move", shift_x=20.0, shift_y=15.0)
    return scene, edit, grid_cfg


def _scenario_06_pitched_roof_height_scaling() -> Tuple[Scene, ChangeMeshHeightEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    mesh = create_pitched_roof_mesh("pitch_scale", xmin=40.0, xmax=60.0, ymin=40.0, ymax=60.0,
                                    eave_height=8.0, ridge_height=15.0, ridge_orientation="x")
    scene.add_mesh(mesh)
    edit = ChangeMeshHeightEdit("pitch_scale", new_height=25.0)
    return scene, edit, grid_cfg


def _scenario_07_l_shaped_mesh() -> Tuple[Scene, AddMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    l_mesh = create_l_shaped_mesh("l_mesh", xmin=30.0, ymin=30.0,
                                  total_width=30.0, total_length=30.0,
                                  wing_width=15.0, wing_length=15.0,
                                  height=18.0)
    edit = AddMeshEdit(l_mesh)
    return scene, edit, grid_cfg


def _scenario_08_mesh_removal() -> Tuple[Scene, RemoveMeshEdit, PedestrianGridConfig]:
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    m1 = create_box_mesh("m1", 20.0, 35.0, 20.0, 35.0, 0.0, 15.0)
    m2 = create_pitched_roof_mesh("m_remove", 60.0, 75.0, 60.0, 75.0, eave_height=10.0, ridge_height=18.0)
    scene.add_mesh(m1)
    scene.add_mesh(m2)
    edit = RemoveMeshEdit("m_remove")
    return scene, edit, grid_cfg


SCENARIO_DEFINITIONS = [
    MeshAuditScenario("SCEN_01", "Rotated Box", "Add 45-deg rotated diamond box mesh", _scenario_01_rotated_box),
    MeshAuditScenario("SCEN_02", "Pitched Roof", "Add dual-pitch gable roof building", _scenario_02_pitched_roof),
    MeshAuditScenario("SCEN_03", "Overhang", "Add building with 12m cantilever canopy", _scenario_03_overhang_canopy),
    MeshAuditScenario("SCEN_04", "Replacement", "Replace flat roof with taller pitched roof", _scenario_04_flat_to_pitched_replacement),
    MeshAuditScenario("SCEN_05", "Translation", "Translate rotated prism across domain", _scenario_05_rotated_prism_translation),
    MeshAuditScenario("SCEN_06", "Height Scaling", "Scale pitched roof ridge from 15m to 25m", _scenario_06_pitched_roof_height_scaling),
    MeshAuditScenario("SCEN_07", "L-Shaped", "Add re-entrant corner L-shaped building mesh", _scenario_07_l_shaped_mesh),
    MeshAuditScenario("SCEN_08", "Removal", "Remove pitched roof building from multi-building scene", _scenario_08_mesh_removal),
]


def run_mesh_certificate_audit(output_dir: Optional[str] = None,
                               tolerances: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Runs the full mesh certificate audit suite across all scenarios and tolerances.
    
    Generates:
        <output_dir>/mesh_dependency_audit.csv
        <output_dir>/mesh_audit_summary.json
    """
    if tolerances is None:
        tolerances = [1.0, 2.0]

    utc_now = datetime.now(timezone.utc)
    timestamp_str = utc_now.strftime("%Y%m%d_%H%M%S")

    if output_dir is None:
        output_dir = os.path.join("results", f"mesh_validation_{timestamp_str}")

    os.makedirs(output_dir, exist_ok=True)

    weather = Weather(
        air_temperature=300.15,
        relative_humidity=50.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=750.0,
        diffuse_horizontal_irradiance=150.0
    )

    audit_rows: List[Dict[str, Any]] = []
    total_runs = 0
    total_violations = 0

    for sc_def in SCENARIO_DEFINITIONS:
        for tol in tolerances:
            scene_base, edit, grid_cfg = sc_def.setup_fn()
            config = SimulationConfig(
                latitude=40.7128, longitude=-74.0060,
                date="2026-06-21", local_time="12:00:00",
                tmrt_tolerance=tol,
                sky_patch_configuration=16,
                max_svf_search_dist_m=30.0
            )

            # 1. Baseline Full Recompute
            res_base = full_recompute(scene_base, weather, config)

            # 2. Ground-Truth Full Recompute
            scene_after, _ = edit.apply(scene_base)
            t0_full = time.perf_counter()
            res_full = full_recompute(scene_after, weather, config)
            t_full = time.perf_counter() - t0_full

            # 3. Certified Incremental Update
            t0_inc = time.perf_counter()
            inc_res, cert = incremental_update_certified(scene_base, scene_after, res_base, edit, weather, config)
            t_inc = time.perf_counter() - t0_inc

            # 4. Decoupled Independent Audit
            audit_metrics = audit_certificate_independently(
                full_tmrt=res_full.tmrt,
                incremental_tmrt=inc_res.result.tmrt,
                predicted_bound=cert.predicted_error_bound,
                reused_mask=inc_res.reused_mask,
                tolerance=tol
            )

            is_sound = audit_metrics["is_sound"]
            num_violations = audit_metrics["num_certificate_violations"]
            total_violations += num_violations
            total_runs += 1

            speedup = t_full / max(1e-6, inc_res.time_selective_recompute_sec)

            row = {
                "scenario_id": sc_def.scenario_id,
                "typology": sc_def.typology,
                "description": sc_def.description,
                "edit_type": edit.edit_type,
                "tolerance_k": tol,
                "total_cells": audit_metrics["total_cells"],
                "recomputed_cells": audit_metrics["recomputed_cells"],
                "reused_cells": audit_metrics["certified_reused_cells"],
                "reused_fraction": round(audit_metrics["reused_fraction"], 4),
                "max_predicted_bound_k": round(audit_metrics["max_predicted_bound"], 4),
                "max_actual_error_k": round(audit_metrics["max_actual_error"], 4),
                "reused_max_actual_error_k": round(audit_metrics["reused_max_actual_error"], 4),
                "min_slack_k": round(audit_metrics["min_slack"], 6),
                "num_violations": num_violations,
                "is_sound": is_sound,
                "is_within_tolerance": audit_metrics["is_within_tolerance"],
                "time_incremental_s": round(t_inc, 4),
                "time_selective_recomp_s": round(inc_res.time_selective_recompute_sec, 4),
                "time_full_s": round(t_full, 4),
                "speedup_ratio": round(speedup, 2)
            }
            audit_rows.append(row)

    # Write CSV
    csv_path = os.path.join(output_dir, "mesh_dependency_audit.csv")
    fieldnames = list(audit_rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)

    # Write JSON Summary
    summary = {
        "timestamp_utc": utc_now.isoformat(),
        "total_scenarios": len(SCENARIO_DEFINITIONS),
        "total_runs": total_runs,
        "total_violations": total_violations,
        "all_sound": (total_violations == 0),
        "output_directory": output_dir,
        "csv_path": csv_path,
        "mean_reused_fraction": float(np.mean([r["reused_fraction"] for r in audit_rows])),
        "max_reused_fraction": float(np.max([r["reused_fraction"] for r in audit_rows])),
        "mean_speedup_ratio": float(np.mean([r["speedup_ratio"] for r in audit_rows])),
    }
    json_path = os.path.join(output_dir, "mesh_audit_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary
