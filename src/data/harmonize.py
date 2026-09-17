"""
Harmonization Module — Unifies Multi-Source Geodata onto a 1-meter UTM Grid.
Reprojects building polygons to UTM, rasterizes heights, merges with ground DEM,
and produces the canonical 2.5D Digital Surface Model (DSM).
"""

import logging
from typing import Any, Dict, Optional, Tuple

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from shapely.geometry import box

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)


def build_unified_grid(
    buildings_gdf: gpd.GeoDataFrame,
    dem_array: np.ndarray,
    met_data: Dict[str, Any],
    config: Optional[ProjectConfig] = None,
    study_area: Optional[StudyArea] = None,
) -> Dict[str, Any]:
    """
    Unifies buildings, DEM, and meteorological parameters onto the canonical 1m UTM grid.

    Args:
        buildings_gdf: Building footprints with 'height_m' (EPSG:4326).
        dem_array: 1m ground elevation raster (H, W) in meters.
        met_data: Meteorological scalar inputs from ERA5 or Open-Meteo.
        config: Project configuration.
        study_area: Target study area.

    Returns:
        Dictionary with:
          - 'dsm': (H, W) float32 2.5D Digital Surface Model (ground elevation + building height)
          - 'dem': (H, W) float32 ground elevation
          - 'building_raster': (H, W) float32 building heights
          - 'buildings_table': GeoDataFrame reprojected to UTM, clipped to study area
          - 'met_data': Meteorological dictionary
          - 'metadata': Grid transformation, bounds, and CRS attributes
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area

    config.data.ensure_dirs()

    utm_bounds = study_area.utm_bounds
    resolution_m = study_area.resolution_m
    dst_crs = CRS.from_epsg(study_area.utm_zone)

    # 1. Compute target grid dimensions
    dst_width = int(round((utm_bounds[2] - utm_bounds[0]) / resolution_m))
    dst_height = int(round((utm_bounds[3] - utm_bounds[1]) / resolution_m))

    dst_transform = from_bounds(
        *utm_bounds,
        dst_width,
        dst_height,
    )

    logger.info(
        f"Harmonizing grid: bounds={utm_bounds}, shape=({dst_height}, {dst_width}), "
        f"resolution={resolution_m}m, CRS={dst_crs}"
    )

    # 2. Reproject buildings to target UTM CRS
    if buildings_gdf.crs != dst_crs:
        logger.info(f"Reprojecting buildings from {buildings_gdf.crs} to {dst_crs}...")
        buildings_utm = buildings_gdf.to_crs(dst_crs)
    else:
        buildings_utm = buildings_gdf.copy()

    # 3. Spatial clip/filter to study area bounding box
    bbox_geom = box(*utm_bounds)
    buildings_clipped = buildings_utm[buildings_utm.intersects(bbox_geom)].copy()
    logger.info(f"Retained {len(buildings_clipped)} of {len(buildings_gdf)} buildings intersecting study area.")

    # 4. Rasterize building footprints with their height values
    shapes = [
        (geom, float(height))
        for geom, height in zip(buildings_clipped.geometry, buildings_clipped["height_m"])
        if geom is not None and not geom.is_empty and float(height) > 0
    ]

    building_raster = np.zeros((dst_height, dst_width), dtype=np.float32)
    if shapes:
        rasterize(
            shapes=shapes,
            out=building_raster,
            transform=dst_transform,
            all_touched=False,
            default_value=0.0,
            dtype=np.float32,
        )

    # 5. Form the 2.5D Digital Surface Model (DSM = Ground DEM + Building Heights)
    # Ensure DEM matches grid dimensions
    if dem_array.shape != (dst_height, dst_width):
        logger.warning(
            f"DEM shape {dem_array.shape} does not match grid ({dst_height}, {dst_width}). Resizing..."
        )
        dem_aligned = np.resize(dem_array, (dst_height, dst_width))
    else:
        dem_aligned = dem_array

    dsm = (dem_aligned + building_raster).astype(np.float32)

    # 6. Save cached artifacts for Stage 1 & Stage 2 pipelines
    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")
    dsm_cache_path = config.data.cache_dir / f"{safe_name}_dsm_1m.npy"
    np.save(dsm_cache_path, dsm)

    dsm_tif_path = config.data.processed_dir / f"{safe_name}_dsm_1m.tif"
    with rasterio.open(
        dsm_tif_path,
        "w",
        driver="GTiff",
        height=dst_height,
        width=dst_width,
        count=1,
        dtype=rasterio.float32,
        crs=dst_crs,
        transform=dst_transform,
    ) as dst:
        dst.write(dsm, 1)

    # Also save buildings table in processed parquet
    buildings_table_path = config.data.processed_dir / f"{safe_name}_buildings_utm.parquet"
    buildings_clipped.to_parquet(buildings_table_path)

    metadata = {
        "study_area": study_area.name,
        "utm_bounds": utm_bounds,
        "resolution_m": resolution_m,
        "crs": f"EPSG:{study_area.utm_zone}",
        "transform": dst_transform,
        "shape": (dst_height, dst_width),
        "height_min": float(np.nanmin(dsm)),
        "height_max": float(np.nanmax(dsm)),
        "building_count": len(buildings_clipped),
        "paths": {
            "dsm_npy": str(dsm_cache_path),
            "dsm_tif": str(dsm_tif_path),
            "buildings_parquet": str(buildings_table_path),
        },
    }

    logger.info(
        f"Unified DSM generated: min={metadata['height_min']:.2f}m, "
        f"max={metadata['height_max']:.2f}m, building_pixels={np.count_nonzero(building_raster):,}"
    )

    return {
        "dsm": dsm,
        "dem": dem_aligned,
        "building_raster": building_raster,
        "buildings_table": buildings_clipped,
        "met_data": met_data,
        "metadata": metadata,
    }
