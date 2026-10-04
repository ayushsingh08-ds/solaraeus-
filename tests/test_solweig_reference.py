"""
Unit tests for the reference deterministic SOLWEIG solver.
"""

import numpy as np
import pytest
from solaraeus.core.geometry import UrbanGrid, AddBuilding
from solaraeus.core.solweig import (
    ReferenceSOLWEIGSolver, WeatherParameters, SOLWEIGConfig, compute_shadow_mask, compute_sky_view_factor
)


def test_flat_terrain_analytical_limits():
    grid = UrbanGrid(np.zeros((30, 30)), dx=1.0)
    weather = WeatherParameters(sun_altitude_deg=45.0, sun_azimuth_deg=180.0)
    config = SOLWEIGConfig(num_azimuth_svf=16, max_search_dist_m=50.0)

    solver = ReferenceSOLWEIGSolver(weather, config)
    state = solver.solve(grid)

    # On completely flat ground with no obstacles:
    # 1. Shadow mask must be 1.0 everywhere
    assert np.allclose(state.shadow_mask, 1.0)
    # 2. SVF must be 1.0 everywhere
    assert np.allclose(state.svf, 1.0)
    # 3. T_mrt should be uniform
    assert np.isclose(np.min(state.t_mrt), np.max(state.t_mrt), atol=1e-5)
    # 4. T_mrt should be higher than air temp in sunlight
    assert np.all(state.t_mrt > (weather.t_air_k - 273.15))


def test_building_shadow_direction():
    # Grid: 50x50. Sun at South (azimuth 180 deg).
    # Building at center (row 25..30, col 20..30).
    # Light comes from South (higher row indices towards South).
    # Rays step towards South; so shadow is cast towards North (lower row indices).
    h = np.zeros((60, 60))
    h[35:45, 25:35] = 20.0
    grid = UrbanGrid(h, dx=1.0)

    weather = WeatherParameters(sun_altitude_deg=45.0, sun_azimuth_deg=180.0)
    solver = ReferenceSOLWEIGSolver(weather)
    state = solver.solve(grid)

    # Ground north of building (rows < 35, cols 25..35) must be shadowed
    shadowed_patch = state.shadow_mask[20:35, 28:32]
    assert np.any(shadowed_patch == 0.0)

    # Ground south of building (rows > 45) must remain fully illuminated
    illuminated_south = state.shadow_mask[48:58, 28:32]
    assert np.all(illuminated_south == 1.0)

    # T_mrt in shadow must be noticeably lower than unshaded sunny ground
    t_mrt_shadow = state.t_mrt[25, 30]
    t_mrt_sun = state.t_mrt[55, 30]
    assert t_mrt_sun - t_mrt_shadow > 10.0  # Typically >15K difference


def test_solver_determinism():
    grid = UrbanGrid(np.random.RandomState(42).uniform(0, 15, size=(30, 30)), dx=1.0)
    weather = WeatherParameters()
    solver = ReferenceSOLWEIGSolver(weather)

    state1 = solver.solve(grid)
    state2 = solver.solve(grid)

    assert np.array_equal(state1.shadow_mask, state2.shadow_mask)
    assert np.array_equal(state1.svf, state2.svf)
    assert np.array_equal(state1.t_mrt, state2.t_mrt)
