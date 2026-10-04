"""
Shortwave radiation calculations on human standing cylinder.
Includes direct beam, diffuse sky, and surface-reflected fluxes.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

from urban_comfort.config import Weather, Material
from urban_comfort.solar.solar_position import SolarPosition


@dataclass
class ShortwaveFluxes:
    """Shortwave radiant flux densities incident on a standing human (W / m^2)."""
    k_dir: np.ndarray             # Weighted direct solar flux
    k_diff: np.ndarray            # Weighted diffuse sky + reflected flux
    k_total: np.ndarray           # k_dir + k_diff
    direct_horizontal: np.ndarray # I_dir * sin(alt) * shadow_mask


def compute_shortwave_fluxes(weather: Weather, solar_pos: SolarPosition,
                             shadow_mask: np.ndarray, svf: np.ndarray,
                             ground_material: Material,
                             wall_material: Material,
                             f_up: float = 0.06, f_down: float = 0.06,
                             f_side: float = 0.22) -> ShortwaveFluxes:
    """
    Computes 6-directional shortwave fluxes on a standing human model.
    """
    if not solar_pos.is_daylight:
        zeros = np.zeros_like(shadow_mask)
        return ShortwaveFluxes(k_dir=zeros, k_diff=zeros, k_total=zeros, direct_horizontal=zeros)

    alt_rad = solar_pos.altitude_rad
    sin_alt = math.sin(alt_rad)

    sx, sy, sz = solar_pos.sun_vector
    # Directional incidence cosines for 4 cardinal vertical sides
    cos_east = max(0.0, sx)
    cos_west = max(0.0, -sx)
    cos_north = max(0.0, sy)
    cos_south = max(0.0, -sy)

    # 1. Direct shortwave fluxes
    i_dir = weather.direct_normal_irradiance
    direct_horiz = i_dir * sin_alt * shadow_mask

    k_dir_up = direct_horiz
    k_dir_down = np.zeros_like(shadow_mask)
    k_dir_e = i_dir * cos_east * shadow_mask
    k_dir_w = i_dir * cos_west * shadow_mask
    k_dir_n = i_dir * cos_north * shadow_mask
    k_dir_s = i_dir * cos_south * shadow_mask

    k_dir_weighted = (
        f_up * k_dir_up +
        f_down * k_dir_down +
        f_side * (k_dir_e + k_dir_w + k_dir_n + k_dir_s)
    )

    # 2. Diffuse sky radiation
    d_diff = weather.diffuse_horizontal_irradiance
    k_diff_up = d_diff * svf
    k_diff_side = 0.5 * d_diff * svf

    # 3. Reflected shortwave from ground (hits down sensor)
    g_ground = direct_horiz + d_diff * svf
    k_refl_ground = ground_material.albedo * g_ground

    # 4. Reflected shortwave from walls (hits side sensors)
    g_wall = 0.5 * (i_dir + d_diff)
    k_refl_wall = wall_material.albedo * (1.0 - svf) * g_wall

    k_diff_weighted = (
        f_up * k_diff_up +
        f_down * k_refl_ground +
        f_side * 4.0 * (k_diff_side + k_refl_wall)
    )

    k_total = k_dir_weighted + k_diff_weighted

    return ShortwaveFluxes(
        k_dir=k_dir_weighted,
        k_diff=k_diff_weighted,
        k_total=k_total,
        direct_horizontal=direct_horiz
    )
