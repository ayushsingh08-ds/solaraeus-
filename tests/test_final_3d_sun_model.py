"""
Test suite for Astronomical Solar Model (Part 8, 16).
"""

from datetime import date
from pathlib import Path
import pytest
from urban_comfort.solar.sun_model import sun_model

ROOT = Path(__file__).resolve().parent.parent


def test_east_to_west_movement():
    ref_date = date(2024, 4, 15)
    # 09:00 morning
    m_pos = sun_model.compute_position(ref_date, 9.0)
    # 15:00 afternoon
    a_pos = sun_model.compute_position(ref_date, 15.0)

    # In morning: East vector is positive (X > 0)
    assert m_pos.sun_vector[0] > 0.0, "Morning sun must be in Eastern sky"
    # In afternoon: East vector is negative (X < 0, toward West)
    assert a_pos.sun_vector[0] < 0.0, "Afternoon sun must be in Western sky"


def test_solar_noon_elevation_maximum():
    ref_date = date(2024, 4, 15)
    m_pos = sun_model.compute_position(ref_date, 9.0)
    noon_pos = sun_model.compute_position(ref_date, 12.33)
    e_pos = sun_model.compute_position(ref_date, 17.0)

    assert noon_pos.altitude_deg > m_pos.altitude_deg
    assert noon_pos.altitude_deg > e_pos.altitude_deg


def test_seasonal_zenith_bifurcation():
    # April 15: Sun declination < 12.97°N -> Sun passes south of zenith at noon
    apr_prof = sun_model.compute_daily_profile(date(2024, 4, 15))
    assert not apr_prof.passes_north_of_zenith, "April 15 sun should be south of zenith"

    # June 21: Sun declination = 23.45° > 12.97°N -> Sun passes north of zenith at noon
    jun_prof = sun_model.compute_daily_profile(date(2024, 6, 21))
    assert jun_prof.passes_north_of_zenith, "June 21 sun should pass north of zenith in Bengaluru"


def test_below_horizon_no_direct_rays():
    ref_date = date(2024, 4, 15)
    night_pos = sun_model.compute_position(ref_date, 2.0)
    assert night_pos.altitude_deg < 0.0
    assert night_pos.is_daylight is False
