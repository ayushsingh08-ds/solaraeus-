"""
ERA5 Meteorology Loader & Processor.
Fetches Copernicus ERA5 reanalysis single-level variables, converts accumulations to W/m²,
calculates pedestrian-height wind speed and relative humidity via Magnus formula,
with automatic fallback to Open-Meteo when CDS API credentials are not configured.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import requests
import xarray as xr

from src.config import ProjectConfig, SimulationConfig, StudyArea

logger = logging.getLogger(__name__)

# Valid ERA5 single-level variable names
ERA5_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_solar_radiation_downwards",
    "surface_solar_radiation_downward_clear_sky",
    "surface_thermal_radiation_downwards",
]


def _compute_relative_humidity(ta_c: float, tdew_c: float) -> float:
    """Calculates relative humidity (%) using the Magnus formula."""
    a = 17.625
    b = 243.04
    gamma = (a * tdew_c) / (b + tdew_c) - (a * ta_c) / (b + ta_c)
    return float(np.clip(100.0 * np.exp(gamma), 0.0, 100.0))


def _adjust_wind_to_pedestrian_height(wind_10m: float, z_ped: float = 1.1, z0: float = 0.7) -> float:
    """
    Adjusts 10m wind speed to pedestrian height using the logarithmic wind profile.
    Default z0 = 0.7m represents high-density urban roughness.
    """
    if wind_10m <= 0.0:
        return 0.1  # Minimal air movement
    factor = np.log(max(z_ped, 0.01) / z0) / np.log(10.0 / z0)
    return float(max(0.1, wind_10m * factor))


def _fetch_openmeteo_fallback(
    study_area: StudyArea,
    date_str: str,
    utc_hour: int,
) -> Dict[str, Any]:
    """
    No-key fallback fetching near-current or historical weather from Open-Meteo.
    Uses archive-api for historical dates and api.open-meteo.com for recent dates.
    """
    from datetime import datetime, timezone
    req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    days_ago = (datetime.now(timezone.utc).date() - req_date).days

    # Select appropriate Open-Meteo service endpoint
    if days_ago > 5:
        base_url = "https://archive-api.open-meteo.com/v1/archive"
        logger.info(f"Querying Open-Meteo Archive API for {study_area.name} on {date_str}...")
    else:
        base_url = "https://api.open-meteo.com/v1/forecast"
        logger.info(f"Querying Open-Meteo Forecast/Recent API for {study_area.name} on {date_str}...")

    url = (
        f"{base_url}"
        f"?latitude={study_area.lat_center}&longitude={study_area.lon_center}"
        f"&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,wind_speed_10m,"
        f"wind_direction_10m,shortwave_radiation,direct_radiation,diffuse_radiation,cloud_cover"
        f"&start_date={date_str}&end_date={date_str}&timezone=UTC"
    )

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning(f"Open-Meteo query failed ({e}). Using typical NYC mid-summer meteorology.")
        data = {}

    hourly = data.get("hourly", {})
    idx = min(utc_hour, len(hourly.get("time", [])) - 1) if hourly.get("time") else 0

    ta_c = float(hourly["temperature_2m"][idx]) if "temperature_2m" in hourly else 28.5
    tdew_c = float(hourly["dew_point_2m"][idx]) if "dew_point_2m" in hourly else 18.0
    rh = float(hourly["relative_humidity_2m"][idx]) if "relative_humidity_2m" in hourly else _compute_relative_humidity(ta_c, tdew_c)
    w10 = float(hourly["wind_speed_10m"][idx]) if "wind_speed_10m" in hourly else 2.5
    wdir = float(hourly["wind_direction_10m"][idx]) if "wind_direction_10m" in hourly else 180.0
    ssrd = float(hourly["shortwave_radiation"][idx]) if "shortwave_radiation" in hourly else 650.0
    c_cov = float(hourly["cloud_cover"][idx]) / 100.0 if "cloud_cover" in hourly else 0.1

    # Meteorological direction convention -> u, v components
    dir_rad = np.deg2rad(wdir)
    u10 = -w10 * np.sin(dir_rad)
    v10 = -w10 * np.cos(dir_rad)

    # Estimate downward longwave from air temperature & cloud fraction (Prata formula)
    sigma = 5.670374419e-8
    t_kelvin = ta_c + 273.15
    vp_hpa = 6.112 * np.exp((17.67 * ta_c) / (ta_c + 243.5)) * (rh / 100.0)
    eps_clear = 1.0 - (1.0 + (46.5 * vp_hpa / t_kelvin)) * np.exp(-np.sqrt(1.2 + 3.0 * (46.5 * vp_hpa / t_kelvin)))
    eps_sky = eps_clear * (1.0 + 0.22 * (c_cov ** 2))
    strd = float(eps_sky * sigma * (t_kelvin ** 4))

    v_ped = _adjust_wind_to_pedestrian_height(w10)

    return {
        "source": "Open-Meteo",
        "date": date_str,
        "utc_hour": utc_hour,
        "Ta": round(ta_c, 2),
        "Tdew": round(tdew_c, 2),
        "RH": round(rh, 1),
        "u10": round(float(u10), 2),
        "v10": round(float(v10), 2),
        "v_10m": round(w10, 2),
        "v_ped": round(v_ped, 2),
        "SSRD": round(max(0.0, ssrd), 1),
        "SSRD_clear": round(max(ssrd, 750.0), 1),
        "STRD": round(strd, 1),
        "cloud_fraction": round(c_cov, 2),
    }


def load_era5(
    config: Optional[ProjectConfig] = None,
    study_area: Optional[StudyArea] = None,
    simulation: Optional[SimulationConfig] = None,
    force_download: bool = False,
) -> Dict[str, Any]:
    """
    Loads ERA5 meteorological data for the configured date, hour, and study area.
    If CDS API is configured and succeeds, NetCDF is downloaded and processed.
    Otherwise, gracefully falls back to Open-Meteo or cached inputs.
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area
    if simulation is None:
        simulation = config.simulation

    config.data.ensure_dirs()

    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")
    date_parts = simulation.date.split("-")
    year, month, day = date_parts[0], date_parts[1], date_parts[2]
    hour_str = f"{simulation.utc_hour:02d}"

    nc_filename = f"era5_{safe_name}_{simulation.date}_{hour_str}.nc"
    nc_path = config.data.raw_dir / nc_filename

    # If already downloaded, extract from NetCDF
    if nc_path.exists() and not force_download:
        logger.info(f"Extracting ERA5 variables from local cache {nc_path}")
        return _extract_from_netcdf(nc_path, simulation.date, simulation.utc_hour)

    # Attempt CDS API retrieval
    cdsapirc = Path.home() / ".cdsapirc"
    has_cds_config = cdsapirc.exists()

    if has_cds_config:
        try:
            import cdsapi
            logger.info(f"Connecting to CDS API for {simulation.date} {hour_str}:00 UTC...")
            client = cdsapi.Client()
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": ["reanalysis"],
                    "variable": ERA5_VARIABLES,
                    "year": [year],
                    "month": [month],
                    "day": [day],
                    "time": [f"{hour_str}:00"],
                    "area": list(study_area.area_era5),  # [N, W, S, E]
                    "data_format": "netcdf",
                    "download_format": "unarchived",
                },
                str(nc_path),
            )
            logger.info(f"ERA5 NetCDF saved to {nc_path}")
            return _extract_from_netcdf(nc_path, simulation.date, simulation.utc_hour)
        except Exception as e:
            logger.warning(f"CDS API query failed ({e}). Falling back to Open-Meteo.")

    # Fallback to Open-Meteo
    return _fetch_openmeteo_fallback(study_area, simulation.date, simulation.utc_hour)


