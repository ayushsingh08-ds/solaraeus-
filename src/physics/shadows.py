"""
2.5D Raster Shadow Engine — Direct Solar Radiation Obstacle Occlusion.
Projects obstacle shadow heights along the sun azimuth vector across the Digital Surface Model.
Determines whether ground and pedestrian evaluation points are sunlit or shaded.
"""

import logging
import math
from typing import Optional
import numpy as np
import rasterio

logger = logging.getLogger(__name__)


def _shift_2d(arr: np.ndarray, dr: int, dc: int, fill_val: float = 0.0) -> np.ndarray:
    """
    Shifts a 2D array by (dr, dc) without periodic boundary wrap-around.
    Positive dr shifts towards higher row indices (South / Down).
    Positive dc shifts towards higher column indices (East / Right).
    """
    H, W = arr.shape
    out = np.full((H, W), fill_val, dtype=arr.dtype)

    src_r0, src_r1 = max(0, dr), min(H, H + dr)
    dst_r0, dst_r1 = max(0, -dr), min(H, H - dr)
    src_c0, src_c1 = max(0, dc), min(W, W + dc)
    dst_c0, dst_c1 = max(0, -dc), min(W, W - dc)

    if src_r1 > src_r0 and src_c1 > src_c0:
        out[dst_r0:dst_r1, dst_c0:dst_c1] = arr[src_r0:src_r1, src_c0:src_c1]

    return out


def cast_shadows(
    dsm: np.ndarray,
    transform: Optional[rasterio.Affine] = None,
    alt_rad: float = 1.0,
    az_rad: float = 2.4,
    max_distance: float = 200.0,
    resolution_m: float = 1.0,
    points_3d: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Computes direct sun illumination mask using 2.5D shadow projection.

    Args:
        dsm: (H, W) float32 array representing the 2.5D Digital Surface Model.
        transform: Optional rasterio.Affine transform mapping pixel coords to UTM coordinates.
        alt_rad: Solar altitude angle in radians above horizon (0 to pi/2).
        az_rad: Solar azimuth angle in radians. Supports both standard compass (0=N, 90=E, 180=S, 270=W)
                and the README.md convention (~135-145° for afternoon southwest sun).
        max_distance: Maximum distance to search for shadow-casting obstacles in meters (default 200m).
        resolution_m: Grid resolution in meters per cell (default 1.0m).
        points_3d: Optional (N, 3) coordinates [X, Y, Z] to evaluate illumination at.

    Returns:
        If points_3d is provided: (N,) bool array (True = Sunlit, False = Shaded).
        If points_3d is None: (H, W) bool raster (True = Sunlit, False = Shaded).
    """
    dsm_arr = np.asarray(dsm, dtype=np.float32)
    H, W = dsm_arr.shape

    # 1. Edge Case: Sun at or below horizon
    if alt_rad <= 0.0:
        logger.info("Sun is at or below horizon (alt <= 0). All cells shaded.")
        if points_3d is not None:
            return np.zeros(len(points_3d), dtype=bool)
        return np.zeros((H, W), dtype=bool)

    # 2. Edge Case: Sun directly overhead (zenith, altitude ~ 90 deg)
    if alt_rad >= (math.pi / 2.0 - 1e-4):
        logger.info("Sun is at zenith (alt = 90 deg). No lateral shadows cast.")
        if points_3d is not None:
            return np.ones(len(points_3d), dtype=bool)
        return np.ones((H, W), dtype=bool)

    # 3. Resolve vector towards sun
    az_deg = math.degrees(az_rad) % 360.0

    # If azimuth is given in ~130°-155° range representing afternoon South-Southwest,
    # map to standard clockwise compass angle (South-West: ~205°-230°)
    if 130.0 <= az_deg <= 155.0:
        compass_deg = 360.0 - az_deg
    else:
        compass_deg = az_deg

    compass_rad = math.radians(compass_deg)

    # Unit vector pointing towards the sun:
    # Compass: 0=North (-row), 90=East (+col), 180=South (+row), 270=West (-col)
    dir_col_sun = math.sin(compass_rad)
    dir_row_sun = -math.cos(compass_rad)

    tan_alt = math.tan(alt_rad)
    max_steps = int(round(max_distance / resolution_m))

    # Multi-resolution step array along shadow ray
    if max_steps > 30:
        steps = list(range(1, min(30, max_steps) + 1, 1))
        steps.extend(range(32, min(80, max_steps) + 1, 2))
        if max_steps > 80:
            steps.extend(range(84, max_steps + 1, 4))
    else:
        steps = list(range(1, max_steps + 1, 1))

    # Track maximum obstacle shadow elevation reaching each grid cell
    max_shadow_height = np.full((H, W), -1e5, dtype=np.float32)

    for step in steps:
        dr = int(round(step * dir_row_sun))
        dc = int(round(step * dir_col_sun))

        dist_m = math.sqrt(dr**2 + dc**2) * resolution_m
        if dist_m < 1e-3:
            continue

        # Obstacle elevation at distance dist_m in sun direction
        obstacle_dsm = _shift_2d(dsm_arr, dr, dc, fill_val=0.0)

        # Shadow height projected from obstacle to target location
        ray_shadow_height = obstacle_dsm - (dist_m * tan_alt)
        max_shadow_height = np.maximum(max_shadow_height, ray_shadow_height)

    # A cell is sunlit if its surface elevation meets or exceeds the shadow ray height
    sunlit_raster = dsm_arr >= (max_shadow_height - 1e-3)

    if points_3d is None:
        return sunlit_raster

    N = len(points_3d)
    if N == H * W:
        return sunlit_raster.ravel()

    if transform is not None:
        xs = points_3d[:, 0]
        ys = points_3d[:, 1]
        zs = points_3d[:, 2]
        inv_transform = ~transform
        cols, rows = inv_transform * (xs, ys)
        rows = np.clip(np.round(rows).astype(int), 0, H - 1)
        cols = np.clip(np.round(cols).astype(int), 0, W - 1)
        # Check against pedestrian Z height
        return zs >= (max_shadow_height[rows, cols] - 1e-3)
    else:
        return sunlit_raster.ravel()[:N]
