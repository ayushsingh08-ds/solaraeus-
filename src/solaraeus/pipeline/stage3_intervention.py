"""
Stage 3: Intervention Simulation Pipeline.

Introduces urban design interventions (such as canopy shade structures and tree plantings),
integrates their watertight 3D meshes into the urban canyon scene, executes forward microclimate
simulation, and evaluates pedestrian cooling deltas (ΔTmrt, ΔUTCI).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from solaraeus.core.config import Material, SimulationConfig, Weather
from solaraeus.core.geometry.mesh import TriangleMesh
from solaraeus.core.geometry.scene import Scene
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.reference.full_recompute import SimulationResult, full_recompute


def create_shade_panel_mesh(panel_def: Dict[str, Any]) -> TriangleMesh:
    """Builds watertight 3D box mesh for the shade canopy from definition dict."""
    edit_mag = panel_def.get("edit_magnitude", {})
    p_len = float(edit_mag.get("length_m", 6.0))
    p_wid = float(edit_mag.get("width_m", 3.0))
    p_thick = float(edit_mag.get("panel_thickness_m", 0.10))
    p_under = float(edit_mag.get("underside_height_above_ground_m", 3.5))
    p_top = float(edit_mag.get("top_height_above_ground_m", 3.6))

    local_poly = panel_def["modified_geometry_local"]["geometry"]["coordinates"][0]
    pts_2d = local_poly[:-1] if np.allclose(local_poly[0], local_poly[-1]) else local_poly
    pts_2d = np.array(pts_2d, dtype=np.float64)

    # Check 2D footprint area and winding
    signed_area = 0.5 * sum(
        pts_2d[i, 0] * pts_2d[(i + 1) % len(pts_2d), 1] - pts_2d[(i + 1) % len(pts_2d), 0] * pts_2d[i, 1]
        for i in range(len(pts_2d))
    )
    ccw_pts = pts_2d[::-1] if signed_area < 0 else pts_2d

    v_base = np.column_stack([ccw_pts, np.full(len(ccw_pts), p_under, dtype=np.float64)])
    v_top = np.column_stack([ccw_pts, np.full(len(ccw_pts), p_top, dtype=np.float64)])
    vertices_3d = np.vstack([v_base, v_top])

    triangles_list = []
    n = len(ccw_pts)
    for i in range(n):
        j = (i + 1) % n
        triangles_list.append((i, j, j + n))
        triangles_list.append((i, j + n, i + n))
    triangles_list.append((4, 5, 6))
    triangles_list.append((4, 6, 7))
    triangles_list.append((0, 2, 1))
    triangles_list.append((0, 3, 2))
    triangles_3d = np.array(triangles_list, dtype=np.int64)

    return TriangleMesh(
        id=panel_def.get("intervention_id", "BLR_SHADE_001"),
        vertices=vertices_3d,
        triangles=triangles_3d,
        material_id="SHADE_PANEL_ASSUMED_001",
        enabled=True,
        metadata={
            "length_m": p_len,
            "width_m": p_wid,
            "underside_m": p_under,
            "top_m": p_top,
        },
    )


def run_stage_intervention(
    config: PipelineConfig,
    baseline_scene: Optional[Scene] = None,
    baseline_result: Optional[SimulationResult] = None,
) -> Tuple[Scene, SimulationResult, Dict[str, Any], Dict[str, Any]]:
    """
    Executes Stage 3: Intervention Simulation.

    Args:
        config: Pipeline configuration.
        baseline_scene: Baseline scene from Stage 1/2.
        baseline_result: Baseline simulation result from Stage 2.

    Returns:
        Tuple of (intervention_scene, intervention_result, cooling_delta_dict, summary_dict).
    """
    dest_dir = config.output_dir / "03_intervention"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 3: Intervention] Simulating urban intervention scenario")
        print(f"  Destination: {dest_dir}")
        print(f"=========================================================================")

    # Load baseline scene if not passed
    if baseline_scene is None:
        scene_path = config.output_dir / "01_data_ingestion" / "scene_mesh.json"
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        baseline_scene = Scene.from_dict(scene_data)

    # Load baseline result if not passed
    if baseline_result is None:
        base_calc_dir = config.output_dir / "02_calculation"
        baseline_tmrt = np.load(base_calc_dir / "baseline_tmrt.npz")["tmrt"]
        baseline_utci = np.load(base_calc_dir / "baseline_utci.npz")["utci"]
    else:
        baseline_tmrt = baseline_result.tmrt
        baseline_utci = baseline_result.utci

    # Load intervention definition
    panel_path = config.data_dir / "intervention_definition.json"
    if not panel_path.exists():
        panel_path = config.data_dir / "data" / "processed" / "intervention_definition.json"
    if not panel_path.exists():
        raise FileNotFoundError(f"Intervention definition not found in: {config.data_dir}")

    panel_def = json.loads(panel_path.read_text(encoding="utf-8"))
    panel_mesh = create_shade_panel_mesh(panel_def)

    # Create intervention scene by cloning baseline scene and inserting intervention mesh
    intervention_scene = Scene(
        meshes={**baseline_scene.meshes, panel_mesh.id: panel_mesh},
        materials=baseline_scene.materials.copy(),
        ground=baseline_scene.ground,
        pedestrian_grid=baseline_scene.pedestrian_grid,
        metadata={"intervention_id": panel_def.get("intervention_id", "BLR_SHADE_001")},
    )
    mat_shade = Material(
        id="SHADE_PANEL_ASSUMED_001",
        albedo=0.40,
        emissivity=0.90,
        surface_temperature_k=313.15,
        is_opaque=True,
    )
    intervention_scene.materials["SHADE_PANEL_ASSUMED_001"] = mat_shade

    # Save intervention mesh
    dest_dir.joinpath("intervention_mesh.json").write_text(
        json.dumps(intervention_scene.to_dict(), indent=2), encoding="utf-8"
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
        tmrt_tolerance_k=0.5,
        sky_patch_configuration=32,
        max_svf_search_dist_m=120.0,
    )

    t_start = time.perf_counter()
    int_result: SimulationResult = full_recompute(intervention_scene, weather, sim_config)
    t_elapsed = time.perf_counter() - t_start

    # Save intervention arrays
    np.savez_compressed(dest_dir / "intervention_shadow.npz", shadow_mask=int_result.shadow_mask)
    np.savez_compressed(dest_dir / "intervention_tmrt.npz", tmrt=int_result.tmrt)
    np.savez_compressed(dest_dir / "intervention_utci.npz", utci=int_result.utci)

    # Compute cooling deltas (Negative indicates cooling)
    delta_tmrt = int_result.tmrt - baseline_tmrt
    delta_utci = int_result.utci - baseline_utci

    valid_delta_tmrt = delta_tmrt[~np.isnan(delta_tmrt)]
    valid_delta_utci = delta_utci[~np.isnan(delta_utci)]

    max_cooling_tmrt = float(np.nanmin(delta_tmrt))
    max_cooling_utci = float(np.nanmin(delta_utci))
    cells_cooled_tmrt_1k = int((delta_tmrt <= -1.0).sum())
    cells_cooled_utci_05k = int((delta_utci <= -0.5).sum())

    cooling_deltas = {
        "max_tmrt_cooling_k": abs(max_cooling_tmrt),
        "max_utci_cooling_k": abs(max_cooling_utci),
        "mean_delta_tmrt_k": float(np.mean(valid_delta_tmrt)) if len(valid_delta_tmrt) else 0.0,
        "mean_delta_utci_k": float(np.mean(valid_delta_utci)) if len(valid_delta_utci) else 0.0,
        "cells_cooled_tmrt_gt_1k": cells_cooled_tmrt_1k,
        "cells_cooled_utci_gt_05k": cells_cooled_utci_05k,
    }
    (dest_dir / "cooling_delta.json").write_text(json.dumps(cooling_deltas, indent=2), encoding="utf-8")

    summary = {
        "stage": "03_intervention",
        "status": "COMPLETED",
        "intervention_id": panel_def.get("intervention_id", "BLR_SHADE_001"),
        "wall_time_sec": round(t_elapsed, 3),
        "cooling_deltas": cooling_deltas,
        "artifacts": {
            "mesh": "intervention_mesh.json",
            "shadow": "intervention_shadow.npz",
            "tmrt": "intervention_tmrt.npz",
            "utci": "intervention_utci.npz",
            "cooling_delta": "cooling_delta.json",
        },
    }
    (dest_dir / "intervention_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Intervention simulation completed in {t_elapsed:.2f} s")
        print(f"  Max pedestrian cooling: Tmrt = -{cooling_deltas['max_tmrt_cooling_k']:.2f} K, UTCI = -{cooling_deltas['max_utci_cooling_k']:.2f} K")
        print(f"  Pedestrian cells with >= 1.0 K cooling: {cells_cooled_tmrt_1k}")
        print(f"  Stage 3 completed successfully.")

    return intervention_scene, int_result, cooling_deltas, summary
