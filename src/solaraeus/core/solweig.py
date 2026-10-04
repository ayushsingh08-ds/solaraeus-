"""
Pinned, deterministic CPU reference solver for single-timestep SOLWEIG calculations.
Implements exact 2.5D shadow-marching, multi-azimuth Sky View Factor (SVF),
6-directional radiant flux integration, and Mean Radiant Temperature (T_mrt).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional
import math
import numpy as np

from solaraeus.core.geometry import UrbanGrid

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant (W / m^2 K^4)


@dataclass(frozen=True)
class WeatherParameters:
    """Fixed atmospheric and thermal boundary conditions for a single timestep."""
    sun_altitude_deg: float = 45.0
    sun_azimuth_deg: float = 180.0  # 0 = North, 90 = East, 180 = South, 270 = West
    i_dir: float = 700.0            # Direct normal irradiance (W / m^2)
    d_diff: float = 150.0           # Diffuse horizontal irradiance (W / m^2)
    t_air_k: float = 300.15         # Air temperature (27 C)
    t_wall_k: float = 305.15        # Wall surface temperature (32 C)
    t_ground_k: float = 308.15      # Ground surface temperature (35 C)
    albedo_wall: float = 0.20
    albedo_ground: float = 0.15
    emissivity_air: float = 0.82
    emissivity_wall: float = 0.90
    emissivity_ground: float = 0.95


@dataclass(frozen=True)
class SOLWEIGConfig:
    """Numerical parameters and human cylinder weighting factors."""
    num_azimuth_svf: int = 32
    max_search_dist_m: float = 120.0
    a_k: float = 0.70               # Human shortwave absorption coefficient
    a_l: float = 0.97               # Human longwave absorption coefficient
    f_up: float = 0.06              # Weighting factor for upward surface
    f_down: float = 0.06            # Weighting factor for downward surface
    f_side: float = 0.22            # Weighting factor for each of 4 cardinal sides


@dataclass
class SOLWEIGState:
    """Full simulation state at ground/pedestrian level."""
    shadow_mask: np.ndarray         # Shape (ny, nx), float: 1.0 = lit, 0.0 = shadow
    svf: np.ndarray                 # Shape (ny, nx), float in [0.0, 1.0]
    s_str: np.ndarray               # Shape (ny, nx), total absorbed flux (W / m^2)
    t_mrt: np.ndarray               # Shape (ny, nx), Mean Radiant Temp in Celsius
    k_dir: np.ndarray               # Shortwave direct absorbed component
    k_diff: np.ndarray              # Shortwave diffuse + reflected absorbed component
    l_long: np.ndarray              # Longwave absorbed component


def compute_shadow_mask(grid: UrbanGrid, sun_altitude_deg: float, sun_azimuth_deg: float,
                        roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes direct beam line-of-sight visibility (1.0 = illuminated, 0.0 = shadowed)
    using vectorized heightfield horizon ray-stepping along the sun vector.
    """
    ny, nx = grid.shape
    dx = grid.dx
    z_ped = grid.z_ped
    heights = grid.heights

    alt_rad = math.radians(sun_altitude_deg)
    if alt_rad <= 0.0:
        return np.zeros((ny, nx), dtype=np.float64)

    az_rad = math.radians(sun_azimuth_deg)
    tan_alt = math.tan(alt_rad)

    # Step vector along ground pointing towards sun
    # Azimuth 0 = North (+Y in matrix if Y=0 is South, or -Y if row 0 is North).
    # Standard GIS convention: Row 0 is North (top), row ny-1 is South (bottom).
    # Col 0 is West (left), col nx-1 is East (right).
    # Sun azimuth measured clockwise from North:
    # North (0 deg): step_r = -1 (towards row 0), step_c = 0
    # East (90 deg): step_r = 0, step_c = +1
    # South (180 deg): step_r = +1, step_c = 0
    # West (270 deg): step_r = 0, step_c = -1
    dir_r = -math.cos(az_rad)
    dir_c = math.sin(az_rad)

    shadow_mask = np.ones((ny, nx), dtype=np.float64)
    # Maximum ray steps across domain
    diag_dist = math.hypot(ny, nx) * dx
    max_steps = int(math.ceil(diag_dist / dx))

    # Determine cells to compute
    if roi_mask is not None:
        calc_y, calc_x = np.where(roi_mask)
    else:
        calc_y, calc_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(calc_y) == 0:
        return shadow_mask

    # Step distances in meters
    step_indices = np.arange(1, max_steps + 1, dtype=np.float64)
    step_dists_m = step_indices * dx
    step_r = step_indices * (dir_r * dx) / dx
    step_c = step_indices * (dir_c * dx) / dx

    # Vectorized check per row or chunks for memory efficiency
    batch_size = 2048
    for start in range(0, len(calc_y), batch_size):
        end = min(start + batch_size, len(calc_y))
        by = calc_y[start:end]
        bx = calc_x[start:end]

        # For each point, trace along ray
        # Array of sampled coordinates: (N_pts, N_steps)
        sample_r = np.rint(by[:, None] + step_r[None, :]).astype(np.int64)
        sample_c = np.rint(bx[:, None] + step_c[None, :]).astype(np.int64)

        # Check bounds
        valid = (sample_r >= 0) & (sample_r < ny) & (sample_c >= 0) & (sample_c < nx)

        # Obstacle height required to block ray: z_ped + dist * tan(alt)
        ray_heights = z_ped + step_dists_m[None, :] * tan_alt

        # Extract terrain heights
        # Replace out-of-bound coords with (0, 0)
        safe_r = np.where(valid, sample_r, 0)
        safe_c = np.where(valid, sample_c, 0)
        terrain_h = heights[safe_r, safe_c]

        # Obstruction condition
        blocked = valid & (terrain_h > ray_heights)
        is_shadowed = np.any(blocked, axis=1)

        shadow_mask[by[is_shadowed], bx[is_shadowed]] = 0.0

    return shadow_mask


