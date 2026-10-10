"""The shared result type for candidate affected-region computation.

`AffectedRegionResult` is returned by both the box-based
(`affected_region.py`) and mesh-based (`mesh_affected_region.py`) affected-region
calculations.  It lives on its own so that neither of those modules has to
import the other just to name the return type -- that import was the last
structural cycle inside `incremental/`.

Split out of `incremental/affected_region.py`; the dataclass body is
byte-identical to the original.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


@dataclass
class AffectedRegionResult:
    """Candidate affected region output with fallback diagnostics."""

    candidate_mask: np.ndarray  # (ny, nx) boolean mask: True where candidate region applies
    candidate_bbox: Tuple[
        float, float, float, float
    ]  # (xmin, xmax, ymin, ymax) in world coordinates
    is_fallback: bool  # True if numerical instability forces full recomputation
    fallback_reason: Optional[str]  # Descriptive reason when is_fallback is True
    shadow_length_m: float  # Estimated maximum shadow plume length (m)
    safety_margin_m: float  # Applied safety margin padding (m)
    old_projection_bbox: Tuple[float, float, float, float]
    new_projection_bbox: Tuple[float, float, float, float]