def _extract_from_netcdf(nc_path: Path, date_str: str, utc_hour: int) -> Dict[str, Any]:
    """Reads scalar meteorological values from downloaded ERA5 NetCDF."""
    with xr.open_dataset(nc_path) as ds:
        # Check standard shortnames or long names in ERA5 netCDF
        def get_val(var_names):
            for v in var_names:
                if v in ds.variables:
                    arr = ds[v].values
                    # Extract spatial and temporal mean/scalar
                    return float(np.nanmean(arr))
            return None

        t2m_k = get_val(["t2m", "2m_temperature"]) or 301.65  # ~28.5 °C
        d2m_k = get_val(["d2m", "2m_dewpoint_temperature"]) or 291.15  # ~18 °C
        u10 = get_val(["u10", "10m_u_component_of_wind"]) or 1.5
        v10 = get_val(["v10", "10m_v_component_of_wind"]) or 2.0

        # Accumulated radiation in Joules/m^2 -> divide by 3600s for average W/m^2
        ssrd_j = get_val(["ssrd", "surface_solar_radiation_downwards"]) or 2.34e6
        ssrdc_j = get_val(["ssrdc", "surface_solar_radiation_downward_clear_sky"]) or 2.88e6
        strd_j = get_val(["strd", "surface_thermal_radiation_downwards"]) or 1.35e6

        ssrd = max(0.0, ssrd_j / 3600.0)
        ssrd_clear = max(ssrd, ssrdc_j / 3600.0)
        strd = max(0.0, strd_j / 3600.0)

        ta_c = t2m_k - 273.15
        tdew_c = d2m_k - 273.15
        rh = _compute_relative_humidity(ta_c, tdew_c)

        w10 = float(np.sqrt(u10**2 + v10**2))
        v_ped = _adjust_wind_to_pedestrian_height(w10)
        c_cov = float(np.clip(1.0 - (ssrd / max(ssrd_clear, 1.0)), 0.0, 1.0))

        return {
            "source": "ERA5",
            "date": date_str,
            "utc_hour": utc_hour,
            "Ta": round(ta_c, 2),
            "Tdew": round(tdew_c, 2),
            "RH": round(rh, 1),
            "u10": round(float(u10), 2),
            "v10": round(float(v10), 2),
            "v_10m": round(w10, 2),
            "v_ped": round(v_ped, 2),
            "SSRD": round(ssrd, 1),
            "SSRD_clear": round(ssrd_clear, 1),
            "STRD": round(strd, 1),
            "cloud_fraction": round(c_cov, 2),
        }


# Convenience alias matching mainbackendpart.md
load = load_era5
