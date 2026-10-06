"""
Direct solar shadow mask computation across pedestrian grids.
"""

from __future__ import annotations
from typing import Optional, List
import numpy as np

from urban_comfort.geometry.scene import Scene
from urban_comfort.geometry.primitives import Building
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.ray_intersection import intersect_rays_aabb_batch


def compute_direct_shadow_mask(scene: Scene, grid: PedestrianGrid,
                               solar_pos: SolarPosition,
                               roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes a 2D binary shadow mask across the pedestrian grid.
    
    Parameters:
        scene: Scene object containing active buildings.
        grid: PedestrianGrid defining receptor coordinates.
        solar_pos: SolarPosition containing the unit sun vector.
        roi_mask: Optional (ny, nx) boolean mask. If provided, only cells
                  where roi_mask is True are recomputed; other cells default to 1.0.
                  
    Returns:
        shadow_mask: (ny, nx) float64 array, 1.0 = illuminated, 0.0 = shaded.
    """
    ny, nx = grid.shape
    shadow_mask = np.ones((ny, nx), dtype=np.float64)

    # Nighttime condition: zero solar illumination
    if not solar_pos.is_daylight:
        return np.zeros((ny, nx), dtype=np.float64)

    active_buildings = scene.get_active_buildings()
    active_meshes = scene.get_active_meshes() if hasattr(scene, "get_active_meshes") else []
    if not active_buildings and not active_meshes:
        return shadow_mask

    # Determine cells to evaluate
    if roi_mask is not None:
        eval_indices_y, eval_indices_x = np.where(roi_mask)
    else:
        eval_indices_y, eval_indices_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(eval_indices_y) == 0:
        return shadow_mask

    # Extract 3D coordinates for selected receptor points
    eval_x = grid.x_coords[eval_indices_x]
    eval_y = grid.y_coords[eval_indices_y]
    eval_z = np.full_like(eval_x, grid.z_ped)
    origins = np.column_stack([eval_x, eval_y, eval_z])

    sun_dir = solar_pos.sun_vector
    is_occluded = np.zeros(len(origins), dtype=bool)

    # Test occlusion against each building
    for bldg in active_buildings:
        bounds = bldg.bounds_3d
        # Ray test towards sun
        hits, _ = intersect_rays_aabb_batch(origins, sun_dir, bounds)
        is_occluded |= hits

        # Also check if pedestrian point falls directly within building footprint
        inside_footprint = (
            (origins[:, 0] >= bounds[0]) & (origins[:, 0] <= bounds[1]) &
            (origins[:, 1] >= bounds[2]) & (origins[:, 1] <= bounds[3]) &
            (origins[:, 2] <= bounds[5])
        )
        is_occluded |= inside_footprint

    # Test occlusion against triangular meshes
    if active_meshes:
        from urban_comfort.visibility.mesh_ray_intersection import intersect_rays_scene_meshes
        mesh_hits, _ = intersect_rays_scene_meshes(origins, sun_dir, active_meshes, early_exit=True)
        is_occluded |= mesh_hits

    # Apply occlusion results
    shadowed_y = eval_indices_y[is_occluded]
    shadowed_x = eval_indices_x[is_occluded]
    shadow_mask[shadowed_y, shadowed_x] = 0.0

    return shadow_mask
