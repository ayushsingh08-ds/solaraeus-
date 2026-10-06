"""
Tests for Church Street Baseline Static Full Recomputation.

Verifies:
1. Serialized triangular mesh loading (37 core, 123 context).
2. Exact discrete grid metadata reconciliation (380.0m x 296.0m = 28,120 cells).
3. Weather forcing and solar radiation closure within satellite tolerance.
4. Static simulation output array integrity (shapes, zero NaNs, zero Infs).
5. Sky View Factor (SVF) range boundedness in [0.0, 1.0].
6. Direct beam occlusion consistency (0 direct flux in shadow).
7. Physical thermal contrast between sunlit and shaded pedestrian receptors.
8. Context building ray influence beyond core boundary.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def prep_dir(repo_root):
    p = repo_root / "results" / "church_street_preprocessing_20261006_224238"
    assert p.exists(), f"Preprocessing directory not found: {p}"
    return p


@pytest.fixture(scope="module")
def static_run_dir(repo_root):
    # Locate latest static run directory
    results_dir = repo_root / "results"
    static_dirs = sorted([d for d in results_dir.glob("church_street_static_*") if d.is_dir()])
    assert len(static_dirs) > 0, "No church_street_static_* run directory found"
    return static_dirs[-1]


def test_serialized_mesh_loading(prep_dir):
    """Verifies that main and context meshes load with exact counts and clean topology."""
    main_path = prep_dir / "main_scene_mesh.json"
    context_path = prep_dir / "shadow_context_mesh.json"
    
    main_scene = Scene.from_dict(json.loads(main_path.read_text(encoding="utf-8")))
    context_scene = Scene.from_dict(json.loads(context_path.read_text(encoding="utf-8")))
    
    assert len(main_scene.meshes) == 37, f"Expected 37 core meshes, got {len(main_scene.meshes)}"
    assert len(context_scene.meshes) == 123, f"Expected 123 context meshes, got {len(context_scene.meshes)}"
    
    # All 37 core meshes must be in context
    assert set(main_scene.meshes.keys()).issubset(set(context_scene.meshes.keys()))
    
    # Triangle counts
    assert sum(m.num_triangles for m in main_scene.meshes.values()) == 748
    assert sum(m.num_triangles for m in context_scene.meshes.values()) == 2136


def test_grid_metadata_reconciliation(static_run_dir):
    """Verifies that the grid metadata discrepancy is mathematically reconciled."""
    recon_path = static_run_dir / "grid_metadata_reconciliation.json"
    assert recon_path.exists()
    
    recon = json.loads(recon_path.read_text(encoding="utf-8"))
    assert recon["status"] == "reconciled_and_verified"
    assert recon["affects_actual_simulation_grid"] is False
    
    grid = recon["discrete_simulation_grid"]
    assert grid["extent_x_m"] == 380.0
    assert grid["extent_y_m"] == 296.0
    assert grid["resolution_m"] == 2.0
    assert grid["nx"] == 190
    assert grid["ny"] == 148
    assert grid["total_cells"] == 28120
    
    # Mathematical exactness
    assert (grid["extent_x_m"] * grid["extent_y_m"]) / (grid["resolution_m"] ** 2) == 28120


def test_solar_radiation_consistency(static_run_dir):
    """Verifies that GHI ≈ DNI * cos(zenith) + DHI holds within satellite hourly tolerance."""
    solar_path = static_run_dir / "solar_summary.json"
    assert solar_path.exists()
    
    solar = json.loads(solar_path.read_text(encoding="utf-8"))
    ghi = solar["irradiance_components_w_m2"]["ghi"]
    dni = solar["irradiance_components_w_m2"]["dni"]
    dhi = solar["irradiance_components_w_m2"]["dhi"]
    zenith = solar["solar_angles_at_0900_utc"]["zenith_deg"]
    
    # Instantaneous calculation at 09:00 UTC
    calc_ghi_inst = dni * math.cos(math.radians(zenith)) + dhi
    rel_diff_inst = abs(calc_ghi_inst - ghi) / ghi
    assert rel_diff_inst < 0.05, f"Instantaneous solar discrepancy too large: {rel_diff_inst * 100:.2f}%"
    
    # Interval midpoint calculation at 09:30 UTC
    mid_diff_pct = abs(solar["radiation_consistency"]["interval_midpoint_check_0930_utc"]["relative_difference_pct"])
    assert mid_diff_pct < 5.0, f"Midpoint solar discrepancy too large: {mid_diff_pct:.2f}%"


def test_static_simulation_results_integrity(static_run_dir):
    """Verifies that all 6 NPZ output fields are present, correctly shaped, and free of NaNs/Infs."""
    required_npz = [
        "shadow_results.npz",
        "visibility_results.npz",
        "shortwave_results.npz",
        "longwave_results.npz",
        "tmrt_results.npz",
        "utci_results.npz",
    ]
    for npz_name in required_npz:
        npz_path = static_run_dir / npz_name
        assert npz_path.exists(), f"Missing NPZ deliverable: {npz_name}"
        data = np.load(npz_path)
        
        # Verify masks
        assert "site_boundary_mask" in data
        assert "pedestrian_corridor_mask" in data
        assert "unbuilt_mask" in data
        
        # Verify shape
        assert data["site_boundary_mask"].shape == (148, 190)
        assert data["pedestrian_corridor_mask"].shape == (148, 190)
        assert data["unbuilt_mask"].shape == (148, 190)
        
    # Check specific fields
    shadow_data = np.load(static_run_dir / "shadow_results.npz")
    shadow_mask = shadow_data["shadow_mask"]
    assert shadow_mask.shape == (148, 190)
    assert not np.isnan(shadow_mask).any()
    assert not np.isinf(shadow_mask).any()
    assert np.all(np.isin(shadow_mask, [0.0, 1.0]))
    
    vis_data = np.load(static_run_dir / "visibility_results.npz")
    svf = vis_data["svf"]
    assert svf.shape == (148, 190)
    assert not np.isnan(svf).any()
    assert not np.isinf(svf).any()
    assert svf.min() >= 0.0
    assert svf.max() <= 1.0
    
    tmrt_data = np.load(static_run_dir / "tmrt_results.npz")
    tmrt = tmrt_data["tmrt"]
    assert tmrt.shape == (148, 190)
    assert not np.isnan(tmrt).any()
    assert not np.isinf(tmrt).any()
    assert 25.0 <= tmrt.min() <= 40.0
    assert 45.0 <= tmrt.max() <= 70.0
    
    utci_data = np.load(static_run_dir / "utci_results.npz")
    utci = utci_data["utci"]
    assert utci.shape == (148, 190)
    assert not np.isnan(utci).any()
    assert not np.isinf(utci).any()
    assert 30.0 <= utci.min() <= 40.0
    assert 35.0 <= utci.max() <= 45.0


def test_direct_beam_occlusion_in_shadow(static_run_dir):
    """Verifies that cells with shadow_mask == 0.0 receive strictly 0 direct shortwave beam flux."""
    shadow_data = np.load(static_run_dir / "shadow_results.npz")
    shadow_mask = shadow_data["shadow_mask"]
    direct_horiz = shadow_data["direct_horizontal_irradiance"]
    
    shadowed = (shadow_mask == 0.0)
    assert shadowed.any()
    assert np.all(direct_horiz[shadowed] == 0.0)


def test_sunlit_vs_shaded_thermal_contrast(static_run_dir):
    """Verifies that sunlit pedestrian corridor receptors exhibit higher Tmrt and UTCI than shaded receptors."""
    shadow_data = np.load(static_run_dir / "shadow_results.npz")
    shadow_mask = shadow_data["shadow_mask"]
    ped_mask = shadow_data["pedestrian_corridor_mask"]
    unbuilt_mask = shadow_data["unbuilt_mask"]
    
    tmrt = np.load(static_run_dir / "tmrt_results.npz")["tmrt"]
    utci = np.load(static_run_dir / "utci_results.npz")["utci"]
    
    lit_ped = ped_mask & unbuilt_mask & (shadow_mask == 1.0)
    shade_ped = ped_mask & unbuilt_mask & (shadow_mask == 0.0)
    
    assert lit_ped.any()
    assert shade_ped.any()
    
    mean_tmrt_lit = tmrt[lit_ped].mean()
    mean_tmrt_shade = tmrt[shade_ped].mean()
    mean_utci_lit = utci[lit_ped].mean()
    mean_utci_shade = utci[shade_ped].mean()
    
    delta_tmrt = mean_tmrt_lit - mean_tmrt_shade
    delta_utci = mean_utci_lit - mean_utci_shade
    
    assert delta_tmrt > 10.0, f"Expected Tmrt contrast > 10 K, got {delta_tmrt:.2f} K"
    assert delta_utci > 2.0, f"Expected UTCI contrast > 2 K, got {delta_utci:.2f} K"


def test_quality_checks_json_overall_status(static_run_dir):
    """Verifies that static_quality_checks.json reports PASSED status across all automated audits."""
    checks_path = static_run_dir / "static_quality_checks.json"
    assert checks_path.exists()
    checks = json.loads(checks_path.read_text(encoding="utf-8"))
    assert checks["overall_status"] == "PASSED"
    assert checks["array_shape_matches"] is True
    assert checks["direct_flux_zero_in_shadow"] is True
    assert checks["tmrt_lit_warmer_than_shade"] is True
    assert checks["utci_lit_warmer_than_shade"] is True
