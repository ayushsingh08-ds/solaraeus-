"""
Unit tests for radiative flux decomposition (src/physics/radiation.py).
"""

import numpy as np
import pytest

from src.physics.radiation import compute_radiation


def test_radiation_sunlit_open_area():
    """
    Test case 1 (masterbackendsteps.md):
    Sunlit point in open area at midday on a clear summer day:
    Total shortwave flux K_total should be roughly 400-600 W/m^2.
    Direct solar flux should be dominant (>300 W/m^2).
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

    k_dir = float(fluxes["K_direct"][0])
    k_diff = float(fluxes["K_diffuse"][0])
    k_tot = float(fluxes["K_total"][0])
    l_down = float(fluxes["L_down"][0])
    l_up = float(fluxes["L_up"][0])

    # Direct shortwave must be positive and substantial
    assert k_dir > 350.0, f"Direct solar {k_dir:.1f} W/m^2 should be > 350 W/m^2"
    assert 400.0 <= k_tot <= 650.0, f"Total shortwave {k_tot:.1f} W/m^2 should be in [400, 650]"

    # Longwave fluxes should be physically realistic for summer (~350-550 W/m^2)
    assert 300.0 <= l_down <= 550.0, f"L_down {l_down:.1f} W/m^2 out of physical bounds"
    assert 350.0 <= l_up <= 600.0, f"L_up {l_up:.1f} W/m^2 out of physical bounds"


def test_radiation_shaded_canyon():
    """
    Test case 2 (masterbackendsteps.md):
    Shaded point in deep canyon (SVF = 0.35, sunlit = False):
    Direct solar flux must be strictly 0.0 W/m^2.
    Total shortwave should be much lower (< 100 W/m^2, only diffuse sky radiation).
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

    k_dir = float(fluxes["K_direct"][0])
    k_diff = float(fluxes["K_diffuse"][0])
    k_tot = float(fluxes["K_total"][0])

    # Shaded direct flux MUST be 0.0
    assert k_dir == 0.0, f"Shaded point received non-zero direct flux: {k_dir}"
    assert k_tot == k_diff
    assert k_tot < 100.0, f"Shaded canyon shortwave {k_tot:.1f} W/m^2 should be < 100 W/m^2"


def test_radiation_contrast_sun_vs_shade():
    """
    Test case 3: Side-by-side array test confirming sunlit vs shaded contrast.
    """
    sunlit = np.array([True, False])
    svf = np.array([0.95, 0.40], dtype=np.float32)

    fluxes = compute_radiation(
        sunlit_mask=sunlit,
        svf=svf,
        SSRD=700.0,
        Ta=30.0,
    )

    k_sun = float(fluxes["K_total"][0])
    k_shade = float(fluxes["K_total"][1])

    assert k_sun > 4.0 * k_shade, f"Sunlit shortwave ({k_sun:.1f}) should be >4x shaded ({k_shade:.1f})"

    # Ground temperature excess: sunlit ground emits more upward longwave than shaded ground
    l_up_sun = float(fluxes["L_up"][0])
    l_up_shade = float(fluxes["L_up"][1])
    assert l_up_sun > l_up_shade, f"Sunlit ground L_up ({l_up_sun:.1f}) should exceed shade ({l_up_shade:.1f})"
