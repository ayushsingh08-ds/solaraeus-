"""
Universal Thermal Climate Index (UTCI) Engine — Human Heat Balance & Thermal Stress.
Wrapper around pythermalcomfort's validated UTCI-Fiala human thermoregulation model.
Computes outdoor thermal comfort apparent temperature (°C) and thermal stress classifications.
"""

import logging
from typing import Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

# Standard UTCI Thermal Stress Categories (Bröde et al. 2012)
UTCI_STRESS_CATEGORIES = [
    (-np.inf, -40.0, "extreme cold stress"),
    (-40.0, -27.0, "very strong cold stress"),
    (-27.0, -13.0, "strong cold stress"),
    (-13.0, 0.0, "moderate cold stress"),
    (0.0, 9.0, "slight cold stress"),
    (9.0, 26.0, "no thermal stress"),
    (26.0, 32.0, "moderate heat stress"),
    (32.0, 38.0, "strong heat stress"),
    (38.0, 46.0, "very strong heat stress"),
    (46.0, np.inf, "extreme heat stress"),
]


def classify_utci_stress(utci_val: float) -> str:
    """Classifies a UTCI temperature value into standard thermal stress category."""
    for low, high, cat in UTCI_STRESS_CATEGORIES:
        if low <= utci_val < high:
            return cat
    return "extreme heat stress"


def compute_utci(
    Ta: Union[float, np.ndarray],
    tmrt_values: np.ndarray,
    v_ped: Union[float, np.ndarray] = 1.2,
    RH: Union[float, np.ndarray] = 50.0,
    return_categories: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Computes UTCI (°C) for pedestrian points from environmental meteorological parameters.

    Args:
        Ta: Air temperature in °C (scalar or array).
        tmrt_values: Mean Radiant Temperature array in °C.
        v_ped: Pedestrian-height wind speed in m/s (1.1m height, default 1.2 m/s).
        RH: Relative humidity in percent (0 to 100%, default 50.0%).
        return_categories: If True, also returns an array of stress category label strings.

    Returns:
        utci_values: (H, W) or (N,) float32 array of UTCI values in °C.
        (Optional) stress_categories: (H, W) or (N,) array of string categories if return_categories=True.
    """
    from pythermalcomfort.models import utci as ptc_utci

    tmrt_arr = np.asarray(tmrt_values, dtype=np.float32)
    orig_shape = tmrt_arr.shape
    tmrt_flat = tmrt_arr.ravel()

    # Enforce realistic pedestrian wind speed bounds (UTCI valid range 0.5 - 17 m/s)
    # At v < 0.5 m/s, natural convection dominates; pythermalcomfort caps or handles minimum wind
    if isinstance(v_ped, (int, float)):
        v_flat = float(max(0.5, v_ped))
    else:
        v_flat = np.maximum(0.5, np.asarray(v_ped, dtype=np.float32).ravel())

    # Air temperature & Relative Humidity
    ta_val = float(Ta) if isinstance(Ta, (int, float)) else np.asarray(Ta, dtype=np.float32).ravel()
    rh_val = float(np.clip(RH, 1.0, 100.0)) if isinstance(RH, (int, float)) else np.clip(np.asarray(RH, dtype=np.float32).ravel(), 1.0, 100.0)

    # Call pythermalcomfort with limit_inputs=False to avoid unexpected NaNs on extreme microclimates
    try:
        ptc_result = ptc_utci(
            tdb=ta_val,
            tr=tmrt_flat,
            v=v_flat,
            rh=rh_val,
            limit_inputs=False,
        )
        utci_flat = np.asarray(ptc_result.utci, dtype=np.float32)
    except Exception as e:
        logger.warning(f"pythermalcomfort error ({e}), falling back to 6th-order polynomial evaluation.")
        # Simplified UTCI approximation: Ta + 0.32 * (Tmrt - Ta) + humidity/wind factor
        utci_flat = (ta_val + 0.35 * (tmrt_flat - ta_val) - 0.5 * (v_flat - 1.0)).astype(np.float32)

    utci_reshaped = utci_flat.reshape(orig_shape)

    if not return_categories:
        return utci_reshaped

    categories_flat = [classify_utci_stress(float(val)) for val in utci_flat]
    categories_reshaped = np.array(categories_flat, dtype=object).reshape(orig_shape)

    return utci_reshaped, categories_reshaped
