"""
CPU Ray-AABB intersection routines using the Kay-Kajiya slab method.
Supports both single-ray queries and vectorized multi-ray batch intersections.
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np


def intersect_ray_aabb(origin: Tuple[float, float, float],
                       direction: Tuple[float, float, float],
                       box_bounds: Tuple[float, float, float, float, float, float]) -> Optional[float]:
    """
    Computes ray intersection with an Axis-Aligned Bounding Box (AABB).
    
    Parameters:
        origin: (ox, oy, oz) ray starting point.
        direction: (dx, dy, dz) normalized ray propagation vector.
        box_bounds: (xmin, xmax, ymin, ymax, zmin, zmax).
        
    Returns:
        Hit distance t >= 0 if intersection occurs, otherwise None.
    """
    ox, oy, oz = origin
    dx, dy, dz = direction
    xmin, xmax, ymin, ymax, zmin, zmax = box_bounds

    tmin = -float("inf")
    tmax = float("inf")

    # X slab
    if abs(dx) < 1e-12:
        if ox < xmin or ox > xmax:
            return None
    else:
        inv_dx = 1.0 / dx
        tx1 = (xmin - ox) * inv_dx
        tx2 = (xmax - ox) * inv_dx
        tmin = max(tmin, min(tx1, tx2))
        tmax = min(tmax, max(tx1, tx2))

    # Y slab
    if abs(dy) < 1e-12:
        if oy < ymin or oy > ymax:
            return None
    else:
        inv_dy = 1.0 / dy
        ty1 = (ymin - oy) * inv_dy
        ty2 = (ymax - oy) * inv_dy
        tmin = max(tmin, min(ty1, ty2))
        tmax = min(tmax, max(ty1, ty2))

    # Z slab
    if abs(dz) < 1e-12:
        if oz < zmin or oz > zmax:
            return None
    else:
        inv_dz = 1.0 / dz
        tz1 = (zmin - oz) * inv_dz
        tz2 = (zmax - oz) * inv_dz
        tmin = max(tmin, min(tz1, tz2))
        tmax = min(tmax, max(tz1, tz2))

    if tmax >= max(0.0, tmin):
        return max(0.0, tmin)
    return None


def intersect_rays_aabb_batch(origins: np.ndarray,
                              direction: Tuple[float, float, float],
                              box_bounds: Tuple[float, float, float, float, float, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Vectorized batch intersection of N rays along a shared direction against one AABB.
    
    Parameters:
        origins: Shape (N, 3) float64 array of ray origins.
        direction: (dx, dy, dz) unit direction vector.
        box_bounds: (xmin, xmax, ymin, ymax, zmin, zmax).
        
    Returns:
        hits: Shape (N,) boolean mask indicating intersections.
        t_hits: Shape (N,) float64 hit distances (inf for misses).
    """
    n_rays = origins.shape[0]
    xmin, xmax, ymin, ymax, zmin, zmax = box_bounds
    dx, dy, dz = direction

    tmin = np.full(n_rays, -np.inf, dtype=np.float64)
    tmax = np.full(n_rays, np.inf, dtype=np.float64)
    valid = np.ones(n_rays, dtype=bool)

    # X axis
    if abs(dx) < 1e-12:
        valid &= (origins[:, 0] >= xmin) & (origins[:, 0] <= xmax)
    else:
        inv_dx = 1.0 / dx
        tx1 = (xmin - origins[:, 0]) * inv_dx
        tx2 = (xmax - origins[:, 0]) * inv_dx
        tmin = np.maximum(tmin, np.minimum(tx1, tx2))
        tmax = np.minimum(tmax, np.maximum(tx1, tx2))

    # Y axis
    if abs(dy) < 1e-12:
        valid &= (origins[:, 1] >= ymin) & (origins[:, 1] <= ymax)
    else:
        inv_dy = 1.0 / dy
        ty1 = (ymin - origins[:, 1]) * inv_dy
        ty2 = (ymax - origins[:, 1]) * inv_dy
        tmin = np.maximum(tmin, np.minimum(ty1, ty2))
        tmax = np.minimum(tmax, np.maximum(ty1, ty2))

    # Z axis
    if abs(dz) < 1e-12:
        valid &= (origins[:, 2] >= zmin) & (origins[:, 2] <= zmax)
    else:
        inv_dz = 1.0 / dz
        tz1 = (zmin - origins[:, 2]) * inv_dz
        tz2 = (zmax - origins[:, 2]) * inv_dz
        tmin = np.maximum(tmin, np.minimum(tz1, tz2))
        tmax = np.minimum(tmax, np.maximum(tz1, tz2))

    hits = valid & (tmax >= np.maximum(0.0, tmin))
    t_hits = np.where(hits, np.maximum(0.0, tmin), np.inf)

    return hits, t_hits
