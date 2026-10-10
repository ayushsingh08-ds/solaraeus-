"""`SimulationResult`: the single output contract of the whole engine.

Every solver -- full reference, exact incremental, certified incremental,
CPU or GPU -- returns one of these.  Seven NumPy arrays plus a metadata dict,
with no disk I/O in between.  `incremental/` needs the *type* without needing
the reference solver, so it lives here on its own to keep the import graph
acyclic.

Split out of `reference/full_recompute.py`; byte-identical to the original.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np


@dataclass
class SimulationResult:
    """Complete simulation output across all computed physical fields."""
    shadow_mask: np.ndarray                     # Binary direct beam visibility (1.0 lit, 0.0 shadow)
    direct_irradiance: np.ndarray               # Direct horizontal shortwave irradiance (W / m^2)
    visibility_fields: Dict[str, np.ndarray]    # {"svf": np.ndarray}
    shortwave_flux: np.ndarray                  # Total absorbed shortwave flux density (W / m^2)
    longwave_flux: np.ndarray                   # Total absorbed longwave flux density (W / m^2)
    tmrt: np.ndarray                            # Mean Radiant Temperature in Celsius (deg C)
    utci: np.ndarray                            # Universal Thermal Climate Index in Celsius (deg C)
    metadata: Dict[str, Any]                    # Timestamps, runtimes, solar parameters, diagnostics

    @property
    def svf(self) -> np.ndarray:
        return self.visibility_fields["svf"]
