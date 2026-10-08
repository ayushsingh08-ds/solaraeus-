"""
Full reference recomputation path for single-timestep SOLWEIG-compatible urban thermal comfort.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import time
import numpy as np

from urban_comfort.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes, ShortwaveFluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes, LongwaveFluxes
from urban_comfort.radiation.tmrt import compute_tmrt, RadiantState
from urban_comfort.comfort.utci import compute_utci


@dataclass
class SimulationResult:
    """Complete simulation output across all computed physical fields."""
    shadow_mask: np.ndarray                     # Binary direct beam visibility (1.0 lit, 0.0 shadow)
    direct_irradiance: np.ndarray               # Direct horizontal shortwave irradiance (W / m^2)
    visibility_fields: Dict[str, np.ndarray]    # {"svf": np.ndarray}
    shortwave_flux: np.ndarray                  # Total absorbed shortwave flux density (W / m^2)
    longwave_flux: np.ndarray                   # Total absorbed longwave flux density (W / m^2)
    tmrt: np.ndarray                            # Mean Radiant Temperature in Celsius (deg C)
    utci: np.ndarray                            # Universal Thermal Climate Index in Celsius (deg C)
    metadata: Dict[str, Any]                    # Timestamps, runtimes, solar parameters, diagnostics

    @property
    def svf(self) -> np.ndarray:
        return self.visibility_fields["svf"]


def full_recompute(scene: Scene, weather: Weather,
                   config: SimulationConfig,
                   backend: Optional[str] = None) -> SimulationResult:
    """
    Executes a deterministic full recomputation of all microclimatic fields from scratch.
    
    Parameters:
        scene: Scene container with buildings, ground, and grid specs.
        weather: Weather boundary conditions.
        config: Simulation control and geographic parameters.
        backend: Optional backend override ('cpu', 'gpu', or 'auto').
        
    Returns:
        SimulationResult containing all evaluated spatial fields.
    """
    selected_backend = (backend or getattr(config, "backend", "cpu")).lower()
    if selected_backend == "gpu":
        from urban_comfort.backend.gpu_backend import GPUBackend
        return GPUBackend().full_simulate(scene, weather, config)
    elif selected_backend == "auto":
        from urban_comfort.backend import get_backend
        return get_backend("auto").full_simulate(scene, weather, config)

    t_start = time.perf_counter()

    # 1. Parse Datetime and Compute Solar Position
    dt_str = f"{config.date} {config.local_time}"
    dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    dt_utc = dt_naive.replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

    # 2. Instantiate Pedestrian Calculation Grid
    grid = PedestrianGrid(scene.pedestrian_grid)

    # 3. Direct Solar Shadows
    t0_shadow = time.perf_counter()
    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    t_shadow = time.perf_counter() - t0_shadow

    # 4. Directional Visibility & Sky View Factor
    t0_svf = time.perf_counter()
    svf = compute_sky_view_factor(
        scene, grid,
        num_azimuths=config.sky_patch_configuration,
        max_search_dist_m=config.max_svf_search_dist_m
    )
    t_svf = time.perf_counter() - t0_svf

    # 5. Radiative Exchange (Shortwave + Longwave)
    t0_rad = time.perf_counter()
    wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
    ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)

    sw_fluxes = compute_shortwave_fluxes(
        weather, solar_pos, shadow_mask, svf, ground_mat, wall_mat
    )
    lw_fluxes = compute_longwave_fluxes(
        weather, svf, ground_mat, wall_mat
    )
    radiant_state = compute_tmrt(sw_fluxes.k_total, lw_fluxes.l_total)
    t_rad = time.perf_counter() - t0_rad

    # 6. Thermal Comfort (UTCI)
    t0_utci = time.perf_counter()
    air_temp_c = weather.air_temperature - 273.15
    utci = compute_utci(
        air_temp_c=air_temp_c,
        tmrt_c=radiant_state.tmrt_c,
        wind_speed_ms=weather.wind_speed,
        relative_humidity=weather.relative_humidity
    )
    t_utci = time.perf_counter() - t0_utci

    t_total = time.perf_counter() - t_start

    metadata = {
        "solar_altitude_deg": solar_pos.altitude_deg,
        "solar_azimuth_deg": solar_pos.azimuth_deg,
        "solar_zenith_deg": solar_pos.zenith_deg,
        "sun_vector": solar_pos.sun_vector,
        "is_daylight": solar_pos.is_daylight,
        "timing_shadow_sec": t_shadow,
        "timing_svf_sec": t_svf,
        "timing_radiation_sec": t_rad,
        "timing_utci_sec": t_utci,
        "timing_total_sec": t_total,
        "num_buildings": len(scene.get_active_buildings()),
        "total_cells": grid.total_cells,
        "air_temperature_c": air_temp_c
    }

    return SimulationResult(
        shadow_mask=shadow_mask,
        direct_irradiance=sw_fluxes.direct_horizontal,
        visibility_fields={"svf": svf},
        shortwave_flux=sw_fluxes.k_total,
        longwave_flux=lw_fluxes.l_total,
        tmrt=radiant_state.tmrt_c,
        utci=utci,
        metadata=metadata
    )
