"""
Unit and property-based tests for Certificate Soundness:
Verifies that actual_error(x) <= predicted_bound(x) across 100% of domain cells.
"""

import numpy as np
import pytest
from solaraeus.core.geometry import UrbanGrid, AddBuilding, RemoveBuilding, ChangeHeight, MoveBuilding
from solaraeus.core.solweig import WeatherParameters, SOLWEIGConfig
from solaraeus.benchmark.runner import run_experiment


@pytest.mark.parametrize("tol", [0.1, 0.5, 1.0, 2.0])
def test_certificate_soundness_add_building(tol):
    grid = UrbanGrid(np.zeros((50, 50)), dx=1.0)
    weather = WeatherParameters(sun_altitude_deg=45.0, sun_azimuth_deg=180.0)
    config = SOLWEIGConfig(num_azimuth_svf=16, max_search_dist_m=40.0)
    edit = AddBuilding(xmin=20, xmax=28, ymin=25, ymax=33, height=14.0)

    rec = run_experiment(grid, edit, weather, config, tolerance_k=tol, case_name="test_add")

    assert rec.is_sound, f"Soundness violated! {rec.num_violations} violations with max {rec.max_violation_k} K"
    assert rec.is_within_tolerance, "Reused cells exceeded user tolerance threshold!"


@pytest.mark.parametrize("tol", [0.2, 0.8])
def test_certificate_soundness_remove_building(tol):
    h = np.zeros((50, 50))
    h[20:30, 20:30] = 15.0
    grid = UrbanGrid(h, dx=1.0)
    weather = WeatherParameters(sun_altitude_deg=35.0, sun_azimuth_deg=135.0)
    config = SOLWEIGConfig(num_azimuth_svf=16, max_search_dist_m=40.0)
    edit = RemoveBuilding(xmin=20, xmax=29, ymin=20, ymax=29)

    rec = run_experiment(grid, edit, weather, config, tolerance_k=tol, case_name="test_remove")

    assert rec.is_sound, f"Soundness violated on remove: max violation {rec.max_violation_k} K"
    assert rec.is_within_tolerance


def test_exact_unchanged_region_zero_error():
    # Large domain: 80x80. Small edit at (10, 10).
    # Far corner at (70..80, 70..80) is far beyond max_search_dist (30m) and shadow frustum.
    grid = UrbanGrid(np.zeros((80, 80)), dx=1.0)
    weather = WeatherParameters(sun_altitude_deg=60.0, sun_azimuth_deg=180.0)
    config = SOLWEIGConfig(num_azimuth_svf=16, max_search_dist_m=25.0)
    edit = AddBuilding(xmin=10, xmax=15, ymin=10, ymax=15, height=8.0)

    rec = run_experiment(grid, edit, weather, config, tolerance_k=0.5, case_name="test_exact_zero")

    far_patch_err = rec.actual_error_map[60:80, 60:80]
    far_patch_bnd = rec.predicted_bound_map[60:80, 60:80]

    # In far patch, both bound and error should be identically zero
    assert np.allclose(far_patch_err, 0.0, atol=1e-12)
    assert np.allclose(far_patch_bnd, 0.0, atol=1e-12)
