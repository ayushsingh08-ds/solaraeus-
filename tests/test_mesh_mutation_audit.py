"""
Mesh Mutation Audit Testing for SOLARAEUS.

Executes synthetic mutation tests on mesh-based certified incremental updates
to verify that the independent audit detector is non-vacuous and reliably flags
certificate violations when safety invariants or error bounds are corrupted.
"""

from __future__ import annotations
import math
import numpy as np
import pytest

from urban_comfort.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.mesh import create_box_mesh, create_pitched_roof_mesh
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.solar.solar_position import calculate_solar_position
from urban_comfort.incremental.mesh_update import ChangeMeshHeightEdit
from urban_comfort.incremental.update import incremental_update_certified
from urban_comfort.benchmark.independent_audit import audit_certificate_independently
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci


@pytest.fixture
def mesh_audit_scene() -> Tuple[Scene, Scene, SimulationConfig, Weather]:
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1)
    scene = Scene(pedestrian_grid=grid_cfg)
    scene.add_mesh(create_box_mesh("mesh_bldg", 25.0, 45.0, 25.0, 45.0, 0.0, 15.0))

    cfg = SimulationConfig(
        latitude=48.8566,
        longitude=2.3522,
        date="2026-07-15",
        local_time="14:00:00",
        pedestrian_height=1.1,
        grid_resolution=1.0,
        tmrt_tolerance=0.5,
        numerical_tolerance=0.05,
        sky_patch_configuration=16,
        max_svf_search_dist_m=80.0
    )

    weather = Weather(
        air_temperature=30.0,
        relative_humidity=45.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=850.0,
        diffuse_horizontal_irradiance=150.0
    )

    # Edit: increase height 15m -> 28m (+13m)
    edit = ChangeMeshHeightEdit("mesh_bldg", new_height=28.0)
    new_scene, _ = edit.apply(scene)

    return scene, new_scene, cfg, weather


def test_clean_mesh_audit_is_sound_with_zero_violations(mesh_audit_scene):
    """Verify that unmutated mesh incremental recomputation is 100% sound with 0 violations."""
    scene, new_scene, cfg, weather = mesh_audit_scene
    edit = ChangeMeshHeightEdit("mesh_bldg", new_height=28.0)

    prev_res = full_recompute(scene, weather, cfg)
    full_res = full_recompute(new_scene, weather, cfg)

    inc_res, cert = incremental_update_certified(scene, new_scene, prev_res, edit, weather, cfg)

    audit = audit_certificate_independently(
        full_tmrt=full_res.tmrt,
        incremental_tmrt=inc_res.result.tmrt,
        predicted_bound=cert.predicted_error_bound,
        reused_mask=inc_res.reused_mask,
        tolerance=cfg.tmrt_tolerance
    )

    assert audit["is_sound"] is True
    assert audit["num_certificate_violations"] == 0
    assert audit["num_tolerance_violations"] == 0
    assert audit["min_slack"] >= -1e-6
    assert audit["reused_max_actual_error"] <= cfg.tmrt_tolerance + 1e-6


def test_mutation_zero_predicted_error_bound(mesh_audit_scene):
    """
    Mutation A: Artificially set predicted error bound to zero everywhere.
    The audit must detect that actual error exceeds the zero bound on reused cells.
    """
    scene, new_scene, cfg, weather = mesh_audit_scene
    edit = ChangeMeshHeightEdit("mesh_bldg", new_height=28.0)

    prev_res = full_recompute(scene, weather, cfg)
    full_res = full_recompute(new_scene, weather, cfg)

    inc_res, cert = incremental_update_certified(scene, new_scene, prev_res, edit, weather, cfg)

    # Mutate: Zero out predicted error bound
    mutated_bound = np.zeros_like(cert.predicted_error_bound)

    audit = audit_certificate_independently(
        full_tmrt=full_res.tmrt,
        incremental_tmrt=inc_res.result.tmrt,
        predicted_bound=mutated_bound,
        reused_mask=inc_res.reused_mask,
        tolerance=cfg.tmrt_tolerance
    )

    # Must flag violations because actual error on reused cells > 0
    if np.any(inc_res.reused_mask):
        reused_errors = np.abs(full_res.tmrt - inc_res.result.tmrt)[inc_res.reused_mask]
        if np.max(reused_errors) > 1e-4:
            assert audit["is_sound"] is False
            assert audit["num_certificate_violations"] > 0
            assert audit["min_slack"] < 0.0


def test_mutation_unsafe_recompute_truncation(mesh_audit_scene):
    """
    Mutation B: Severely truncate the recompute region so cells where shadow actually
    changed are erroneously reused with zero predicted bound.
    The audit must flag substantial certificate violations and tolerance violations.
    """
    scene, new_scene, cfg, weather = mesh_audit_scene
    edit = ChangeMeshHeightEdit("mesh_bldg", new_height=28.0)

    prev_res = full_recompute(scene, weather, cfg)
    full_res = full_recompute(new_scene, weather, cfg)

    grid = PedestrianGrid(new_scene.pedestrian_grid)

    # Mutate: only recompute a tiny 1-cell box, reusing all other cells
    mutated_recompute_mask = np.zeros(grid.shape, dtype=bool)
    mutated_recompute_mask[40, 40] = True
    mutated_reused_mask = ~mutated_recompute_mask

    # Naive assembly reusing prev_res elsewhere
    mutated_tmrt = prev_res.tmrt.copy()
    mutated_tmrt[mutated_recompute_mask] = full_res.tmrt[mutated_recompute_mask]

    # Mutate bound to claim error is 0 everywhere
    mutated_bound = np.zeros(grid.shape, dtype=np.float64)

    audit = audit_certificate_independently(
        full_tmrt=full_res.tmrt,
        incremental_tmrt=mutated_tmrt,
        predicted_bound=mutated_bound,
        reused_mask=mutated_reused_mask,
        tolerance=cfg.tmrt_tolerance
    )

    # Significant violations must be detected
    assert audit["is_sound"] is False
    assert audit["num_certificate_violations"] > 0
    assert audit["is_within_tolerance"] is False
    assert audit["num_tolerance_violations"] > 0
    assert audit["max_actual_error"] > 5.0  # Dramatic error due to omitted shadow plume!
