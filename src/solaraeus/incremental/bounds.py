"""
Computable directional visibility bounds, solid-angle SVF bounds,
and conservative Lipschitz / interval propagation to Mean Radiant Temperature (T_mrt).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import math
import numpy as np

from solaraeus.core.geometry import UrbanGrid, EditBoundingBox
from solaraeus.core.solweig import WeatherParameters, SOLWEIGConfig, SOLWEIGState, SIGMA


@dataclass
class CertificateResult:
    """Evaluation output of the incremental certification engine."""
    error_bound: np.ndarray        # B_T(x): Computable upper bound on |T_mrt_inc - T_mrt_full| (K)
    delta_s_max: np.ndarray        # Maximum possible flux perturbation (W / m^2)
    delta_svf_max: np.ndarray      # Maximum possible SVF perturbation in [0, 1]
    in_shadow_frustum: np.ndarray  # Boolean mask: cells within directional shadow frustum
    dirty_mask: np.ndarray         # Boolean mask: cells where B_T(x) > tolerance


def compute_shadow_frustum_mask(grid: UrbanGrid, bbox: EditBoundingBox,
                                weather: WeatherParameters) -> np.ndarray:
    """
    Computes a conservative 2D ground-plane mask of the shadow frustum cast by the edit volume.
    Any cell outside this mask is provably guaranteed to have ZERO direct shadow change.
    """
    ny, nx = grid.shape
    dx = grid.dx
    z_ped = grid.z_ped

    alt_rad = math.radians(weather.sun_altitude_deg)
    if alt_rad <= 0.0:
        return np.ones((ny, nx), dtype=bool)

    az_rad = math.radians(weather.sun_azimuth_deg)

    # Maximum height of obstacle that could cast shadow
    h_max = max(bbox.h_before_max, bbox.h_after_max)
    if h_max <= z_ped:
        # Edit is below pedestrian level; direct shadow cannot reach ground
        frustum = np.zeros((ny, nx), dtype=bool)
        frustum[bbox.ymin:bbox.ymax + 1, bbox.xmin:bbox.xmax + 1] = True
        return frustum

    # Maximum shadow length from obstacle top to pedestrian level
    max_shadow_len_m = (h_max - z_ped) / math.tan(alt_rad)
    max_shadow_steps = int(math.ceil(max_shadow_len_m / dx)) + 2  # +2 cells safety margin

    # Obstacle shadows ground in direction OPPOSITE to sun vector:
    # Sun direction in matrix coords: dir_r = -cos(az), dir_c = sin(az)
    # Shadow falls towards: shadow_dir_r = +cos(az), shadow_dir_c = -sin(az)
    shadow_step_r = math.cos(az_rad)
    shadow_step_c = -math.sin(az_rad)

    frustum = np.zeros((ny, nx), dtype=bool)

    # Footprint of edit is always included
    frustum[bbox.ymin:bbox.ymax + 1, bbox.xmin:bbox.xmax + 1] = True

    # Vectorized Minkowski sweep along shadow trajectory
    steps = np.arange(0, max_shadow_steps + 1)
    offset_r = np.rint(steps * shadow_step_r).astype(np.int64)
    offset_c = np.rint(steps * shadow_step_c).astype(np.int64)

    # Apply bounding envelope of footprint + offsets
    y_indices, x_indices = np.where(frustum)
    for dr, dc in zip(offset_r, offset_c):
        shifted_y = np.clip(y_indices + dr, 0, ny - 1)
        shifted_x = np.clip(x_indices + dc, 0, nx - 1)
        frustum[shifted_y, shifted_x] = True

    return frustum


def compute_svf_decay_bound(grid: UrbanGrid, bbox: EditBoundingBox,
                            config: SOLWEIGConfig) -> np.ndarray:
    """
    Computes a conservative upper bound on |Delta SVF(x)| as a function of Euclidean
    distance from the edit bounding box.
    Guarantees: Delta SVF(x) <= min(1.0, W_proj * Delta_h / (2 * pi * r^2))
    Beyond max_search_dist_m, Delta SVF(x) is identically 0.
    """
    ny, nx = grid.shape
    dx = grid.dx

    if bbox.delta_h_max <= 1e-6:
        return np.zeros((ny, nx), dtype=np.float64)

    # Grid cell coordinates in meters
    y_coords = np.arange(ny, dtype=np.float64) * dx
    x_coords = np.arange(nx, dtype=np.float64) * dx
    X, Y = np.meshgrid(x_coords, y_coords)

    # Bounding box physical extent in meters
    box_x_min = bbox.xmin * dx
    box_x_max = bbox.xmax * dx
    box_y_min = bbox.ymin * dx
    box_y_max = bbox.ymax * dx

    # Distance to axis-aligned rectangle (0 inside, Euclidean distance outside)
    dx_dist = np.maximum(0.0, np.maximum(box_x_min - X, X - box_x_max))
    dy_dist = np.maximum(0.0, np.maximum(box_y_min - Y, Y - box_y_max))
    dist = np.hypot(dx_dist, dy_dist)

    # Effective projected width of the edit volume
    # Diagonal footprint width ensures conservative solid angle bound for all azimuths
    w_proj = math.sqrt(2.0) * bbox.width_m
    delta_h = bbox.delta_h_max

    # Solid angle bound: Delta_Omega <= min(2*pi, (w_proj * delta_h) / r^2)
    # For r close to 0 (inside or adjacent to footprint), bound is 1.0
    r_effective = np.maximum(dx, dist)
    svf_bound = (w_proj * delta_h) / (2.0 * math.pi * (r_effective ** 2))

    # Cells inside or touching footprint can have SVF change up to 1.0
    svf_bound[dist < dx] = 1.0
    svf_bound = np.clip(svf_bound, 0.0, 1.0)

    # Hard zero cutoff beyond reference solver's maximum horizon search distance
    # Add box radius to cutoff for strict safety
    box_radius = 0.5 * math.hypot(box_x_max - box_x_min, box_y_max - box_y_min)
    svf_bound[dist > (config.max_search_dist_m + box_radius)] = 0.0

    return svf_bound


def evaluate_certificate(grid: UrbanGrid, cached_state: SOLWEIGState,
                         bbox: EditBoundingBox, weather: WeatherParameters,
                         config: SOLWEIGConfig, tolerance_k: float) -> CertificateResult:
    """
    Evaluates the certificate B_T(x) across the entire domain in O(1) operations per cell.
    Identifies cells where B_T(x) <= tolerance_k for guaranteed safe reuse.
    """
    ny, nx = grid.shape

    # 1. Shadow Frustum mask
    in_frustum = compute_shadow_frustum_mask(grid, bbox, weather)

    # 2. SVF decay bound
    delta_svf_max = compute_svf_decay_bound(grid, bbox, config)

    # 3. Direct beam maximum potential perturbation
    alt_rad = math.radians(weather.sun_altitude_deg)
    az_rad = math.radians(weather.sun_azimuth_deg)
    sin_alt = math.sin(alt_rad)
    cos_alt = math.cos(alt_rad)

    s_north = cos_alt * math.cos(az_rad)
    s_east = cos_alt * math.sin(az_rad)
    cos_side_max = max(0.0, abs(s_north), abs(s_east))

    # Direct shortwave flux received by standing human in full sunlight
    k_dir_max_step = weather.i_dir * (
        config.f_up * sin_alt +
        config.f_side * cos_side_max +
        config.f_down * weather.albedo_ground * sin_alt
    )

    delta_k_dir = np.where(in_frustum, k_dir_max_step, 0.0)

    # 4. Diffuse and longwave flux bounds from SVF perturbation
    # Diffuse shortwave sensitivity
    c_diff = (
        config.f_up * weather.d_diff +
        config.f_side * 4.0 * (0.5 * weather.d_diff + 0.5 * weather.albedo_wall * (weather.i_dir + weather.d_diff)) +
        config.f_down * weather.albedo_ground * weather.d_diff
    )
    delta_k_diff = c_diff * delta_svf_max

    # Longwave sensitivity
    l_sky = weather.emissivity_air * SIGMA * (weather.t_air_k ** 4)
    l_wall = weather.emissivity_wall * SIGMA * (weather.t_wall_k ** 4)
    l_contrast = abs(l_sky - l_wall)

    c_long = (config.f_up + 2.0 * config.f_side) * l_contrast
    delta_l_long = c_long * delta_svf_max

    # Total absorbed flux bound: Delta S_max
    delta_s_max = config.a_k * (delta_k_dir + delta_k_diff) + config.a_l * delta_l_long

    # 5. Exact Concave Interval Stefan-Boltzmann propagation:
    # B_T(x) = (S_cached / sigma)^0.25 - (max(1.0, S_cached - delta_s_max) / sigma)^0.25
    s_cached = np.maximum(10.0, cached_state.s_str)
    s_lower = np.maximum(1.0, s_cached - delta_s_max)

    t_cached = np.power(s_cached / SIGMA, 0.25)
    t_lower = np.power(s_lower / SIGMA, 0.25)
    b_t = t_cached - t_lower  # Guaranteed conservative upper bound in Kelvin

    # Dirty cells: where bound exceeds tolerance
    dirty_mask = b_t > float(tolerance_k)

    return CertificateResult(
        error_bound=b_t,
        delta_s_max=delta_s_max,
        delta_svf_max=delta_svf_max,
        in_shadow_frustum=in_frustum,
        dirty_mask=dirty_mask
    )
