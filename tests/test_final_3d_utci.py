"""
Test suite for 3D UTCI Comfort Calculation (Part 11, 16).
"""

import numpy as np
import pytest
from urban_comfort.integration.utci_3d import utci_3d_engine


def test_utci_responds_to_tmrt():
    tmrt_hot = np.full((10, 10), 52.0)
    tmrt_cool = np.full((10, 10), 38.0)

    res_hot = utci_3d_engine.compute_field(tmrt_hot, air_temp_c=35.0)
    res_cool = utci_3d_engine.compute_field(tmrt_cool, air_temp_c=35.0)

    assert res_cool.mean_utci_c < res_hot.mean_utci_c
    assert "STRESS" in res_hot.stress_category.upper()


def test_utci_responds_to_air_temp_and_wind():
    tmrt = np.full((10, 10), 45.0)
    res_low_wind = utci_3d_engine.compute_field(tmrt, air_temp_c=35.0, wind_speed_ms=0.8)
    res_high_wind = utci_3d_engine.compute_field(tmrt, air_temp_c=35.0, wind_speed_ms=3.5)

    # In warm conditions with high Tmrt, moderate wind provides cooling convective relief
    assert res_high_wind.mean_utci_c < res_low_wind.mean_utci_c
