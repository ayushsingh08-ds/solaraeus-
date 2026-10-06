"""
Directional visibility, horizon obstruction, and Sky View Factor (SVF) for triangular meshes.

Implements discrete multi-azimuth horizon scanning over 3D triangular mesh geometry
using exact top-surface mesh height rasterization, consistent with SOLWEIG/UMEP formulation.
"""

from __future__ import annotations
import math
from typing import Optional, List, Tuple
import numpy as np

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.visibility.mesh_ray_intersection import intersect_rays_mesh_batch


def rasterize_mesh_to_height_grid(mesh: TriangleMesh,
                                  grid: PedestrianGrid,
                                  out_grid: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes the maximum vertical top-surface height field of a TriangleMesh on the pedestrian grid.
    
    Uses downward vertical ray casting from above the mesh bounding box to find the exact
    uppermost envelope elevation at every grid cell center.
    
    Parameters:
        mesh: TriangleMesh instance.
        grid: PedestrianGrid providing spatial coordinates.
        out_grid: Optional (ny, nx) array to accumulate into via np.maximum.
        
    Returns:
        h_grid: (ny, nx) float64 array of obstacle heights in meters (0.0 where no mesh exists).
    """
    if out_grid is None:
        h_grid = np.zeros(grid.shape, dtype=np.float64)
    else:
        h_grid = out_grid

    if not mesh.enabled or mesh.num_triangles == 0:
        return h_grid

    # If the entire mesh is below pedestrian height, it does not obstruct the upper hemisphere
    if mesh.zmax <= grid.z_ped:
        return h_grid

    xmin, xmax, ymin, ymax = mesh.footprint_bounds_2d

    # Determine overlapping cell index bounds
    ix_min = max(0, int(np.floor((xmin - grid.origin_x) / grid.dx)))
    ix_max = min(grid.nx, int(np.ceil((xmax - grid.origin_x) / grid.dx)))
    iy_min = max(0, int(np.floor((ymin - grid.origin_y) / grid.dx)))
    iy_max = min(grid.ny, int(np.ceil((ymax - grid.origin_y) / grid.dx)))

    if ix_min >= ix_max or iy_min >= iy_max:
        return h_grid

    sub_X = grid.X[iy_min:iy_max, ix_min:ix_max]
    sub_Y = grid.Y[iy_min:iy_max, ix_min:ix_max]
    n_sub = sub_X.size

    # Shoot rays downward from above the mesh top
    z_high = mesh.zmax + 1.0
    origins = np.column_stack([
        sub_X.ravel(),
        sub_Y.ravel(),
        np.full(n_sub, z_high, dtype=np.float64)
    ])
    direction = (0.0, 0.0, -1.0)

    hits, t_hits = intersect_rays_mesh_batch(origins, direction, mesh)

    if np.any(hits):
        sub_heights = np.where(hits, z_high - t_hits, 0.0).reshape(sub_X.shape)
        h_grid[iy_min:iy_max, ix_min:ix_max] = np.maximum(
            h_grid[iy_min:iy_max, ix_min:ix_max],
            sub_heights
        )

    return h_grid


def rasterize_scene_meshes_to_height_grid(scene: Scene, grid: PedestrianGrid) -> np.ndarray:
    """
    Rasterizes all active triangular meshes in a Scene onto the pedestrian grid.
    
    Returns:
        h_grid: (ny, nx) float64 array of maximum surface heights across all active meshes.
    """
    h_grid = np.zeros(grid.shape, dtype=np.float64)
    active_meshes = scene.get_active_meshes()
    for mesh in active_meshes:
        rasterize_mesh_to_height_grid(mesh, grid, out_grid=h_grid)
    return h_grid


def compute_mesh_sky_view_factor(scene: Scene,
                                 grid: PedestrianGrid,
                                 num_azimuths: int = 32,
                                 max_search_dist_m: float = 120.0,
                                 roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes hemispherical Sky View Factor (SVF) in [0.0, 1.0] for triangular meshes.
    
    Parameters:
        scene: Scene containing active TriangleMeshes.
        grid: PedestrianGrid defining receptor coordinates.
        num_azimuths: Number of discrete horizon search directions (default 32).
        max_search_dist_m: Maximum horizon search radius in meters.
        roi_mask: Optional (ny, nx) boolean mask for selective evaluation.
        
    Returns:
        svf: (ny, nx) float64 array of Sky View Factors in [0.0, 1.0].
    """
    ny, nx = grid.shape
    svf = np.ones((ny, nx), dtype=np.float64)

    active_meshes = scene.get_active_meshes()
    if not active_meshes:
        return svf

    h_mesh_grid = rasterize_scene_meshes_to_height_grid(scene, grid)

    # Determine receptors to evaluate
    if roi_mask is not None:
        eval_indices_y, eval_indices_x = np.where(roi_mask)
    else:
        eval_indices_y, eval_indices_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(eval_indices_y) == 0:
        return svf

    x_pts = grid.x_coords[eval_indices_x]
    y_pts = grid.y_coords[eval_indices_y]
    z_ped = grid.z_ped
    n_pts = len(x_pts)

    azimuths_deg = np.linspace(0.0, 360.0, num_azimuths, endpoint=False)
    step_dx = max(0.5, grid.dx * 0.5)
    steps = np.arange(step_dx, max_search_dist_m + step_dx, step_dx)

    batch_size = 512
    for b_start in range(0, n_pts, batch_size):
        b_end = min(b_start + batch_size, n_pts)
        bx = x_pts[b_start:b_end]
        by = y_pts[b_start:b_end]
        b_count = b_end - b_start

        batch_cos2 = np.zeros(b_count, dtype=np.float64)

        for az_deg in azimuths_deg:
            az_rad = math.radians(az_deg)
            dir_x = math.sin(az_rad)
            dir_y = math.cos(az_rad)

            sample_x = bx[:, None] + dir_x * steps[None, :]
            sample_y = by[:, None] + dir_y * steps[None, :]

            # Grid index mapping
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
            delta_h = np.maximum(0.0, sample_h - z_ped)
            tan_elev = delta_h / steps[None, :]
            max_tan_elev = np.max(tan_elev, axis=1)

            # cos^2(elev) = 1 / (1 + tan^2(elev))
            batch_cos2 += 1.0 / (1.0 + max_tan_elev ** 2)

        batch_svf = batch_cos2 / float(num_azimuths)

        # Footprint check: receptors inside or under building envelopes have SVF = 0.0
        recept_ix = np.clip(
            np.floor((bx - grid.origin_x) / grid.dx).astype(np.int64),
            0, nx - 1
        )
        recept_iy = np.clip(
            np.floor((by - grid.origin_y) / grid.dx).astype(np.int64),
            0, ny - 1
        )
        inside_footprint = h_mesh_grid[recept_iy, recept_ix] > z_ped
        batch_svf[inside_footprint] = 0.0

        svf[eval_indices_y[b_start:b_end], eval_indices_x[b_start:b_end]] = np.clip(batch_svf, 0.0, 1.0)

    return svf
