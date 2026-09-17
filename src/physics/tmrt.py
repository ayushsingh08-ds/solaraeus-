"""
Mean Radiant Temperature (Tmrt) Engine — 6-Directional Human Cylinder Model.
Converts directional shortwave and longwave radiant fluxes into Mean Radiant Temperature (°C)
via the Stefan-Boltzmann law according to standard outdoor thermal comfort models (VDI 3787 / Höppe).
"""

import logging
import math
from typing import Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant (W / m^2 / K^4)


def compute_tmrt(
    fluxes: Dict[str, np.ndarray],
    weights: Tuple[float, ...] = (0.06, 0.06, 0.22, 0.22, 0.22, 0.22),
    human_absorptivity_sw: float = 0.70,
    human_emissivity_lw: float = 0.97,
    ground_albedo: float = 0.18,
    alt_rad: Optional[float] = None,
) -> np.ndarray:
    """
    Computes Mean Radiant Temperature (Tmrt in °C) from radiative fluxes.

    Args:
        fluxes: Dictionary of fluxes containing 'K_direct', 'K_diffuse', 'L_down', 'L_up'.
        weights: Cylinder projection weights (top, bottom, 4 lateral sides). Default (0.06, 0.06, 0.22*4).
        human_absorptivity_sw: Standard shortwave absorptivity of human body (default 0.70).
        human_emissivity_lw: Standard longwave emissivity/absorptivity of human body (default 0.97).
        ground_albedo: Surface shortwave reflectivity (default 0.18 for urban asphalt/pavement).
        alt_rad: Optional solar altitude angle in radians for lateral cylinder projection.

    Returns:
        np.ndarray of Tmrt values in °C matching the input flux array shapes.
    """
    k_direct = np.asarray(fluxes["K_direct"], dtype=np.float32)
    k_diffuse = np.asarray(fluxes["K_diffuse"], dtype=np.float32)
    l_down = np.asarray(fluxes["L_down"], dtype=np.float32)
    l_up = np.asarray(fluxes["L_up"], dtype=np.float32)

    w_top, w_bottom, w_side1, w_side2, w_side3, w_side4 = weights
    w_sides_total = w_side1 + w_side2 + w_side3 + w_side4  # 0.88

    # 1. Shortwave Radiant Flux Absorbed by Human Cylinder (S_short)
    # - Top surface: receives horizontal direct + diffuse sky
    k_top = k_direct + k_diffuse

    # - Bottom surface: receives ground-reflected shortwave
    k_bottom = ground_albedo * (k_direct + k_diffuse)

    # - Lateral cylinder sides:
    # Diffuse from surroundings: half sky, half ground/walls
    k_sides_diffuse = 0.5 * k_diffuse + 0.5 * k_bottom

    # Direct beam projected onto standing human cylinder:
    # Projected area factor f_p depends on solar altitude (standard VDI formula)
    if alt_rad is not None and alt_rad > 0:
        alt_deg = math.degrees(alt_rad)
        f_p = 0.308 * math.cos(math.radians(alt_deg * (0.998 - (alt_deg**2) / 50000.0)))
        f_p = max(0.15, min(0.35, f_p))
    else:
        f_p = 0.28  # Typical projection factor for standing person at midday sun

    # Lateral direct beam contribution
    k_sides_direct = f_p * (k_direct / max(math.sin(alt_rad) if alt_rad and alt_rad > 0 else 0.85, 0.2))

    k_absorbed = human_absorptivity_sw * (
        w_top * k_top
        + w_bottom * k_bottom
        + w_sides_total * (k_sides_diffuse + k_sides_direct)
    )

    # 2. Longwave Radiant Flux Absorbed by Human Cylinder (S_long)
    # Top receives L_down, bottom receives L_up, lateral sides receive 50% down + 50% up
    l_absorbed = human_emissivity_lw * (
        w_top * l_down
        + w_bottom * l_up
        + w_sides_total * (0.5 * l_down + 0.5 * l_up)
    )

    # 3. Total Mean Radiant Flux Load (S_str in W/m^2)
    s_str = k_absorbed + l_absorbed

    # 4. Stefan-Boltzmann Inversion to Mean Radiant Temperature (Tmrt)
    # Tmrt = (S_str / (eps_p * sigma))^(1/4) - 273.15
    rad_ratio = np.maximum(s_str / (human_emissivity_lw * SIGMA), 1.0)
    tmrt_c = (rad_ratio ** 0.25) - 273.15

    return tmrt_c.astype(np.float32)
