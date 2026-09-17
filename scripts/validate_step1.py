"""
Step 1 Validation Script for Solaraeus Data Pipeline.
Downloads and harmonizes Overture Buildings, SRTM DEM, and ERA5/Open-Meteo Meteorology.
Validates the 2.5D DSM raster and produces diagnostic visualizations.
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import matplotlib.pyplot as plt
import numpy as np

from src.config import ProjectConfig, WASHINGTON_SQUARE_PARK
from src.data import dem_loader, era5_loader, harmonize, overture_loader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("validate_step1")


def main():
    logger.info("=" * 60)
    logger.info("SOLARAEUS STAGE 1 — DATA PIPELINE VALIDATION")
    logger.info("=" * 60)

    cfg = ProjectConfig(study_area=WASHINGTON_SQUARE_PARK)
    cfg.data.ensure_dirs()

    # ---- 1. DATA ACQUISITION ----
    logger.info("\n[1/4] Loading Overture Buildings...")
    buildings_gdf = overture_loader.load_buildings(cfg)

    logger.info("\n[2/4] Loading Meteorological Data (ERA5 / Open-Meteo)...")
    met_data = era5_loader.load_era5(cfg)
    logger.info(f"Meteorological state: {met_data}")

    logger.info("\n[3/4] Loading Ground Elevation (SRTM 30m)...")
    dem_array, dem_transform = dem_loader.load_dem(cfg)
    logger.info(f"DEM shape={dem_array.shape}, min={dem_array.min():.2f}m, max={dem_array.max():.2f}m")

    # ---- 2. HARMONIZATION ----
    logger.info("\n[4/4] Harmonizing to 1m UTM Grid...")
    unified = harmonize.build_unified_grid(
        buildings_gdf=buildings_gdf,
        dem_array=dem_array,
        met_data=met_data,
        config=cfg,
    )

    dsm = unified["dsm"]
    dem = unified["dem"]
    building_raster = unified["building_raster"]
    buildings_table = unified["buildings_table"]
    meta = unified["metadata"]

    # ---- 3. SANITY CHECKS ----
    logger.info("\n" + "=" * 60)
    logger.info("SANITY CHECK METRICS")
    logger.info("=" * 60)
    logger.info(f"Study Area: {meta['study_area']}")
    logger.info(f"UTM Grid Shape: {dsm.shape} (Rows x Cols at {meta['resolution_m']}m resolution)")
    logger.info(f"Ground DEM Elevation: min={dem.min():.2f}m, max={dem.max():.2f}m, mean={dem.mean():.2f}m")
    logger.info(f"Building Heights: max={building_raster.max():.2f}m, mean_occupied={building_raster[building_raster > 0].mean():.2f}m")
    logger.info(f"Total 2.5D DSM Elevation: min={dsm.min():.2f}m, max={dsm.max():.2f}m")
    logger.info(f"Building footprint coverage: {(np.count_nonzero(building_raster) / dsm.size) * 100:.1f}%")

    # Verify park area (central open space) has low building footprint
    h, w = dsm.shape
    center_box = building_raster[h // 3 : 2 * h // 3, w // 3 : 2 * w // 3]
    park_open_pct = (np.count_nonzero(center_box == 0) / center_box.size) * 100
    logger.info(f"Center park zone open space: {park_open_pct:.1f}% unbuilt ground")

    # ---- 4. MATPLOTLIB VISUAL DIAGNOSTICS ----
    logger.info("\nGenerating diagnostic plots...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), constrained_layout=True)

    # 1. Ground DEM
    im0 = axes[0].imshow(dem, cmap="terrain", origin="upper")
    axes[0].set_title(f"1. Ground DEM (SRTM 30m Resampled)\nMin: {dem.min():.1f}m, Max: {dem.max():.1f}m", fontsize=11)
    axes[0].set_xlabel("UTM Easting (m relative)")
    axes[0].set_ylabel("UTM Northing (m relative)")
    plt.colorbar(im0, ax=axes[0], label="Elevation (m ASL)", shrink=0.7)

    # 2. Building Footprints & Heights
    im1 = axes[1].imshow(building_raster, cmap="magma", origin="upper")
    axes[1].set_title(f"2. Building Heights (Overture Maps)\n{len(buildings_table)} Buildings, Max Height: {building_raster.max():.1f}m", fontsize=11)
    axes[1].set_xlabel("UTM Easting (m relative)")
    plt.colorbar(im1, ax=axes[1], label="Height Above Ground (m)", shrink=0.7)

    # 3. Final 2.5D DSM
    im2 = axes[2].imshow(dsm, cmap="viridis", origin="upper")
    axes[2].set_title(f"3. Unified 2.5D DSM (DEM + Buildings)\nWashington Square Park (1m Resolution)", fontsize=11)
    axes[2].set_xlabel("UTM Easting (m relative)")
    plt.colorbar(im2, ax=axes[2], label="Surface Elevation (m)", shrink=0.7)

    # Add North arrow on DSM plot
    axes[2].annotate(
        "N",
        xy=(0.93, 0.90),
        xytext=(0.93, 0.82),
        arrowprops=dict(facecolor="white", edgecolor="black", width=2, headwidth=8),
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="white",
        xycoords="axes fraction",
    )

    out_fig = cfg.data.figure_dir / "dsm_wsp_validation.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()
    logger.info(f"Diagnostic plot saved to: {out_fig}")

    # Also save primary dsm figure
    primary_fig = cfg.data.figure_dir / "dsm_wsp.png"
    plt.figure(figsize=(8, 7))
    plt.imshow(dsm, cmap="viridis", origin="upper")
    plt.colorbar(label="Elevation (m)")
    plt.title(f"Solaraeus — 2.5D DSM: {meta['study_area']} (1m resolution)\n"
              f"Grid: {dsm.shape[1]}x{dsm.shape[0]}m | Elevation: [{dsm.min():.1f}m, {dsm.max():.1f}m]")
    plt.xlabel("Easting (m relative)")
    plt.ylabel("Northing (m relative)")
    plt.tight_layout()
    plt.savefig(primary_fig, dpi=200)
    plt.close()
    logger.info(f"Primary DSM plot saved to: {primary_fig}")

    logger.info("\nStep 1 validation completed successfully!")


if __name__ == "__main__":
    main()
