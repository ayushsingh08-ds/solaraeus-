"""
Tests for Church Street Overhead Shade-Panel Intervention Simulation.

Verifies:
1. Panel mesh construction (8 vertices, 12 triangles, watertight, non-degenerate, outward/upward/downward normals).
2. Panel orientation and non-colliding placement.
3. Baseline and intervention configuration equality.
4. Pure full recomputation without incremental computation or cache reuse.
5. Difference array shapes and physical consistency (shading and cooling).
6. Quality checks schema and validity.
7. Reproducibility metadata and provenance.
8. Final completion decision readiness token.
"""

import json
from pathlib import Path
import numpy as np
import pytest

from urban_comfort.geometry.mesh import TriangleMesh


@pytest.fixture(scope="module")
def shade_run_dir() -> Path:
    results_dir = Path(__file__).resolve().parent.parent / "results"
    shade_dirs = sorted(results_dir.glob("church_street_shade_full_*"))
    assert len(shade_dirs) > 0, "No church_street_shade_full_* directory found in results/"
    return shade_dirs[-1]


def test_panel_mesh_validation_artifact(shade_run_dir):
    """Verifies that panel_validation.json confirms valid watertight 8-vert 12-tri mesh."""
    panel_val_path = shade_run_dir / "panel_validation.json"
    assert panel_val_path.exists()
    
    val = json.loads(panel_val_path.read_text(encoding="utf-8"))
    assert val["panel_id"] == "BLR_SHADE_001"
    assert val["object_id"] == "CANOPY_001"
    assert val["vertices"] == 8
    assert val["triangles"] == 12
    assert val["dimensions"] == [6.0, 3.0, 0.1]
    assert abs(val["area"] - 18.0) < 1e-4
    assert val["underside_height"] == 3.5
    assert val["top_height"] == 3.6
    assert abs(val["bearing_true_north"] - 103.028) < 0.01
    assert abs(val["bearing_grid_north"] - 102.443) < 0.01
    assert val["material_id"] == "SHADE_PANEL_ASSUMED_001"
    assert val["watertight_status"] is True
    assert val["degenerate_triangle_count"] == 0
    assert val["placement_status"] == "valid_non_colliding"


def test_configuration_equality(shade_run_dir):
    """Verifies that baseline and intervention configurations are identical except for the panel."""
    cfg_path = shade_run_dir / "configuration_comparison.json"
    assert cfg_path.exists()
    
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["status"] == "identical_except_intervention_panel"
    assert cfg["grid_resolution"] == 2.0
    assert cfg["receptor_height"] == 1.1
    assert cfg["solar_timestamp"] == "2024-04-15 09:00:00 UTC"
    assert abs(cfg["solar_altitude_deg"] - 57.916) < 0.01
    assert cfg["weather_forcing"]["air_temperature_c"] == 35.0
    assert cfg["weather_forcing"]["station_distance_km"] == 2.56
    assert cfg["svf_azimuth_count"] == 32
    assert cfg["terrain_policy"] == "flat_ground_z0"
    assert cfg["context_building_count"] == 123
    assert cfg["intervention_panel_count"] == 1
    assert cfg["incremental_computation_used"] is False


def test_pure_full_recomputation_used(shade_run_dir):
    """Verifies that incremental computation was explicitly not used."""
    prov_path = shade_run_dir / "provenance.json"
    assert prov_path.exists()
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    assert prov["incremental_computation_used"] is False

    qc_path = shade_run_dir / "quality_checks.json"
    assert qc_path.exists()
    qc = json.loads(qc_path.read_text(encoding="utf-8"))
    assert qc["incremental_computation_used"] is False


