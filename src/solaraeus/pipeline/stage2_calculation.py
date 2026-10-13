"""
Stage 2: Baseline Microclimate Calculation Pipeline.

Executes 3D raytraced shadow casting, sky view factor (SVF), shortwave and longwave
radiation balance, and computes Mean Radiant Temperature (Tmrt) and UTCI thermal comfort.
Applies building footprint masking to ensure indoor building interiors are not
represented as physical outdoor pedestrian temperatures.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import affine
import numpy as np
import pandas as pd
import rasterio.features
from shapely.geometry import Polygon

from solaraeus.core.config import Material, SimulationConfig, Weather
from solaraeus.core.geometry.scene import Scene
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.reference.full_recompute import SimulationResult, full_recompute


def run_stage_calculation(
    config: PipelineConfig,
    scene: Optional[Scene] = None,
    grid_info: Optional[Dict[str, Any]] = None,
) -> Tuple[SimulationResult, Dict[str, Any]]:
    """
    Executes Stage 2: Baseline Microclimate Calculation.

    Args:
        config: Pipeline configuration.
        scene: In-memory scene from Stage 1 (or loaded from disk if None).
        grid_info: In-memory pedestrian grid info from Stage 1.

    Returns:
        Tuple of (SimulationResult, summary_dict).
    """
    dest_dir = config.output_dir / "02_calculation"
    dest_dir.mkdir(parents=True, exist_ok=True)

    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    city_config_path = root_dir / "configs" / "cities" / f"{config.area.lower()}.json"
    city_info: Optional[Dict[str, Any]] = None
    if city_config_path.exists():
        city_info = json.loads(city_config_path.read_text(encoding="utf-8"))

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 2: Calculation] Running baseline microclimate simulation")
        print(f"  Area:        {config.area}")
        print(f"  Destination: {dest_dir.resolve()}")
        print(f"=========================================================================")

    # 1. Load scene from Stage 1 artifacts if not passed
    if scene is None:
        scene_path = config.output_dir / "01_data_ingestion" / "scene_mesh.json"
        if not scene_path.exists():
            raise FileNotFoundError(f"Missing Stage 1 scene mesh at: {scene_path}")
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        scene = Scene.from_dict(scene_data)

    if grid_info is None:
        grid_path = config.output_dir / "01_data_ingestion" / "pedestrian_grid.json"
        if grid_path.exists():
            grid_info = json.loads(grid_path.read_text(encoding="utf-8"))
        else:
            gcfg = scene.pedestrian_grid
            grid_info = {
                "origin_x_m": gcfg.origin_x,
                "origin_y_m": gcfg.origin_y,
                "extent_x_m": gcfg.extent_x,
                "extent_y_m": gcfg.extent_y,
                "resolution_m": gcfg.resolution,
                "nx": gcfg.nx,
                "ny": gcfg.ny,
                "total_cells": gcfg.total_cells,
            }

    # 2. Standard urban materials
    mat_wall = Material(id="building_wall", albedo=0.30, emissivity=0.90, surface_temperature=308.15, is_opaque=True)
    mat_roof = Material(id="building_roof", albedo=0.20, emissivity=0.90, surface_temperature=308.15, is_opaque=True)
    mat_ground = Material(id="ground", albedo=0.20, emissivity=0.95, surface_temperature=308.15, is_opaque=True)
    mat_pavement = Material(id="pavement", albedo=0.30, emissivity=0.95, surface_temperature=308.15, is_opaque=True)

    scene.materials = {
        "default_wall": mat_wall,
        "default_ground": mat_ground,
        "building_wall": mat_wall,
        "building_roof": mat_roof,
        "ground": mat_ground,
        "pavement": mat_pavement,
    }

    # 3. Dynamic Weather & Simulation Configuration Loading
    sim_date = "2026-10-13"
    sim_local_time = "12:00:00"
    lat = float(city_info["coordinates"]["latitude"]) if city_info else 12.9749
    lon = float(city_info["coordinates"]["longitude"]) if city_info else 77.6054

    # Resolve weather file
    weather_csv_path: Optional[Path] = None
    if city_info and "data_paths" in city_info:
        p = Path(city_info["data_paths"].get("weather_csv", ""))
        if not p.is_absolute():
            p = root_dir / p
        if p.exists():
            weather_csv_path = p
    if weather_csv_path is None and config.data_dir:
        cand = config.data_dir / "weather_24h.csv"
        if cand.exists():
            weather_csv_path = cand

    air_temp_k = 308.15
    rel_hum = 38.0
    wind_spd = 2.0
    wind_dir = 90.0
    dni = 800.0
    dhi = 150.0

    if weather_csv_path and weather_csv_path.exists():
        try:
            w_df = pd.read_csv(weather_csv_path)
            # Pick solar noon row or peak irradiance row
            if "direct_normal_irradiance_wm2" in w_df.columns:
                peak_idx = int(w_df["direct_normal_irradiance_wm2"].idxmax())
                row = w_df.iloc[peak_idx]
            else:
                row = w_df.iloc[12] if len(w_df) > 12 else w_df.iloc[0]

            if "air_temperature_k" in row and not pd.isna(row["air_temperature_k"]):
                air_temp_k = float(row["air_temperature_k"])
            elif "air_temperature_c" in row and not pd.isna(row["air_temperature_c"]):
                air_temp_k = float(row["air_temperature_c"]) + 273.15

            if "relative_humidity_pct" in row and not pd.isna(row["relative_humidity_pct"]):
                rh_val = float(row["relative_humidity_pct"])
                rel_hum = rh_val if rh_val > 1.0 else rh_val * 100.0

            if "wind_speed_ms" in row and not pd.isna(row["wind_speed_ms"]):
                wind_spd = float(row["wind_speed_ms"])

            if "wind_direction_deg" in row and not pd.isna(row["wind_direction_deg"]):
                wind_dir = float(row["wind_direction_deg"])

            if "direct_normal_irradiance_wm2" in row and not pd.isna(row["direct_normal_irradiance_wm2"]):
                dni = float(row["direct_normal_irradiance_wm2"])

            if "diffuse_horizontal_irradiance_wm2" in row and not pd.isna(row["diffuse_horizontal_irradiance_wm2"]):
                dhi = float(row["diffuse_horizontal_irradiance_wm2"])

            if "datetime_utc" in row and not pd.isna(row["datetime_utc"]):
                dt_str = str(row["datetime_utc"]).replace("Z", "").replace("T", " ")
                parts = dt_str.split(" ")
                sim_date = parts[0]
                sim_utc_time = parts[1][:8] if len(parts) > 1 else "06:30:00"
                utc_offset = 0.0
                if city_info:
                    utc_offset = float(city_info.get("utc_offset_hours", city_info.get("coordinates", {}).get("utc_offset_hours", 0.0)))
                dt_u = datetime.strptime(f"{sim_date} {sim_utc_time}", "%Y-%m-%d %H:%M:%S")
                dt_loc = dt_u + timedelta(hours=utc_offset)
                sim_local_time = dt_loc.strftime("%H:%M:%S")
            else:
                sim_utc_time = sim_local_time

            if config.verbose:
                print(f"  Loaded weather from: {weather_csv_path.name} (Sim Date: {sim_date}, Local Time: {sim_local_time}, UTC: {sim_utc_time})")
        except Exception as e:
            if config.verbose:
                print(f"  Warning loading weather CSV: {e}, using scenario defaults.")
            sim_utc_time = sim_local_time
    elif city_info and "simulation_weather" in city_info:
        sw = city_info["simulation_weather"]
        sim_date = sw.get("date", sim_date)
        sim_local_time = sw.get("local_time", sim_local_time)
        utc_offset = float(city_info.get("utc_offset_hours", 0.0))
        dt_l = datetime.strptime(f"{sim_date} {sim_local_time}", "%Y-%m-%d %H:%M:%S")
        dt_u = dt_l - timedelta(hours=utc_offset)
        sim_utc_time = dt_u.strftime("%H:%M:%S")
        air_temp_k = sw.get("air_temperature_c", 32.6) + 273.15
        rel_hum = sw.get("relative_humidity_pct", 45.0)
        wind_spd = sw.get("wind_speed_ms", 2.5)
        wind_dir = sw.get("wind_direction_deg", 90.0)
        dni = sw.get("direct_normal_irradiance_wm2", 850.0)
        dhi = sw.get("diffuse_horizontal_irradiance_wm2", 150.0)
    else:
        sim_utc_time = sim_local_time

    weather = Weather(
        air_temperature=air_temp_k,
        relative_humidity=rel_hum,
        wind_speed=wind_spd,
        wind_direction=wind_dir,
        direct_normal_irradiance=dni,
        diffuse_horizontal_irradiance=dhi,
    )

    sim_config = SimulationConfig(
        latitude=lat,
        longitude=lon,
        date=sim_date,
        local_time=sim_utc_time,
        pedestrian_height=1.1,
        grid_resolution=config.grid_resolution_m,
        tmrt_tolerance=0.5,
        sky_patch_configuration=32,
        max_svf_search_dist_m=120.0,
    )

    # 4. Execute Full Recomputation
    t_start = time.perf_counter()
    result: SimulationResult = full_recompute(scene, weather, sim_config)
    t_elapsed = time.perf_counter() - t_start

    # 5. Compute Building Interior Mask
    nx = grid_info["nx"]
    ny = grid_info["ny"]
    res = grid_info["resolution_m"]
    ox = grid_info["origin_x_m"]
    oy = grid_info["origin_y_m"]
    ymax = oy + ny * res

    building_mask = np.zeros((ny, nx), dtype=bool)
    local_bldgs = scene.metadata.get("building_polygons_local", [])
    if local_bldgs:
        try:
            poly_list = [Polygon(b["coordinates"]) for b in local_bldgs if len(b.get("coordinates", [])) >= 3]
            aff = affine.Affine(res, 0.0, ox, 0.0, -res, ymax)
            m_top_down = rasterio.features.rasterize(
                [(p, 1) for p in poly_list],
                out_shape=(ny, nx),
                transform=aff,
                fill=0,
                dtype=np.uint8
            )
            building_mask = np.flipud(m_top_down) > 0
        except Exception as e:
            if config.verbose:
                print(f"  Warning creating building raster mask: {e}")
    elif scene.buildings:
        for b in scene.buildings.values():
            in_x = (np.arange(nx) * res + ox >= b.xmin) & (np.arange(nx) * res + ox <= b.xmax)
            in_y = (np.arange(ny) * res + oy >= b.ymin) & (np.arange(ny) * res + oy <= b.ymax)
            building_mask[np.ix_(in_y, in_x)] = True

    outdoor_mask = ~building_mask

    # Mask building interiors with NaN for outdoor pedestrian metric statistics
    tmrt_outdoor = np.where(outdoor_mask, result.tmrt, np.nan)
    utci_outdoor = np.where(outdoor_mask, result.utci, np.nan)

    # 6. Save simulation arrays
    np.savez_compressed(dest_dir / "baseline_shadow.npz", shadow_mask=result.shadow_mask)
    np.savez_compressed(dest_dir / "baseline_svf.npz", svf=result.svf)
    np.savez_compressed(dest_dir / "baseline_tmrt.npz", tmrt=tmrt_outdoor)
    np.savez_compressed(dest_dir / "baseline_utci.npz", utci=utci_outdoor)
    np.savez_compressed(dest_dir / "building_mask.npz", building_mask=building_mask)

    tmrt_valid = tmrt_outdoor[outdoor_mask]
    utci_valid = utci_outdoor[outdoor_mask]
    svf_valid = result.svf[outdoor_mask]
    sunlit_valid = result.shadow_mask[outdoor_mask]

    summary = {
        "stage": "02_calculation",
        "status": "COMPLETED",
        "wall_time_sec": round(t_elapsed, 3),
        "simulation_timestamp": {
            "date": sim_date,
            "local_time": sim_local_time,
            "utc_time": sim_utc_time,
            "timezone": city_info.get("timezone", city_info.get("coordinates", {}).get("timezone", "UTC")) if city_info else "UTC",
            "latitude": lat,
            "longitude": lon,
        },
        "weather_boundary_conditions": {
            "air_temperature_c": round(air_temp_k - 273.15, 2),
            "relative_humidity_pct": round(rel_hum, 1),
            "wind_speed_ms": round(wind_spd, 2),
            "wind_direction_deg": round(wind_dir, 1),
            "direct_normal_irradiance_wm2": round(dni, 1),
            "diffuse_horizontal_irradiance_wm2": round(dhi, 1),
        },
        "metrics": {
            "tmrt_mean_c": float(np.mean(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "tmrt_min_c": float(np.min(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "tmrt_max_c": float(np.max(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "utci_mean_c": float(np.mean(utci_valid)) if len(utci_valid) else 0.0,
            "utci_min_c": float(np.min(utci_valid)) if len(utci_valid) else 0.0,
            "utci_max_c": float(np.max(utci_valid)) if len(utci_valid) else 0.0,
            "svf_mean": float(np.mean(svf_valid)) if len(svf_valid) else 0.0,
            "sunlit_fraction": float(np.mean(sunlit_valid)) if len(sunlit_valid) else 0.0,
            "outdoor_pedestrian_cells": int(np.sum(outdoor_mask)),
            "building_interior_cells": int(np.sum(building_mask)),
        },
        "timings": {
            "timing_shadow_sec": result.metadata.get("timing_shadow_sec", 0.0),
            "timing_svf_sec": result.metadata.get("timing_svf_sec", 0.0),
            "timing_radiation_sec": result.metadata.get("timing_radiation_sec", 0.0),
            "timing_utci_sec": result.metadata.get("timing_utci_sec", 0.0),
        },
        "artifacts": {
            "shadow": "baseline_shadow.npz",
            "svf": "baseline_svf.npz",
            "tmrt": "baseline_tmrt.npz",
            "utci": "baseline_utci.npz",
            "building_mask": "building_mask.npz",
        },
    }

    summary_file = dest_dir / "baseline_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Baseline calculation finished in {t_elapsed:.2f} s")
        print(f"  Outdoor Evaluated Cells: {summary['metrics']['outdoor_pedestrian_cells']} ({np.sum(building_mask)} building cells masked)")
        print(f"  Mean Tmrt: {summary['metrics']['tmrt_mean_c']:.2f} °C, Max Tmrt: {summary['metrics']['tmrt_max_c']:.2f} °C")
        print(f"  Mean UTCI: {summary['metrics']['utci_mean_c']:.2f} °C")
        print(f"  Sunlit fraction: {summary['metrics']['sunlit_fraction'] * 100:.1f}%")
        print(f"  Stage 2 completed successfully.")

    return result, summary
