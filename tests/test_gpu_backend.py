"""
Deterministic CPU vs GPU Simulation Backend Parity Tests.

Validates that the GPU execution backend produces identical results (or results well within
rigorous numerical tolerances) compared to the trusted CPU reference solver across:
- Direct shadow masks
- Directional visibility and Sky View Factor (SVF)
- Radiative fluxes (shortwave, longwave)
- Thermal comfort metrics (Tmrt, UTCI)
across diverse synthetic geometries and boundary conditions.
"""

from __future__ import annotations
import math
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.mesh import TriangleMesh, create_box_mesh
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition, calculate_solar_position
from urban_comfort.backend import (
    SimulationBackend, CPUBackend, GPUBackend,
    get_backend, is_gpu_available, FlattenedSceneGeometry
)
from urban_comfort.reference.full_recompute import full_recompute


# Check if CUDA GPU is functional
HAS_GPU = is_gpu_available()


@pytest.fixture
def standard_weather():
    return Weather(
        air_temperature=308.15,
        relative_humidity=25.0,
        wind_speed=1.5,
        wind_direction=90.0,
        direct_normal_irradiance=750.0,
        diffuse_horizontal_irradiance=180.0
    )


@pytest.fixture
def standard_config():
    return SimulationConfig(
        latitude=12.9716,
        longitude=77.5946,
        date="2024-04-15",
        local_time="09:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        sky_patch_configuration=32,
        max_svf_search_dist_m=60.0
    )


def test_backend_factory_and_availability():
    cpu_b = get_backend("cpu")
    assert isinstance(cpu_b, CPUBackend)
    assert cpu_b.name == "cpu"
    assert cpu_b.is_available() is True

    auto_b = get_backend("auto")
    assert isinstance(auto_b, (CPUBackend, GPUBackend))

    with pytest.raises(ValueError, match="Unknown simulation backend"):
        get_backend("invalid_backend_name")

    if HAS_GPU:
        gpu_b = get_backend("gpu")
        assert isinstance(gpu_b, GPUBackend)
        assert gpu_b.name == "gpu"
        assert gpu_b.is_available() is True


