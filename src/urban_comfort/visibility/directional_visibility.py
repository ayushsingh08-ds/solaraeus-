"""
Directional sky visibility and multi-azimuth Sky View Factor (SVF) calculation.
"""

from __future__ import annotations
import math
from typing import Optional, List
import numpy as np

from urban_comfort.geometry.scene import Scene
from urban_comfort.geometry.primitives import Building
from urban_comfort.grid.pedestrian_grid import PedestrianGrid


def compute_sky_view_factor(scene: Scene, grid: PedestrianGrid,
                            num_azimuths: int = 32,
                            max_search_dist_m: float = 120.0,
                            roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes hemispherical Sky View Factor (SVF) in [0.0, 1.0] across the pedestrian grid.
    
    Parameters:
        scene: Scene object with active buildings.
        grid: PedestrianGrid defining calculation receptors.
        num_azimuths: Number of discrete horizon search directions (default 32).
        max_search_dist_m: Maximum search horizon in meters.
        roi_mask: Optional (ny, nx) boolean mask for selective computation.
        
    Returns:
        svf: (ny, nx) float64 array of Sky View Factors in [0.0, 1.0].
    """
    ny, nx = grid.shape
    svf = np.ones((ny, nx), dtype=np.float64)

    active_buildings = scene.get_active_buildings()
    active_meshes = scene.get_active_meshes()
    if not active_buildings and not active_meshes:
        return svf

    if roi_mask is not None:
        eval_indices_y, eval_indices_x = np.where(roi_mask)
    else:
        eval_indices_y, eval_indices_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(eval_indices_y) == 0:
        return svf

    # Receptor coordinates
    x_pts = grid.x_coords[eval_indices_x]
    y_pts = grid.y_coords[eval_indices_y]
    z_ped = grid.z_ped
    n_pts = len(x_pts)

    # Building bounding boxes: (xmin, xmax, ymin, ymax, zmin, zmax)
    bldg_boxes = [b.bounds_3d for b in active_buildings]

    # Pre-rasterize meshes to height grid if meshes are present
    h_mesh_grid: Optional[np.ndarray] = None
    if active_meshes:
        from urban_comfort.visibility.mesh_visibility import rasterize_scene_meshes_to_height_grid
        h_mesh_grid = rasterize_scene_meshes_to_height_grid(scene, grid)

    # Precompute azimuth unit vectors
    azimuths_deg = np.linspace(0.0, 360.0, num_azimuths, endpoint=False)
    cos2_elev_sum = np.zeros(n_pts, dtype=np.float64)

    # Distance sampling steps along ray
    step_dx = max(0.5, grid.dx * 0.5)
    steps = np.arange(step_dx, max_search_dist_m + step_dx, step_dx)

    # Process in batches for cache and memory efficiency
    batch_size = 512
    for b_start in range(0, n_pts, batch_size):
        b_end = min(b_start + batch_size, n_pts)
        bx = x_pts[b_start:b_end]
        by = y_pts[b_start:b_end]
        b_count = b_end - b_start

        batch_cos2 = np.zeros(b_count, dtype=np.float64)

        for az_deg in azimuths_deg:
            az_rad = math.radians(az_deg)
            # Azimuth 0 = North (+Y), 90 = East (+X)
            dir_x = math.sin(az_rad)
            dir_y = math.cos(az_rad)

            # Sample points along ray: shape (b_count, n_steps)
            sample_x = bx[:, None] + dir_x * steps[None, :]
            sample_y = by[:, None] + dir_y * steps[None, :]

            max_tan_elev = np.zeros(b_count, dtype=np.float64)

            # Check AABB obstacle heights
            for bounds in bldg_boxes:
                xmin, xmax, ymin, ymax, _, zmax = bounds
                in_bldg = (
                    (sample_x >= xmin) & (sample_x <= xmax) &
                    (sample_y >= ymin) & (sample_y <= ymax)
                )
                if not np.any(in_bldg):
                    continue

                # Obstacle height above pedestrian receptor
                delta_h = max(0.0, zmax - z_ped)
                tan_elev = np.where(in_bldg, delta_h / steps[None, :], 0.0)
                max_tan_elev = np.maximum(max_tan_elev, np.max(tan_elev, axis=1))

            # Check mesh obstacle heights if meshes are present
            if h_mesh_grid is not None:
                sample_ix = np.clip(
                    np.floor((sample_x - grid.origin_x) / grid.dx).astype(np.int64),
                    0, nx - 1
                )
                sample_iy = np.clip(
                    np.floor((sample_y - grid.origin_y) / grid.dx).astype(np.int64),
                    0, ny - 1
                )
                in_bounds = (
                    (sample_x >= grid.origin_x) &
                    (sample_x <= grid.origin_x + grid.extent_x) &
                    (sample_y >= grid.origin_y) &
                    (sample_y <= grid.origin_y + grid.extent_y)
                )
                sample_h = np.where(in_bounds, h_mesh_grid[sample_iy, sample_ix], 0.0)
                delta_h_mesh = np.maximum(0.0, sample_h - z_ped)
                tan_elev_mesh = delta_h_mesh / steps[None, :]
                max_tan_elev = np.maximum(max_tan_elev, np.max(tan_elev_mesh, axis=1))

            # cos^2(elev) = 1 / (1 + tan^2(elev))
            batch_cos2 += 1.0 / (1.0 + max_tan_elev ** 2)

        batch_svf = batch_cos2 / float(num_azimuths)

        # Inside AABB building footprint check: if receptor is inside a building, SVF = 0.0
        for bounds in bldg_boxes:
            xmin, xmax, ymin, ymax, _, _ = bounds
            inside = (bx >= xmin) & (bx <= xmax) & (by >= ymin) & (by <= ymax)
            batch_svf[inside] = 0.0

        # Inside mesh footprint check: if receptor is inside or under a mesh envelope, SVF = 0.0
        if h_mesh_grid is not None:
            recept_ix = np.clip(
                np.floor((bx - grid.origin_x) / grid.dx).astype(np.int64),
                0, nx - 1
            )
            recept_iy = np.clip(
                np.floor((by - grid.origin_y) / grid.dx).astype(np.int64),
                0, ny - 1
            )
            inside_mesh = h_mesh_grid[recept_iy, recept_ix] > z_ped
            batch_svf[inside_mesh] = 0.0

        svf[eval_indices_y[b_start:b_end], eval_indices_x[b_start:b_end]] = np.clip(batch_svf, 0.0, 1.0)

    return svf
