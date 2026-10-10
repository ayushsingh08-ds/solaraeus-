"""
Visibility subpackage for ray-primitive intersection, direct shadows, and directional SVF.
"""

from solaraeus.visibility.ray_intersection import (
    intersect_ray_aabb, intersect_rays_aabb_batch
)
from solaraeus.visibility.mesh_ray_intersection import (
    intersect_ray_triangle, intersect_ray_mesh,
    intersect_rays_mesh_batch, intersect_rays_scene_meshes
)
from solaraeus.visibility.shadow import compute_direct_shadow_mask
from solaraeus.visibility.mesh_shadow import compute_mesh_direct_shadow_mask
from solaraeus.visibility.directional_visibility import compute_sky_view_factor
from solaraeus.visibility.mesh_visibility import (
    compute_mesh_sky_view_factor,
    rasterize_mesh_to_height_grid,
    rasterize_scene_meshes_to_height_grid
)

__all__ = [
    "intersect_ray_aabb",
    "intersect_rays_aabb_batch",
    "intersect_ray_triangle",
    "intersect_ray_mesh",
    "intersect_rays_mesh_batch",
    "intersect_rays_scene_meshes",
    "compute_direct_shadow_mask",
    "compute_mesh_direct_shadow_mask",
    "compute_sky_view_factor",
    "compute_mesh_sky_view_factor",
    "rasterize_mesh_to_height_grid",
    "rasterize_scene_meshes_to_height_grid",
]
