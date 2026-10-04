"""
Pedestrian Query Grid Generator.
Constructs a regular 3D grid of pedestrian evaluation points (N, 3) at 1.1m height,
calculates spatial coordinate transforms, and generates walkable surface masks.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import rasterio
from rasterio.transform import from_bounds

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)


def create_pedestrian_grid(
    config: Optional[ProjectConfig] = None,
    dsm: Optional[np.ndarray] = None,
    dem: Optional[np.ndarray] = None,
    building_raster: Optional[np.ndarray] = None,
    transform: Optional[rasterio.Affine] = None,
    study_area: Optional[StudyArea] = None,
) -> Tuple[np.ndarray, np.ndarray, rasterio.Affine, Tuple[int, int]]:
    """
    Constructs the pedestrian point grid at 1.1m elevation above ground level.

    Args:
        config: Project configuration.
        dsm: (H, W) 2.5D DSM raster.
        dem: (H, W) Ground DEM elevation raster.
        building_raster: (H, W) Building height raster (0 where no building).
        transform: Affine transform mapping pixel coords to UTM.
        study_area: Target study area.

    Returns:
        (pedestrian_points, pedestrian_mask, transform, grid_shape):
          - pedestrian_points: (N, 3) float32 coordinates [UTM_X, UTM_Y, Elevation_Z]
          - pedestrian_mask: (N,) bool array (True = walkable outdoor ground / street)
          - transform: rasterio.Affine transform
          - grid_shape: (H, W) tuple
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area

    config.data.ensure_dirs()

    # If DSM is missing, load from cache
    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")
    if dsm is None:
        dsm_path = config.data.cache_dir / f"{safe_name}_dsm_1m.npy"
        if dsm_path.exists():
            dsm = np.load(dsm_path)
        else:
            raise FileNotFoundError(f"DSM not provided and cache not found at {dsm_path}")

    H, W = dsm.shape

    # Reconstruct transform if not provided
    if transform is None:
        transform = from_bounds(
            *study_area.utm_bounds,
            W,
            H,
        )

    # If DEM is not supplied, approximate ground elevation by lowest neighboring pixels or relative base
    if dem is None:
        dem_tif = config.data.processed_dir / f"{safe_name}_dem_utm_1m.tif"
        if dem_tif.exists():
            with rasterio.open(dem_tif) as src:
                dem = src.read(1)
        else:
            dem = np.full((H, W), np.min(dsm), dtype=np.float32)

    # 1. Compute cell centers in UTM coordinates
    # Row 0 is north, Col 0 is west
    rows, cols = np.indices((H, W))
    xs, ys = rasterio.transform.xy(transform, rows.ravel(), cols.ravel(), offset="center")
    xs = np.array(xs, dtype=np.float32)
    ys = np.array(ys, dtype=np.float32)

    # 2. Pedestrian height elevation (Z = ground_dem + 1.1m)
    ped_height = config.simulation.pedestrian_height_m
    zs = (dem.ravel() + ped_height).astype(np.float32)

    pedestrian_points = np.column_stack([xs, ys, zs])  # Shape: (N, 3)
    N = len(pedestrian_points)

    # 3. Create pedestrian walkable surface mask
    # A point is walkable if it is outside building footprints
    if building_raster is not None:
        pedestrian_mask = (building_raster == 0.0).ravel()
    else:
        # If building raster not passed directly, building footprint = where DSM exceeds ground by > 1.5m
        elevation_diff = dsm - dem
        pedestrian_mask = (elevation_diff < 1.5).ravel()

    n_walkable = int(np.count_nonzero(pedestrian_mask))
    walkable_pct = (n_walkable / N) * 100.0

    logger.info(
        f"Pedestrian grid created: {N:,} total points, {n_walkable:,} walkable outdoor points ({walkable_pct:.1f}%)."
    )

    # 4. Save to binary cache (.npz)
    grid_cache_path = config.data.cache_dir / f"{safe_name}_pedestrian_grid.npz"
    np.savez_compressed(
        grid_cache_path,
        points=pedestrian_points,
        mask=pedestrian_mask,
        shape=np.array([H, W]),
        bounds=np.array(study_area.utm_bounds),
        transform=np.array(transform),
    )
    logger.info(f"Saved pedestrian grid cache to {grid_cache_path}")

    # 5. Export walkable grid metadata JSON for frontend avatar controller
    walkable_json_path = config.data.data_out_dir / "walkable_grid.json"
    walkable_meta = {
        "studyArea": study_area.name,
        "utmBounds": {
            "xmin": study_area.utm_bounds[0],
            "ymin": study_area.utm_bounds[1],
            "xmax": study_area.utm_bounds[2],
            "ymax": study_area.utm_bounds[3],
        },
        "shape": [H, W],
        "resolutionM": study_area.resolution_m,
        "totalPoints": N,
        "walkablePoints": n_walkable,
        "walkablePercent": round(walkable_pct, 1),
    }
    with open(walkable_json_path, "w") as f:
        json.dump(walkable_meta, f, indent=2)
    logger.info(f"Exported avatar walkable navigation metadata to {walkable_json_path}")

    return pedestrian_points, pedestrian_mask, transform, (H, W)


# Convenience alias for the documented public API
create = create_pedestrian_grid
