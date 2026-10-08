"""
Test suite for Coupled Physical Cloud Model (Part 8A, 16).
"""

import math
import numpy as np
import pytest
from urban_comfort.solar.cloud_model import cloud_model


def test_clear_sky_mode():
    state_clear = cloud_model.create_state(preset="Clear")
    assert state_clear.cover_fraction == 0.0
    mask = cloud_model.generate_cloud_mask(state_clear)
    assert np.all(mask == 0.0)

    # Radiation coupling under clear sky: transmittance must be 1.0
    c_rad = cloud_model.compute_radiation_coupling(state_clear, 850.0, 140.0, 360.0, mask)
    assert np.allclose(c_rad["cloud_transmittance_field"], 1.0)
    assert c_rad["mean_dni"] == pytest.approx(850.0)
    assert c_rad["dhi"] == pytest.approx(140.0)
    assert c_rad["l_sky"] == pytest.approx(360.0)


def test_cloud_radiation_monotonicity():
    state_few = cloud_model.create_state(preset="Few")
    state_overcast = cloud_model.create_state(preset="Overcast")

    m_few = cloud_model.generate_cloud_mask(state_few)
    m_overcast = cloud_model.generate_cloud_mask(state_overcast)

    rad_few = cloud_model.compute_radiation_coupling(state_few, 850.0, 140.0, 360.0, m_few)
    rad_overcast = cloud_model.compute_radiation_coupling(state_overcast, 850.0, 140.0, 360.0, m_overcast)

    # Overcast must have lower direct beam than Few
    assert rad_overcast["mean_dni"] < rad_few["mean_dni"]
    # Overcast must have higher sky longwave than Few
    assert rad_overcast["l_sky"] > rad_few["l_sky"]


def test_analytic_shadow_offset():
    state_broken = cloud_model.create_state(preset="Broken", base_height_m=1000.0)
    mask = cloud_model.generate_cloud_mask(state_broken)

    # At 45° altitude, shadow length = H / tan(45°) = 1000m
    # Azimuth 180° (South) -> Shadow direction is North (shift_y > 0)
    _, offset_m = cloud_model.compute_ground_shadow_projection(
        mask, sun_altitude_deg=45.0, sun_azimuth_deg=180.0, cloud_height_m=1000.0
    )
    assert abs(offset_m[0]) < 1e-3, "East-west shift should be ~0 when sun is Due South"
    assert offset_m[1] == pytest.approx(1000.0, rel=1e-3), "Northward shadow shift should equal 1000m"


def test_seed_reproducibility():
    s1 = cloud_model.create_state(preset="Scattered", seed=123)
    s2 = cloud_model.create_state(preset="Scattered", seed=123)
    m1 = cloud_model.generate_cloud_mask(s1)
    m2 = cloud_model.generate_cloud_mask(s2)
    assert np.array_equal(m1, m2), "Identical seed must yield bit-for-bit identical cloud mask"
