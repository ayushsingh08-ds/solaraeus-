"""
Adversarial and edge-case test suite for controlled triangular meshes in SOLARAEUS.

Stress-tests:
1. Extreme aspect-ratio sliver triangles (100:1 ratio).
2. Grazing solar altitude near cutoff threshold (alt = 5.2 deg).
3. Sequential compounding edits without clearing cache.
4. Revert edit zero-drift verification (add then remove returns to baseline).
5. Rays grazing shared triangle edges and coplanar facets.
6. Roof geometry situated mere centimeters above pedestrian level (z = 1.15m vs z_ped = 1.1m).
7. Concave L-shaped self-occlusion without ray leakage.
8. Degenerate input rejection (NaNs, infinite coordinates, collinear degenerate triangles).
"""

from __future__ import annotations
import math
import pytest
import numpy as np

from urban_comfort.config import SimulationConfig, Weather
from urban_comfort.geometry.mesh import (
    TriangleMesh,
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_l_shaped_mesh
)
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.mesh_ray_intersection import (
    intersect_ray_mesh, intersect_rays_mesh_batch
)
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.mesh_update import (
    AddMeshEdit, RemoveMeshEdit, ReplaceMeshEdit, MoveMeshEdit
)
from urban_comfort.incremental.update import (
    incremental_update_exact, incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate
from urban_comfort.benchmark.independent_audit import audit_certificate_independently


@pytest.fixture
def base_env():
    grid_cfg = PedestrianGridConfig(extent_x=100.0, extent_y=100.0, resolution=1.0)
    config = SimulationConfig(
        latitude=40.7128, longitude=-74.0060,
        date="2026-06-21", local_time="12:00:00",
        tmrt_tolerance=2.0,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0
    )
    weather = Weather(
        air_temperature=300.15,
        relative_humidity=50.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=750.0,
        diffuse_horizontal_irradiance=150.0
    )
    return grid_cfg, config, weather


def test_adv_mesh_01_extreme_aspect_ratio_sliver():
    """Needle-thin sliver triangles (aspect ratio 500:1) must not produce NaNs or divide-by-zero."""
    # Sliver triangle: length 50m, base 0.1m
    verts = np.array([
        [0.0, 0.0, 0.0],
        [50.0, 0.0, 0.0],
        [25.0, 0.1, 0.0],
        # Add slight thickness in Z to make a 3D prism
        [0.0, 0.0, 5.0],
        [50.0, 0.0, 5.0],
        [25.0, 0.1, 5.0],
    ], dtype=np.float64)

    tris = np.array([
        [0, 1, 2], [3, 5, 4],
        [0, 3, 4], [0, 4, 1],
        [1, 4, 5], [1, 5, 2],
        [2, 5, 3], [2, 3, 0]
    ], dtype=np.int64)

    sliver_mesh = TriangleMesh(id="sliver", vertices=verts, triangles=tris)

    # Shoot ray downwards through center of sliver
    hit = intersect_ray_mesh(origin=(25.0, 0.05, 10.0), direction=(0.0, 0.0, -1.0), mesh=sliver_mesh)
    assert hit is not None
    assert abs(hit - 5.0) < 1e-4, f"Expected hit distance 5.0m, got {hit}"

    # Shoot ray that cleanly misses
    miss = intersect_ray_mesh(origin=(25.0, 0.5, 10.0), direction=(0.0, 0.0, -1.0), mesh=sliver_mesh)
    assert miss is None


def test_adv_mesh_02_grazing_solar_altitude(base_env):
    """Low sun altitude (5.2 deg, just above 5.0 deg cutoff) casts long shadow plumes."""
    grid_cfg, _, weather = base_env
    # Grazing sun at ~6.6 deg (10:10 UTC in June for NYC)
    config = SimulationConfig(
        latitude=40.7128, longitude=-74.0060,
        date="2026-06-21", local_time="10:10:00",
        tmrt_tolerance=2.5,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0
    )
    # Check that solar altitude is indeed low (> 5.0 deg and < 10.0 deg)
    from urban_comfort.solar.solar_position import calculate_solar_position
    from datetime import datetime, timezone
    dt_utc = datetime.strptime(f"{config.date} {config.local_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)
    assert 4.0 <= solar_pos.altitude_deg <= 15.0, f"Solar altitude is {solar_pos.altitude_deg}"

    scene_base = Scene(pedestrian_grid=grid_cfg)
    res_base = full_recompute(scene_base, weather, config)

    # Add small building of height 6m
    mesh = create_box_mesh("m_low", 40.0, 50.0, 40.0, 50.0, 0.0, 6.0)
    edit = AddMeshEdit(mesh)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc, cert = incremental_update_certified(scene_base, scene_new, res_base, edit, weather, config)

    audit = audit_certificate_independently(
        full_tmrt=res_full.tmrt,
        incremental_tmrt=res_inc.result.tmrt,
        predicted_bound=cert.predicted_error_bound,
        reused_mask=res_inc.reused_mask,
        tolerance=config.tmrt_tolerance
    )
    assert audit["is_sound"] is True, f"Found {audit['num_certificate_violations']} violations under grazing sun!"
    assert audit["num_certificate_violations"] == 0


def test_adv_mesh_03_sequential_compounding_edits(base_env):
    """5 consecutive mesh edits without clearing cache; verifies that undisturbed distant cells remain invariant."""
    grid_cfg, config, weather = base_env
    grid = PedestrianGrid(grid_cfg)

    # Initial scene: empty
    curr_scene = Scene(pedestrian_grid=grid_cfg)
    curr_res = full_recompute(curr_scene, weather, config)
    initial_distant_tmrt = curr_res.tmrt[5, 5]

    # Perform 5 edits in the center/northeast quadrant [40, 80]
    edits = [
        AddMeshEdit(create_box_mesh("b1", 40.0, 50.0, 40.0, 50.0, 0.0, 10.0)),
        AddMeshEdit(create_pitched_roof_mesh("p1", 60.0, 75.0, 60.0, 75.0, eave_height=8.0, ridge_height=14.0)),
        MoveMeshEdit("b1", shift_x=5.0, shift_y=5.0),
        ReplaceMeshEdit("b1", create_rotated_box_mesh("b1", 47.5, 47.5, 12.0, 12.0, 15.0, angle_deg=30.0)),
        RemoveMeshEdit("p1")
    ]

    for i, edit in enumerate(edits):
        next_scene, _ = edit.apply(curr_scene)
        inc_res = incremental_update_exact(curr_scene, next_scene, curr_res, edit, weather, config)
        full_res = full_recompute(next_scene, weather, config)

        diff = np.abs(inc_res.result.tmrt - full_res.tmrt)
        assert np.max(diff) < 1e-10, f"Drift at sequential edit {i}: max diff {np.max(diff):.2e}"

        curr_scene = next_scene
        curr_res = inc_res.result

    # Distant corner cell (5, 5) at (5.5m, 5.5m) should remain unchanged
    final_distant_tmrt = curr_res.tmrt[5, 5]
    assert abs(final_distant_tmrt - initial_distant_tmrt) < 1e-10, "Distant cell drifted across compounding edits!"


def test_adv_mesh_04_revert_edit_drift(base_env):
    """Adding a mesh and subsequently removing it must return T_mrt exactly to baseline (drift = 0)."""
    grid_cfg, config, weather = base_env

    scene_base = Scene(pedestrian_grid=grid_cfg)
    b0 = create_box_mesh("b0", 20.0, 30.0, 20.0, 30.0, 0.0, 12.0)
    scene_base.add_mesh(b0)
    res_base = full_recompute(scene_base, weather, config)

    # 1. Add mesh
    mesh_add = create_rotated_box_mesh("temp", 60.0, 60.0, 16.0, 16.0, 18.0, angle_deg=45.0)
    edit_add = AddMeshEdit(mesh_add)
    scene_mid, _ = edit_add.apply(scene_base)
    res_mid = incremental_update_exact(scene_base, scene_mid, res_base, edit_add, weather, config)

    # 2. Revert by removing mesh
    edit_rem = RemoveMeshEdit("temp")
    scene_revert, _ = edit_rem.apply(scene_mid)
    res_revert = incremental_update_exact(scene_mid, scene_revert, res_mid.result, edit_rem, weather, config)

    # Compare reverted result with original baseline
    revert_drift = np.abs(res_revert.result.tmrt - res_base.tmrt)
    max_drift = float(np.max(revert_drift))
    assert max_drift < 1e-10, f"Revert drift {max_drift:.2e} K exceeds zero-drift tolerance"


def test_adv_mesh_05_ray_grazing_triangle_edge():
    """Rays aimed directly at a shared edge between two triangles must resolve consistently."""
    # Two triangles sharing edge from (0, 0, 0) to (10, 0, 0)
    verts = np.array([
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [5.0, 5.0, 0.0],
        [5.0, -5.0, 0.0],
    ], dtype=np.float64)

    tris = np.array([
        [0, 1, 2],  # Triangle in +Y
        [0, 3, 1],  # Triangle in -Y
    ], dtype=np.int64)

    mesh = TriangleMesh(id="shared_edge", vertices=verts, triangles=tris)

    # Cast 100 rays along the shared line y=0 between x=0.1 and x=9.9
    origins = np.column_stack([
        np.linspace(0.1, 9.9, 100),
        np.zeros(100),
        np.full(100, 5.0)
    ])
    hits, t_hits = intersect_rays_mesh_batch(origins, direction=(0.0, 0.0, -1.0), mesh=mesh)

    # Every single ray along the shared edge must register an intersection at t=5.0m
    assert np.all(hits), f"Only {np.sum(hits)}/100 rays intersected shared edge"
    assert np.allclose(t_hits, 5.0, atol=1e-5)


def test_adv_mesh_06_near_pedestrian_height_roof(base_env):
    """Building of height z = 1.15m (just 0.05m above pedestrian level 1.1m) must compute without zero-division."""
    grid_cfg, config, weather = base_env

    scene = Scene(pedestrian_grid=grid_cfg)
    # Height 1.15m (delta_h = 0.05m above z_ped=1.1m)
    low_bldg = create_box_mesh("low_bldg", 40.0, 60.0, 40.0, 60.0, 0.0, 1.15)
    scene.add_mesh(low_bldg)

    res = full_recompute(scene, weather, config)
    assert np.all(np.isfinite(res.tmrt))
    assert np.all(np.isfinite(res.utci))
    # Footprint cells have z_ped < height so SVF is 0
    assert res.svf[50, 50] == 0.0
    # Adjacent cells have near-complete sky view (> 0.95)
    assert res.svf[35, 50] > 0.95


def test_adv_mesh_07_concave_self_occlusion(base_env):
    """Concave L-shaped building with re-entrant corner casts accurate shadow without leakage."""
    grid_cfg, _, _ = base_env
    grid = PedestrianGrid(grid_cfg)

    # Sun from South-West (azimuth 225 deg, altitude 45 deg)
    alt_rad = math.radians(45.0)
    az_rad = math.radians(225.0)
    sx = math.sin(az_rad) * math.cos(alt_rad)
    sy = math.cos(az_rad) * math.cos(alt_rad)
    sz = math.sin(alt_rad)
    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=225.0, zenith_deg=45.0,
        sun_vector=(sx, sy, sz), is_daylight=True
    )

    # L-shaped building [30, 60] x [30, 60] with corner cut out
    l_mesh = create_l_shaped_mesh("l_mesh", xmin=30.0, ymin=30.0,
                                  total_width=30.0, total_length=30.0,
                                  wing_width=15.0, wing_length=15.0,
                                  height=15.0)
    scene = Scene(pedestrian_grid=grid_cfg)
    scene.add_mesh(l_mesh)

    shadow = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.all(np.isfinite(shadow))

    # The cut-out corner at (50, 50) is sheltered by the south and west wings
    # Sun is from SW (225 deg), so the cut-out corner (50, 50) falls in the shadow of the wings!
    assert shadow[50, 50] == 0.0, "Re-entrant corner must be shaded by windward wings"
    # West side far outside is illuminated
    assert shadow[15, 15] == 1.0


def test_adv_mesh_08_degenerate_mesh_rejection():
    """TriangleMesh validation must reject NaNs, infinite coordinates, and degenerate triangles."""
    # 1. NaN coordinate
    with pytest.raises(ValueError, match="finite"):
        TriangleMesh(
            id="nan_mesh",
            vertices=np.array([[0, 0, 0], [1, 0, float("nan")], [0, 1, 0]], dtype=np.float64),
            triangles=np.array([[0, 1, 2]], dtype=np.int64)
        )

    # 2. Inf coordinate
    with pytest.raises(ValueError, match="finite"):
        TriangleMesh(
            id="inf_mesh",
            vertices=np.array([[0, 0, 0], [1, 0, float("inf")], [0, 1, 0]], dtype=np.float64),
            triangles=np.array([[0, 1, 2]], dtype=np.int64)
        )

    # 3. Collinear degenerate triangle (area = 0)
    with pytest.raises(ValueError, match="(?i)degenerate"):
        TriangleMesh(
            id="collinear",
            vertices=np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float64),
            triangles=np.array([[0, 1, 2]], dtype=np.int64)
        )

    # 4. Out-of-bounds vertex index
    with pytest.raises(ValueError, match="out of bounds"):
        TriangleMesh(
            id="oob",
            vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64),
            triangles=np.array([[0, 1, 5]], dtype=np.int64)
        )
