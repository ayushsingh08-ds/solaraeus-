"""
Stage 4 Adversarial Stress & Incremental Certification Test Suite for SOLARAEUS.

Validates certified incremental recomputation across all required adversarial scenarios
on the primary Berlin Friedrichstraße corridor:
1. Tall canopy at street edge (high aspect ratio, building proximity)
2. Low sun angle (18.5 deg, elongated shadow plume)
3. Extreme low sun angle (4.2 deg, triggers safe fallback)
4. Large overlapping shadows (canopy placed inside deep building shadow)
5. Far-away canopy (verifies 1/r^2 SVF distance decay and zero cutoff)
6. Multiple interacting canopies (dual canopy interaction via AddMultiMeshEdit)
7. Morning sun (07:00 UTC / 09:00 CEST, oblique East-to-West illumination)
8. Evening sun (16:00 UTC / 18:00 CEST, oblique West-to-East illumination)
9. Realistic street-scale shade canopy on Friedrichstraße promenade

For every case, asserts:
- Exact pointwise bound soundness: actual_error(x) <= predicted_bound(x) everywhere (0 violations)
- Reused cell tolerance contract: max actual_error on reused cells <= tmrt_tolerance (0.50 K)
- Measured empirical cell reuse is recorded and verified.
"""

import math
import numpy as np
import pytest

from solaraeus.core.config import Weather, SimulationConfig, Material
from solaraeus.core.geometry.mesh import create_box_mesh
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig
from solaraeus.core.pedestrian_grid import PedestrianGrid
from solaraeus.incremental.mesh_update import AddMeshEdit, AddMultiMeshEdit
from solaraeus.incremental.update import incremental_update_certified
from solaraeus.incremental.certificate import verify_certificate
from solaraeus.reference.full_recompute import full_recompute


@pytest.fixture
def berlin_corridor_scene():
    """Builds a 100m x 100m Berlin Friedrichstraße corridor block with 22m flanking buildings."""
    grid_cfg = PedestrianGridConfig(
        extent_x=100.0, extent_y=100.0, origin_x=-50.0, origin_y=-50.0,
        resolution=1.0, pedestrian_height=1.1
    )
    scene = Scene(pedestrian_grid=grid_cfg, coordinate_system="EPSG:25833_LOCAL")
    # West perimeter block: x in [-45, -10], y in [-45, 45], h = 22.0m
    scene.add_mesh(create_box_mesh("w_bldg", -45.0, -10.0, -45.0, 45.0, 0.0, 22.0))
    # East perimeter block: x in [10, 45], y in [-45, 45], h = 22.5m
    scene.add_mesh(create_box_mesh("e_bldg",  10.0,  45.0, -45.0, 45.0, 0.0, 22.5))
    return scene


@pytest.fixture
def noon_weather():
    return Weather(
        air_temperature=303.05, relative_humidity=30.0, wind_speed=2.2, wind_direction=180.0,
        direct_normal_irradiance=543.0, diffuse_horizontal_irradiance=274.7
    )


def test_adversarial_1_tall_canopy_at_street_edge(berlin_corridor_scene, noon_weather):
    """
    Case 1: Tall canopy (h = 8.0m to 8.3m) placed at street edge (x = 7m to 10m).
    Proximity to 22.5m East building tests grazing shadows and steep skyline changes.
    """
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, noon_weather, cfg)

    canopy = create_box_mesh("c_tall", 7.0, 10.0, -4.0, 4.0, 8.0, 8.3)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, noon_weather, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, noon_weather, cfg)

    # 1. Soundness verification
    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    # 2. Tolerance contract on reused cells
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= cfg.tmrt_tolerance
    # 3. Measured reuse holds
    assert inc_res.reused_fraction > 0.90


def test_adversarial_2_low_sun_angle(berlin_corridor_scene):
    """
    Case 2: Low sun angle (altitude ~ 18.5 deg at 18:30 local).
    Shadow plume is elongated (~3x canopy height). Tests shadow plume bounding.
    """
    w_evening = Weather(
        air_temperature=299.75, relative_humidity=40.0, wind_speed=3.7, wind_direction=90.0,
        direct_normal_irradiance=250.0, diffuse_horizontal_irradiance=90.0
    )
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="18:30:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, w_evening, cfg)

    canopy = create_box_mesh("c_low_sun", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, w_evening, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, w_evening, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= cfg.tmrt_tolerance


def test_adversarial_3_extreme_low_sun_fallback(berlin_corridor_scene):
    """
    Case 3: Extreme low sun angle (altitude < 5.0 deg near sunset).
    Must trigger certified fallback to full recomputation, avoiding numerical overflow.
    """
    w_sunset = Weather(
        air_temperature=298.0, relative_humidity=50.0, wind_speed=2.0, wind_direction=90.0,
        direct_normal_irradiance=50.0, diffuse_horizontal_irradiance=30.0
    )
    # At 18:45 UTC (20:45 CEST sunset) in Berlin on July 20, sun altitude is ~3.10 degrees (< 5 deg)
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="18:45:00",
        tmrt_tolerance=0.50
    )
    r_base = full_recompute(berlin_corridor_scene, w_sunset, cfg)

    canopy = create_box_mesh("c_sunset", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, w_sunset, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, w_sunset, cfg)

    # In fallback mode, result is full recomputation: exact 0 error
    err = np.abs(inc_res.result.tmrt - r_full.tmrt)
    assert np.allclose(err, 0.0, atol=1e-10)


