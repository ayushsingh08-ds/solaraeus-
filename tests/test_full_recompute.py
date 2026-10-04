"""
Unit tests for the full reference recomputation path.
Verifies complete pipeline execution, physical energy bounds, and determinism.
"""

import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import create_single_box_scene, create_canyon_scene
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult


@pytest.fixture
def baseline_weather():
    return Weather(
        air_temperature=301.15,          # 28 C
        relative_humidity=50.0,
        wind_speed=2.0,                  # 2 m/s
        wind_direction=180.0,
        direct_normal_irradiance=800.0,  # 800 W/m^2
        diffuse_horizontal_irradiance=160.0
    )


@pytest.fixture
def baseline_config():
    return SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="12:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        sky_patch_configuration=16
    )


def test_full_recompute_execution(baseline_weather, baseline_config):
    scene = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
    result = full_recompute(scene, baseline_weather, baseline_config)

    assert isinstance(result, SimulationResult)
    ny = scene.pedestrian_grid.ny
    nx = scene.pedestrian_grid.nx

    # All fields must have correct shape
    assert result.shadow_mask.shape == (ny, nx)
    assert result.direct_irradiance.shape == (ny, nx)
    assert result.svf.shape == (ny, nx)
    assert result.shortwave_flux.shape == (ny, nx)
    assert result.longwave_flux.shape == (ny, nx)
    assert result.tmrt.shape == (ny, nx)
    assert result.utci.shape == (ny, nx)

    # Check finite values (no NaNs or Infs)
    assert np.all(np.isfinite(result.tmrt))
    assert np.all(np.isfinite(result.utci))
    assert np.all(np.isfinite(result.shortwave_flux))
    assert np.all(np.isfinite(result.longwave_flux))


def test_physical_contrast_sun_vs_shade(baseline_weather, baseline_config):
    # Single 14x14x18m building at center of 60x60m domain
    scene = create_single_box_scene(extent_m=60.0, box_size=14.0, box_height=18.0)
    result = full_recompute(scene, baseline_weather, baseline_config)

    # Building bounds: [23, 37] x [23, 37]
    # Identify pedestrian ground cells that are shaded (outside building) vs fully illuminated
    shaded_cells = (result.shadow_mask == 0.0)
    sunlit_cells = (result.shadow_mask == 1.0)

    assert np.any(shaded_cells), "There must be shaded cells cast by the building!"
    assert np.any(sunlit_cells), "There must be sunlit cells on open ground!"

    mean_tmrt_sun = float(np.mean(result.tmrt[sunlit_cells]))
    # For shaded ground cells not inside the building itself
    # Check max contrast between unshaded open ground and deep building shadow
    min_tmrt_shade = float(np.min(result.tmrt[shaded_cells]))

    # Direct beam elimination causes significant drop in Tmrt (> 10 K)
    assert mean_tmrt_sun - min_tmrt_shade > 10.0


def test_full_recompute_determinism(baseline_weather, baseline_config):
    scene = create_canyon_scene(extent_m=60.0, canyon_width=14.0, building_height=16.0)

    res1 = full_recompute(scene, baseline_weather, baseline_config)
    res2 = full_recompute(scene, baseline_weather, baseline_config)

    assert np.array_equal(res1.shadow_mask, res2.shadow_mask)
    assert np.array_equal(res1.svf, res2.svf)
    assert np.array_equal(res1.tmrt, res2.tmrt)
    assert np.array_equal(res1.utci, res2.utci)


def test_nighttime_recompute(baseline_weather):
    scene = create_single_box_scene(extent_m=40.0)
    # 04:00 UTC = 00:00 EDT (true midnight in NYC in July)
    night_config = SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="04:00:00",
        sky_patch_configuration=16
    )

    result = full_recompute(scene, baseline_weather, night_config)

    # Nighttime: zero direct and diffuse shortwave
    assert np.all(result.shadow_mask == 0.0)
    assert np.all(result.direct_irradiance == 0.0)
    assert np.all(result.shortwave_flux == 0.0)

    # Tmrt should be close to wall/air temperatures (around 20-35 C)
    assert np.all(result.tmrt < 40.0)