def test_difference_arrays_and_physical_effects(shade_run_dir):
    """Verifies shape equality, 0 NaNs/Infs, and significant local cooling under panel."""
    diff_path = shade_run_dir / "difference_fields.npz"
    assert diff_path.exists()
    
    with np.load(diff_path) as data:
        diff_shadow = data["diff_shadow"]
        diff_svf = data["diff_svf"]
        diff_tmrt = data["diff_tmrt"]
        diff_utci = data["diff_utci"]
        
    assert diff_shadow.shape == (148, 190)
    assert diff_svf.shape == (148, 190)
    assert diff_tmrt.shape == (148, 190)
    assert diff_utci.shape == (148, 190)
    
    assert not np.any(np.isnan(diff_shadow))
    assert not np.any(np.isnan(diff_svf))
    assert not np.any(np.isnan(diff_tmrt))
    assert not np.any(np.isnan(diff_utci))
    
    assert not np.any(np.isinf(diff_tmrt))
    assert not np.any(np.isinf(diff_utci))
    
    # Shadow mask difference must only be 0.0 (unchanged) or -1.0 (new shadow cast by panel)
    unique_shadow_diff = np.unique(diff_shadow)
    assert np.all(np.isin(unique_shadow_diff, [-1.0, 0.0]))
    
    # At least 1 cell must be newly shaded
    n_shaded = int(np.sum(diff_shadow == -1.0))
    assert n_shaded >= 4
    
    # Significant cooling in shaded cells
    min_tmrt_diff = float(np.min(diff_tmrt))
    min_utci_diff = float(np.min(diff_utci))
    assert min_tmrt_diff <= -10.0, f"Expected Tmrt cooling <= -10K, got {min_tmrt_diff:.2f}K"
    assert min_utci_diff <= -2.5, f"Expected UTCI relief <= -2.5K, got {min_utci_diff:.2f}K"


def test_quality_checks_json(shade_run_dir):
    """Verifies quality_checks.json overall status and metrics."""
    qc_path = shade_run_dir / "quality_checks.json"
    assert qc_path.exists()
    qc = json.loads(qc_path.read_text(encoding="utf-8"))
    
    assert qc["status"] == "PASSED"
    assert qc["shape_equality"] is True
    assert qc["svf_range_checks"]["svf_valid_interval"] is True
    assert qc["shadow_mask_validity"]["baseline_binary_only"] is True
    assert qc["shadow_mask_validity"]["intervention_binary_only"] is True
    assert qc["panel_mesh_validity"]["watertight"] is True
    assert qc["panel_mesh_validity"]["degenerate_triangles"] == 0
    assert qc["main_boundary_mask_consistency"] is True
    assert qc["corridor_mask_consistency"] is True
    assert qc["configuration_equality"] is True
    assert qc["incremental_computation_used"] is False


def test_all_12_diagnostic_plots_exist(shade_run_dir):
    """Verifies that all 12 required diagnostic plots were generated."""
    plots_dir = shade_run_dir / "plots"
    assert plots_dir.exists()
    
    expected_plots = [
        "baseline_geometry.png",
        "intervention_geometry.png",
        "panel_location.png",
        "baseline_shadow_map.png",
        "intervention_shadow_map.png",
        "shadow_difference.png",
        "svf_difference.png",
        "shortwave_difference.png",
        "longwave_difference.png",
        "tmrt_difference.png",
        "utci_difference.png",
        "changed_cells_map.png",
    ]
    for plot_name in expected_plots:
        p = plots_dir / plot_name
        assert p.exists(), f"Missing plot: {plot_name}"
        assert p.stat().st_size > 1000, f"Plot {plot_name} is empty or corrupted"


def test_readiness_decision_and_mandatory_qualification(shade_run_dir):
    """Verifies that the report contains the mandatory qualification and completion decision."""
    report_path = shade_run_dir / "shade_panel_full_recomputation_report.md"
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    
    mandatory_qual = "The shade-panel result is an exploratory full-recomputation comparison using real-world building geometry, partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties."
    assert mandatory_qual in text
    
    assert "READY_FOR_SHADE_PANEL_INCREMENTAL_COMPARISON" in text
    assert "Full-recomputation intervention comparison" in text
    assert "Exploratory real-world geometry case study" in text
    assert "Modeled difference under fixed assumptions" in text


# =========================================================================
# Incremental Intervention Comparison Tests
# =========================================================================

@pytest.fixture(scope="module")
def shade_inc_run_dir() -> Path:
    results_dir = Path(__file__).resolve().parent.parent / "results"
    inc_dirs = sorted(results_dir.glob("church_street_shade_incremental_*"))
    assert len(inc_dirs) > 0, "No church_street_shade_incremental_* directory found in results/"
    return inc_dirs[-1]


