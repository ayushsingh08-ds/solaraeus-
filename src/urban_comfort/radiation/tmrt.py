"""
Mean Radiant Temperature (T_mrt) calculation via Stefan-Boltzmann law inversion.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from urban_comfort.config import SIGMA


@dataclass
class RadiantState:
    """Integrated radiant absorption and resulting Mean Radiant Temperature."""
    s_str: np.ndarray       # Total absorbed radiant flux density (W / m^2)
    tmrt_c: np.ndarray      # Mean Radiant Temperature in Celsius (deg C)
    tmrt_k: np.ndarray      # Mean Radiant Temperature in Kelvin (K)


def compute_tmrt(k_total: np.ndarray, l_total: np.ndarray,
                 a_k: float = 0.70, a_l: float = 0.97) -> RadiantState:
    """
    Computes total absorbed flux S_str and Mean Radiant Temperature (T_mrt).
    
    Parameters:
        k_total: Shortwave radiant flux incident on human body (W / m^2).
        l_total: Longwave radiant flux incident on human body (W / m^2).
        a_k: Human body shortwave absorption coefficient (default 0.70).
        a_l: Human body longwave absorption coefficient (default 0.97).
        
    Returns:
        RadiantState containing S_str, tmrt_c, and tmrt_k.
    """
    s_str = a_k * k_total + a_l * l_total

    # Stefan-Boltzmann inversion: T_mrt = (S_str / sigma)^0.25
    # Enforce minimum positive flux to prevent numerical instability
    safe_s = np.maximum(1.0, s_str)
    tmrt_k = np.power(safe_s / SIGMA, 0.25)
    tmrt_c = tmrt_k - 273.15

    return RadiantState(s_str=s_str, tmrt_c=tmrt_c, tmrt_k=tmrt_k)
