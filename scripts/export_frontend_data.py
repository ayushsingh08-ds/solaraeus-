#!/usr/bin/env python3
"""
Frontend Data Exporter.
Converts Solaraeus microclimate simulation grids (DSM, SVF, Shadows, Tmrt, UTCI)
into JSON data contracts stored in outputs/json/ and outputs/data/ for the React/Three.js frontend.
"""

import json
import logging
import math
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np

from src.config import ProjectConfig, WASHINGTON_SQUARE_PARK
from src.data import era5_loader
from src.physics import (
    compute_radiation,
    compute_solar_position,
    compute_tmrt,
    compute_utci,
    cast_shadows,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("export_frontend_data")


def round_2d(arr: np.ndarray, decimals: int = 1) -> list:
    """Rounds a 2D numpy array and returns nested Python lists."""
    return np.round(arr, decimals).tolist()


def main():
    logger.info("Starting frontend data contract export...")
    cfg = ProjectConfig(study_area=WASHINGTON_SQUARE_PARK)
    cfg.data.ensure_dirs()
    safe_name = cfg.study_area.name.lower().replace(" ", "_").replace("/", "_")

    json_dir = cfg.data.json_dir
    data_dir = cfg.data.data_out_dir
    json_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load intermediate geometry & SVF
    dsm_path = cfg.data.cache_dir / f"{safe_name}_dsm_1m.npy"
    svf_path = cfg.data.cache_dir / f"{safe_name}_svf_1m.npy"
    grid_path = cfg.data.cache_dir / f"{safe_name}_pedestrian_grid.npz"

    if not dsm_path.exists() or not svf_path.exists():
        raise FileNotFoundError("Missing cached DSM or SVF. Run scripts/run_stage1.py first.")

    dsm = np.load(dsm_path)
    svf = np.load(svf_path)
    H, W = dsm.shape

    bounds_dict = {
        "xmin": cfg.study_area.utm_bounds[0],
        "ymin": cfg.study_area.utm_bounds[1],
        "xmax": cfg.study_area.utm_bounds[2],
        "ymax": cfg.study_area.utm_bounds[3],
    }

    # 2. Export simulation_config.json
    config_json = {
        "studyArea": {
            "name": cfg.study_area.name,
            "latCenter": cfg.study_area.lat_center,
            "lonCenter": cfg.study_area.lon_center,
            "utmZone": cfg.study_area.utm_zone,
            "bounds": bounds_dict,
            "resolutionM": cfg.study_area.resolution_m,
            "shape": [H, W],
        },
        "simulation": {
            "date": cfg.simulation.date,
            "dayOfYear": cfg.simulation.day_of_year,
            "pedestrianHeightM": cfg.simulation.pedestrian_height_m,
            "nSvFDirections": cfg.simulation.n_svf_directions,
            "svfMaxRadiusM": cfg.simulation.svf_max_radius_m,
        },
        "dataSources": {
            "overtureVersion": "2024-07-22.0",
            "era5Date": cfg.simulation.date,
            "demSource": "SRTM 30m Global (AWS Skadi)",
        },
    }
    (data_dir / "simulation_config.json").write_text(json.dumps(config_json, indent=2), encoding="utf-8")
    logger.info("Saved outputs/data/simulation_config.json")

    # 3. Define diurnal time steps (EDT = UTC - 4h)
    # Hours: 08:00, 10:00, 12:00, 14:00, 16:00, 18:00 EDT -> 12, 14, 16, 18, 20, 22 UTC
    time_steps = [
        {"utc": f"{cfg.simulation.date}T12:00:00", "local": "08:00 EDT", "hourFloat": 8.0, "utcHour": 12},
        {"utc": f"{cfg.simulation.date}T14:00:00", "local": "10:00 EDT", "hourFloat": 10.0, "utcHour": 14},
        {"utc": f"{cfg.simulation.date}T16:00:00", "local": "12:00 EDT", "hourFloat": 12.0, "utcHour": 16},
        {"utc": f"{cfg.simulation.date}T18:00:00", "local": "14:00 EDT", "hourFloat": 14.0, "utcHour": 18},
        {"utc": f"{cfg.simulation.date}T20:00:00", "local": "16:00 EDT", "hourFloat": 16.0, "utcHour": 20},
        {"utc": f"{cfg.simulation.date}T22:00:00", "local": "18:00 EDT", "hourFloat": 18.0, "utcHour": 22},
    ]
    (data_dir / "available_times.json").write_text(json.dumps(time_steps, indent=2), encoding="utf-8")
    logger.info("Saved outputs/data/available_times.json")

    # 4. Export static metrics: DSM, DEM, SVF, and Walkable Grid
    date_tag = cfg.simulation.date.replace("-", "")

    dem_path = cfg.data.processed_dir / f"{safe_name}_dem_utm_1m.tif"
    if dem_path.exists():
        import rasterio
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
    else:
        dem = np.full_like(dsm, 6.0)

    building_height = np.maximum(0.0, dsm - dem)
    is_building = building_height > 2.0

    dsm_json = {
        "metric": "dsm",
        "date": cfg.simulation.date,
        "timeUtc": f"{cfg.simulation.date}T00:00:00",
        "bounds": bounds_dict,
        "resolutionM": cfg.study_area.resolution_m,
        "shape": [H, W],
        "values": round_2d(dsm, 1),
        "description": "Digital Surface Model elevation ASL (m)",
        "units": "m",
        "vmin": float(np.min(dsm)),
        "vmax": float(np.max(dsm)),
    }
    (json_dir / f"dsm_{date_tag}_0000.json").write_text(json.dumps(dsm_json), encoding="utf-8")
    logger.info(f"Saved outputs/json/dsm_{date_tag}_0000.json")

    dem_json = {
        "metric": "dem",
        "date": cfg.simulation.date,
        "timeUtc": f"{cfg.simulation.date}T00:00:00",
        "bounds": bounds_dict,
        "resolutionM": cfg.study_area.resolution_m,
        "shape": [H, W],
        "values": round_2d(dem, 1),
        "description": "Bare-earth DEM elevation ASL (m)",
        "units": "m",
        "vmin": float(np.min(dem)),
        "vmax": float(np.max(dem)),
    }
    (json_dir / f"dem_{date_tag}_0000.json").write_text(json.dumps(dem_json), encoding="utf-8")
    logger.info(f"Saved outputs/json/dem_{date_tag}_0000.json")

    svf_json = {
        "metric": "svf",
        "date": cfg.simulation.date,
        "timeUtc": f"{cfg.simulation.date}T00:00:00",
        "bounds": bounds_dict,
        "resolutionM": cfg.study_area.resolution_m,
        "shape": [H, W],
        "values": round_2d(svf, 3),
        "description": "Sky View Factor (Steyn 1980 360-degree ray march)",
        "units": "dimensionless",
        "vmin": 0.0,
        "vmax": 1.0,
    }
    (json_dir / f"svf_{date_tag}_0000.json").write_text(json.dumps(svf_json), encoding="utf-8")
    logger.info(f"Saved outputs/json/svf_{date_tag}_0000.json")

    # Export walkable mask & bare ground elevation for instant, 100% collision-free avatar physics
    walkable_json = {
        "studyArea": cfg.study_area.name,
        "shape": [H, W],
        "baseElevation": 6.0,
        "walkable": (~is_building).astype(int).tolist(),
        "groundElevation": round_2d(dem, 1),
    }
    (data_dir / "walkable_grid.json").write_text(json.dumps(walkable_json), encoding="utf-8")
    logger.info("Saved outputs/data/walkable_grid.json with 2D walkable grid and ground elevations")

    # 5. Export time-varying metrics for each diurnal hour
    # Affine transform for Washington Square Park
    from rasterio.transform import from_bounds
    transform = from_bounds(*cfg.study_area.utm_bounds, W, H)

    for step in time_steps:
        utc_hour = step["utcHour"]
        time_tag = f"{utc_hour:02d}00"
        logger.info(f"Computing & exporting microclimate for {step['local']} ({step['utc']})...")

        # Solar position
        alt_rad, az_rad = compute_solar_position(
            lat=cfg.study_area.lat_center,
            utc_hour=utc_hour,
            day_of_year=cfg.simulation.day_of_year,
            lon=cfg.study_area.lon_center,
        )

        # Shadows
        sunlit_mask = cast_shadows(
            dsm=dsm,
            transform=transform,
            alt_rad=alt_rad,
            az_rad=az_rad,
            max_distance=cfg.simulation.svf_max_radius_m,
        )

        # Weather for this hour
        # Approximate diurnal temperature and radiation curve
        # Solar noon is around 17-18 UTC
        hour_offset = abs(utc_hour - 17.5)
        solar_factor = max(0.0, math.sin(max(0.0, alt_rad)))
        ssrd = 850.0 * solar_factor
        strd = 380.0 + 10.0 * math.cos(hour_offset * math.pi / 12)
        ta = 28.0 + 6.0 * math.exp(-0.5 * (hour_offset / 3.0) ** 2)
        rh = 55.0 - 10.0 * math.exp(-0.5 * (hour_offset / 3.0) ** 2)
        v_ped = 1.5

        # Radiation fluxes
        fluxes = compute_radiation(
            sunlit_mask=sunlit_mask,
            svf=svf,
            SSRD=ssrd,
            STRD=strd,
            Ta=ta,
            Tdew=18.0,
            cloud_fraction=0.1,
            alt_rad=alt_rad,
            atmospheric_transmission=cfg.simulation.atmospheric_transmission,
            sky_emissivity=cfg.simulation.sky_emissivity,
            ground_emissivity=cfg.simulation.ground_emissivity,
        )

        # Tmrt & UTCI
        tmrt = compute_tmrt(fluxes=fluxes)
        utci = compute_utci(Ta=ta, tmrt_values=tmrt, v_ped=v_ped, RH=rh)

        # Save shadows JSON
        shadow_json = {
            "metric": "shadows",
            "date": cfg.simulation.date,
            "timeUtc": step["utc"],
            "solarAltitudeDeg": round(math.degrees(alt_rad), 2),
            "solarAzimuthDeg": round(math.degrees(az_rad), 2),
            "bounds": bounds_dict,
            "resolutionM": cfg.study_area.resolution_m,
            "shape": [H, W],
            "values": sunlit_mask.astype(np.int8).tolist(),
            "description": "Direct Solar Shading Mask (1=Sunlit, 0=Shaded)",
            "units": "binary",
            "vmin": 0.0,
            "vmax": 1.0,
        }
        (json_dir / f"shadows_{date_tag}_{time_tag}.json").write_text(json.dumps(shadow_json), encoding="utf-8")

        # Save Tmrt JSON
        tmrt_json = {
            "metric": "tmrt",
            "date": cfg.simulation.date,
            "timeUtc": step["utc"],
            "solarAltitudeDeg": round(math.degrees(alt_rad), 2),
            "solarAzimuthDeg": round(math.degrees(az_rad), 2),
            "bounds": bounds_dict,
            "resolutionM": cfg.study_area.resolution_m,
            "shape": [H, W],
            "values": round_2d(tmrt, 1),
            "description": "Mean Radiant Temperature (°C)",
            "units": "°C",
            "vmin": 25.0,
            "vmax": 75.0,
        }
        (json_dir / f"tmrt_{date_tag}_{time_tag}.json").write_text(json.dumps(tmrt_json), encoding="utf-8")

        # Save UTCI JSON
        utci_json = {
            "metric": "utci",
            "date": cfg.simulation.date,
            "timeUtc": step["utc"],
            "solarAltitudeDeg": round(math.degrees(alt_rad), 2),
            "solarAzimuthDeg": round(math.degrees(az_rad), 2),
            "bounds": bounds_dict,
            "resolutionM": cfg.study_area.resolution_m,
            "shape": [H, W],
            "values": round_2d(utci, 1),
            "description": "Universal Thermal Climate Index (°C)",
            "units": "°C",
            "vmin": 20.0,
            "vmax": 48.0,
        }
        (json_dir / f"utci_{date_tag}_{time_tag}.json").write_text(json.dumps(utci_json), encoding="utf-8")

    logger.info("Frontend data contracts exported successfully!")


if __name__ == "__main__":
    main()
