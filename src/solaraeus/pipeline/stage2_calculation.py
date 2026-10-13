"""
Stage 2: Baseline Microclimate Calculation Pipeline.

Executes 3D raytraced shadow casting, sky view factor (SVF), shortwave and longwave
radiation balance, and computes Mean Radiant Temperature (Tmrt) and UTCI thermal comfort.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

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

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 2: Calculation] Running baseline microclimate simulation")
        print(f"  Destination: {dest_dir}")
        print(f"=========================================================================")

    # Load scene from Stage 1 artifacts if not passed
    if scene is None:
        scene_path = config.output_dir / "01_data_ingestion" / "scene_mesh.json"
        if not scene_path.exists():
            raise FileNotFoundError(f"Missing Stage 1 scene mesh at: {scene_path}")
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        scene = Scene.from_dict(scene_data)

    # Standard urban materials
    mat_wall = Material(id="building_wall", albedo=0.30, emissivity=0.90, surface_temperature_k=308.15, is_opaque=True)
    mat_roof = Material(id="building_roof", albedo=0.20, emissivity=0.90, surface_temperature_k=308.15, is_opaque=True)
    mat_ground = Material(id="ground", albedo=0.20, emissivity=0.95, surface_temperature_k=308.15, is_opaque=True)
    mat_pavement = Material(id="pavement", albedo=0.30, emissivity=0.95, surface_temperature_k=308.15, is_opaque=True)

    scene.materials = {
        "default_wall": mat_wall,
        "default_ground": mat_ground,
        "building_wall": mat_wall,
        "building_roof": mat_roof,
        "ground": mat_ground,
        "pavement": mat_pavement,
    }

    # Standard local weather (Bengaluru peak solar noon conditions)
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
    result: SimulationResult = full_recompute(scene, weather, sim_config)
    t_elapsed = time.perf_counter() - t_start

    # Save simulation arrays
    np.savez_compressed(dest_dir / "baseline_shadow.npz", shadow_mask=result.shadow_mask)
    np.savez_compressed(dest_dir / "baseline_svf.npz", svf=result.svf)
    np.savez_compressed(dest_dir / "baseline_tmrt.npz", tmrt=result.tmrt)
    np.savez_compressed(dest_dir / "baseline_utci.npz", utci=result.utci)

    tmrt_valid = result.tmrt[~np.isnan(result.tmrt)]
    utci_valid = result.utci[~np.isnan(result.utci)]
    svf_valid = result.svf[~np.isnan(result.svf)]

    summary = {
        "stage": "02_calculation",
        "status": "COMPLETED",
        "wall_time_sec": round(t_elapsed, 3),
        "metrics": {
            "tmrt_mean_c": float(np.mean(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "tmrt_min_c": float(np.min(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "tmrt_max_c": float(np.max(tmrt_valid)) if len(tmrt_valid) else 0.0,
            "utci_mean_c": float(np.mean(utci_valid)) if len(utci_valid) else 0.0,
            "utci_min_c": float(np.min(utci_valid)) if len(utci_valid) else 0.0,
            "utci_max_c": float(np.max(utci_valid)) if len(utci_valid) else 0.0,
            "svf_mean": float(np.mean(svf_valid)) if len(svf_valid) else 0.0,
            "sunlit_fraction": float(np.mean(result.shadow_mask)),
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
        },
    }

    summary_file = dest_dir / "baseline_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Baseline calculation finished in {t_elapsed:.2f} s")
        print(f"  Mean Tmrt: {summary['metrics']['tmrt_mean_c']:.2f} °C, Mean UTCI: {summary['metrics']['utci_mean_c']:.2f} °C")
        print(f"  Sunlit fraction: {summary['metrics']['sunlit_fraction'] * 100:.1f}%")
        print(f"  Stage 2 completed successfully.")

    return result, summary
