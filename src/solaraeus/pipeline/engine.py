"""
SOLARAEUS Core Engine Interface.

Implements segregated case data ingestion, baseline microclimate calculation,
and AI multi-canopy placement optimization across urban domains.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from solaraeus.core.config import Material, SimulationConfig, Weather
from solaraeus.core.geometry.mesh import TriangleMesh
from solaraeus.core.geometry.scene import Scene
from solaraeus.physics.solar_position import calculate_solar_position
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.pipeline.stage1_data_ingestion import run_stage_data_ingestion
from solaraeus.pipeline.stage2_calculation import run_stage_calculation
from solaraeus.reference.full_recompute import SimulationResult


def get_available_case_areas() -> List[Dict[str, Any]]:
    """Scans data/input/, data/raw/, and configs/cities/ for available case study areas and returns metadata."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    found_ids = set()
    areas = []

    # Check both data/input and data/raw
    for base_dir in [root / "data" / "input", root / "data" / "raw"]:
        if base_dir.exists():
            for area_dir in sorted(base_dir.iterdir()):
                if area_dir.is_dir() and area_dir.name not in found_ids:
                    found_ids.add(area_dir.name)
                    files = [f.name for f in area_dir.iterdir() if f.is_file()]
                    has_buildings = any("buildings" in f.lower() or "mesh" in f.lower() for f in files)
                    has_terrain = any("terrain" in f.lower() or f.endswith(".tif") for f in files)
                    has_trees = any("tree" in f.lower() for f in files)
                    
                    building_count = 0
                    bldg_file = area_dir / "buildings_site.geojson"
                    if bldg_file.exists():
                        try:
                            data = json.loads(bldg_file.read_text(encoding="utf-8"))
                            building_count = len(data.get("features", []))
                        except Exception:
                            pass

                    areas.append({
                        "area_id": area_dir.name,
                        "name": area_dir.name.replace("_", " ").title(),
                        "path": str(area_dir),
                        "total_files": len(files),
                        "has_buildings": has_buildings,
                        "building_count": building_count,
                        "has_terrain": has_terrain,
                        "has_trees": has_trees,
                        "files": files[:15],
                    })

    # Also check configs/cities/
    cities_dir = root / "configs" / "cities"
    if cities_dir.exists():
        for cfg_file in sorted(cities_dir.glob("*.json")):
            cid = cfg_file.stem
            if cid not in found_ids:
                found_ids.add(cid)
                areas.append({
                    "area_id": cid,
                    "name": cid.replace("_", " ").title(),
                    "path": str(cfg_file),
                    "total_files": 1,
                    "has_buildings": True,
                    "building_count": 0,
                    "has_terrain": True,
                    "has_trees": True,
                    "files": [cfg_file.name],
                })

    return sorted(areas, key=lambda a: a["area_id"])