def test_incremental_provenance_and_metadata(shade_inc_run_dir):
    """Verifies that incremental metadata reports cache reuse, cell and ray counts."""
    prov_path = shade_inc_run_dir / "provenance.json"
    assert prov_path.exists()
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    
    assert prov["incremental_computation_used"] is True
    assert prov["reused_cell_count"] == 28048
    assert prov["recomputed_cell_count"] == 72
    assert prov["reused_percentage"] > 99.0
    assert prov["affected_ray_count"] == 2376
    assert prov["total_ray_count"] == 927960
    assert prov["ray_work_reduction_pct"] > 99.0
    assert prov["grid_shape"] == [148, 190]
    assert prov["grid_resolution"] == 2.0
    assert prov["solar_timestamp"] == "2024-04-15 09:00:00 UTC"
    assert abs(prov["solar_angles"]["altitude_deg"] - 57.916) < 0.01
    assert "baseline_artifact_hashes" in prov
    assert "frozen_full_artifact_hashes" in prov
    assert prov["certificate_status"]["status"] == "certified"
    assert prov["certificate_status"]["violations_count"] == 0
    assert prov["certificate_status"]["is_valid"] is True


def test_incremental_cache_and_dependencies(shade_inc_run_dir):
    """Verifies cache lineage and explicit dependency reachability."""
    cache_path = shade_inc_run_dir / "cache_dependency_summary.json"
    assert cache_path.exists()
    cdata = json.loads(cache_path.read_text(encoding="utf-8"))
    
    assert cdata["cached_fields_count"] == 7
    assert cdata["edit_type"] == "mesh_added"
    assert "shadow_mask" in cdata["invalidated_downstream_fields"]
    assert "svf" in cdata["invalidated_downstream_fields"]
    assert "tmrt" in cdata["invalidated_downstream_fields"]
    assert "utci" in cdata["invalidated_downstream_fields"]
    assert cdata["source_scene_hash"] != cdata["target_scene_hash"]


def test_incremental_numerical_parity_vs_frozen_full(shade_inc_run_dir, shade_run_dir):
    """Verifies numerical parity between incremental outputs and frozen full recomputation."""
    # Load incremental fields
    inc_shadow = np.load(shade_inc_run_dir / "incremental_shadow.npz")["shadow_mask"]
    inc_svf = np.load(shade_inc_run_dir / "incremental_visibility.npz")["svf"]
    inc_dir_sw = np.load(shade_inc_run_dir / "incremental_shortwave.npz")["direct_horizontal"]
    inc_tot_sw = np.load(shade_inc_run_dir / "incremental_shortwave.npz")["k_total"]
    inc_tot_lw = np.load(shade_inc_run_dir / "incremental_longwave.npz")["l_total"]
    inc_tmrt = np.load(shade_inc_run_dir / "incremental_tmrt.npz")["tmrt"]
    inc_utci = np.load(shade_inc_run_dir / "incremental_utci.npz")["utci"]
    
    # Load frozen full reference fields
    full_shadow = np.load(shade_run_dir / "intervention_shadow.npz")["shadow_mask"]
    full_svf = np.load(shade_run_dir / "intervention_visibility.npz")["svf"]
    full_dir_sw = np.load(shade_run_dir / "intervention_shortwave.npz")["direct_horizontal"]
    full_tot_sw = np.load(shade_run_dir / "intervention_shortwave.npz")["k_total"]
    full_tot_lw = np.load(shade_run_dir / "intervention_longwave.npz")["l_total"]
    full_tmrt = np.load(shade_run_dir / "intervention_tmrt.npz")["tmrt"]
    full_utci = np.load(shade_run_dir / "intervention_utci.npz")["utci"]
    
    # Grid shape check
    assert inc_shadow.shape == full_shadow.shape == (148, 190)
    assert inc_svf.shape == full_svf.shape == (148, 190)
    assert inc_tmrt.shape == full_tmrt.shape == (148, 190)
    assert inc_utci.shape == full_utci.shape == (148, 190)
    
    # NaN and Inf check
    assert not np.any(np.isnan(inc_tmrt))
    assert not np.any(np.isinf(inc_tmrt))
    assert not np.any(np.isnan(inc_svf))
    assert not np.any(np.isnan(inc_utci))
    
    # Direct shadow and direct shortwave must match identically
    max_shadow_err = float(np.max(np.abs(inc_shadow - full_shadow)))
    max_dir_sw_err = float(np.max(np.abs(inc_dir_sw - full_dir_sw)))
    assert max_shadow_err == 0.0, f"Direct shadow mismatch: {max_shadow_err}"
    assert max_dir_sw_err == 0.0, f"Direct shortwave mismatch: {max_dir_sw_err}"
    
    # Tmrt maximum error must strictly satisfy the 0.5 K tolerance
    tmrt_err = np.abs(inc_tmrt - full_tmrt)
    max_tmrt_err = float(np.max(tmrt_err))
    assert max_tmrt_err <= 0.50, f"Tmrt error ({max_tmrt_err:.4f} K) exceeded tolerance (0.50 K)"
    assert max_tmrt_err < 0.05, f"Tmrt error ({max_tmrt_err:.4f} K) higher than expected ~0.03 K"
    
    # SVF maximum error within 0.01
    max_svf_err = float(np.max(np.abs(inc_svf - full_svf)))
    assert max_svf_err < 0.01, f"SVF error ({max_svf_err:.4f}) exceeded 0.01"
    
    # UTCI maximum error within tolerance
    max_utci_err = float(np.max(np.abs(inc_utci - full_utci)))
    assert max_utci_err <= 0.50, f"UTCI error ({max_utci_err:.4f} K) exceeded tolerance"


