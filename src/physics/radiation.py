"""
Radiative Flux Decomposition Engine — Direct/Diffuse Solar and Longwave Thermal Fluxes.
Computes shortwave fluxes (direct solar beam, diffuse sky solar) and longwave thermal
fluxes (downward sky/wall emission, upward ground emission) at pedestrian height.
"""

import logging
import math
from typing import Any, Dict, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant (W / m^2 / K^4)


def compute_radiation(
    sunlit_mask: np.ndarray,
    svf: np.ndarray,
    SSRD: float = 650.0,
    STRD: Optional[float] = None,
    Ta: float = 28.5,
    Tdew: float = 18.0,
    cloud_fraction: float = 0.1,
    alt_rad: Optional[float] = None,
    atmospheric_transmission: float = 0.75,
    sky_emissivity: float = 0.85,
    ground_emissivity: float = 0.95,
    wall_emissivity: float = 0.90,
    ground_temp_offset_k: float = 4.0,
    wall_temp_offset_k: float = 0.0,
) -> Dict[str, np.ndarray]:
    """
    Computes directional and hemispherical radiant flux components (W/m^2).

    Args:
        sunlit_mask: Boolean array indicating direct sun illumination (True = Sunlit, False = Shaded).
        svf: Array of Sky View Factor values in range [0.0, 1.0].
        SSRD: Surface Solar Radiation Downwards from ERA5 / Open-Meteo in W/m^2.
        STRD: Surface Thermal Radiation Downwards in W/m^2. If None, estimated from Ta and humidity.
        Ta: Air temperature in °C.
        Tdew: Dewpoint temperature in °C.
        cloud_fraction: Cloud cover fraction [0.0, 1.0].
        alt_rad: Solar altitude angle in radians.
        atmospheric_transmission: Direct beam transmission factor (default 0.75).
        sky_emissivity: Apparent sky emissivity (default 0.85).
        ground_emissivity: Ground surface emissivity (default 0.95).
        wall_emissivity: Vertical facade emissivity (default 0.90).
        ground_temp_offset_k: Excess temperature of sunlit ground above Ta in Kelvin (default 4.0K).
        wall_temp_offset_k: Excess temperature of urban facades above Ta in Kelvin (default 0.0K).

    Returns:
        Dictionary of flux arrays (W/m^2):
            - 'K_direct': Direct beam solar flux
            - 'K_diffuse': Diffuse sky solar flux
            - 'K_total': Total shortwave solar flux (K_direct + K_diffuse)
            - 'L_down': Downward & lateral longwave thermal flux from sky and building walls
            - 'L_up': Upward longwave thermal flux from ground
            - 'L_total': Total longwave thermal flux (L_down + L_up)
            - 'total_absorbed': Integrated absorbed flux for thermal comfort assessment
    """
    sunlit_arr = np.asarray(sunlit_mask, dtype=bool)
    svf_arr = np.clip(np.asarray(svf, dtype=np.float32), 0.0, 1.0)

    # 1. Shortwave Diffuse vs Direct Decomposition
    # Empirical diffuse fraction based on cloud fraction
    c_cov = float(np.clip(cloud_fraction, 0.0, 1.0))
    diffuse_fraction = float(np.clip(0.20 + 0.80 * (c_cov ** 1.5), 0.15, 1.0))

    ssrd_val = max(0.0, float(SSRD))
    ssrd_diffuse = ssrd_val * diffuse_fraction
    ssrd_direct = ssrd_val * (1.0 - diffuse_fraction)

    # Direct solar flux on horizontal plane: SSRD_direct * transmission * sunlit_mask
    k_direct = (ssrd_direct * atmospheric_transmission * sunlit_arr.astype(np.float32)).astype(np.float32)

    # Diffuse solar flux proportional to Sky View Factor
    k_diffuse = (ssrd_diffuse * svf_arr).astype(np.float32)

    k_total = k_direct + k_diffuse

    # 2. Longwave Thermal Fluxes
    t_air_k = float(Ta) + 273.15

    # Sky downward longwave radiation
    if STRD is not None and STRD > 0:
        l_sky_val = float(STRD)
    else:
        # Prata / Brunt clear-sky formula + cloud correction
        vp_hpa = 6.112 * math.exp((17.67 * Ta) / (Ta + 243.5))
        eps_clear = 1.0 - (1.0 + (46.5 * vp_hpa / t_air_k)) * math.exp(-math.sqrt(1.2 + 3.0 * (46.5 * vp_hpa / t_air_k)))
        eps_eff = eps_clear * (1.0 + 0.22 * (c_cov ** 2))
        l_sky_val = eps_eff * SIGMA * (t_air_k ** 4)

    # Wall thermal emission (T_wall = T_air + offset)
    t_wall_k = t_air_k + float(wall_temp_offset_k)
    l_wall_val = wall_emissivity * SIGMA * (t_wall_k ** 4)

    # Downward & lateral longwave: sky contribution (SVF) + wall contribution (1 - SVF)
    l_down = (l_sky_val * svf_arr + l_wall_val * (1.0 - svf_arr)).astype(np.float32)

    # Ground thermal emission (T_ground = T_air + offset on sunlit areas)
    # Sunlit ground heats up above ambient air temperature
    t_ground_k = t_air_k + (ground_temp_offset_k * sunlit_arr.astype(np.float32))
    l_up = (ground_emissivity * SIGMA * (t_ground_k ** 4)).astype(np.float32)

    l_total = l_down + l_up

    # Total combined radiant load incident on a standard horizontal/lateral receptor
    total_absorbed = (k_total + l_down + l_up).astype(np.float32)

    return {
        "K_direct": k_direct,
        "K_diffuse": k_diffuse,
        "K_total": k_total,
        "L_down": l_down,
        "L_up": l_up,
        "L_total": l_total,
        "total_absorbed": total_absorbed,
    }
