"""
Overture Maps Building Footprints & Height Loader.
Downloads building footprints within bounding box and applies height imputation.
"""

import logging
from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)


def load_buildings(
    config: Optional[ProjectConfig] = None,
    study_area: Optional[StudyArea] = None,
    force_download: bool = False,
) -> gpd.GeoDataFrame:
    """
    Downloads or loads cached building footprints from Overture Maps.

    Overture bounding box order: (W, S, E, N) / (min_lon, min_lat, max_lon, max_lat)

    Args:
        config: Project configuration containing data directories.
        study_area: Target study area. Defaults to config.study_area if not provided.
        force_download: If True, re-downloads even if cached parquet exists.

    Returns:
        geopandas.GeoDataFrame with geometry and cleaned 'height_m'.
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area

    config.data.ensure_dirs()

    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")
    cache_path = config.data.raw_dir / f"{safe_name}_buildings.parquet"

    if cache_path.exists() and not force_download:
        logger.info(f"Loading cached Overture buildings from {cache_path}")
        buildings = gpd.read_parquet(cache_path)
    else:
        logger.info(
            f"Downloading Overture buildings for '{study_area.name}' "
            f"bbox={study_area.bbox_overture} (W, S, E, N)..."
        )
        import overturemaps

        # bbox order for overturemaps: (min_lon, min_lat, max_lon, max_lat)
        buildings = overturemaps.geodataframe(
            overture_type="building",
            bbox=study_area.bbox_overture,
        )

        # Save raw download for reproducible runs
        buildings.to_parquet(cache_path)
        logger.info(f"Saved raw Overture buildings to {cache_path}")

    # Ensure geographic CRS is explicitly defined
    if buildings.crs is None:
        buildings = buildings.set_crs(epsg=4326)

    # --- Height Imputation & Quality Checks ---
    height = pd.to_numeric(buildings.get("height"), errors="coerce")
    floors = pd.to_numeric(buildings.get("num_floors"), errors="coerce")

    # Treat zero and negative values as missing
    height = height.where(height > 0)
    height_coverage = (height.notna().mean() * 100.0) if len(buildings) > 0 else 0.0

    # Fallback logic: height -> floors * 3m -> NYC mid-rise default (8.0m)
    buildings["height_m"] = height.fillna(floors * 3.0).fillna(8.0).astype(np.float32)

    logger.info(f"Overture buildings loaded: count={len(buildings)}, CRS={buildings.crs}")
    logger.info(f"Original height coverage: {height_coverage:.1f}%")
    logger.info(f"Imputed height_m summary: min={buildings['height_m'].min():.1f}m, "
                f"mean={buildings['height_m'].mean():.1f}m, max={buildings['height_m'].max():.1f}m")

    return buildings


# Convenience alias for the documented public API
load = load_buildings
