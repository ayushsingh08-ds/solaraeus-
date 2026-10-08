"""
Authoritative 3D UTCI Engine for SOLARAEUS.

Computes the Universal Thermal Climate Index (UTCI) field from active 3D Tmrt
and concurrent ambient meteorological inputs:
- Air temperature Ta (°C)
- Mean radiant temperature Tmrt (°C)
- 10m Wind speed v10 (m/s)
- Relative humidity RH (%) or water vapor pressure Pa (kPa)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from urban_comfort.comfort.utci import compute_utci, get_thermal_stress_category


@dataclass
class UTCI3DResult:
    utci_c: np.ndarray  # Shape: (ny, nx)
    mean_utci_c: float
    min_utci_c: float
    max_utci_c: float
    stress_category: str
    cooling_delta_k: float  # Difference from baseline


class UTCI3DEngine:
    """Computes spatial human thermal comfort index from 3D Tmrt."""

    def __init__(self):
        pass

    def compute_field(
        self,
        tmrt_field: np.ndarray,
        air_temp_c: float = 35.0,
        wind_speed_ms: float = 1.5,
        relative_humidity_pct: float = 19.7,
        baseline_mean_utci: float = 37.15,
    ) -> UTCI3DResult:
        """
        Calculates 2D UTCI field from spatial Tmrt field and weather state.
        """
        utci_grid = compute_utci(
            air_temp_c=air_temp_c,
            tmrt_c=tmrt_field,
            wind_speed_ms=wind_speed_ms,
            relative_humidity=relative_humidity_pct,
        )

        mean_val = float(np.mean(utci_grid))
        min_val = float(np.min(utci_grid))
        max_val = float(np.max(utci_grid))
        stress = get_thermal_stress_category(mean_val)
        delta_k = mean_val - baseline_mean_utci

        return UTCI3DResult(
            utci_c=utci_grid,
            mean_utci_c=mean_val,
            min_utci_c=min_val,
            max_utci_c=max_val,
            stress_category=stress,
            cooling_delta_k=delta_k,
        )


# Global default engine
utci_3d_engine = UTCI3DEngine()
