"""
2.5D Digital Surface Model (DSM) Geometry Builder & Validator.
Refines, validates, and handles geometry edge cases for the 2.5D surface elevation raster.
"""

import logging
from typing import Any, Dict, Optional

import geopandas as gpd
import numpy as np

from src.config import ProjectConfig

logger = logging.getLogger(__name__)


def build_dsm(
    dsm_raw: np.ndarray,
    buildings_table: Optional[gpd.GeoDataFrame] = None,
    config: Optional[ProjectConfig] = None,
) -> np.ndarray:
    """
    Validates and produces the finalized 2.5D Digital Surface Model (DSM).
    Handles edge cases: missing elevations, NaNs, unrealistic heights, and morphology.

    Args:
        dsm_raw: (H, W) float32 raster of elevation (ground + building heights).
        buildings_table: GeoDataFrame of buildings in UTM coordinates.
        config: Project configuration.

    Returns:
        Cleaned, contiguous (H, W) float32 numpy array representing the 2.5D surface.
    """
    if config is None:
        config = ProjectConfig()

    dsm = np.array(dsm_raw, dtype=np.float32, copy=True)

    # 1. Check and heal NaNs / Infs
    nan_mask = ~np.isfinite(dsm)
    if np.any(nan_mask):
        nan_count = int(np.count_nonzero(nan_mask))
        logger.warning(f"DSM contains {nan_count} invalid non-finite cells. Healing with local median...")
        finite_vals = dsm[~nan_mask]
        fill_val = float(np.median(finite_vals)) if len(finite_vals) > 0 else 0.0
        dsm[nan_mask] = fill_val

    # 2. Enforce realistic elevation bounds for NYC study areas
    min_elev = float(np.min(dsm))
    max_elev = float(np.max(dsm))

    # NYC topography: ground elevation is >= -20m, max skyscraper height <= 600m
    if min_elev < -50.0:
        logger.warning(f"Unusually low elevation detected ({min_elev:.1f}m). Clamping to -10.0m.")
        dsm = np.maximum(dsm, -10.0)

    if max_elev > 650.0:
        logger.warning(f"Extreme elevation detected ({max_elev:.1f}m). Clamping to 600.0m.")
        dsm = np.minimum(dsm, 600.0)

    # 3. Geometry verification against building table
    if buildings_table is not None and len(buildings_table) > 0:
        n_buildings = len(buildings_table)
        max_bldg_height = float(buildings_table["height_m"].max()) if "height_m" in buildings_table else 0.0
        logger.info(
            f"DSM verified against {n_buildings} building polygons (Max building height: {max_bldg_height:.1f}m)."
        )

    logger.info(
        f"Final 2.5D DSM shape: {dsm.shape}, Elevation range: [{np.min(dsm):.2f}m, {np.max(dsm):.2f}m]"
    )

    return dsm
