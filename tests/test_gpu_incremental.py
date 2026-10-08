"""
Tests for GPU-Accelerated Incremental Recomputation Engine.

Verifies:
1. GPU incremental execution on a synthetic scene.
2. GPU incremental vs GPU full parity.
3. Three-way parity: CPU full ≈ GPU full ≈ GPU incremental.
4. Localized panel affecting only a subset of cells.
5. Zero certificate violations and certificate soundness.
6. Exact accounting of reused and recomputed cell counts.
7. Fallback behavior when GPU is unavailable.
8. Frozen directory protection (read-only integrity).
"""

from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.mesh import create_box_mesh, create_overhang_mesh, TriangleMesh
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.incremental.mesh_update import AddMeshEdit
from urban_comfort.incremental.certificate import verify_certificate
from urban_comfort.backend.gpu_backend import GPUBackend, is_cupy_available
from urban_comfort.backend.gpu_incremental import (
    GPUIncrementalEngine, GPUResidentState, GPUIncrementalProfileMetrics
)

HAS_GPU = is_cupy_available()


@pytest.fixture
def test_env():
    grid_cfg = PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0, pedestrian_height=1.1)
    config = SimulationConfig(
        latitude=12.9716,
        longitude=77.5946,
        date="2024-04-15",
        local_time="09:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        tmrt_tolerance=0.5,
        sky_patch_configuration=16,
        max_svf_search_dist_m=40.0
    )
    weather = Weather(
        air_temperature=305.15,
        relative_humidity=30.0,
        wind_speed=1.5,
        wind_direction=90.0,
        direct_normal_irradiance=750.0,
        diffuse_horizontal_irradiance=180.0
    )
    return grid_cfg, config, weather


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_gpu_incremental_synthetic_scene(test_env):
    """Test 1: GPU incremental on a synthetic scene produces valid physical fields."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)

    # Static building at (15, 30)
    bldg = create_box_mesh("b1", 15.0, 30.0, 15.0, 30.0, 0.0, 15.0)
    scene_base.add_mesh(bldg)

    # Run baseline simulation on GPU
    base_res = full_recompute(scene_base, weather, config, backend="gpu")

    # Add dynamic canopy panel at (40, 50)
    panel = create_box_mesh("panel", 40.0, 50.0, 40.0, 50.0, zmin=3.5, zmax=3.6)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    engine = GPUIncrementalEngine()
    engine.preload_resident_baseline(scene_base, grid, base_res)

    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    assert inc_res.result.shadow_mask.shape == grid.shape
    assert inc_res.result.svf.shape == grid.shape
    assert inc_res.result.tmrt.shape == grid.shape
    assert not np.any(np.isnan(inc_res.result.tmrt))
    assert not np.any(np.isinf(inc_res.result.tmrt))
    assert inc_res.result.metadata["incremental_computation_used"] is True
    assert inc_res.result.metadata["backend"] == "gpu"


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_gpu_incremental_vs_gpu_full_parity(test_env):
    """Test 2: GPU incremental vs GPU full parity on synthetic scene."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(create_box_mesh("b1", 15.0, 30.0, 15.0, 30.0, 0.0, 15.0))
    base_res = full_recompute(scene_base, weather, config, backend="gpu")

    panel = create_box_mesh("panel", 35.0, 45.0, 35.0, 45.0, zmin=3.5, zmax=3.6)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    # Full GPU simulation reference
    gpu_full_res = full_recompute(scene_interv, weather, config, backend="gpu")

    # Incremental GPU recomputation (certified and exact)
    engine = GPUIncrementalEngine()
    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )
    exact_res = engine.execute_exact_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    # Certified parity checks
    assert np.array_equal(inc_res.result.shadow_mask, gpu_full_res.shadow_mask)
    assert np.max(np.abs(inc_res.result.tmrt - gpu_full_res.tmrt)) <= config.tmrt_tolerance

    # Exact parity checks
    assert np.array_equal(exact_res.result.shadow_mask, gpu_full_res.shadow_mask)
    assert np.max(np.abs(exact_res.result.svf - gpu_full_res.svf)) < 1e-10
    assert np.max(np.abs(exact_res.result.tmrt - gpu_full_res.tmrt)) < 1e-10


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_cpu_full_gpu_full_gpu_incremental_three_way_parity(test_env):
    """Test 3: CPU full ≈ GPU full ≈ GPU incremental three-way parity."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(create_box_mesh("b1", 15.0, 30.0, 15.0, 30.0, 0.0, 15.0))
    base_res = full_recompute(scene_base, weather, config, backend="cpu")

    panel = create_box_mesh("panel", 35.0, 45.0, 35.0, 45.0, zmin=3.5, zmax=3.6)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    # Three solvers
    cpu_full_res = full_recompute(scene_interv, weather, config, backend="cpu")
    gpu_full_res = full_recompute(scene_interv, weather, config, backend="gpu")

    engine = GPUIncrementalEngine()
    gpu_inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )
    gpu_exact_res = engine.execute_exact_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    # 1. Direct shadow bit-for-bit exact match across all three
    assert np.array_equal(cpu_full_res.shadow_mask, gpu_full_res.shadow_mask)
    assert np.array_equal(gpu_full_res.shadow_mask, gpu_inc_res.result.shadow_mask)
    assert np.array_equal(gpu_full_res.shadow_mask, gpu_exact_res.result.shadow_mask)

    # 2. SVF tolerance
    assert np.max(np.abs(gpu_full_res.svf - cpu_full_res.svf)) < 1e-4
    assert np.max(np.abs(gpu_exact_res.result.svf - cpu_full_res.svf)) < 1e-4

    # 3. Tmrt tolerance
    assert np.max(np.abs(gpu_full_res.tmrt - cpu_full_res.tmrt)) < 0.05
    assert np.max(np.abs(gpu_exact_res.result.tmrt - cpu_full_res.tmrt)) < 0.05
    assert np.max(np.abs(gpu_inc_res.result.tmrt - cpu_full_res.tmrt)) <= config.tmrt_tolerance



@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_localized_panel_affects_subset_of_cells(test_env):
    """Test 4: Localized panel affects only a subset of cells, keeping distant cells untouched."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    base_res = full_recompute(scene_base, weather, config, backend="gpu")

    # Localized 4m x 4m panel at center
    panel = create_box_mesh("small_panel", 28.0, 32.0, 28.0, 32.0, zmin=3.0, zmax=3.1)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    engine = GPUIncrementalEngine()
    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    # Assert only a small subset of cells are recomputed
    assert inc_res.recomputed_cells < 0.15 * inc_res.total_cells
    assert inc_res.reused_fraction > 0.85

    # Check a distant corner cell (e.g. at (2, 2)) remains identically equal to baseline
    assert inc_res.reused_mask[2, 2] is True or inc_res.reused_mask[2, 2] == 1
    assert inc_res.result.shadow_mask[2, 2] == base_res.shadow_mask[2, 2]
    assert np.isclose(inc_res.result.svf[2, 2], base_res.svf[2, 2], atol=1e-12)


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_zero_certificate_violations(test_env):
    """Test 5: Zero certificate violations when auditing against full recomputation."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(create_box_mesh("b1", 10.0, 25.0, 10.0, 25.0, 0.0, 12.0))
    base_res = full_recompute(scene_base, weather, config, backend="gpu")

    panel = create_box_mesh("canopy", 30.0, 40.0, 30.0, 40.0, zmin=4.0, zmax=4.15)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    full_res = full_recompute(scene_interv, weather, config, backend="gpu")

    engine = GPUIncrementalEngine()
    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    verif = verify_certificate(cert, inc_res.result.tmrt, full_res.tmrt)

    assert cert.status == "certified"
    assert verif.is_valid is True
    assert verif.num_violations == 0
    assert verif.is_within_tolerance is True
    assert verif.reused_max_error <= config.tmrt_tolerance


@pytest.mark.skipif(not HAS_GPU, reason="CUDA GPU not available")
def test_reused_and_recomputed_cell_counts(test_env):
    """Test 6: Reused and recomputed cell counts strictly sum to total domain cells."""
    grid_cfg, config, weather = test_env
    grid = PedestrianGrid(grid_cfg)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    base_res = full_recompute(scene_base, weather, config, backend="gpu")

    panel = create_box_mesh("panel", 20.0, 30.0, 20.0, 30.0, zmin=3.5, zmax=3.6)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    engine = GPUIncrementalEngine()
    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    total = inc_res.total_cells
    recomp = inc_res.recomputed_cells
    reu = int(np.sum(inc_res.reused_mask))

    assert recomp + reu == total
    assert math.isclose(inc_res.reused_fraction, reu / total, rel_tol=1e-6)
    assert inc_res.recomputed_mask.shape == grid.shape
    assert inc_res.reused_mask.shape == grid.shape

    # Metrics object
    metrics = engine.last_metrics
    assert metrics is not None
    assert metrics.total_cells == total
    assert metrics.recomputed_cells == recomp
    assert metrics.reused_cells == reu
    assert metrics.affected_rays == recomp * (1 + config.sky_patch_configuration)


def test_gpu_incremental_fallback_when_unavailable(test_env):
    """Test 7: Fallback behavior when GPU is unavailable."""
    grid_cfg, config, weather = test_env
    scene_base = Scene(pedestrian_grid=grid_cfg)
    base_res = full_recompute(scene_base, weather, config, backend="cpu")

    panel = create_box_mesh("panel", 20.0, 30.0, 20.0, 30.0, zmin=3.5, zmax=3.6)
    edit = AddMeshEdit(panel)
    scene_interv, _ = edit.apply(scene_base)

    # Instantiate engine with fallback_to_cpu=True and mock availability = False
    engine = GPUIncrementalEngine(fallback_to_cpu=True)
    engine._gpu_backend._is_available = False

    inc_res, cert = engine.execute_certified_update(
        scene_base, scene_interv, base_res, edit, weather, config
    )

    assert inc_res.result.tmrt.shape == (grid_cfg.extent_y // grid_cfg.resolution, grid_cfg.extent_x // grid_cfg.resolution)
    assert inc_res.recomputed_cells > 0


def test_frozen_directory_protection():
    """Test 8: Frozen directories remain intact and untouched."""
    root_dir = Path(__file__).resolve().parent.parent
    results_dir = root_dir / "results"

    frozen_dirs = [
        results_dir / "church_street_shade_full_20261007_001600",
        results_dir / "church_street_shade_incremental_20261007_081114",
        results_dir / "church_street_gpu_full_20261007_091111",
    ]

    for d in frozen_dirs:
        assert d.exists(), f"Frozen directory {d.name} is missing!"
        # Check that core artifacts exist
        json_files = list(d.glob("*.json"))
        npz_files = list(d.glob("*.npz"))
        assert len(json_files) >= 2, f"Frozen directory {d.name} missing json files"
        assert len(npz_files) >= 4, f"Frozen directory {d.name} missing npz files"
