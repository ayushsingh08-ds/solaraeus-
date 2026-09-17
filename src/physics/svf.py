"""
Sky View Factor (SVF) Engine — Steyn (1980) Horizon Ray-Marching.
Computes the fraction of visible sky at each grid point / pedestrian coordinate
by finding the maximum horizon elevation angle in n_dir azimuthal directions.
"""

import logging
from typing import Optional, Union
import numpy as np
import rasterio

logger = logging.getLogger(__name__)


def _shift_2d(arr: np.ndarray, dr: int, dc: int, fill_val: float = 0.0) -> np.ndarray:
    """
    Shifts a 2D array by (dr, dc) without periodic boundary wrap-around.
    Positive dr shifts downward (towards higher row indices / South).
    Positive dc shifts rightward (towards higher column indices / East).
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


def compute_svf(
    dsm: np.ndarray,
    transform: Optional[rasterio.Affine] = None,
    points_3d: Optional[np.ndarray] = None,
    n_dir: int = 360,
    max_radius: float = 200.0,
    resolution_m: float = 1.0,
    adaptive_sampling: bool = True,
) -> np.ndarray:
    """
    Computes Sky View Factor (SVF) using Steyn's (1980) formula:
        SVF = (1 / n_dir) * sum_{k=1}^{n_dir} cos^2(beta_{max}(theta_k))
    where beta_{max}(theta_k) is the maximum horizon elevation angle along direction theta_k.

    Args:
        dsm: (H, W) float32 array representing the 2.5D Digital Surface Model.
        transform: Optional rasterio.Affine transform mapping pixel coords to UTM coordinates.
        points_3d: Optional (N, 3) coordinates [X, Y, Z] to sample SVF values at.
        n_dir: Number of azimuth search directions (default 360).
        max_radius: Maximum search distance in meters (default 200m).
        resolution_m: Grid resolution in meters per cell (default 1.0m).
        adaptive_sampling: If True, uses multi-resolution radial stepping to accelerate ray-marching.

    Returns:
        If points_3d is provided: (N,) float32 array of SVF values.
        If points_3d is None: (H, W) float32 raster of SVF values in range [0.0, 1.0].
    """
    dsm_arr = np.asarray(dsm, dtype=np.float32)
    H, W = dsm_arr.shape

    # Construct distance search steps
    max_steps = int(round(max_radius / resolution_m))
    if adaptive_sampling and max_steps > 30:
        steps = list(range(1, min(30, max_steps) + 1, 1))
        if max_steps > 30:
            steps.extend(range(32, min(80, max_steps) + 1, 2))
        if max_steps > 80:
            steps.extend(range(84, max_steps + 1, 4))
    else:
        steps = list(range(1, max_steps + 1, 1))

    # Azimuth angles theta_k in [0, 2*pi)
    angles = np.linspace(0.0, 2.0 * np.pi, n_dir, endpoint=False, dtype=np.float32)

    svf_accum = np.zeros((H, W), dtype=np.float32)

    for theta in angles:
        # Direction unit vector (x is East / col, y is North / -row)
        dx = float(np.cos(theta))
        dy = float(np.sin(theta))

        max_tan_beta = np.zeros((H, W), dtype=np.float32)

        for step in steps:
            dr = -int(round(step * dy))
            dc = int(round(step * dx))

            dist_m = np.sqrt(dr**2 + dc**2) * resolution_m
            if dist_m < 1e-3:
                continue

            shifted_dsm = _shift_2d(dsm_arr, dr, dc, fill_val=0.0)
            delta_z = shifted_dsm - dsm_arr
            tan_beta = delta_z / dist_m

            max_tan_beta = np.maximum(max_tan_beta, tan_beta)

        # Horizon angle beta_max (clamped to >= 0)
        beta_max = np.arctan(np.maximum(0.0, max_tan_beta))
        svf_accum += np.cos(beta_max) ** 2

    svf_raster = np.clip(svf_accum / float(n_dir), 0.0, 1.0).astype(np.float32)

    if points_3d is None:
        return svf_raster

    # Sample SVF at target 3D points
    N = len(points_3d)
    if N == H * W:
        return svf_raster.ravel()

    if transform is not None:
        xs = points_3d[:, 0]
        ys = points_3d[:, 1]
        inv_transform = ~transform
        cols, rows = inv_transform * (xs, ys)
        rows = np.clip(np.round(rows).astype(int), 0, H - 1)
        cols = np.clip(np.round(cols).astype(int), 0, W - 1)
        return svf_raster[rows, cols]
    else:
        # Fallback: assume points_3d indices match flattened grid
        return svf_raster.ravel()[:N]