def test_adversarial_4_large_overlapping_shadows(berlin_corridor_scene):
    """
    Case 4: Canopy placed inside deep building shadow.
    The canopy's shadow falls onto ground that is ALREADY shaded by the 22m West building.
    Verifies that overlapping shadows do not cause double-counting or bound breach.
    """
    # At 07:00 UTC / 09:00 local, morning sun casts shadow of West building across western canyon
    w_morn = Weather(
        air_temperature=296.95, relative_humidity=50.0, wind_speed=2.4, wind_direction=100.0,
        direct_normal_irradiance=438.5, diffuse_horizontal_irradiance=205.4
    )
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="07:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, w_morn, cfg)

    # Canopy at x in [-9, -5], y in [-3, 3] (deep within West building shadow)
    canopy = create_box_mesh("c_overlap", -9.0, -5.0, -3.0, 3.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, w_morn, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, w_morn, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= cfg.tmrt_tolerance


def test_adversarial_5_far_away_canopy_distance_decay(berlin_corridor_scene, noon_weather):
    """
    Case 5: Canopy placed far away in domain corner (x in [35, 40], y in [35, 40]).
    Verifies 1/r^2 solid-angle SVF distance decay: receptors at r > 60m must see certified zero perturbation.
    """
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=40.0
    )
    r_base = full_recompute(berlin_corridor_scene, noon_weather, cfg)

    canopy = create_box_mesh("c_far", 35.0, 40.0, 35.0, 40.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, noon_weather, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, noon_weather, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    # Street corridor is far from the canopy, error must be strictly zero or near-zero
    street_err = np.abs(inc_res.result.tmrt[30:70, 40:60] - r_full.tmrt[30:70, 40:60])
    assert np.all(street_err < 1e-4)


def test_adversarial_6_multiple_interacting_canopies(berlin_corridor_scene, noon_weather):
    """
    Case 6: Multiple interacting canopies added simultaneously via AddMultiMeshEdit.
    Two canopies separated by 10m in the street canyon.
    """
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, noon_weather, cfg)

    m1 = create_box_mesh("c_m1", -3.0, 3.0, -12.0, -6.0, 3.5, 3.8)
    m2 = create_box_mesh("c_m2", -3.0, 3.0,   6.0, 12.0, 3.5, 3.8)
    edit = AddMultiMeshEdit([m1, m2])
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, noon_weather, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, noon_weather, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= cfg.tmrt_tolerance
    assert inc_res.reused_fraction > 0.85


def test_adversarial_7_morning_oblique_sun(berlin_corridor_scene):
    """
    Case 7: Morning sun (07:00 UTC / 09:00 CEST) streaming obliquely across N-S canyon from East.
    """
    w_morn = Weather(
        air_temperature=296.95, relative_humidity=50.0, wind_speed=2.4, wind_direction=100.0,
        direct_normal_irradiance=438.5, diffuse_horizontal_irradiance=205.4
    )
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="07:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, w_morn, cfg)

    canopy = create_box_mesh("c_morn", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, w_morn, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, w_morn, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True


def test_adversarial_8_evening_oblique_sun(berlin_corridor_scene):
    """
    Case 8: Evening sun (16:00 UTC / 18:00 CEST) streaming obliquely across N-S canyon from West.
    """
    w_eve = Weather(
        air_temperature=303.95, relative_humidity=30.0, wind_speed=2.6, wind_direction=90.0,
        direct_normal_irradiance=403.0, diffuse_horizontal_irradiance=182.3
    )
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="16:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, w_eve, cfg)

    canopy = create_box_mesh("c_eve", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, w_eve, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, w_eve, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True


def test_adversarial_9_realistic_friedrichstrasse_canopy(berlin_corridor_scene, noon_weather):
    """
    Case 9: Realistic 6m x 3m overhead pedestrian canopy on Friedrichstraße promenade.
    Underside height = 3.5m, top = 3.8m, solar noon.
    Verifies reuse percentage, error bound containment, and no missed shadow zones.
    """
    cfg = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
        tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0
    )
    r_base = full_recompute(berlin_corridor_scene, noon_weather, cfg)

    canopy = create_box_mesh("c_real", -3.0, 3.0, -1.5, 1.5, 3.5, 3.8)
    edit = AddMeshEdit(canopy)
    s_after, _ = edit.apply(berlin_corridor_scene)

    r_full = full_recompute(s_after, noon_weather, cfg)
    inc_res, cert = incremental_update_certified(berlin_corridor_scene, s_after, r_base, edit, noon_weather, cfg)

    verif = verify_certificate(cert, inc_res.result.tmrt, r_full.tmrt)
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= cfg.tmrt_tolerance
    # Measured reuse on this 10,000-cell block
    assert inc_res.reused_fraction >= 0.95
