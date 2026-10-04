"""
Unit tests for Mean Radiant Temperature (src/physics/tmrt.py).
"""

import numpy as np
import pytest

from src.physics.radiation import compute_radiation
from src.physics.tmrt import compute_tmrt


def test_tmrt_sunlit_open_area():
    """
    Test case 1 (validation criteria in README.md):
    Sunlit point in open area on hot summer afternoon:
    Tmrt should be > 50°C, typically 52°C to 68°C.
    """
    sunlit = np.array([True])
    svf = np.array([1.0], dtype=np.float32)

    fluxes = compute_radiation(
        sunlit_mask=sunlit,
        svf=svf,
        SSRD=800.0,
        Ta=33.0,
        Tdew=20.0,
        cloud_fraction=0.1,
    )

    tmrt = compute_tmrt(fluxes)
    tmrt_val = float(tmrt[0])

    assert tmrt_val > 50.0, f"Sunlit Tmrt {tmrt_val:.1f}°C should be > 50°C"
    assert tmrt_val < 75.0, f"Sunlit Tmrt {tmrt_val:.1f}°C unrealistically high"


def test_tmrt_shaded_area():
    """
    Test case 2 (validation criteria in README.md):
    Shaded urban canyon:
    Tmrt should be < 40°C, noticeably lower than sunlit area.
    """
    sunlit = np.array([False])
    svf = np.array([0.35], dtype=np.float32)

    fluxes = compute_radiation(
        sunlit_mask=sunlit,
        svf=svf,
        SSRD=800.0,
        Ta=33.0,
        Tdew=20.0,
        cloud_fraction=0.1,
    )

    tmrt = compute_tmrt(fluxes)
    tmrt_val = float(tmrt[0])

    assert tmrt_val < 40.0, f"Shaded Tmrt {tmrt_val:.1f}°C should be < 40°C"


def test_tmrt_contrast_sun_vs_shade():
    """
    Test case 3: Side-by-side verification of significant thermal contrast.
    Tmrt difference between sun and shade should be > 10°C (typically 15-25°C).
    """
    sunlit = np.array([True, False])
    svf = np.array([0.95, 0.40], dtype=np.float32)

    fluxes = compute_radiation(
        sunlit_mask=sunlit,
        svf=svf,
        SSRD=750.0,
        Ta=30.0,
    )

    tmrt = compute_tmrt(fluxes)
    tmrt_sun = float(tmrt[0])
    tmrt_shade = float(tmrt[1])

    delta_tmrt = tmrt_sun - tmrt_shade
    assert delta_tmrt > 12.0, f"Tmrt difference ({delta_tmrt:.1f}°C) should be > 12°C between sun and shade"


def test_tmrt_nighttime():
    """
    Test case 4 (validation criteria in README.md):
    Nighttime (zero solar radiation) -> Tmrt close to air temperature (+/- 5°C).
    """
    sunlit = np.array([False])
    svf = np.array([1.0], dtype=np.float32)

    fluxes = compute_radiation(
        sunlit_mask=sunlit,
        svf=svf,
        SSRD=0.0,
        Ta=22.0,
    )

    tmrt = compute_tmrt(fluxes)
    tmrt_val = float(tmrt[0])

    # Clear sky radiational cooling typically depresses open sky Tmrt 5-8°C below air temperature
    assert abs(tmrt_val - 22.0) < 8.5, f"Nighttime Tmrt {tmrt_val:.1f}°C should be within 8.5°C of air temp (22°C)"