def test_flattened_scene_geometry_conversion():
    scene = Scene(pedestrian_grid=PedestrianGridConfig(extent_x=50.0, extent_y=50.0))
    bldg = Building(
        id="b1",
        footprint=BoundingBox2D(xmin=10.0, xmax=20.0, ymin=10.0, ymax=20.0),
        height=15.0,
        material_id="default_wall"
    )
    scene.add_building(bldg)

    mesh = create_box_mesh("m1", 25.0, 35.0, 25.0, 35.0, 0.0, 12.0, material_id="default_wall")
    scene.add_mesh(mesh)

    geom = FlattenedSceneGeometry.from_scene(scene)
    assert geom.num_buildings == 1
    assert geom.num_triangles == 12
    assert geom.num_vertices == 8
    assert len(geom.bldg_boxes) == 1
    assert np.allclose(geom.bldg_boxes[0], [10.0, 20.0, 10.0, 20.0, 0.0, 15.0])

    # Test conversion of buildings to triangles
    geom_tri = FlattenedSceneGeometry.from_scene(scene, convert_buildings_to_triangles=True)
    assert geom_tri.num_buildings == 1
    assert geom_tri.num_triangles == 24  # 12 (mesh) + 12 (converted building)
    assert geom_tri.num_vertices == 16


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_synthetic_single_building_shadow_parity():
    """Validates exact bit parity of direct shadow between CPU and GPU for a single AABB building."""
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0, pedestrian_height=1.1))
    scene = Scene(pedestrian_grid=grid.config)
    bldg = Building(
        id="box",
        footprint=BoundingBox2D(xmin=20.0, xmax=35.0, ymin=20.0, ymax=35.0),
        height=16.1
    )
    scene.add_building(bldg)

    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=(0.0, -math.cos(math.radians(45.0)), math.sin(math.radians(45.0))),
        is_daylight=True
    )

    cpu_b = CPUBackend()
    gpu_b = GPUBackend()

    cpu_mask = cpu_b.compute_direct_shadow(scene, grid, solar_pos)
    gpu_mask = gpu_b.compute_direct_shadow(scene, grid, solar_pos)

    assert cpu_mask.shape == gpu_mask.shape
    diff_count = np.sum(cpu_mask != gpu_mask)
    assert diff_count == 0, f"Discrepancy in single building shadow mask: {diff_count} differing cells"


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_synthetic_canyon_shadow_and_svf_parity():
    """Validates CPU vs GPU parity on a two-building urban street canyon."""
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0, pedestrian_height=1.1))
    scene = Scene(pedestrian_grid=grid.config)

    # East building and West building forming a North-South canyon between X=20 and X=40
    scene.add_building(Building("east_bldg", BoundingBox2D(5.0, 20.0, 5.0, 55.0), height=20.0))
    scene.add_building(Building("west_bldg", BoundingBox2D(40.0, 55.0, 5.0, 55.0), height=20.0))

    solar_pos = SolarPosition(
        altitude_deg=60.0, azimuth_deg=135.0, zenith_deg=30.0,
        sun_vector=(
            math.sin(math.radians(135.0)) * math.cos(math.radians(60.0)),
            math.cos(math.radians(135.0)) * math.cos(math.radians(60.0)),
            math.sin(math.radians(60.0))
        ),
        is_daylight=True
    )

    cpu_b = CPUBackend()
    gpu_b = GPUBackend()

    # 1. Shadow comparison
    cpu_shadow = cpu_b.compute_direct_shadow(scene, grid, solar_pos)
    gpu_shadow = gpu_b.compute_direct_shadow(scene, grid, solar_pos)
    diff_shadow = np.sum(cpu_shadow != gpu_shadow)
    assert diff_shadow == 0, f"Canyon shadow mismatch: {diff_shadow} differing cells"

    # 2. SVF comparison
    cpu_svf = cpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=60.0)
    gpu_svf = gpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=60.0)

    svf_max_diff = np.max(np.abs(cpu_svf - gpu_svf))
    svf_mean_diff = np.mean(np.abs(cpu_svf - gpu_svf))

    assert svf_max_diff < 1e-4, f"Canyon SVF max diff exceeded: {svf_max_diff:.6e}"
    assert svf_mean_diff < 1e-6, f"Canyon SVF mean diff exceeded: {svf_mean_diff:.6e}"


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_synthetic_triangle_mesh_shadow_and_svf_parity():
    """Validates CPU vs GPU parity on 3D triangular mesh objects."""
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=50.0, extent_y=50.0, resolution=1.0, pedestrian_height=1.1))
    scene = Scene(pedestrian_grid=grid.config)

    # 12-triangle box mesh
    mesh1 = create_box_mesh("m_box1", 15.0, 30.0, 15.0, 30.0, 0.0, 18.0)
    mesh2 = create_box_mesh("m_box2", 35.0, 45.0, 35.0, 45.0, 0.0, 10.0)
    scene.add_mesh(mesh1)
    scene.add_mesh(mesh2)

    solar_pos = SolarPosition(
        altitude_deg=50.0, azimuth_deg=220.0, zenith_deg=40.0,
        sun_vector=(
            math.sin(math.radians(220.0)) * math.cos(math.radians(50.0)),
            math.cos(math.radians(220.0)) * math.cos(math.radians(50.0)),
            math.sin(math.radians(50.0))
        ),
        is_daylight=True
    )

    cpu_b = CPUBackend()
    gpu_b = GPUBackend()

    # Shadow check
    cpu_shadow = cpu_b.compute_direct_shadow(scene, grid, solar_pos)
    gpu_shadow = gpu_b.compute_direct_shadow(scene, grid, solar_pos)
    assert np.array_equal(cpu_shadow, gpu_shadow), "Mesh shadow mask discrepancy between CPU and GPU"

    # SVF check
    cpu_svf = cpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=50.0)
    gpu_svf = gpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=50.0)

    max_diff = np.max(np.abs(cpu_svf - gpu_svf))
    assert max_diff < 1e-4, f"Mesh SVF max diff exceeded: {max_diff:.6e}"


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_synthetic_mixed_scene_parity():
    """Validates parity on mixed scenes with both AABB buildings and TriangleMeshes."""
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0, pedestrian_height=1.1))
    scene = Scene(pedestrian_grid=grid.config)

    # 1 AABB Building
    scene.add_building(Building("bldg_aabb", BoundingBox2D(10.0, 25.0, 10.0, 25.0), height=14.0))

    # 1 TriangleMesh
    scene.add_mesh(create_box_mesh("mesh_box", 35.0, 50.0, 30.0, 45.0, 0.0, 16.0))

    solar_pos = SolarPosition(
        altitude_deg=40.0, azimuth_deg=160.0, zenith_deg=50.0,
        sun_vector=(
            math.sin(math.radians(160.0)) * math.cos(math.radians(40.0)),
            math.cos(math.radians(160.0)) * math.cos(math.radians(40.0)),
            math.sin(math.radians(40.0))
        ),
        is_daylight=True
    )

    cpu_b = CPUBackend()
    gpu_b = GPUBackend()

    cpu_shadow = cpu_b.compute_direct_shadow(scene, grid, solar_pos)
    gpu_shadow = gpu_b.compute_direct_shadow(scene, grid, solar_pos)
    assert np.array_equal(cpu_shadow, gpu_shadow)

    cpu_svf = cpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=60.0)
    gpu_svf = gpu_b.compute_sky_view_factor(scene, grid, num_azimuths=32, max_search_dist_m=60.0)
    assert np.max(np.abs(cpu_svf - gpu_svf)) < 1e-4


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_roi_mask_selective_evaluation_parity():
    """Validates that roi_mask selective evaluation preserves uncomputed cells and matches CPU on active cells."""
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=40.0, extent_y=40.0, resolution=1.0))
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_building(Building("b1", BoundingBox2D(15.0, 25.0, 15.0, 25.0), height=12.0))

    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=(0.0, -math.cos(math.radians(45.0)), math.sin(math.radians(45.0))),
        is_daylight=True
    )

    # ROI mask covering only the Northern half (Y >= 20)
    roi_mask = np.zeros(grid.shape, dtype=bool)
    roi_mask[20:, :] = True

    cpu_b = CPUBackend()
    gpu_b = GPUBackend()

    cpu_shadow = cpu_b.compute_direct_shadow(scene, grid, solar_pos, roi_mask=roi_mask)
    gpu_shadow = gpu_b.compute_direct_shadow(scene, grid, solar_pos, roi_mask=roi_mask)

    # Inactive region must remain 1.0 (illuminated)
    assert np.all(cpu_shadow[:20, :] == 1.0)
    assert np.all(gpu_shadow[:20, :] == 1.0)
    # Active region must match exactly
    assert np.array_equal(cpu_shadow[20:, :], gpu_shadow[20:, :])


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_synthetic_end_to_end_full_simulate_parity(standard_weather, standard_config):
    """
    Validates end-to-end full simulation parity between CPU and GPU solvers across all physical fields.
    """
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=50.0, extent_y=50.0, resolution=1.0))
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_mesh(create_box_mesh("m1", 15.0, 30.0, 15.0, 30.0, 0.0, 16.0))

    cpu_res = full_recompute(scene, standard_weather, standard_config, backend="cpu")
    gpu_res = full_recompute(scene, standard_weather, standard_config, backend="gpu")

    # 1. Shadow mask
    diff_shadow = np.sum(cpu_res.shadow_mask != gpu_res.shadow_mask)
    assert diff_shadow == 0, f"Shadow mask discrepancy: {diff_shadow}"

    # 2. SVF
    svf_max_diff = float(np.max(np.abs(cpu_res.svf - gpu_res.svf)))
    assert svf_max_diff < 1e-4, f"SVF max diff: {svf_max_diff:.6e}"

    # 3. Direct horizontal irradiance
    direct_max_diff = float(np.max(np.abs(cpu_res.direct_irradiance - gpu_res.direct_irradiance)))
    assert direct_max_diff < 1e-4, f"Direct irradiance max diff: {direct_max_diff:.6e}"

    # 4. Total shortwave flux
    sw_max_diff = float(np.max(np.abs(cpu_res.shortwave_flux - gpu_res.shortwave_flux)))
    assert sw_max_diff < 0.01, f"Shortwave flux max diff: {sw_max_diff:.6e} W/m2"

    # 5. Total longwave flux
    lw_max_diff = float(np.max(np.abs(cpu_res.longwave_flux - gpu_res.longwave_flux)))
    assert lw_max_diff < 0.01, f"Longwave flux max diff: {lw_max_diff:.6e} W/m2"

    # 6. Mean Radiant Temperature (Tmrt)
    tmrt_max_diff = float(np.max(np.abs(cpu_res.tmrt - gpu_res.tmrt)))
    assert tmrt_max_diff < 0.05, f"Tmrt max diff: {tmrt_max_diff:.6e} K (tolerance 0.05 K)"

    # 7. UTCI
    utci_max_diff = float(np.max(np.abs(cpu_res.utci - gpu_res.utci)))
    assert utci_max_diff < 0.05, f"UTCI max diff: {utci_max_diff:.6e} C"

    # 8. Check profiling metadata
    assert "gpu_profile" in gpu_res.metadata
    profile = gpu_res.metadata["gpu_profile"]
    assert profile is not None
    assert profile["total_runtime_s"] > 0.0
    assert profile["kernel_runtime_s"] > 0.0
    assert profile["total_ray_count"] > 0
    assert profile["num_triangles"] == 12


