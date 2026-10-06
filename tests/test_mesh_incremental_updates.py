"""
Unit tests for exact and certified incremental recomputations on triangular meshes.
"""

from __future__ import annotations
import math
import time
import pytest
import numpy as np

from urban_comfort.geometry.mesh import (
    create_box_mesh,
    create_rotated_box_mesh,
    create_pitched_roof_mesh,
    create_overhang_mesh
)
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.config import SimulationConfig, Weather
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.mesh_update import (
    AddMeshEdit, RemoveMeshEdit, ReplaceMeshEdit, MoveMeshEdit, ChangeMeshHeightEdit
)
from urban_comfort.incremental.update import (
    incremental_update_exact, incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate


@pytest.fixture
def sim_environment():
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


def test_exact_incremental_add_mesh(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline scene: single rotated box mesh at (30, 50)
    m1 = create_rotated_box_mesh("m1", 30.0, 50.0, 12.0, 12.0, 15.0, 30.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m1)
    res_base = full_recompute(scene_base, weather, config)

    # Edit: add pitched roof mesh at (70, 50)
    m2 = create_pitched_roof_mesh("m2", 65.0, 75.0, 45.0, 55.0, eave_height=8.0, ridge_height=16.0)
    edit = AddMeshEdit(m2)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc = incremental_update_exact(scene_base, scene_new, res_base, edit, weather, config)

    # Reused cells must be identical to full recomputation
    diff = np.abs(res_inc.result.tmrt - res_full.tmrt)
    assert np.max(diff) < 1e-10, f"Max difference {np.max(diff):.2e} exceeds float precision"
    assert res_inc.reused_fraction > 0.0, "Exact update must reuse unaffected cells"


def test_exact_incremental_remove_mesh(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline scene with 2 meshes
    m1 = create_box_mesh("m1", 20.0, 35.0, 20.0, 35.0, 0.0, 15.0)
    m2 = create_pitched_roof_mesh("m2", 60.0, 75.0, 60.0, 75.0, eave_height=10.0, ridge_height=18.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m1)
    scene_base.add_mesh(m2)
    res_base = full_recompute(scene_base, weather, config)

    # Remove m2
    edit = RemoveMeshEdit("m2")
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc = incremental_update_exact(scene_base, scene_new, res_base, edit, weather, config)

    diff = np.abs(res_inc.result.tmrt - res_full.tmrt)
    assert np.max(diff) < 1e-10, f"Max difference {np.max(diff):.2e} exceeds precision"


def test_exact_incremental_replace_mesh(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline: flat roof building
    m_flat = create_box_mesh("b_replace", 40.0, 60.0, 40.0, 60.0, 0.0, 12.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m_flat)
    res_base = full_recompute(scene_base, weather, config)

    # Replace with pitched roof
    m_pitch = create_pitched_roof_mesh("b_replace", 40.0, 60.0, 40.0, 60.0, eave_height=12.0, ridge_height=22.0)
    edit = ReplaceMeshEdit("b_replace", m_pitch)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc = incremental_update_exact(scene_base, scene_new, res_base, edit, weather, config)

    diff = np.abs(res_inc.result.tmrt - res_full.tmrt)
    assert np.max(diff) < 1e-10, f"Max difference {np.max(diff):.2e} exceeds precision"


def test_exact_incremental_move_mesh(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline: rotated box at (35, 35)
    m = create_rotated_box_mesh("m_move", 35.0, 35.0, 10.0, 10.0, 14.0, angle_deg=45.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m)
    res_base = full_recompute(scene_base, weather, config)

    # Move by dx=15, dy=15
    edit = MoveMeshEdit("m_move", shift_x=15.0, shift_y=15.0)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc = incremental_update_exact(scene_base, scene_new, res_base, edit, weather, config)

    diff = np.abs(res_inc.result.tmrt - res_full.tmrt)
    assert np.max(diff) < 1e-10, f"Max difference {np.max(diff):.2e} exceeds precision"


def test_exact_incremental_change_mesh_height(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline: box of height 10m
    m = create_box_mesh("m_height", 40.0, 55.0, 40.0, 55.0, 0.0, 10.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m)
    res_base = full_recompute(scene_base, weather, config)

    # Double height to 20m
    edit = ChangeMeshHeightEdit("m_height", new_height=20.0)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)
    res_inc = incremental_update_exact(scene_base, scene_new, res_base, edit, weather, config)

    diff = np.abs(res_inc.result.tmrt - res_full.tmrt)
    assert np.max(diff) < 1e-10, f"Max difference {np.max(diff):.2e} exceeds precision"


def test_certified_incremental_update_mesh_soundness(sim_environment):
    grid_cfg, config, weather = sim_environment

    # Baseline scene
    m1 = create_rotated_box_mesh("m1", 30.0, 50.0, 10.0, 10.0, 12.0, 30.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m1)
    res_base = full_recompute(scene_base, weather, config)

    # Edit: add pitched roof mesh at (70, 50)
    m2 = create_pitched_roof_mesh("m2", 65.0, 75.0, 45.0, 55.0, eave_height=8.0, ridge_height=14.0)
    edit = AddMeshEdit(m2)
    scene_new, _ = edit.apply(scene_base)

    res_full = full_recompute(scene_new, weather, config)

    # Certified update with tolerance 2.0 K
    res_inc, cert = incremental_update_certified(scene_base, scene_new, res_base, edit, weather, config)

    # Verify certificate soundness against ground-truth full recompute
    verif = verify_certificate(cert, res_inc.result.tmrt, res_full.tmrt)

    assert cert.status == "certified"
    assert verif.is_valid, f"Certificate invalid! {verif.num_violations} violations with max {verif.max_violation} K"
    assert verif.num_violations == 0
    assert verif.is_within_tolerance
    assert verif.reused_max_error <= config.tmrt_tolerance, (
        f"Reused max error ({verif.reused_max_error:.4f} K) exceeded tolerance ({config.tmrt_tolerance} K)"
    )
    assert cert.reused_cells > 0.70 * cert.total_cells, (
        f"Expected > 70% reuse, got {cert.reused_cells / cert.total_cells:.1%}"
    )


def test_mesh_selective_recompute_speedup(sim_environment):
    grid_cfg, config, weather = sim_environment

    m1 = create_box_mesh("m1", 20.0, 30.0, 20.0, 30.0, 0.0, 15.0)
    scene_base = Scene(pedestrian_grid=grid_cfg)
    scene_base.add_mesh(m1)
    res_base = full_recompute(scene_base, weather, config)

    m2 = create_box_mesh("m2", 80.0, 90.0, 80.0, 90.0, 0.0, 15.0)
    edit = AddMeshEdit(m2)
    scene_new, _ = edit.apply(scene_base)

    # Time full recompute
    t0_full = time.perf_counter()
    res_full = full_recompute(scene_new, weather, config)
    t_full = time.perf_counter() - t0_full

    # Time certified incremental update
    t0_inc = time.perf_counter()
    res_inc, cert = incremental_update_certified(scene_base, scene_new, res_base, edit, weather, config)
    t_inc = time.perf_counter() - t0_inc

    # Both recomputations produce compliant results
    verif = verify_certificate(cert, res_inc.result.tmrt, res_full.tmrt)
    assert verif.is_valid

    # Selective recomputation step should be faster than full recompute
    assert res_inc.time_selective_recompute_sec < t_full, (
        f"Selective recompute ({res_inc.time_selective_recompute_sec:.4f}s) was not faster than full ({t_full:.4f}s)"
    )
