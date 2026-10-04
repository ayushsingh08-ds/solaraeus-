"""
Unit tests for Universal Thermal Climate Index (src/physics/utci.py).
"""

import numpy as np
import pytest

from src.physics.utci import compute_utci, classify_utci_stress


def test_utci_hot_sunny_conditions():
    """
    Test case 1 (validation criteria in README.md):
    Hot sunny summer conditions (Ta = 33°C, Tmrt = 60°C, v = 1.2 m/s, RH = 50%):
    UTCI should be > 40°C (very strong heat stress).
    """
    tmrt = np.array([60.0], dtype=np.float32)

    utci_val, categories = compute_utci(
        Ta=33.0,
        tmrt_values=tmrt,
        v_ped=1.2,
        RH=50.0,
        return_categories=True,
    )

    val = float(utci_val[0])
    cat = str(categories[0])

    assert val >= 40.0, f"Sunlit UTCI {val:.1f}°C should be >= 40.0°C"
    assert "strong heat stress" in cat, f"Expected strong/very strong heat stress, got: {cat}"


def test_utci_shaded_conditions():
    """
    Test case 2 (validation criteria in README.md):
    Same conditions but shaded (Tmrt = 35°C):
    UTCI should be around 34-39°C.
    """
    tmrt = np.array([35.0], dtype=np.float32)

    utci_val, categories = compute_utci(
        Ta=33.0,
        tmrt_values=tmrt,
        v_ped=1.2,
        RH=50.0,
        return_categories=True,
    )

    val = float(utci_val[0])

    assert 32.0 <= val <= 38.0, f"Shaded UTCI {val:.1f}°C should be in [32, 38]"


def test_utci_contrast_sun_vs_shade():
    """
    Test case 3: Side-by-side verification that UTCI(sun) > UTCI(shade) by a notable margin (>5°C).
    """
    tmrts = np.array([62.0, 34.0], dtype=np.float32)

    utci_vals = compute_utci(
        Ta=33.0,
        tmrt_values=tmrts,
        v_ped=1.2,
        RH=50.0,
    )

    utci_sun = float(utci_vals[0])
    utci_shade = float(utci_vals[1])
    diff = utci_sun - utci_shade

    assert diff > 5.0, f"UTCI sun-shade difference ({diff:.1f}°C) should exceed 5°C"


def test_utci_cold_conditions():
    """
    Test case 4 (validation criteria in README.md):
    Cold conditions (Ta = 2°C, Tmrt = 5°C, v = 3.0 m/s, RH = 70%):
    UTCI should be < 10°C (slight to moderate/strong cold stress).
    """
    tmrt = np.array([5.0], dtype=np.float32)

    utci_val, categories = compute_utci(
        Ta=2.0,
        tmrt_values=tmrt,
        v_ped=3.0,
        RH=70.0,
        return_categories=True,
    )

    val = float(utci_val[0])
    assert val < 10.0, f"Cold UTCI {val:.1f}°C should be < 10.0°C"
