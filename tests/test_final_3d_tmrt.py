"""
Test suite for 3D Mean Radiant Temperature (Tmrt) (Part 10, 16).
"""

from datetime import date
from pathlib import Path
import numpy as np
import pytest
from urban_comfort.integration.tmrt_3d import tmrt_3d_engine
from urban_comfort.solar.sun_model import sun_model
from urban_comfort.solar.cloud_model import cloud_model

ROOT = Path(__file__).resolve().parent.parent


def test_tmrt_scenario_cooling_delta():
    ref_date = date(2024, 4, 15)
    sun_pos = sun_model.compute_position(ref_date, 14.5)
    c_state = cloud_model.create_state(preset="Clear")

    res_base = tmrt_3d_engine.compute_field(sun_pos, c_state, scenario="baseline")
    res_panels = tmrt_3d_engine.compute_field(sun_pos, c_state, scenario="panels")
    res_comb = tmrt_3d_engine.compute_field(sun_pos, c_state, scenario="combined")

    # Adding interventions must reduce mean Tmrt
    assert res_panels.mean_tmrt_c < res_base.mean_tmrt_c
    assert res_comb.mean_tmrt_c < res_panels.mean_tmrt_c
    # Localized peak cooling relief under shade panel
    max_cooling = np.max(res_base.tmrt_c - res_panels.tmrt_c)
    assert max_cooling > 8.0, "Expected at least 8K localized Tmrt relief under sail"


def test_tmrt_cloud_attenuation():
    ref_date = date(2024, 4, 15)
    sun_pos = sun_model.compute_position(ref_date, 14.5)
    c_clear = cloud_model.create_state(preset="Clear")
    c_overcast = cloud_model.create_state(preset="Overcast")

    res_clear = tmrt_3d_engine.compute_field(sun_pos, c_clear, scenario="baseline")
    res_overcast = tmrt_3d_engine.compute_field(sun_pos, c_overcast, scenario="baseline")

    # Overcast conditions reduce direct shortwave substantially, leading to lower daytime Tmrt
    assert res_overcast.mean_tmrt_c < res_clear.mean_tmrt_c
