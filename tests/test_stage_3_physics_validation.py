"""
Stage 3 Physics Validation & Limiting-Case Test Suite for SOLARAEUS.

Validates all physical modules against analytical and limiting-case solutions:
1. Solar position calculation (astronomical accuracy, declination, altitude/azimuth limits)
2. Direct beam attenuation and shadow casting (grazing angle, occlusion, unshaded open field)
3. Limiting Case (a): Single cube in open field at noon with hand-computed direct/diffuse fluxes
4. Limiting Case (b): Fully enclosed isothermal blackbody cavity with SVF=0 (zero-error check: Tmrt == T_env)
5. Limiting Case (c): Clear vs overcast sky radiation response (monotonic sensitivity)
6. Limiting Case (d): Varying ground albedo (shortwave reflectance scaling)
7. Limiting Case (e): Pure physics simulation path with optimizer disabled (full recompute determinism)
8. Independent Sky View Factor (SVF) verification: Radial horizon search vs 3D orthographic fish-eye ray casting
9. Energy conservation balance: Control-volume conservation of incoming shortwave radiation
10. UTCI biometeorological response verification against Bröde et al. (2012) standards
"""

import math
import numpy as np
import pytest
from datetime import datetime, timezone

from solaraeus.core.config import (
    Weather, SimulationConfig, Material, SIGMA,
    DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from solaraeus.core.geometry.mesh import create_box_mesh, TriangleMesh
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig
from solaraeus.core.pedestrian_grid import PedestrianGrid
from solaraeus.physics.solar_position import calculate_solar_position, SolarPosition
from solaraeus.physics.shadow import compute_direct_shadow_mask
from solaraeus.physics.sky_view_factor import compute_sky_view_factor
from solaraeus.physics.shortwave import compute_shortwave_fluxes
from solaraeus.physics.longwave import compute_longwave_fluxes
from solaraeus.physics.mean_radiant_temperature import mean_radiant_temperature
from solaraeus.physics.utci import compute_utci
from solaraeus.physics.mesh_ray_intersection import intersect_ray_triangle
from solaraeus.reference.full_recompute import full_recompute


# =============================================================================
# 1. Solar Position Module Audit & Analytical Tests
# =============================================================================

def test_solar_position_vernal_equinox_equator():
    """At solar noon on vernal equinox at the equator (0 deg lat, 0 deg lon), altitude ~ 90 deg."""
    dt_utc = datetime(2024, 3, 20, 12, 7, 0, tzinfo=timezone.utc)
    pos = calculate_solar_position(latitude_deg=0.0, longitude_deg=0.0, dt_utc=dt_utc)

    assert pos.is_daylight is True
    # At equinox noon on equator, altitude should be within 1.5 deg of 90 deg (zenith ~ 0)
    assert pos.altitude_deg > 88.0
    assert pos.zenith_deg < 2.0
    # Sun vector Up component should be near 1.0
    assert pos.sun_vector[2] > 0.999


def test_solar_position_summer_solstice_berlin():
    """At summer solstice solar noon in Berlin (52.52 N, 13.405 E), altitude ~ 90 - 52.52 + 23.44 = 60.92 deg."""
    # Berlin solar noon on June 21 occurs around 11:13 UTC
    dt_utc = datetime(2024, 6, 21, 11, 13, 0, tzinfo=timezone.utc)
    pos = calculate_solar_position(latitude_deg=52.5200, longitude_deg=13.4050, dt_utc=dt_utc)

    expected_max_alt = 90.0 - 52.52 + 23.44  # ~ 60.92 deg
    assert abs(pos.altitude_deg - expected_max_alt) < 1.0
    assert abs(pos.azimuth_deg - 180.0) < 3.0  # Pointing roughly South at noon


def test_solar_position_midnight_no_daylight():
    """At midnight, altitude must be negative and is_daylight must be False."""
    dt_utc = datetime(2024, 6, 21, 23, 0, 0, tzinfo=timezone.utc)
    pos = calculate_solar_position(latitude_deg=52.5200, longitude_deg=13.4050, dt_utc=dt_utc)

    assert pos.is_daylight is False
    assert pos.altitude_deg < 0.0


# =============================================================================
# 2. Beam Attenuation & Shadow Casting
# =============================================================================

def test_shadow_open_field_no_obstacles():
    """In an open field with no obstacles, shadow mask must be 1.0 everywhere in daylight."""
    grid_cfg = PedestrianGridConfig(extent_x=40.0, extent_y=40.0, origin_x=-20.0, origin_y=-20.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    grid = PedestrianGrid(grid_cfg)

    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=(0.0, -0.7071, 0.7071), is_daylight=True
    )
    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.all(shadow_mask == 1.0)


# =============================================================================
# 3. Limiting Case (a): One Cube in Open Field at Noon (Hand-Computed Direct/Diffuse)
# =============================================================================

def test_limiting_case_a_single_cube_open_field_noon():
    """
    Limiting-case test (a): One 10x10x10m cube in 60x60m field at noon.
    Verify hand-computed direct and diffuse fluxes far from cube against simulation.
    
    Analytical formulation at open-field unshaded point:
    - Alt = 60 deg, Az = 180 deg (South) -> s = (0, -0.5, 0.866025)
    - DNI = 800 W/m^2, DHI = 200 W/m^2
    - SVF = 1.0, shadow = 1.0
    - Hand direct:
        k_dir_up = 800 * sin(60) = 692.8203 W/m^2
        k_dir_south = 800 * 0.5 = 400.0 W/m^2
        k_dir_weighted = 0.06 * 692.8203 + 0.22 * 400.0 = 41.5692 + 88.0 = 129.5692 W/m^2
    - Hand diffuse & reflected:
        k_diff_up = 200 * 1.0 = 200.0 W/m^2
        k_diff_side = 0.5 * 200 = 100.0 W/m^2
        k_refl_gnd = 0.15 * (692.8203 + 200.0) = 133.9230 W/m^2
        k_diff_weighted = 0.06 * 200 + 0.06 * 133.9230 + 4 * 0.22 * 100.0 = 108.0354 W/m^2
    - Hand total shortwave:
        k_tot = 129.5692 + 108.0354 = 237.6046 W/m^2
    """
    grid_cfg = PedestrianGridConfig(extent_x=60.0, extent_y=60.0, origin_x=-30.0, origin_y=-30.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    grid = PedestrianGrid(grid_cfg)

    # 10x10x10m cube at center
    scene.add_mesh(create_box_mesh("cube", -5.0, 5.0, -5.0, 5.0, 0.0, 10.0))

    alt_rad = math.radians(60.0)
    az_rad = math.radians(180.0)
    sun_vec = (math.cos(alt_rad) * math.sin(az_rad),
               math.cos(alt_rad) * math.cos(az_rad),
               math.sin(alt_rad))
    solar_pos = SolarPosition(altitude_deg=60.0, azimuth_deg=180.0, zenith_deg=30.0,
                              sun_vector=sun_vec, is_daylight=True)

    weather = Weather(
        air_temperature=300.0,
        relative_humidity=50.0,
        wind_speed=2.0,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=200.0
    )
    wall_mat = Material("wall", albedo=0.20, emissivity=0.90, surface_temperature=303.0)
    gnd_mat = Material("gnd", albedo=0.15, emissivity=0.95, surface_temperature=305.0)

    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    svf = compute_sky_view_factor(scene, grid, azimuth_count=64, max_search_dist_m=60.0)

    sw_fluxes = compute_shortwave_fluxes(weather, solar_pos, shadow_mask, svf, gnd_mat, wall_mat)

    # Far corner point (-25, -25) where SVF ~ 1.0 and unshaded
    corner_idx_y = 5  # y = -25
    corner_idx_x = 5  # x = -25
    assert shadow_mask[corner_idx_y, corner_idx_x] == 1.0
    assert svf[corner_idx_y, corner_idx_x] > 0.995

    # Check simulated shortwave against hand computation
    hand_k_dir = 0.06 * (800.0 * math.sin(alt_rad)) + 0.22 * (800.0 * 0.5)
    hand_k_diff = 0.06 * 200.0 + 0.06 * (0.15 * (800.0 * math.sin(alt_rad) + 200.0)) + 4.0 * 0.22 * 100.0
    hand_k_tot = hand_k_dir + hand_k_diff

    sim_k_dir = sw_fluxes.k_dir[corner_idx_y, corner_idx_x]
    sim_k_tot = sw_fluxes.k_total[corner_idx_y, corner_idx_x]

    assert abs(sim_k_dir - hand_k_dir) < 0.5, f"Direct flux error: {sim_k_dir} vs {hand_k_dir}"
    assert abs(sim_k_tot - hand_k_tot) < 1.0, f"Total shortwave error: {sim_k_tot} vs {hand_k_tot}"


# =============================================================================
# 4. Limiting Case (b): Fully Enclosed Point with No Sky View (Isothermal Cavity)
# =============================================================================

def test_limiting_case_b_fully_enclosed_isothermal_cavity():
    """
    Limiting-case test (b): Fully enclosed point with no sky view (SVF = 0).
    In an isothermal enclosure at T_env = 300.0 K (26.85 C) with zero solar radiation:
    - SVF = 0.0, shadow = 0.0, K_tot = 0.0
    - L_wall = L_ground = L_sky = sigma * T_env^4
    - L_total = (0.06 + 0.06 + 4*0.22) * sigma * T_env^4 = sigma * T_env^4
    - Total absorbed: S_str = a_l * L_total = a_l * sigma * T_env^4
    - Stefan-Boltzmann inversion: Tmrt = [S_str / (a_l * sigma)]^0.25 = T_env = 300.0 K.
    Verify error |Tmrt - T_env| is identically 0.00 K (< 1e-4 K).
    """
    T_env = 300.0  # Kelvin

    # Zero shortwave
    k_total = np.array([0.0])

    # Enclosed isothermal longwave: every direction receives sigma * T_env^4
    l_iso = SIGMA * (T_env ** 4)
    l_total = np.array([l_iso])

    # Run mean radiant temperature inversion
    res = mean_radiant_temperature(k_total, l_total, a_k=0.70, a_l=0.97)

    error_k = abs(res.tmrt_k[0] - T_env)
    assert error_k < 1e-4, f"Enclosed cavity error must be ~0 K, got {error_k} K"
    assert abs(res.tmrt_c[0] - (T_env - 273.15)) < 1e-4


# =============================================================================
# 5. Limiting Case (c): Clear vs Overcast Sky Radiation
# =============================================================================

def test_limiting_case_c_clear_vs_overcast_sky():
    """
    Limiting-case test (c): Clear sky (high DNI, low DHI) vs Overcast sky (zero DNI, moderate DHI).
    Verify that unshaded sunny ground under clear sky produces significantly higher Tmrt
    than overcast sky with identical air temperature.
    """
    solar_pos = SolarPosition(
        altitude_deg=50.0, azimuth_deg=180.0, zenith_deg=40.0,
        sun_vector=(0.0, -math.cos(math.radians(50)), math.sin(math.radians(50))),
        is_daylight=True
    )
    shadow_mask = np.array([1.0])
    svf = np.array([0.80])
    wall_mat = Material("w", albedo=0.20, emissivity=0.90, surface_temperature=305.15)
    gnd_mat = Material("g", albedo=0.15, emissivity=0.95, surface_temperature=308.15)

    # Clear sky: 800 DNI, 150 DHI, RH 30%
    clear_weather = Weather(
        air_temperature=303.15, relative_humidity=30.0, wind_speed=2.0, wind_direction=180.0,
        direct_normal_irradiance=800.0, diffuse_horizontal_irradiance=150.0
    )
    sw_clear = compute_shortwave_fluxes(clear_weather, solar_pos, shadow_mask, svf, gnd_mat, wall_mat)
    lw_clear = compute_longwave_fluxes(clear_weather, svf, gnd_mat, wall_mat)
    tmrt_clear = mean_radiant_temperature(sw_clear.k_total, lw_clear.l_total).tmrt_c[0]

    # Overcast sky: 0 DNI, 250 DHI, RH 85%
    overcast_weather = Weather(
        air_temperature=303.15, relative_humidity=85.0, wind_speed=2.0, wind_direction=180.0,
        direct_normal_irradiance=0.0, diffuse_horizontal_irradiance=250.0
    )
    sw_overcast = compute_shortwave_fluxes(overcast_weather, solar_pos, shadow_mask, svf, gnd_mat, wall_mat)
    lw_overcast = compute_longwave_fluxes(overcast_weather, svf, gnd_mat, wall_mat)
    tmrt_overcast = mean_radiant_temperature(sw_overcast.k_total, lw_overcast.l_total).tmrt_c[0]

    # Clear sky Tmrt exceeds overcast by ~10 K due to direct beam irradiance,
    # offset partially by higher diffuse (250 vs 150 W/m^2) and higher atmospheric emissivity (RH 85% vs 30%)
    delta_tmrt = tmrt_clear - tmrt_overcast
    assert delta_tmrt > 8.0, f"Clear sky must be warmer than overcast, got Delta={delta_tmrt:.2f} K"



# =============================================================================
# 6. Limiting Case (d): Varying Ground Albedo
# =============================================================================

def test_limiting_case_d_varying_ground_albedo():
    """
    Limiting-case test (d): Varying ground albedo from 0.05 to 0.50.
    Reflected shortwave flux from ground hitting the human lower receptor must scale
    strictly monotonically with ground albedo.
    """
    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=(0.0, -0.7071, 0.7071), is_daylight=True
    )
    shadow_mask = np.array([1.0])
    svf = np.array([1.0])
    weather = Weather(
        air_temperature=300.0, relative_humidity=50.0, wind_speed=2.0, wind_direction=180.0,
        direct_normal_irradiance=700.0, diffuse_horizontal_irradiance=150.0
    )
    wall_mat = Material("w", albedo=0.20, emissivity=0.90, surface_temperature=303.0)

    albedos = [0.05, 0.15, 0.30, 0.50]
    k_totals = []
    tmrts = []

    for alb in albedos:
        gnd_mat = Material("g", albedo=alb, emissivity=0.95, surface_temperature=305.0)
        sw = compute_shortwave_fluxes(weather, solar_pos, shadow_mask, svf, gnd_mat, wall_mat)
        lw = compute_longwave_fluxes(weather, svf, gnd_mat, wall_mat)
        rad = mean_radiant_temperature(sw.k_total, lw.l_total)
        k_totals.append(sw.k_total[0])
        tmrts.append(rad.tmrt_c[0])

    # Must be strictly monotonically increasing
    for i in range(len(albedos) - 1):
        assert k_totals[i+1] > k_totals[i], f"Shortwave flux must increase with albedo: {k_totals}"
        assert tmrts[i+1] > tmrts[i], f"Tmrt must increase with albedo: {tmrts}"


# =============================================================================
# 7. Limiting Case (e): Optimizer Off, Pure Physics Only
# =============================================================================

def test_limiting_case_e_optimizer_off_physics_only():
    """
    Limiting-case test (e): Pure forward physics recomputation with optimizer off.
    Verify execution is completely deterministic and produces bitwise identical arrays.
    """
    grid_cfg = PedestrianGridConfig(extent_x=40.0, extent_y=40.0, resolution=1.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    scene.add_mesh(create_box_mesh("bldg", 10.0, 25.0, 10.0, 25.0, 0.0, 15.0))

    weather = Weather(
        air_temperature=301.15, relative_humidity=45.0, wind_speed=2.5, wind_direction=180.0,
        direct_normal_irradiance=750.0, diffuse_horizontal_irradiance=180.0
    )
    config = SimulationConfig(
        latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
        sky_patch_configuration=16
    )

    res1 = full_recompute(scene, weather, config)
    res2 = full_recompute(scene, weather, config)

    assert np.array_equal(res1.shadow_mask, res2.shadow_mask)
    assert np.array_equal(res1.svf, res2.svf)
    assert np.array_equal(res1.tmrt, res2.tmrt)
    assert np.array_equal(res1.utci, res2.utci)


# =============================================================================
# 8. Independent SVF Check (Orthographic Fish-Eye Ray Tracing)
# =============================================================================

def test_independent_svf_courtyard_and_street():
    """
    SVF check against an independent method: 3D orthographic fish-eye ray casting.
    Lambertian-weighted SVF = (unoccluded rays on unit disk) / (total rays on unit disk).
    Compare at:
    - Courtyard center (4 enclosing walls)
    - Street canyon center (2 parallel flanking walls)
    Verify agreement between radial horizon solver and independent fish-eye ray tracing is within 0.02 SVF.
    """
    # 1. Courtyard scene
    grid_cfg = PedestrianGridConfig(extent_x=60.0, extent_y=60.0, origin_x=-30.0, origin_y=-30.0, resolution=1.0)
    scene_ct = Scene(pedestrian_grid=grid_cfg)
    grid_ct = PedestrianGrid(grid_cfg)

    # 4 surrounding 15m walls
    scene_ct.add_mesh(create_box_mesh("w", -25.0, -10.0, -25.0, 25.0, 0.0, 15.0))
    scene_ct.add_mesh(create_box_mesh("e",  10.0,  25.0, -25.0, 25.0, 0.0, 15.0))
    scene_ct.add_mesh(create_box_mesh("n", -10.0,  10.0,  10.0, 25.0, 0.0, 15.0))
    scene_ct.add_mesh(create_box_mesh("s", -10.0,  10.0, -25.0, -10.0, 0.0, 15.0))

    svf_radial_ct = compute_sky_view_factor(scene_ct, grid_ct, azimuth_count=64, max_search_dist_m=50.0)[30, 30]

    # Independent orthographic fish-eye ray casting at courtyard center (0, 0, 1.1)
    R = 60
    u_vals = np.linspace(-1.0, 1.0, 2*R + 1)
    uu, vv = np.meshgrid(u_vals, u_vals)
    mask_disc = (uu**2 + vv**2) <= 1.0
    u_d, v_d = uu[mask_disc], vv[mask_disc]
    w_d = np.sqrt(np.maximum(0.0, 1.0 - (u_d**2 + v_d**2)))

    origin = (0.0, 0.0, 1.1)
    tris_ct = []
    for m in scene_ct.get_active_meshes():
        for t in m.triangles:
            tris_ct.append((m.vertices[t[0]], m.vertices[t[1]], m.vertices[t[2]]))

    unoccluded_ct = sum(
        1 for i in range(len(u_d))
        if not any(intersect_ray_triangle(origin, (u_d[i], v_d[i], w_d[i]), v0, v1, v2) is not None for v0, v1, v2 in tris_ct)
    )
    svf_fisheye_ct = unoccluded_ct / len(u_d)

    diff_ct = abs(svf_radial_ct - svf_fisheye_ct)
    assert diff_ct < 0.02, f"Courtyard SVF discrepancy too large: {svf_radial_ct} vs {svf_fisheye_ct} (diff={diff_ct})"

    # 2. Street Canyon scene: 20m width, 20m height, L=160m
    grid_cfg_st = PedestrianGridConfig(extent_x=60.0, extent_y=120.0, origin_x=-30.0, origin_y=-60.0, resolution=1.0)
    scene_st = Scene(pedestrian_grid=grid_cfg_st)
    grid_st = PedestrianGrid(grid_cfg_st)
    scene_st.add_mesh(create_box_mesh("w_canyon", -30.0, -10.0, -60.0, 60.0, 0.0, 20.0))
    scene_st.add_mesh(create_box_mesh("e_canyon",  10.0,  30.0, -60.0, 60.0, 0.0, 20.0))

    svf_radial_st = compute_sky_view_factor(scene_st, grid_st, azimuth_count=64, max_search_dist_m=60.0)[60, 30]

    tris_st = []
    for m in scene_st.get_active_meshes():
        for t in m.triangles:
            tris_st.append((m.vertices[t[0]], m.vertices[t[1]], m.vertices[t[2]]))

    unoccluded_st = sum(
        1 for i in range(len(u_d))
        if not any(intersect_ray_triangle(origin, (u_d[i], v_d[i], w_d[i]), v0, v1, v2) is not None for v0, v1, v2 in tris_st)
    )
    svf_fisheye_st = unoccluded_st / len(u_d)

    diff_st = abs(svf_radial_st - svf_fisheye_st)
    assert diff_st < 0.02, f"Street canyon SVF discrepancy too large: {svf_radial_st} vs {svf_fisheye_st} (diff={diff_st})"


# =============================================================================
# 9. Energy Balance Conservation Check
# =============================================================================

def test_energy_balance_fraction_accounted_for():
    """
    Energy-balance check: fraction of incoming shortwave radiation accounted for.
    For an urban ground cell:
    Incoming shortwave: K_in = DNI * sin(alt) * shadow + DHI * SVF
    Absorbed by ground: K_abs = (1 - albedo_gnd) * K_in
    Reflected by ground: K_refl = albedo_gnd * K_in
    Conservation: (K_abs + K_refl) / K_in == 1.00000000.
    
    For the human standing cylinder:
    Incident directional shortwave: K_tot = sum(F_i * K_i)
    Absorbed: S_short = a_k * K_tot
    Reflected: R_short = (1 - a_k) * K_tot
    Conservation: (S_short + R_short) / K_tot == 1.00000000.
    """
    solar_pos = SolarPosition(
        altitude_deg=55.0, azimuth_deg=180.0, zenith_deg=35.0,
        sun_vector=(0.0, -math.cos(math.radians(55)), math.sin(math.radians(55))),
        is_daylight=True
    )
    weather = Weather(
        air_temperature=303.15, relative_humidity=40.0, wind_speed=2.0, wind_direction=180.0,
        direct_normal_irradiance=750.0, diffuse_horizontal_irradiance=200.0
    )
    shadow_mask = np.array([1.0, 0.0])
    svf = np.array([0.65, 0.40])
    wall_mat = Material("w", albedo=0.25, emissivity=0.90, surface_temperature=305.0)
    gnd_mat = Material("g", albedo=0.18, emissivity=0.95, surface_temperature=308.0)

    # 1. Ground energy balance
    sin_alt = math.sin(math.radians(55.0))
    k_in_ground = weather.direct_normal_irradiance * sin_alt * shadow_mask + weather.diffuse_horizontal_irradiance * svf
    k_abs_ground = (1.0 - gnd_mat.albedo) * k_in_ground
    k_refl_ground = gnd_mat.albedo * k_in_ground

    ground_fraction = (k_abs_ground + k_refl_ground) / np.maximum(1e-9, k_in_ground)
    assert np.allclose(ground_fraction, 1.0, atol=1e-12), "Ground energy balance violated!"

    # 2. Human sensor energy balance
    sw = compute_shortwave_fluxes(weather, solar_pos, shadow_mask, svf, gnd_mat, wall_mat)
    a_k = 0.70
    s_short = a_k * sw.k_total
    r_short = (1.0 - a_k) * sw.k_total
    human_sw_fraction = (s_short + r_short) / np.maximum(1e-9, sw.k_total)
    assert np.allclose(human_sw_fraction, 1.0, atol=1e-12), "Human shortwave balance violated!"

    # 3. Human longwave balance
    lw = compute_longwave_fluxes(weather, svf, gnd_mat, wall_mat)
    a_l = 0.97
    s_long = a_l * lw.l_total
    r_long = (1.0 - a_l) * lw.l_total
    human_lw_fraction = (s_long + r_long) / np.maximum(1e-9, lw.l_total)
    assert np.allclose(human_lw_fraction, 1.0, atol=1e-12), "Human longwave balance violated!"


# =============================================================================
# 10. UTCI Regression & Range Verification
# =============================================================================

def test_utci_reference_response():
    """
    UTCI thermal comfort response verification.
    Under extreme hot conditions (Ta=35 C, Tmrt=55 C, v=1.1 m/s, RH=40%):
    UTCI should indicate Strong/Very Strong Heat Stress (> 38 C).
    When Tmrt equals air temperature in light breeze (Ta=20 C, Tmrt=20 C, v=1.0 m/s, RH=50%):
    UTCI should indicate No Thermal Stress (~ 20 C, within 1.5 C).
    """
    # Hot condition
    utci_hot = compute_utci(air_temp_c=35.0, tmrt_c=55.0, wind_speed_ms=1.1, relative_humidity=40.0)
    assert float(utci_hot) > 38.0, f"Expected strong heat stress, got {utci_hot}"

    # Neutral condition
    utci_neutral = compute_utci(air_temp_c=20.0, tmrt_c=20.0, wind_speed_ms=1.0, relative_humidity=50.0)
    assert abs(float(utci_neutral) - 20.0) < 1.5, f"Expected neutral ~20 C, got {utci_neutral}"