def compute_sky_view_factor(grid: UrbanGrid, config: SOLWEIGConfig,
                            roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes hemispherical Sky View Factor (SVF) via multi-azimuth horizon search.
    svf in [0.0, 1.0], where 1.0 = unobstructed open sky.
    """
    ny, nx = grid.shape
    dx = grid.dx
    z_ped = grid.z_ped
    heights = grid.heights

    num_azi = config.num_azimuth_svf
    max_dist_m = config.max_search_dist_m
    max_steps = max(1, int(math.ceil(max_dist_m / dx)))

    azimuths_deg = np.linspace(0.0, 360.0, num_azi, endpoint=False)

    svf = np.ones((ny, nx), dtype=np.float64)

    if roi_mask is not None:
        calc_y, calc_x = np.where(roi_mask)
    else:
        calc_y, calc_x = np.where(np.ones((ny, nx), dtype=bool))

    if len(calc_y) == 0:
        return svf

    step_indices = np.arange(1, max_steps + 1, dtype=np.float64)
    step_dists_m = step_indices * dx

    batch_size = 1024
    for start in range(0, len(calc_y), batch_size):
        end = min(start + batch_size, len(calc_y))
        by = calc_y[start:end]
        bx = calc_x[start:end]
        n_pts = end - start

        # Sum of cos^2(horizon_elev) across azimuths
        cos2_sum = np.zeros(n_pts, dtype=np.float64)

        for az_deg in azimuths_deg:
            az_rad = math.radians(az_deg)
            dir_r = -math.cos(az_rad)
            dir_c = math.sin(az_rad)

            step_r = np.rint(dir_r * step_indices).astype(np.int64)
            step_c = np.rint(dir_c * step_indices).astype(np.int64)

            sample_r = by[:, None] + step_r[None, :]
            sample_c = bx[:, None] + step_c[None, :]

            valid = (sample_r >= 0) & (sample_r < ny) & (sample_c >= 0) & (sample_c < nx)
            safe_r = np.where(valid, sample_r, 0)
            safe_c = np.where(valid, sample_c, 0)

            obstacle_h = heights[safe_r, safe_c] - z_ped
            # Tan of elevation angle
            tan_elev = np.where(valid, obstacle_h / step_dists_m[None, :], 0.0)
            max_tan_elev = np.maximum(0.0, np.max(tan_elev, axis=1))

            # cos^2(elev) = 1 / (1 + tan^2(elev))
            cos2_sum += 1.0 / (1.0 + max_tan_elev ** 2)

        svf_batch = cos2_sum / float(num_azi)
        svf[by, bx] = np.clip(svf_batch, 0.0, 1.0)

    return svf


def solve_fluxes_and_tmrt(grid: UrbanGrid, shadow_mask: np.ndarray, svf: np.ndarray,
                          weather: WeatherParameters, config: SOLWEIGConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes 6-directional fluxes and T_mrt given shadow mask and SVF.
    Returns: (s_str, t_mrt, k_dir, k_diff, l_long)
    """
    alt_rad = math.radians(weather.sun_altitude_deg)
    az_rad = math.radians(weather.sun_azimuth_deg)

    sin_alt = math.sin(alt_rad)
    cos_alt = math.cos(alt_rad)

    # Unit vector towards sun in (East, North, Up) coordinates:
    # Azimuth from North clockwise: sun_east = sin(az), sun_north = cos(az)
    s_north = cos_alt * math.cos(az_rad)
    s_east = cos_alt * math.sin(az_rad)
    s_south = -s_north
    s_west = -s_east

    # Directional incidence cosines for side sensors
    cos_north = max(0.0, s_north)
    cos_south = max(0.0, s_south)
    cos_east = max(0.0, s_east)
    cos_west = max(0.0, s_west)

    # 1. Shortwave Direct Flux on Human Surfaces:
    # Top sensor (f_up = 0.06): hits top horizontal surface
    k_dir_up = weather.i_dir * sin_alt * shadow_mask
    # Bottom sensor (f_down = 0.06): 0
    k_dir_down = np.zeros_like(shadow_mask)
    # Side vertical sensors (f_side = 0.22 each)
    k_dir_n = weather.i_dir * cos_north * shadow_mask
    k_dir_s = weather.i_dir * cos_south * shadow_mask
    k_dir_e = weather.i_dir * cos_east * shadow_mask
    k_dir_w = weather.i_dir * cos_west * shadow_mask

    k_dir_total = (config.f_up * k_dir_up +
                   config.f_down * k_dir_down +
                   config.f_side * (k_dir_n + k_dir_s + k_dir_e + k_dir_w))

    # 2. Shortwave Diffuse and Reflected:
    # Sky diffuse onto top surface
    k_diff_up = weather.d_diff * svf
    # Diffuse onto side surfaces (roughly half the hemisphere visible)
    k_diff_side = weather.d_diff * 0.5 * svf

    # Reflected from ground (hits down sensor)
    # Ground global solar radiation = I_dir * sin_alt * shadow + D_diff * svf
    g_ground = weather.i_dir * sin_alt * shadow_mask + weather.d_diff * svf
    k_refl_ground = weather.albedo_ground * g_ground
    k_down = k_refl_ground

    # Reflected from walls (hits side surfaces)
    # Wall view factor = (1 - svf)
    g_wall_approx = (weather.i_dir + weather.d_diff) * 0.5
    k_refl_wall = weather.albedo_wall * (1.0 - svf) * g_wall_approx

    k_diff_total = (config.f_up * k_diff_up +
                    config.f_down * k_down +
                    config.f_side * 4.0 * (k_diff_side + k_refl_wall))

    # 3. Longwave Radiation:
    l_sky = weather.emissivity_air * SIGMA * (weather.t_air_k ** 4)
    l_wall = weather.emissivity_wall * SIGMA * (weather.t_wall_k ** 4)
    l_ground = weather.emissivity_ground * SIGMA * (weather.t_ground_k ** 4)

    l_up = svf * l_sky + (1.0 - svf) * l_wall
    l_down = np.full_like(svf, l_ground)
    l_side = 0.5 * svf * l_sky + (1.0 - 0.5 * svf) * l_wall

    l_total = (config.f_up * l_up +
               config.f_down * l_down +
               config.f_side * 4.0 * l_side)

    # 4. Total Absorbed Radiant Flux Density S_str:
    s_str = config.a_k * (k_dir_total + k_diff_total) + config.a_l * l_total

    # 5. Stefan-Boltzmann to T_mrt:
    # T_mrt = (S_str / SIGMA)^0.25 - 273.15
    t_mrt_k = np.power(s_str / SIGMA, 0.25)
    t_mrt_c = t_mrt_k - 273.15

    return s_str, t_mrt_c, k_dir_total, k_diff_total, l_total


class ReferenceSOLWEIGSolver:
    """
    Deterministic reference solver for single-timestep SOLWEIG.
    """

    def __init__(self, weather: Optional[WeatherParameters] = None,
                 config: Optional[SOLWEIGConfig] = None):
        self.weather = weather or WeatherParameters()
        self.config = config or SOLWEIGConfig()

    def solve(self, grid: UrbanGrid) -> SOLWEIGState:
        """Full recomputation on the entire domain."""
        shadow_mask = compute_shadow_mask(grid, self.weather.sun_altitude_deg,
                                          self.weather.sun_azimuth_deg)
        svf = compute_sky_view_factor(grid, self.config)
        s_str, t_mrt, k_dir, k_diff, l_long = solve_fluxes_and_tmrt(
            grid, shadow_mask, svf, self.weather, self.config
        )
        return SOLWEIGState(
            shadow_mask=shadow_mask,
            svf=svf,
            s_str=s_str,
            t_mrt=t_mrt,
            k_dir=k_dir,
            k_diff=k_diff,
            l_long=l_long
        )

    def solve_dirty_cells(self, grid: UrbanGrid, cached_state: SOLWEIGState,
                          dirty_mask: np.ndarray) -> SOLWEIGState:
        """
        Recomputes only dirty cells while reusing cached values for non-dirty cells.
        """
        if not np.any(dirty_mask):
            return cached_state

        new_shadow = cached_state.shadow_mask.copy()
        dirty_shadow = compute_shadow_mask(grid, self.weather.sun_altitude_deg,
                                           self.weather.sun_azimuth_deg,
                                           roi_mask=dirty_mask)
        new_shadow[dirty_mask] = dirty_shadow[dirty_mask]

        new_svf = cached_state.svf.copy()
        dirty_svf = compute_sky_view_factor(grid, self.config, roi_mask=dirty_mask)
        new_svf[dirty_mask] = dirty_svf[dirty_mask]

        s_str, t_mrt, k_dir, k_diff, l_long = solve_fluxes_and_tmrt(
            grid, new_shadow, new_svf, self.weather, self.config
        )

        return SOLWEIGState(
            shadow_mask=new_shadow,
            svf=new_svf,
            s_str=s_str,
            t_mrt=t_mrt,
            k_dir=k_dir,
            k_diff=k_diff,
            l_long=l_long
        )
