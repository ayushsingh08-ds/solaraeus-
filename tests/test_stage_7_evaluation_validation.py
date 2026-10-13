"""
Validation test suite for Stage 7: End-to-End Evaluation, Replication & Sensitivity.

Role: Project Lead / Analyst.
Verifies:
1. All Stage 7 spatial arrays (.npy), figures (.png), and metrics JSON exist and are valid.
2. Berlin baseline vs optimised runs show physically sound cooling (corridor delta ~0.48 K, local >10 K).
3. Cross-city replication runs on Chicago and London contain documented assumptions and valid metrics.
4. Sensitivity suite identifies all environmental and geometric factors shifting thermal indices by > 1.0 °C.
5. Geometric shade consistency validates that ray-traced shadows match analytical solar trigonometry within 1 grid cell (< 1.0 m).
6. Cooling is strictly reported as modelled, not measured.
"""

import json
import os
import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGE_7_DIR = os.path.join(ROOT, "results", "raw", "stage_7")
METRICS_JSON = os.path.join(STAGE_7_DIR, "stage_7_evaluation_metrics.json")


@pytest.fixture(scope="module")
def stage_7_data():
    assert os.path.exists(METRICS_JSON), f"Stage 7 metrics JSON not found: {METRICS_JSON}"
    with open(METRICS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_stage_7_artifacts_exist():
    """Asserts that all spatial arrays, publication figures, and logs exist."""
    required_files = [
        "stage_7_evaluation_metrics.json",
        "stage_7_berlin_cooling_maps.png",
        "stage_7_replication_comparison.png",
        "stage_7_sensitivity_tornado.png",
        "stage_7_shade_consistency.png",
        "berlin_baseline_tmrt.npy",
        "berlin_baseline_utci.npy",
        "berlin_baseline_shadow.npy",
        "berlin_baseline_svf.npy",
        "berlin_optimised_tmrt.npy",
        "berlin_optimised_utci.npy",
        "berlin_delta_tmrt.npy",
        "berlin_delta_utci.npy",
        "chicago_baseline_tmrt.npy",
        "chicago_optimised_tmrt.npy",
        "chicago_delta_tmrt.npy",
        "london_baseline_tmrt.npy",
        "london_optimised_tmrt.npy",
        "london_delta_tmrt.npy",
    ]
    for fname in required_files:
        fpath = os.path.join(STAGE_7_DIR, fname)
        assert os.path.exists(fpath), f"Missing artifact: {fname}"
        assert os.path.getsize(fpath) > 0, f"Artifact is empty: {fname}"


def test_berlin_baseline_and_optimised_physics(stage_7_data):
    """Verifies baseline and optimised microclimate physics on Berlin corridor."""
    berlin = stage_7_data["berlin_primary_evaluation"]
    base_corr = berlin["baseline"]["corridor"]
    opt_corr = berlin["optimised"]["corridor"]
    deltas = berlin["cooling_deltas"]

    # Grid check
    grid = stage_7_data["grid_specification"]
    assert grid["resolution_m"] == 1.0
    assert grid["pedestrian_height_m"] == 1.1
    assert grid["total_cells"] == 48000
    assert base_corr["cells_count"] == 1600

    # Plausible biometeorological ranges
    assert 30.0 <= base_corr["mean_tmrt_c"] <= 55.0
    assert 40.0 <= base_corr["max_tmrt_c"] <= 60.0
    assert 25.0 <= base_corr["mean_utci_c"] <= 38.0

    # Cooling verification
    assert opt_corr["mean_tmrt_c"] < base_corr["mean_tmrt_c"]
    assert deltas["mean_cooling_delta_tmrt_k"] > 0.30
    assert deltas["max_local_cooling_delta_tmrt_k"] >= 10.0
    assert deltas["mean_cooling_delta_utci_k"] > 0.05
    assert deltas["max_local_cooling_delta_utci_k"] >= 2.0


def test_multi_city_replication_results(stage_7_data):
    """Verifies cross-city replication on Chicago and London."""
    repl = stage_7_data["replication_evaluations"]
    assert "chicago" in repl
    assert "london" in repl

    chicago = repl["chicago"]
    assert "Replication with documented assumptions" in chicago["label"]
    assert len(chicago["assumptions"]) >= 3
    assert chicago["delta_tmrt_corridor_mean_k"] >= 0.0

    london = repl["london"]
    assert "Replication with documented assumptions" in london["label"]
    assert len(london["assumptions"]) >= 3
    assert london["delta_tmrt_corridor_mean_k"] > 0.20
    assert london["delta_tmrt_max_local_k"] > 10.0


def test_sensitivity_analysis_factors(stage_7_data):
    """Verifies Berlin sensitivity analysis and > 1 °C factor identification."""
    sens = stage_7_data["sensitivity_analysis"]
    scenarios = sens["all_scenarios"]
    factors_gt_1k = sens["factors_changing_metrics_gt_1k"]

    # Must contain building height, trees on/off, wind speed, irradiance
    factors_evaluated = {sc["factor"] for sc in scenarios}
    assert "Building Height" in factors_evaluated
    assert "Street Vegetation" in factors_evaluated
    assert "Wind Speed" in factors_evaluated
    assert "Solar Irradiance (DNI)" in factors_evaluated

    # At least two scenarios shift metrics by > 1.0 K
    assert len(factors_gt_1k) >= 2
    factor_names_gt_1k = [f["factor"] for f in factors_gt_1k]
    assert "Street Vegetation" in factor_names_gt_1k
    assert "Solar Irradiance (DNI)" in factor_names_gt_1k


def test_geometric_shade_consistency(stage_7_data):
    """Verifies that cast shadow centroids match analytical solar trigonometry (< 1.0 m)."""
    check = stage_7_data["consistency_check"]
    assert check["all_consistent"] is True

    for r in check["records"]:
        assert r["is_physically_consistent"] is True
        assert r["centroid_discrepancy_m"] < 1.0
        assert r["shadow_cells_cast"] > 15
        assert r["shadow_area_m2"] > 15.0


def test_modelled_not_measured_acceptance(stage_7_data):
    """Verifies acceptance criteria and reporting fidelity."""
    crit = stage_7_data["acceptance_criteria"]
    assert crit["every_input_documented"] is True
    assert crit["results_plausible_and_local"] is True
    assert crit["cooling_reported_as_modelled"] is True
    assert crit["stage_status"] == "PASS"