def test_gpu_backend_fallback_behavior():
    """Validates that fallback_to_cpu=True safely degrades to CPU when GPU unavailable."""
    backend = GPUBackend(fallback_to_cpu=True)
    assert backend._fallback_to_cpu is True
    assert backend._cpu_backend is not None


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_church_street_gpu_parity_against_frozen_reference():
    """
    Validates GPU simulation against frozen CPU reference on the full Church Street scene (28,120 cells).
    """
    import json
    from pathlib import Path
    root_dir = Path(__file__).resolve().parent.parent
    frozen_dir = root_dir / "results" / "church_street_shade_full_20261007_001600"
    prep_dir = root_dir / "results" / "church_street_preprocessing_20261006_224238"
    handoff_dir = root_dir / "bengaluru_church_street_manual_handoff_v2" / "bengaluru_church_street_manual_handoff_v2"

    if not frozen_dir.exists() or not prep_dir.exists():
        pytest.skip("Church Street reference directories not found")

    cpu_shadow = np.load(frozen_dir / "intervention_shadow.npz")["shadow_mask"]
    cpu_svf = np.load(frozen_dir / "intervention_visibility.npz")["svf"]
    cpu_tmrt = np.load(frozen_dir / "intervention_tmrt.npz")["tmrt"]
    cpu_utci = np.load(frozen_dir / "intervention_utci.npz")["utci"]

    panel_def = json.loads((handoff_dir / "data" / "processed" / "intervention_definition.json").read_text(encoding="utf-8"))
    context_mesh_json = json.loads((prep_dir / "shadow_context_mesh.json").read_text(encoding="utf-8"))

    local_poly = panel_def["modified_geometry_local"]["geometry"]["coordinates"][0]
    pts_2d = np.array(local_poly[:-1] if np.allclose(local_poly[0], local_poly[-1]) else local_poly, dtype=np.float64)
    signed_area = 0.5 * sum(pts_2d[i, 0] * pts_2d[(i+1)%4, 1] - pts_2d[(i+1)%4, 0] * pts_2d[i, 1] for i in range(4))
    ccw_pts = pts_2d[::-1] if signed_area < 0 else pts_2d

    v_base = np.column_stack([ccw_pts, np.full(4, 3.5, dtype=np.float64)])
    v_top = np.column_stack([ccw_pts, np.full(4, 3.6, dtype=np.float64)])
    vertices_3d = np.vstack([v_base, v_top])

    triangles_list = []
    for i in range(4):
        j = (i + 1) % 4
        triangles_list.append((i, j, j + 4))
        triangles_list.append((i, j + 4, i + 4))
    triangles_list.append((4, 5, 6))
    triangles_list.append((4, 6, 7))
    triangles_list.append((0, 2, 1))
    triangles_list.append((0, 3, 2))
    triangles_3d = np.array(triangles_list, dtype=np.int64)

    panel_mesh = TriangleMesh(
        id=panel_def["intervention_id"],
        vertices=vertices_3d,
        triangles=triangles_3d,
        material_id="SHADE_PANEL_ASSUMED_001",
        enabled=True
    )

    mat_wall = Material(id="building_wall", albedo=0.30, emissivity=0.90, surface_temperature=308.15, is_opaque=True)
    mat_roof = Material(id="building_roof", albedo=0.20, emissivity=0.90, surface_temperature=308.15, is_opaque=True)
    mat_ground = Material(id="ground", albedo=0.20, emissivity=0.95, surface_temperature=308.15, is_opaque=True)
    mat_pavement = Material(id="pavement", albedo=0.30, emissivity=0.95, surface_temperature=308.15, is_opaque=True)
    mat_panel = Material(id="SHADE_PANEL_ASSUMED_001", albedo=0.60, emissivity=0.90, surface_temperature=308.15, is_opaque=True)

    materials = {
        "default_wall": mat_wall,
        "default_ground": mat_ground,
        "building_wall": mat_wall,
        "building_roof": mat_roof,
        "ground": mat_ground,
        "pavement": mat_pavement,
        "SHADE_PANEL_ASSUMED_001": mat_panel,
    }

    scene = Scene.from_dict(context_mesh_json)
    scene.materials = materials
    scene.add_mesh(panel_mesh)

    weather = Weather(
        air_temperature=308.15,
        relative_humidity=19.729,
        wind_speed=1.5,
        wind_direction=90.0,
        direct_normal_irradiance=728.31,
        diffuse_horizontal_irradiance=172.18,
    )
    sim_config = SimulationConfig(
        latitude=12.974900,
        longitude=77.605400,
        date="2024-04-15",
        local_time="09:00:00",
        pedestrian_height=1.1,
        grid_resolution=2.0,
        tmrt_tolerance=0.5,
        sky_patch_configuration=32,
        max_svf_search_dist_m=120.0,
        backend="gpu"
    )

    gpu_backend = GPUBackend()
    gpu_res = gpu_backend.full_simulate(scene, weather, sim_config)

    # 1. Shadow mask exact bit parity
    assert np.array_equal(cpu_shadow, gpu_res.shadow_mask)

    # 2. SVF tolerance parity
    svf_diff = np.abs(cpu_svf - gpu_res.svf)
    assert np.max(svf_diff) < 1e-4

    # 3. Tmrt tolerance parity
    tmrt_diff = np.abs(cpu_tmrt - gpu_res.tmrt)
    assert np.max(tmrt_diff) < 0.05

    # 4. UTCI finite cell parity
    valid = np.isfinite(cpu_utci) & np.isfinite(gpu_res.utci)
    utci_diff = np.abs(cpu_utci[valid] - gpu_res.utci[valid])
    assert np.max(utci_diff) < 0.05

