"""
Physics subpackage: solar position, radiative transfer (shortwave, longwave,
mean radiant temperature), human thermal comfort (UTCI), and the ray-traced
visibility primitives (direct shadow, sky view factor).

Consolidates the former solar/, radiation/, comfort/, and visibility/
subpackages. Public symbols are re-exported here for stable import paths.
"""

from solaraeus.physics.solar_position import SolarPosition, calculate_solar_position
from solaraeus.physics.shortwave import ShortwaveFluxes, compute_shortwave_fluxes
from solaraeus.physics.longwave import (
    LongwaveFluxes, compute_longwave_fluxes, compute_air_emissivity
)
from solaraeus.physics.mean_radiant_temperature import RadiantState, mean_radiant_temperature
from solaraeus.physics.utci import compute_utci, get_thermal_stress_category
from solaraeus.physics.ray_intersection import (
    intersect_ray_aabb, intersect_rays_aabb_batch
)
from solaraeus.physics.mesh_ray_intersection import (
    intersect_ray_triangle, intersect_ray_mesh,
    intersect_rays_mesh_batch, intersect_rays_scene_meshes
)
from solaraeus.physics.shadow import compute_direct_shadow_mask
from solaraeus.physics.mesh_shadow import compute_mesh_direct_shadow_mask
from solaraeus.physics.sky_view_factor import compute_sky_view_factor
from solaraeus.physics.mesh_sky_view_factor import (
    compute_mesh_sky_view_factor,
    rasterize_mesh_to_height_grid,
    rasterize_scene_meshes_to_height_grid,
)

__all__ = [
    "SolarPosition",
    "calculate_solar_position",
    "ShortwaveFluxes",
    "compute_shortwave_fluxes",
    "LongwaveFluxes",
    "compute_longwave_fluxes",
    "compute_air_emissivity",
    "RadiantState",
    "mean_radiant_temperature",
    "compute_utci",
    "get_thermal_stress_category",
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
