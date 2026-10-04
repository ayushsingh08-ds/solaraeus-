"""
Unit tests for solar position calculation (src/physics/solar.py).
"""

import math
import pytest

from src.physics.solar import compute_solar_position, solar_position_degrees


def test_solar_position_nyc_july_afternoon():
    """
    Test case specified in the validation criteria in README.md:
    For NYC (40.7308°N, -73.9975°W) on July 15 (day 196) at 14:00 local (18:00 UTC):
    Altitude should be ~60-65° (or up to ~68° with EoT), azimuth should be ~135-145°.
    """
    lat = 40.7308
    lon = -73.9975
    utc_hour = 18.0
    day_of_year = 196

    alt_rad, az_rad = compute_solar_position(lat, utc_hour, day_of_year, lon)
    alt_deg, az_deg = solar_position_degrees(lat, utc_hour, day_of_year, lon)

    # Check radian / degree consistency
    assert math.isclose(alt_deg, math.degrees(alt_rad), rel_tol=1e-5)
    assert math.isclose(az_deg, math.degrees(az_rad), rel_tol=1e-5)

    # Verify expected bounds from the validation criteria in README.md
    assert 60.0 <= alt_deg <= 70.0, f"Altitude {alt_deg:.1f}° out of expected range [60°, 70°]"
    assert 135.0 <= az_deg <= 146.0, f"Azimuth {az_deg:.1f}° out of expected range [135°, 146°]"

    # Test standard compass azimuth option (clockwise from North: ~217°)
    alt_c, az_c = solar_position_degrees(lat, utc_hour, day_of_year, lon, use_standard_compass=True)
    assert 210.0 <= az_c <= 225.0, f"Compass azimuth {az_c:.1f}° out of expected range [210°, 225°]"


def test_solar_position_equator_noon_equinox():
    """
    Test case: Equator at solar noon on the equinox (day ~80).
    Sun should be directly overhead (altitude = 90°).
    """
    lat = 0.0
    lon = 0.0
    utc_hour = 12.0
    day_of_year = 80

    alt_deg, _ = solar_position_degrees(lat, utc_hour, day_of_year, lon)
    # Note: At nominal clock hour 12:00, Equation of Time (~ -7.5 min) causes a ~1.9° shift from zenith (88.0°)
    assert math.isclose(alt_deg, 90.0, abs_tol=2.5), f"Equator equinox altitude {alt_deg:.1f}° should be ~90°"


def test_solar_position_north_pole_winter():
    """
    Test case: North Pole on winter solstice (day 355).
    Sun should be below the horizon all day (altitude < 0°).
    """
    lat = 90.0
    lon = 0.0
    day_of_year = 355

    for hour in [0.0, 6.0, 12.0, 18.0]:
        alt_deg, _ = solar_position_degrees(lat, hour, day_of_year, lon)
        assert alt_deg < 0.0, f"North pole winter altitude at hour {hour} should be < 0°, got {alt_deg:.1f}°"
