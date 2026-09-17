"""
Step 2 Validation Script for Solaraeus Geometry Subpackage.
Validates 2.5D DSM refinement, 3D pedestrian grid generation, and watertight 3D building mesh extrusion.
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio

from src.config import ProjectConfig, WASHINGTON_SQUARE_PARK
from src.geometry import dsm as dsm_builder
from src.geometry import meshes, pedestrian_grid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("validate_step2")


def main():
    logger.info("=" * 60)
    logger.info("SOLARAEUS STAGE 2 — GEOMETRY PIPELINE VALIDATION")
    logger.info("=" * 60)

    cfg = ProjectConfig(study_area=WASHINGTON_SQUARE_PARK)
    cfg.data.ensure_dirs()
    safe_name = cfg.study_area.name.lower().replace(" ", "_").replace("/", "_")

    # ---- 1. LOAD INTERMEDIATES FROM STEP 1 ----
    logger.info("\n[1/4] Loading cached Step 1 rasters and building tables...")
    dsm_raw_path = cfg.data.cache_dir / f"{safe_name}_dsm_1m.npy"
    dem_tif_path = cfg.data.processed_dir / f"{safe_name}_dem_utm_1m.tif"
    buildings_path = cfg.data.processed_dir / f"{safe_name}_buildings_utm.parquet"

    dsm_raw = np.load(dsm_raw_path)
    with rasterio.open(dem_tif_path) as src:
        dem = src.read(1)
        dem_transform = src.transform

    buildings_table = gpd.read_parquet(buildings_path)
    building_raster = dsm_raw - dem
    building_raster[building_raster < 0] = 0.0

    # ---- 2. STEP 2.1: DSM REFINEMENT & VALIDATION ----
    logger.info("\n[2/4] Validating 2.5D DSM (Step 2.1)...")
    dsm_final = dsm_builder.build_dsm(dsm_raw, buildings_table, cfg)
    logger.info(f"Refined DSM shape: {dsm_final.shape}, range: [{dsm_final.min():.1f}m, {dsm_final.max():.1f}m]")

    # ---- 3. STEP 2.2: PEDESTRIAN GRID CONSTRUCTION ----
    logger.info("\n[3/4] Generating 3D Pedestrian Query Grid (Step 2.2)...")
    points, ped_mask, transform, shape = pedestrian_grid.create_pedestrian_grid(
        config=cfg,
        dsm=dsm_final,
        dem=dem,
        building_raster=building_raster,
        transform=dem_transform,
    )

    N_total = len(points)
    N_walkable = int(np.count_nonzero(ped_mask))
    N_buildings = N_total - N_walkable
    walkable_pct = (N_walkable / N_total) * 100.0

    logger.info("\n" + "=" * 60)
    logger.info("PEDESTRIAN GRID VALIDATION METRICS")
    logger.info("=" * 60)
    logger.info(f"Total pedestrian query points (N): {N_total:,}")
    logger.info(f"Outdoor walkable street/park points: {N_walkable:,} ({walkable_pct:.1f}%)")
    logger.info(f"Masked building footprint points: {N_buildings:,} ({100 - walkable_pct:.1f}%)")
    logger.info(f"Pedestrian elevation range: [{points[:, 2].min():.2f}m, {points[:, 2].max():.2f}m]")

    # Verification: Ensure zero walkable points fall on building heights > 2m
    bldg_flat = building_raster.ravel()
    walkable_bldg_heights = bldg_flat[ped_mask]
    max_height_on_walkable = float(np.max(walkable_bldg_heights))
    logger.info(f"Verification: Max building height at walkable points = {max_height_on_walkable:.2f}m (Expected: 0.0m)")
    assert max_height_on_walkable == 0.0, "Walkable mask erroneously includes building pixels!"

    # ---- 4. STEP 2.3: 3D BUILDING MESH EXTRUSION ----
    logger.info("\n[4/4] Extruding 3D Watertight Building Meshes (Step 2.3)...")
    building_mesh = meshes.build_building_meshes(
        buildings_table=buildings_table,
        dem_array=dem,
        config=cfg,
    )
    logger.info(f"3D mesh vertices: {len(building_mesh.vertices):,}")
    logger.info(f"3D mesh faces: {len(building_mesh.faces):,}")
    logger.info(f"Mesh is_watertight: {building_mesh.is_watertight}")
    logger.info(f"Mesh volume: {building_mesh.volume:,.1f} m³")

    # ---- 5. VISUALIZATION ----
    logger.info("\nGenerating pedestrian grid & mask diagnostic visualization...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=True)

    # Panel 1: Walkable Surface Mask on Top of DSM
    im0 = axes[0].imshow(dsm_final, cmap="gist_earth", origin="upper")
    # Reshape mask to 2D for overlay
    mask_2d = ped_mask.reshape(shape)
    axes[0].imshow(np.ma.masked_where(mask_2d, mask_2d), cmap="Reds", alpha=0.35, origin="upper")
    axes[0].set_title("1. Walkable Streets & Parks vs Building Footprints\n(Red Mask = Building Obstacles)", fontsize=11)
    axes[0].set_xlabel("UTM Easting (m relative)")
    axes[0].set_ylabel("UTM Northing (m relative)")
    plt.colorbar(im0, ax=axes[0], label="Surface Elevation (m)", shrink=0.7)

    # Panel 2: Pedestrian Sampling Points (Subsampled for clarity)
    stride = 6  # Plot every 6th meter point
    sub_mask_2d = mask_2d[::stride, ::stride]
    sub_rows, sub_cols = np.where(sub_mask_2d)

    axes[1].imshow(dsm_final[::stride, ::stride], cmap="gray", origin="upper", alpha=0.6)
    axes[1].scatter(
        sub_cols,
        sub_rows,
        c="#00FFCC",
        s=4,
        alpha=0.6,
        label=f"Walkable Points (Subsampled 1:{stride})",
    )
    axes[1].set_title(f"2. Pedestrian Evaluation Grid ({N_walkable:,} Walkable Nodes)\nWashington Square Park (1.1m Height)", fontsize=11)
    axes[1].set_xlabel(f"Grid Columns (Stride {stride}m)")
    axes[1].legend(loc="lower right", facecolor="#1e1e1e", labelcolor="white")

    # Add north arrow
    axes[1].annotate(
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

    out_fig = cfg.data.figure_dir / "pedestrian_grid_wsp.png"
    plt.savefig(out_fig, dpi=200)
    plt.close()
    logger.info(f"Pedestrian grid visualization saved to: {out_fig}")

    logger.info("\nStep 2 geometry validation completed successfully!")


if __name__ == "__main__":
    main()
