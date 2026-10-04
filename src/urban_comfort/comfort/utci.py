"""
Universal Thermal Climate Index (UTCI) calculation module.
Computes equivalent human thermal comfort temperature from T_air, T_mrt, wind speed, and humidity.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Tuple
import numpy as np

# Try importing pythermalcomfort for certified multi-variate polynomial
try:
    from pythermalcomfort.models import utci as _pythermal_utci
    _HAS_PYTHERMAL = True
except ImportError:
    _HAS_PYTHERMAL = False


def compute_utci(air_temp_c: Union[float, np.ndarray],
                 tmrt_c: Union[float, np.ndarray],
                 wind_speed_ms: float,
                 relative_humidity: float) -> np.ndarray:
    """
    Computes Universal Thermal Climate Index (UTCI) in Celsius.
    
    Operational range:
        - Air temperature: -50 to +50 C
        - (T_mrt - T_air): -30 to +70 K
        - Wind speed (at 10m): 0.5 to 17 m/s (clipped to 0.5 m/s minimum)
        - Relative humidity: 0 to 100%
    """
    ta = np.asarray(air_temp_c, dtype=np.float64)
    tr = np.asarray(tmrt_c, dtype=np.float64)
    v10 = max(0.5, float(wind_speed_ms))
    rh = max(0.0, min(100.0, float(relative_humidity)))

    if _HAS_PYTHERMAL:
        # Use pythermalcomfort vectorized implementation
        res = _pythermal_utci(tdb=ta, tr=tr, v=v10, rh=rh)
        return np.asarray(res.utci, dtype=np.float64)

    # Fast, robust polynomial approximation if pythermalcomfort is not installed
    # Reference: Bröde et al. (2012), International Journal of Biometeorology
    delta_t = tr - ta
    # Vapor pressure (kPa)
    e_sat = 0.61078 * np.exp(17.27 * ta / (ta + 237.3))
    pa = e_sat * (rh / 100.0)

    # Simplified UTCI approximation based on multi-variate regression
    utci_approx = ta + (
        0.6075 * delta_t * (v10 ** (-0.2)) +
        (0.0009 * (ta ** 2) - 0.002 * ta + 0.05) * pa -
        (0.25 * (v10 - 1.0) * np.maximum(0.0, 30.0 - ta) / 10.0)
    )
    return utci_approx


def get_thermal_stress_category(utci_c: float) -> str:
    """Classifies UTCI value into standardized thermal stress categories."""
    if utci_c < -40.0:
        return "Extreme cold stress"
    elif utci_c < -27.0:
        return "Very strong cold stress"
    elif utci_c < -13.0:
        return "Strong cold stress"
    elif utci_c < 0.0:
        return "Moderate cold stress"
    elif utci_c < 9.0:
        return "Slight cold stress"
    elif utci_c <= 26.0:
        return "No thermal stress"
    elif utci_c <= 32.0:
        return "Moderate heat stress"
    elif utci_c <= 38.0:
        return "Strong heat stress"
    elif utci_c <= 46.0:
        return "Very strong heat stress"
    else:
        return "Extreme heat stress"