def test_incremental_error_certificate_soundness(shade_inc_run_dir):
    """Verifies that the computable error certificate is mathematically sound and has zero violations."""
    cert_path = shade_inc_run_dir / "certificate_verification.json"
    assert cert_path.exists()
    cver = json.loads(cert_path.read_text(encoding="utf-8"))
    
    assert cver["status"] == "certified"
    assert cver["is_valid"] is True
    assert cver["num_violations"] == 0
    assert cver["max_violation_k"] == 0.0
    assert cver["is_within_tolerance"] is True
    assert cver["reused_max_error_k"] <= cver["tolerance_k"]
    assert cver["reused_cells"] == 28048
    assert cver["affected_cells"] == 72
    
    # Verify certificate field arrays
    fields_npz = shade_inc_run_dir / "certificate_fields.npz"
    assert fields_npz.exists()
    with np.load(fields_npz) as cdata:
        bound = cdata["predicted_error_bound"]
        actual_err = cdata["actual_error_tmrt"]
        slack = cdata["slack_map"]
        reused_mask = cdata["reused_mask"]
        recomp_mask = cdata["recomputed_mask"]
        
    assert bound.shape == (148, 190)
    assert np.all(slack >= -1e-10), "Negative slack indicates certificate violation!"
    assert np.all(actual_err[reused_mask] <= 0.50 + 1e-10)
    assert int(np.sum(recomp_mask)) == 72
    assert int(np.sum(reused_mask)) == 28048


def test_incremental_all_10_diagnostic_plots_exist(shade_inc_run_dir):
    """Verifies that all 10 required diagnostic publication plots exist and are non-empty."""
    plots_dir = shade_inc_run_dir / "plots"
    assert plots_dir.exists()
    
    expected_plots = [
        "fig01_incremental_vs_full_tmrt.png",
        "fig02_error_certificate_bound_map.png",
        "fig03_reused_vs_recomputed_cells.png",
        "fig04_certificate_slack_map.png",
        "fig05_incremental_vs_full_svf.png",
        "fig06_incremental_vs_full_shadow.png",
        "fig07_incremental_vs_full_utci.png",
        "fig08_error_distribution_histograms.png",
        "fig09_corridor_incremental_comparison.png",
        "fig10_runtime_work_reduction_benchmarks.png",
    ]
    for p_name in expected_plots:
        p = plots_dir / p_name
        assert p.exists(), f"Missing plot: {p_name}"
        assert p.stat().st_size > 1000, f"Plot {p_name} is empty or corrupted"


def test_incremental_quality_checks_and_readiness(shade_inc_run_dir):
    """Verifies quality checks pass and final readiness decision is ACCEPTED_FOR_RESEARCH."""
    qc_path = shade_inc_run_dir / "quality_checks.json"
    assert qc_path.exists()
    qc = json.loads(qc_path.read_text(encoding="utf-8"))
    
    assert qc["all_checks_passed"] is True
    assert qc["readiness_decision"] == "ACCEPTED_FOR_RESEARCH"
    assert qc["checks"]["same_grid_shape"] is True
    assert qc["checks"]["same_solar_timestamp"] is True
    assert qc["checks"]["no_nan_or_inf_in_incremental_output"] is True
    assert qc["checks"]["certificate_violations_zero"] is True
    assert qc["checks"]["maximum_error_within_tolerance"] is True
    assert qc["checks"]["incremental_computation_flag_true"] is True
    
    # Check report file
    rep_path = shade_inc_run_dir / "church_street_shade_panel_incremental_report.md"
    assert rep_path.exists()
    rep_text = rep_path.read_text(encoding="utf-8")
    assert "READINESS DECISION: ACCEPTED_FOR_RESEARCH" in rep_text
    assert "Certificate Violations:          0 (SOUND & VALID)" in rep_text
    assert "Cache Reuse Fraction:            99.74%" in rep_text

