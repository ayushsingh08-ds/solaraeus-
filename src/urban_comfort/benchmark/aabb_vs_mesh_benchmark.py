"""
Comparative AABB vs Mesh Benchmarking Module.

Evaluates parity, physical fidelity, and computational overhead between
canonical Axis-Aligned Bounding Box (AABB) representations and equivalent
watertight triangular-mesh representations across standard urban scenes:
1. Isolated Building (single box, 12 triangles vs 1 AABB)
2. Urban Canyon (two parallel slabs, 24 triangles vs 2 AABBs)
3. Enclosed Courtyard (four perimeter blocks, 48 triangles vs 4 AABBs)
4. Dense 3x3 Grid (9 buildings, 108 triangles vs 9 AABBs)
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import math
import os
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.mesh import TriangleMesh, create_box_mesh
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.validation.metrics import compute_shadow_iou, compute_utci_category_agreement


@dataclass
class BenchmarkSceneDef:
    scene_id: str
    display_name: str
    description: str
    domain_x_m: float
    domain_y_m: float
    buildings: List[Building]


def get_canonical_benchmark_scenes() -> List[BenchmarkSceneDef]:
    """Returns definitions of the 4 canonical benchmark scenes."""
    scenes: List[BenchmarkSceneDef] = []

    # Scene 1: Isolated Building
    scenes.append(BenchmarkSceneDef(
        scene_id="isolated_building",
        display_name="Isolated Building",
        description="Single central high-rise block (20m x 20m, height 25m)",
        domain_x_m=60.0,
        domain_y_m=60.0,
        buildings=[
            Building(id="b_iso", footprint=BoundingBox2D(20.0, 40.0, 20.0, 40.0), height=25.0)
        ]
    ))

    # Scene 2: Urban Canyon
    scenes.append(BenchmarkSceneDef(
        scene_id="urban_canyon",
        display_name="Urban Canyon",
        description="Two parallel slabs (40m x 15m, height 20m) separated by 20m street canyon",
        domain_x_m=80.0,
        domain_y_m=80.0,
        buildings=[
            Building(id="b_canyon_w", footprint=BoundingBox2D(15.0, 30.0, 15.0, 65.0), height=20.0),
            Building(id="b_canyon_e", footprint=BoundingBox2D(50.0, 65.0, 15.0, 65.0), height=20.0),
        ]
    ))

    # Scene 3: Enclosed Courtyard
    scenes.append(BenchmarkSceneDef(
        scene_id="enclosed_courtyard",
        display_name="Enclosed Courtyard",
        description="Four perimeter blocks (height 18m) enclosing a 20m x 20m courtyard",
        domain_x_m=80.0,
        domain_y_m=80.0,
        buildings=[
            Building(id="b_court_s", footprint=BoundingBox2D(15.0, 65.0, 15.0, 30.0), height=18.0),
            Building(id="b_court_n", footprint=BoundingBox2D(15.0, 65.0, 50.0, 65.0), height=18.0),
            Building(id="b_court_w", footprint=BoundingBox2D(15.0, 30.0, 30.0, 50.0), height=18.0),
            Building(id="b_court_e", footprint=BoundingBox2D(50.0, 65.0, 30.0, 50.0), height=18.0),
        ]
    ))

    # Scene 4: Dense 3x3 Grid
    b_grid: List[Building] = []
    for iy in range(3):
        for ix in range(3):
            x1 = 8.0 + ix * 24.0
            x2 = x1 + 16.0
            y1 = 8.0 + iy * 24.0
            y2 = y1 + 16.0
            h = 15.0 + ((ix + 2 * iy) % 4) * 3.0
            b_grid.append(Building(id=f"b_{ix}_{iy}", footprint=BoundingBox2D(x1, x2, y1, y2), height=h))

    scenes.append(BenchmarkSceneDef(
        scene_id="dense_3x3_grid",
        display_name="Dense 3x3 Grid",
        description="Nine urban blocks (16m x 16m, height 15-24m) in a 3x3 regular grid",
        domain_x_m=80.0,
        domain_y_m=80.0,
        buildings=b_grid
    ))

    return scenes


def build_scene_pair(scene_def: BenchmarkSceneDef,
                     resolution_m: float = 1.0,
                     pedestrian_height_m: float = 1.1) -> Tuple[Scene, Scene]:
    """
    Constructs an AABB scene and an equivalent pure-mesh scene from the benchmark scene definition.
    """
    grid_cfg = PedestrianGridConfig(
        extent_x=scene_def.domain_x_m,
        extent_y=scene_def.domain_y_m,
        resolution=resolution_m,
        pedestrian_height=pedestrian_height_m
    )

    scene_aabb = Scene(pedestrian_grid=grid_cfg)
    scene_mesh = Scene(pedestrian_grid=grid_cfg)

    for b in scene_def.buildings:
        scene_aabb.add_building(b)
        mesh_b = create_box_mesh(
            box_id=f"mesh_{b.id}",
            xmin=b.footprint.xmin,
            xmax=b.footprint.xmax,
            ymin=b.footprint.ymin,
            ymax=b.footprint.ymax,
            zmin=0.0,
            zmax=b.height,
            material_id=b.material_id
        )
        scene_mesh.add_mesh(mesh_b)

    return scene_aabb, scene_mesh


def run_single_comparison(scene_def: BenchmarkSceneDef,
                          weather: Weather,
                          config: SimulationConfig) -> Dict[str, Any]:
    """
    Executes full recomputation for both AABB and mesh representations of a scene,
    and returns comprehensive comparative metrics.
    """
    scene_aabb, scene_mesh = build_scene_pair(scene_def, config.grid_resolution, config.pedestrian_height)

    # 1. Full recompute AABB
    t0 = time.perf_counter()
    res_aabb = full_recompute(scene_aabb, weather, config)
    t_aabb = time.perf_counter() - t0

    # 2. Full recompute Mesh
    t0 = time.perf_counter()
    res_mesh = full_recompute(scene_mesh, weather, config)
    t_mesh = time.perf_counter() - t0

    # 3. Direct Shadow Parity
    iou = compute_shadow_iou(res_aabb.shadow_mask, res_mesh.shadow_mask)
    mismatch_cells = int(np.sum(res_aabb.shadow_mask != res_mesh.shadow_mask))

    # 4. SVF Accuracy
    svf_diff = np.abs(res_mesh.svf - res_aabb.svf)
    svf_mae = float(np.mean(svf_diff))
    svf_rmse = float(np.sqrt(np.mean((res_mesh.svf - res_aabb.svf) ** 2)))
    svf_max_diff = float(np.max(svf_diff))

    # 5. Tmrt Fidelity
    tmrt_diff = np.abs(res_mesh.tmrt - res_aabb.tmrt)
    tmrt_mae_k = float(np.mean(tmrt_diff))
    tmrt_rmse_k = float(np.sqrt(np.mean((res_mesh.tmrt - res_aabb.tmrt) ** 2)))
    tmrt_max_diff_k = float(np.max(tmrt_diff))

    # 6. UTCI Agreement
    utci_agreement = compute_utci_category_agreement(res_aabb.utci, res_mesh.utci)

    # 7. Complexity & Runtime
    bldg_count = len(scene_aabb.buildings)
    tri_count = sum(len(m.triangles) for m in scene_mesh.meshes.values())
    overhead_ratio = t_mesh / max(1e-6, t_aabb)

    return {
        "scene_id": scene_def.scene_id,
        "display_name": scene_def.display_name,
        "description": scene_def.description,
        "domain_size_m": f"{scene_def.domain_x_m:.0f}x{scene_def.domain_y_m:.0f}",
        "grid_resolution_m": config.grid_resolution,
        "aabb_building_count": bldg_count,
        "mesh_triangle_count": tri_count,
        "shadow_iou": round(iou, 6),
        "shadow_mismatch_cells": mismatch_cells,
        "svf_mae": round(svf_mae, 6),
        "svf_rmse": round(svf_rmse, 6),
        "svf_max_diff": round(svf_max_diff, 6),
        "tmrt_mae_k": round(tmrt_mae_k, 6),
        "tmrt_rmse_k": round(tmrt_rmse_k, 6),
        "tmrt_max_diff_k": round(tmrt_max_diff_k, 6),
        "utci_category_agreement": round(utci_agreement, 6),
        "runtime_aabb_sec": round(t_aabb, 4),
        "runtime_mesh_sec": round(t_mesh, 4),
        "overhead_ratio": round(overhead_ratio, 2),
    }


def run_aabb_vs_mesh_benchmark(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the comparative AABB vs Mesh benchmark suite across all 4 canonical scenes
    and writes comparison CSV and summary JSON to the output directory.
    """
    if output_dir is None:
        # Default to latest mesh validation directory or create one
        base_results = "results"
        mesh_dirs = [
            os.path.join(base_results, d) for d in os.listdir(base_results)
            if d.startswith("mesh_validation_") and os.path.isdir(os.path.join(base_results, d))
        ] if os.path.exists(base_results) else []

        if mesh_dirs:
            output_dir = sorted(mesh_dirs)[-1]
        else:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("results", f"mesh_validation_{ts}")

    os.makedirs(output_dir, exist_ok=True)

    config = SimulationConfig(
        latitude=48.8566,
        longitude=2.3522,
        date="2026-07-15",
        local_time="14:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        tmrt_tolerance=0.5,
        numerical_tolerance=0.05,
        sky_patch_configuration=16,
        max_svf_search_dist_m=100.0
    )

    weather = Weather(
        air_temperature=30.0,
        relative_humidity=45.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=850.0,
        diffuse_horizontal_irradiance=150.0
    )

    scenes = get_canonical_benchmark_scenes()
    comparison_rows: List[Dict[str, Any]] = []

    for sc in scenes:
        row = run_single_comparison(sc, weather, config)
        comparison_rows.append(row)

    # 1. Write CSV
    csv_path = os.path.join(output_dir, "aabb_vs_mesh_comparison.csv")
    fieldnames = list(comparison_rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_rows)

    # 2. Write Summary JSON
    utc_now = datetime.now(timezone.utc)
    summary = {
        "timestamp_utc": utc_now.isoformat(),
        "total_scenes": len(comparison_rows),
        "output_directory": output_dir,
        "csv_path": csv_path,
        "mean_shadow_iou": float(np.mean([r["shadow_iou"] for r in comparison_rows])),
        "min_shadow_iou": float(np.min([r["shadow_iou"] for r in comparison_rows])),
        "total_shadow_mismatches": int(sum(r["shadow_mismatch_cells"] for r in comparison_rows)),
        "mean_svf_mae": float(np.mean([r["svf_mae"] for r in comparison_rows])),
        "max_svf_mae": float(np.max([r["svf_mae"] for r in comparison_rows])),
        "mean_tmrt_mae_k": float(np.mean([r["tmrt_mae_k"] for r in comparison_rows])),
        "max_tmrt_mae_k": float(np.max([r["tmrt_mae_k"] for r in comparison_rows])),
        "mean_utci_agreement": float(np.mean([r["utci_category_agreement"] for r in comparison_rows])),
        "min_utci_agreement": float(np.min([r["utci_category_agreement"] for r in comparison_rows])),
        "mean_overhead_ratio": float(np.mean([r["overhead_ratio"] for r in comparison_rows])),
        "results": comparison_rows
    }

    json_path = os.path.join(output_dir, "aabb_vs_mesh_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    summary = run_aabb_vs_mesh_benchmark()
    print(f"Benchmark completed successfully! Results written to: {summary['output_directory']}")
    for r in summary["results"]:
        print(f"  {r['display_name']}: IoU={r['shadow_iou']:.6f}, SVF MAE={r['svf_mae']:.6f}, "
              f"Tmrt MAE={r['tmrt_mae_k']:.6f}K, UTCI={r['utci_category_agreement']*100:.2f}%, "
              f"Overhead={r['overhead_ratio']:.2f}x")
