"""
Domain-specific biometeorological and geometric validation metrics.
Includes shadow IoU, UTCI thermal category agreement, and error percentiles.
"""

from __future__ import annotations
from typing import Dict, Tuple
import numpy as np

from urban_comfort.comfort.utci import get_thermal_stress_category


def compute_shadow_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """
    Computes Intersection-over-Union (IoU) of shaded regions (where mask == 0.0).
    Returns 1.0 if both masks have zero shade, otherwise in [0.0, 1.0].
    """
    shade_a = (mask_a <= 0.5)
    shade_b = (mask_b <= 0.5)

    intersection = np.sum(shade_a & shade_b)
    union = np.sum(shade_a | shade_b)

    if union == 0:
        return 1.0
    return float(intersection) / float(union)


def compute_utci_category_agreement(utci_a: np.ndarray, utci_b: np.ndarray) -> float:
    """
    Computes fraction of grid cells where UTCI thermal stress category is identical.
    """
    flat_a = utci_a.ravel()
    flat_b = utci_b.ravel()
    n = len(flat_a)
    if n == 0:
        return 1.0

    agreements = sum(
        1 for a, b in zip(flat_a, flat_b)
        if get_thermal_stress_category(a) == get_thermal_stress_category(b)
    )
    return float(agreements) / float(n)


def compute_error_percentiles(error_map: np.ndarray,
                              percentiles: Tuple[float, ...] = (50.0, 90.0, 95.0, 99.0)) -> Dict[str, float]:
    """
    Computes statistical percentiles of absolute errors.
    """
    flat_errors = np.abs(error_map).ravel()
    if len(flat_errors) == 0:
        return {f"p{int(p)}": 0.0 for p in percentiles}

    vals = np.percentile(flat_errors, percentiles)
    return {f"p{int(p)}": float(v) for p, v in zip(percentiles, vals)}
