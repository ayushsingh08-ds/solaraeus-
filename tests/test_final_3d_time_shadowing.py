"""
Test suite for Time-Based Shadowing and Continuous Integration (Part 8B, 16).
"""

import math
from datetime import date
import numpy as np
import pytest
from urban_comfort.integration.time_shadowing import time_shadowing_engine


def test_analytic_shadow_length_and_direction():
    # 10m height object at 30° altitude, 120° azimuth
    props = time_shadowing_engine.compute_analytic_shadow_properties(
        height_m=10.0, altitude_deg=30.0, azimuth_deg=120.0
    )
    expected_length = 10.0 / math.tan(math.radians(30.0))
    expected_azimuth = (120.0 + 180.0) % 360.0  # 300°

    assert props["shadow_length_m"] == pytest.approx(expected_length, rel=1e-3)
    assert props["shadow_azimuth_deg"] == pytest.approx(expected_azimuth, rel=1e-3)


def test_shadow_length_diurnal_variation():
    # Morning (altitude 25°), Noon (altitude 65°), Afternoon (altitude 30°)
    p_morn = time_shadowing_engine.compute_analytic_shadow_properties(10.0, 25.0, 90.0)
    p_noon = time_shadowing_engine.compute_analytic_shadow_properties(10.0, 65.0, 180.0)
    p_eve = time_shadowing_engine.compute_analytic_shadow_properties(10.0, 20.0, 270.0)

    assert p_noon["shadow_length_m"] < p_morn["shadow_length_m"]
    assert p_noon["shadow_length_m"] < p_eve["shadow_length_m"]


def test_time_integrated_durations():
    ref_date = date(2024, 4, 15)
    sim = time_shadowing_engine.simulate_day(ref_date, start_hour=8.0, end_hour=16.0, step_minutes=30.0)
    total_hours = 8.0  # 8.0 to 16.0

    sunlit = sim["sunlit_duration_map"]
    shadow = sim["shadow_duration_map"]

    # In any cell, sunlit + shadow duration should equal total daytime hours
    assert np.all(sunlit >= 0.0)
    assert np.all(shadow >= 0.0)
    total_cell = sunlit + shadow
    # Within 0.5 hours due to discrete boundaries
    assert np.mean(total_cell) == pytest.approx(total_hours, abs=0.5)