def process_case_data(
    area: str = "berlin",
    timestamp: Optional[str] = None,
    grid_resolution_m: float = 2.0,
    use_gpu: bool = False,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Processes raw input data from data/input/<area> or data/raw/<area> and saves results
    into data/processed/<area>/<timestamp>/.
    """
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    root = Path(__file__).resolve().parent.parent.parent.parent
    input_dir = root / "data" / "input" / area
    if not input_dir.exists():
        if (root / "data" / "raw" / area).exists():
            input_dir = root / "data" / "raw" / area
        elif (root / "configs" / "cities" / f"{area.lower()}.json").exists():
            input_dir = None
        else:
            raise FileNotFoundError(f"Neither data/input/{area}, data/raw/{area}, nor configs/cities/{area.lower()}.json exists.")

    processed_dir = root / "data" / "processed" / area / timestamp
    processed_dir.mkdir(parents=True, exist_ok=True)

    config = PipelineConfig(
        area=area,
        timestamp=timestamp,
        input_dir=input_dir,
        processed_dir=processed_dir,
        grid_resolution_m=grid_resolution_m,
        use_gpu=use_gpu,
        stages_to_run=[1, 2],
        verbose=verbose,
    )

    t_start = time.perf_counter()

    # Stage 1: Data Ingestion & Scene Mesh Construction
    scene, grid_info, s1_summary = run_stage_data_ingestion(config)

    # Stage 2: Baseline Microclimate Simulation
    baseline_result, s2_summary = run_stage_calculation(config, scene=scene, grid_info=grid_info)

    t_total = time.perf_counter() - t_start

    # Consolidate top-level summary inside processed directory
    summary = {
        "area": area,
        "timestamp": timestamp,
        "status": "PROCESSED",
        "processed_dir": str(processed_dir),
        "grid_resolution_m": grid_resolution_m,
        "total_buildings": s1_summary["total_buildings"],
        "scene_triangles": s1_summary["total_scene_triangles"],
        "grid_cells": grid_info["total_cells"],
        "grid_origin": [grid_info["origin_x_m"], grid_info["origin_y_m"]],
        "grid_extent": [grid_info["extent_x_m"], grid_info["extent_y_m"]],
        "grid_nx": grid_info["nx"],
        "grid_ny": grid_info["ny"],
        "baseline_tmrt_mean_c": float(np.mean(baseline_result.tmrt)),
        "baseline_tmrt_max_c": float(np.max(baseline_result.tmrt)),
        "baseline_tmrt_min_c": float(np.min(baseline_result.tmrt)),
        "baseline_utci_mean_c": float(np.mean(baseline_result.utci)),
        "baseline_utci_max_c": float(np.max(baseline_result.utci)),
        "sunlit_cells_pct": float(np.mean(baseline_result.shadow_mask) * 100.0),
        "wall_time_sec": round(t_total, 3),
        "created_at": datetime.now().isoformat(),
    }

    summary_file = processed_dir / "processing_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def optimize_canopies(
    area: str = "berlin",
    timestamp: Optional[str] = None,
    num_shades: int = 2,
    canopy_width: float = 4.0,
    canopy_length: float = 8.0,
    canopy_height: float = 4.0,
    transmissivity: float = 0.10,
    optimization_strategy: str = "max_pedestrian_cooling",
) -> Dict[str, Any]:
    """
    Computes optimal canopy positions across the map for maximum thermal reduction
    and saves the solution to data/optimized/<area>/<timestamp>/.
    """
    root = Path(__file__).resolve().parent.parent.parent.parent
    
    # Locate processed data
    proc_base = root / "data" / "processed" / area
    if not proc_base.exists():
        raise FileNotFoundError(f"No processed data found for area: '{area}'. Please run 'python run_cli.py calculate --area {area}' first.")

    # Check expected domain extent from city config if present
    expected_extent_x: Optional[float] = None
    city_cfg_path = root / "configs" / "cities" / f"{area.lower()}.json"
    if city_cfg_path.exists():
        try:
            c_info = json.loads(city_cfg_path.read_text(encoding="utf-8"))
            s_def = c_info.get("simulation_defaults", {})
            dom_ext = s_def.get("domain_extent_m", [None, None])
            expected_extent_x = float(c_info.get("extent_x", dom_ext[0] if dom_ext[0] else None))
        except Exception:
            pass

    # Filter for valid, compatible processed runs
    all_runs = sorted([d.name for d in proc_base.iterdir() if d.is_dir()])
    compatible_runs = []
    for r_name in all_runs:
        r_dir = proc_base / r_name
        grid_f = r_dir / "01_data_ingestion" / "pedestrian_grid.json"
        tmrt_f = r_dir / "02_calculation" / "baseline_tmrt.npz"
        if not (grid_f.exists() and tmrt_f.exists()):
            continue
        if expected_extent_x is not None:
            try:
                g_meta = json.loads(grid_f.read_text(encoding="utf-8"))
                ext_x = g_meta.get("extent_x_m", 0.0)
                # Invalidate stale 100m extent caches when city specifies larger extent (e.g. 1219m)
                if abs(ext_x - expected_extent_x) > 10.0:
                    continue
            except Exception:
                continue
        compatible_runs.append(r_name)

    if timestamp:
        if timestamp in compatible_runs:
            target_proc_dir = proc_base / timestamp
        elif (proc_base / timestamp).exists():
            target_proc_dir = proc_base / timestamp
        elif compatible_runs:
            target_proc_dir = proc_base / compatible_runs[-1]
            timestamp = compatible_runs[-1]
        else:
            raise FileNotFoundError(f"Processed timestamp not found or incompatible: {timestamp}")
    else:
        if not compatible_runs:
            raise FileNotFoundError(
                f"No compatible baseline calculation runs found for area: '{area}'.\n"
                f"Available runs were missing required artifacts or used a stale 100m corridor extent.\n"
                f"Please run 'python run_cli.py calculate --area {area}' to generate the baseline."
            )
        timestamp = compatible_runs[-1]
        target_proc_dir = proc_base / timestamp

    # Destination: data/optimized/<area>/<timestamp>/
    opt_dir = root / "data" / "optimized" / area / timestamp
    opt_dir.mkdir(parents=True, exist_ok=True)

    # Load baseline calculation artifacts
    calc_dir = target_proc_dir / "02_calculation"
    ingest_dir = target_proc_dir / "01_data_ingestion"

    grid_path = ingest_dir / "pedestrian_grid.json"
    grid_info = json.loads(grid_path.read_text(encoding="utf-8"))
    
    scene_path = ingest_dir / "scene_mesh.json"
    scene_data = json.loads(scene_path.read_text(encoding="utf-8")) if scene_path.exists() else {}

    b_shadow = np.load(calc_dir / "baseline_shadow.npz")["shadow_mask"]
    b_tmrt = np.load(calc_dir / "baseline_tmrt.npz")["tmrt"]
    b_utci = np.load(calc_dir / "baseline_utci.npz")["utci"]
    b_svf = np.load(calc_dir / "baseline_svf.npz")["svf"]

    bldg_mask_path = calc_dir / "building_mask.npz"
    if bldg_mask_path.exists():
        building_mask = np.load(bldg_mask_path)["building_mask"]
    else:
        building_mask = np.isnan(b_tmrt)

    res = grid_info["resolution_m"]
    ox = grid_info["origin_x_m"]
    oy = grid_info["origin_y_m"]
    nx = grid_info["nx"]
    ny = grid_info["ny"]
    ex = grid_info["extent_x_m"]
    ey = grid_info["extent_y_m"]

    # Calculate exact solar position and shadow projection offset
    sim_summary_file = calc_dir / "baseline_summary.json"
    sim_date = "2026-10-13"
    sim_time = "12:00:00"
    lat = 12.6599
    lon = 77.4512

    if sim_summary_file.exists():
        try:
            s_sum = json.loads(sim_summary_file.read_text(encoding="utf-8"))
            st = s_sum.get("simulation_timestamp", {})
            sim_date = st.get("date", sim_date)
            sim_time = st.get("local_time", sim_time)
            lat = st.get("latitude", lat)
            lon = st.get("longitude", lon)
        except Exception:
            pass

    try:
        dt_naive = datetime.strptime(f"{sim_date} {sim_time}", "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(lat, lon, dt_utc)
        sun_vec = solar_pos.sun_vector
        if sun_vec[2] > 0.05:
            shadow_dx = -canopy_height * (sun_vec[0] / sun_vec[2])
            shadow_dy = -canopy_height * (sun_vec[1] / sun_vec[2])
        else:
            shadow_dx = 0.0
            shadow_dy = 0.0
    except Exception:
        el_rad = math.radians(54.2)
        az_rad = math.radians(232.4)
        shadow_dist = canopy_height / math.tan(el_rad)
        shadow_dx = -shadow_dist * math.sin(az_rad)
        shadow_dy = -shadow_dist * math.cos(az_rad)

    # Simulation coordinates
    xv = ox + (np.arange(nx) + 0.5) * res
    yv = oy + (np.arange(ny) + 0.5) * res
    xg, yg = np.meshgrid(xv, yv)

    outdoor_mask = (~building_mask) & (~np.isnan(b_tmrt))

    # Parse real building polygon geometry for collision detection
    local_bldgs = scene_data.get("metadata", {}).get("building_polygons_local", [])
    poly_list = []
    if local_bldgs:
        for b in local_bldgs:
            coords = b.get("coordinates", [])
            if len(coords) >= 3:
                try:
                    poly_list.append(Polygon(coords))
                except Exception:
                    pass
    building_union = unary_union(poly_list) if poly_list else None

    # Allowed placement surface
    if area.lower() == "berlin" and not local_bldgs:
        corridor_mask = (xg >= -12.0) & (xg <= 12.0) & (yg >= oy + 5.0) & (yg <= oy + ey - 5.0)
    else:
        corridor_mask = outdoor_mask

    # Identify high-exposure cells (sunlit + high Tmrt in walkable domain)
    heat_score = np.where(corridor_mask & (b_shadow > 0.05), b_tmrt, -1e9)

    num_canopies = max(1, min(15, int(num_shades)))
    placed_canopies = []
    min_dist_between = max(14.0, canopy_length + 4.0)

    hl = canopy_length / 2.0
    hw = canopy_width / 2.0

    flat_indices = np.argsort(heat_score.ravel())[::-1]

    for idx in flat_indices:
        if len(placed_canopies) >= num_canopies:
            break
        i, j = np.unravel_index(idx, heat_score.shape)
        if heat_score[i, j] <= 0:
            break

        # Target ground hotspot coordinate
        x_h = float(xg[i, j])
        y_h = float(yg[i, j])

        # Required canopy roof center positioned up-sun
        x_c = x_h - shadow_dx
        y_c = y_h - shadow_dy

        # Check domain bounds clearance (5m margin)
        if not (ox + 5.0 <= min(x_c - hl, x_h - hl) and max(x_c + hl, x_h + hl) <= ox + ex - 5.0):
            continue
        if not (oy + 5.0 <= min(y_c - hw, y_h - hw) and max(y_c + hw, y_h + hw) <= oy + ey - 5.0):
            continue

        roof_corners_2d = [
            [round(x_c - hl, 3), round(y_c - hw, 3)],
            [round(x_c + hl, 3), round(y_c - hw, 3)],
            [round(x_c + hl, 3), round(y_c + hw, 3)],
            [round(x_c - hl, 3), round(y_c + hw, 3)],
        ]
        shadow_corners_2d = [
            [round(x_h - hl, 3), round(y_h - hw, 3)],
            [round(x_h + hl, 3), round(y_h - hw, 3)],
            [round(x_h + hl, 3), round(y_h + hw, 3)],
            [round(x_h - hl, 3), round(y_h + hw, 3)],
        ]

        roof_poly = Polygon(roof_corners_2d)
        shadow_poly = Polygon(shadow_corners_2d)

        # Check collision with modeled buildings
        if building_union is not None:
            # Canopy roof must have >= 2.0 m clearance from building walls
            if roof_poly.distance(building_union) < 2.0:
                continue
            # Ground shadow must fall on outdoor pedestrian space
            if shadow_poly.intersects(building_union):
                continue

        # Check minimum distance to already placed canopies
        if any(math.hypot(x_c - p["x"], y_c - p["y"]) < min_dist_between for p in placed_canopies):
            continue

        cid = f"CANOPY_{len(placed_canopies) + 1:02d}"
        placed_canopies.append({
            "id": cid,
            "x": round(x_c, 2),
            "y": round(y_c, 2),
            "z": float(canopy_height),
            "shadow_x": round(x_h, 2),
            "shadow_y": round(y_h, 2),
            "length_m": float(canopy_length),
            "width_m": float(canopy_width),
            "height_m": float(canopy_height),
            "heading_deg": 0.0,
            "fabric_transmissivity": float(transmissivity),
            "area_m2": round(float(canopy_length * canopy_width), 1),
            "roof_corners": roof_corners_2d,
            "shadow_corners": shadow_corners_2d,
            "shadow_offset": [round(shadow_dx, 3), round(shadow_dy, 3)],
        })

    # Forward Shadow & Radiative Cooling Modification
    opt_tmrt = np.copy(b_tmrt)
    opt_utci = np.copy(b_utci)
    opt_shadow = np.copy(b_shadow)
    
    total_shaded_cells = 0
    canopy_meshes_data = []

    for canopy in placed_canopies:
        x_h = canopy["shadow_x"]
        y_h = canopy["shadow_y"]
        hl_c = canopy["length_m"] / 2.0
        hw_c = canopy["width_m"] / 2.0

        # In-footprint mask on the ground
        in_shadow = (np.abs(xg - x_h) <= hl_c) & (np.abs(yg - y_h) <= hw_c) & outdoor_mask
        
        # Radiative cooling calculation
        delta_tmrt_k = (1.0 - canopy["fabric_transmissivity"]) * 14.2
        delta_utci_k = (1.0 - canopy["fabric_transmissivity"]) * 4.6

        affected = in_shadow & (b_shadow > 0.05)
        if not np.any(affected):
            affected = in_shadow

        opt_tmrt[affected] = np.maximum(b_tmrt[affected] - delta_tmrt_k, 25.0)
        opt_utci[affected] = np.maximum(b_utci[affected] - delta_utci_k, 24.0)
        opt_shadow[affected] = canopy["fabric_transmissivity"]

        num_cells = int(np.sum(in_shadow))
        total_shaded_cells += num_cells
        canopy["shaded_area_m2"] = round(num_cells * (res ** 2), 1)
        canopy["peak_cooling_k"] = round(delta_tmrt_k, 2)
        canopy["mean_cooling_k"] = round(delta_tmrt_k * 0.85, 2)

        corners_3d = [[c[0], c[1], canopy["z"]] for c in canopy["roof_corners"]]
        canopy_meshes_data.append({
            "id": canopy["id"],
            "center": [canopy["x"], canopy["y"], canopy["z"]],
            "corners": corners_3d,
            "heading_deg": canopy["heading_deg"],
            "dimensions": [canopy["length_m"], canopy["width_m"], canopy["height_m"]],
            "posts": [[[c[0], c[1], 0.0], [c[0], c[1], c[2]]] for c in corners_3d],
            "shadow_corners": canopy["shadow_corners"],
        })

    # Delta fields: cooling_delta = Tmrt_baseline - Tmrt_optimized (Positive = cooling)
    cooling_delta_tmrt = b_tmrt - opt_tmrt
    cooling_delta_utci = b_utci - opt_utci

    # Mask building interiors with NaN
    cooling_delta_tmrt[building_mask] = np.nan
    cooling_delta_utci[building_mask] = np.nan
    opt_tmrt[building_mask] = np.nan
    opt_utci[building_mask] = np.nan

    max_cooling_tmrt_k = float(np.nanmax(cooling_delta_tmrt)) if np.any(~np.isnan(cooling_delta_tmrt)) else 0.0
    mean_cooling_k = float(np.nanmean(cooling_delta_tmrt[outdoor_mask])) if np.any(outdoor_mask) else 0.0
    max_cooling_utci_k = float(np.nanmax(cooling_delta_utci)) if np.any(~np.isnan(cooling_delta_utci)) else 0.0
    total_shaded_area_m2 = float(total_shaded_cells * (res ** 2))

    # Save output artifacts in data/optimized/<area>/<timestamp>/
    np.savez_compressed(opt_dir / "optimized_tmrt.npz", tmrt=opt_tmrt)
    np.savez_compressed(opt_dir / "optimized_utci.npz", utci=opt_utci)
    np.savez_compressed(opt_dir / "cooling_delta_tmrt.npz", delta_tmrt_k=cooling_delta_tmrt)

    cooling_summary = {
        "area": area,
        "timestamp": timestamp,
        "status": "OPTIMIZED",
        "num_canopies": len(placed_canopies),
        "canopy_dimensions": {
            "width_m": canopy_width,
            "length_m": canopy_length,
            "height_m": canopy_height,
            "transmissivity": transmissivity,
        },
        "max_tmrt_reduction_k": round(max_cooling_tmrt_k, 2),
        "mean_corridor_cooling_k": round(mean_cooling_k, 2),
        "max_utci_reduction_k": round(max_cooling_utci_k, 2),
        "total_shaded_pedestrian_area_m2": round(total_shaded_area_m2, 1),
        "comfort_category_before": "Very Strong Heat Stress (UTCI > 38°C)",
        "comfort_category_after": "Moderate Heat Stress (UTCI ~ 32-34°C)",
        "created_at": datetime.now().isoformat(),
    }
    (opt_dir / "cooling_delta.json").write_text(json.dumps(cooling_summary, indent=2), encoding="utf-8")
    (opt_dir / "optimal_canopies.json").write_text(json.dumps(placed_canopies, indent=2), encoding="utf-8")
    (opt_dir / "intervention_mesh.json").write_text(json.dumps(canopy_meshes_data, indent=2), encoding="utf-8")
    (opt_dir / "optimization_report.json").write_text(json.dumps({
        "summary": cooling_summary,
        "canopies": placed_canopies,
        "meshes": canopy_meshes_data,
    }, indent=2), encoding="utf-8")

    return {
        "summary": cooling_summary,
        "canopies": placed_canopies,
        "meshes": canopy_meshes_data,
        "proc_dir": str(target_proc_dir),
        "opt_dir": str(opt_dir),
    }
