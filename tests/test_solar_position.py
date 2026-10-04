"""
Unit tests for deterministic solar position calculations.
"""

from datetime import datetime, timezone
import math
import pytest
import numpy as np

from urban_comfort.solar.solar_position import (
    calculate_solar_position, calculate_julian_day, SolarPosition
)


def test_julian_day():
    # Known reference: J2000.0 epoch: 2000-01-01 12:00:00 UTC = 2451545.0
    dt_j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    jd = calculate_julian_day(dt_j2000)
    assert math.isclose(jd, 2451545.0, abs_tol=1e-5)


def test_solar_position_summer_solstice_nyc():
    # New York City (40.7128 N, 74.0060 W) near solar noon on June 21, 2024
    # Approximate solar noon in NYC UTC is ~16:56 UTC
    dt = datetime(2024, 6, 21, 17, 0, 0, tzinfo=timezone.utc)
    pos = calculate_solar_position(40.7128, -74.0060, dt)

    assert pos.is_daylight is True
    # At summer solstice in NYC, peak solar altitude is ~72.7 degrees
    assert 70.0 <= pos.altitude_deg <= 75.0
    # Solar noon azimuth should be near South (~180 degrees)
    assert 170.0 <= pos.azimuth_deg <= 190.0

    # Zenith + Altitude = 90
    assert math.isclose(pos.altitude_deg + pos.zenith_deg, 90.0, abs_tol=1e-5)

    # Unit vector magnitude = 1.0
    sx, sy, sz = pos.sun_vector
    norm = math.hypot(sx, sy, sz)
    assert math.isclose(norm, 1.0, abs_tol=1e-6)
    assert sz > 0.0  # Pointing above horizon


def test_solar_position_nighttime():
    # Midnight in London
    dt = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    pos = calculate_solar_position(51.5074, -0.1278, dt)

    assert pos.is_daylight is False
    assert pos.altitude_deg < 0.0
    assert pos.zenith_deg > 90.0


def test_solar_position_determinism():
    dt = datetime(2024, 7, 15, 14, 30, 0, tzinfo=timezone.utc)
    pos1 = calculate_solar_position(48.8566, 2.3522, dt)
    pos2 = calculate_solar_position(48.8566, 2.3522, dt)

    assert pos1.altitude_deg == pos2.altitude_deg
    assert pos1.azimuth_deg == pos2.azimuth_deg
    assert pos1.sun_vector == pos2.sun_vector
