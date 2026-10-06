"""
Mesh Scaling Benchmark Module for SOLARAEUS.

Measures computational performance, scaling characteristics, and peak heap memory
across systematic parametric variations of:
1. Triangle count: M in [12, 48, 192, 768, 3072]
2. Grid resolution: dx in [2.0m, 1.0m, 0.5m] (cell counts N from 1,600 to 25,600)
3. Incremental update efficiency across scaling tiers
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import math
import os
import time
import tracemalloc
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.mesh import TriangleMesh, create_box_mesh
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.incremental.mesh_update import ChangeMeshHeightEdit
from urban_comfort.incremental.update import incremental_update_certified


def create_mesh_scaling_scene(num_buildings: int,
                              extent_m: float = 100.0,
                              resolution_m: float = 1.0,
                              pedestrian_height_m: float = 1.1) -> Scene:
    """
    Constructs a reproducible synthetic urban scene with a regular grid of box meshes.
    
    Parameters:
        num_buildings: Number of box buildings (1, 4, 16, 64, 256).
                       Yields exactly 12 * num_buildings triangles.
        extent_m: Side length of the square domain in meters.
        resolution_m: Grid resolution in meters.
        pedestrian_height_m: Pedestrian height in meters.
    """
    grid_cfg = PedestrianGridConfig(
        extent_x=extent_m,
        extent_y=extent_m,
        resolution=resolution_m,
        pedestrian_height=pedestrian_height_m
    )
    scene = Scene(pedestrian_grid=grid_cfg)

    grid_side = int(math.ceil(math.sqrt(num_buildings)))
    cell_w = extent_m / float(grid_side)
    bldg_w = cell_w * 0.60
    margin = (cell_w - bldg_w) / 2.0

    bldg_idx = 0
    for iy in range(grid_side):
        for ix in range(grid_side):
            if bldg_idx >= num_buildings:
                break
            x1 = ix * cell_w + margin
            x2 = x1 + bldg_w
            y1 = iy * cell_w + margin
            y2 = y1 + bldg_w
            # Deterministic height variation
            height = 15.0 + ((ix * 3 + iy * 5) % 4) * 3.0  # 15.0 to 24.0m
            mesh = create_box_mesh(
                box_id=f"box_{bldg_idx}",
                xmin=x1, xmax=x2,
                ymin=y1, ymax=y2,
                zmin=0.0, zmax=height,
                material_id="default_wall"
            )
            scene.add_mesh(mesh)
            bldg_idx += 1

    return scene


def run_scaling_trial(scene: Scene,
                      config: SimulationConfig,
                      weather: Weather,
                      config_type: str,
                      tier_id: str) -> Dict[str, Any]:
    """
    Executes a single scaling trial:
    - Measures peak heap memory and execution time of full recompute.
    - Measures component times: shadow and SVF.
    - Executes certified incremental update on box_0 height edit.
    - Returns detailed performance record.
    """
    grid = PedestrianGrid(scene.pedestrian_grid)
    tri_count = sum(len(m.triangles) for m in scene.meshes.values())
    bldg_count = len(scene.meshes)

    # 1. Measure Peak Memory and Component Timings during Full Recomputation
    tracemalloc.start()
    t_start = time.perf_counter()

    # Solar position
    from datetime import datetime, timezone
    dt_str = f"{config.date} {config.local_time}"
    dt_utc = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

    # Shadow timing
    t0_shadow = time.perf_counter()
    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    t_shadow = time.perf_counter() - t0_shadow

    # SVF timing
    t0_svf = time.perf_counter()
    svf = compute_sky_view_factor(
        scene, grid,
        num_azimuths=config.sky_patch_configuration,
        max_search_dist_m=config.max_svf_search_dist_m
    )
    t_svf = time.perf_counter() - t0_svf

    # Full recompute pipeline
    res_full = full_recompute(scene, weather, config)
    t_full = time.perf_counter() - t_start

    cur_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak_mem / (1024.0 * 1024.0)

    # 2. Localized Edit and Certified Incremental Recomputation
    # Modify height of first building
    edit = ChangeMeshHeightEdit(mesh_id="box_0", new_height=25.0)
    updated_scene, _ = edit.apply(scene)

    t0_inc = time.perf_counter()
    inc_res, cert = incremental_update_certified(
        scene, updated_scene, res_full, edit, weather, config
    )
    t_inc = time.perf_counter() - t0_inc

    speedup = t_full / max(1e-6, inc_res.time_selective_recompute_sec)

    return {
        "config_type": config_type,
        "tier_id": tier_id,
        "building_count": bldg_count,
        "mesh_triangle_count": tri_count,
        "domain_extent_m": scene.pedestrian_grid.extent_x,
        "grid_resolution_m": config.grid_resolution,
        "grid_cells_total": grid.total_cells,
        "peak_memory_mb": round(peak_mb, 2),
        "time_shadow_sec": round(t_shadow, 4),
        "time_svf_sec": round(t_svf, 4),
        "time_full_recompute_sec": round(t_full, 4),
        "time_incremental_sec": round(t_inc, 4),
        "time_selective_recompute_sec": round(inc_res.time_selective_recompute_sec, 4),
        "reused_cell_fraction": round(inc_res.reused_fraction, 4),
        "recomputed_cells": inc_res.recomputed_cells,
        "speedup_ratio": round(speedup, 2),
    }


def run_mesh_scaling_benchmark(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the full suite of triangle scaling and resolution scaling benchmarks.
    Writes results to CSV and JSON summary.
    """
    if output_dir is None:
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

    weather = Weather(
        air_temperature=30.0,
        relative_humidity=45.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=850.0,
        diffuse_horizontal_irradiance=150.0
    )

    records: List[Dict[str, Any]] = []

    # =========================================================================
    # Part 1: Triangle Count Scaling Matrix (M in [12, 48, 192, 768, 3072])
    # Domain 100x100m, dx = 1.0m (10,000 cells)
    # =========================================================================
    triangle_tiers = [
        (1, "T1_12_tri"),
        (4, "T2_48_tri"),
        (16, "T3_192_tri"),
        (64, "T4_768_tri"),
        (256, "T5_3072_tri"),
    ]

    for n_bldgs, tier_id in triangle_tiers:
        cfg = SimulationConfig(
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
        scene = create_mesh_scaling_scene(n_bldgs, extent_m=100.0, resolution_m=1.0)
        rec = run_scaling_trial(scene, cfg, weather, "triangle_scaling", tier_id)
        records.append(rec)

    # =========================================================================
    # Part 2: Grid Resolution Scaling Matrix (dx in [2.0m, 1.0m, 0.5m])
    # Domain 80x80m, 16 buildings (192 triangles)
    # =========================================================================
    resolution_tiers = [
        (2.0, "R1_2.0m"),
        (1.0, "R2_1.0m"),
        (0.5, "R3_0.5m"),
    ]

    for res, tier_id in resolution_tiers:
        cfg = SimulationConfig(
            latitude=48.8566,
            longitude=2.3522,
            date="2026-07-15",
            local_time="14:00:00",
            pedestrian_height=1.1,
            grid_resolution=res,
            tmrt_tolerance=0.5,
            numerical_tolerance=0.05,
            sky_patch_configuration=16,
            max_svf_search_dist_m=80.0
        )
        scene = create_mesh_scaling_scene(16, extent_m=80.0, resolution_m=res)
        rec = run_scaling_trial(scene, cfg, weather, "resolution_scaling", tier_id)
        records.append(rec)

    # 1. Write CSV
    csv_path = os.path.join(output_dir, "mesh_scaling_results.csv")
    fieldnames = list(records[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # 2. Write Summary JSON
    utc_now = datetime.now(timezone.utc)
    summary = {
        "timestamp_utc": utc_now.isoformat(),
        "total_trials": len(records),
        "output_directory": output_dir,
        "csv_path": csv_path,
        "max_peak_memory_mb": float(np.max([r["peak_memory_mb"] for r in records])),
        "mean_speedup_ratio": float(np.mean([r["speedup_ratio"] for r in records])),
        "triangle_scaling": [r for r in records if r["config_type"] == "triangle_scaling"],
        "resolution_scaling": [r for r in records if r["config_type"] == "resolution_scaling"],
    }

    json_path = os.path.join(output_dir, "mesh_scaling_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    summary = run_mesh_scaling_benchmark()
    print(f"Scaling benchmark completed! Output: {summary['output_directory']}")
    for r in summary["triangle_scaling"]:
        print(f"  [Tri] {r['tier_id']}: M={r['mesh_triangle_count']}, "
              f"Full={r['time_full_recompute_sec']:.3f}s, Mem={r['peak_memory_mb']:.1f}MB, "
              f"Speedup={r['speedup_ratio']:.2f}x")
    for r in summary["resolution_scaling"]:
        print(f"  [Res] {r['tier_id']}: dx={r['grid_resolution_m']}m, N={r['grid_cells_total']}, "
              f"Full={r['time_full_recompute_sec']:.3f}s, Mem={r['peak_memory_mb']:.1f}MB, "
              f"Speedup={r['speedup_ratio']:.2f}x")
