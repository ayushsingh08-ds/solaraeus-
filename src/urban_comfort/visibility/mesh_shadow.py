"""
Direct solar shadow mask computation for triangular meshes across pedestrian grids.
"""

from __future__ import annotations
from typing import Optional, List
import numpy as np

from urban_comfort.geometry.scene import Scene
from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.mesh_ray_intersection import intersect_rays_scene_meshes


def compute_mesh_direct_shadow_mask(scene: Scene,
                                    grid: PedestrianGrid,
                                    solar_pos: SolarPosition,
                                    roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes a 2D binary direct solar shadow mask across the pedestrian grid for mesh geometry.
    
    Parameters:
        scene: Scene object containing active meshes.
        grid: PedestrianGrid defining receptor coordinates at z_ped (1.1m).
        solar_pos: SolarPosition containing the normalized unit sun vector.
        roi_mask: Optional (ny, nx) boolean mask for selective computation.
                  Cells outside roi_mask retain default 1.0 (illuminated).
                  
    Returns:
        shadow_mask: (ny, nx) float64 array: 1.0 = illuminated, 0.0 = shaded.
    """
    ny, nx = grid.shape
    shadow_mask = np.ones((ny, nx), dtype=np.float64)

    # Nighttime check: zero solar illumination
    if not solar_pos.is_daylight:
        return np.zeros((ny, nx), dtype=np.float64)

    active_meshes = scene.get_active_meshes()
    if not active_meshes:
        return shadow_mask

    # Determine cells to evaluate
    if roi_mask is not None:
        eval_indices_y, eval_indices_x = np.where(roi_mask)
    else:
        eval_indices_y, eval_indices_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(eval_indices_y) == 0:
        return shadow_mask

    # Extract 3D coordinates for selected receptor points at pedestrian height (z_ped = 1.1m)
    eval_x = grid.x_coords[eval_indices_x]
    eval_y = grid.y_coords[eval_indices_y]
    eval_z = np.full_like(eval_x, grid.z_ped)
    origins = np.column_stack([eval_x, eval_y, eval_z])

    sun_dir = solar_pos.sun_vector

    # Vectorized multi-mesh ray intersection with early-exit occlusion
    is_occluded, _ = intersect_rays_scene_meshes(
        origins, sun_dir, active_meshes,
        early_exit=True,
        cull_backfaces=False  # Two-sided evaluation for opaque envelopes
    )

    # Apply occlusion results: shaded cells set to 0.0
    shadowed_y = eval_indices_y[is_occluded]
    shadowed_x = eval_indices_x[is_occluded]
    shadow_mask[shadowed_y, shadowed_x] = 0.0

    return shadow_mask
