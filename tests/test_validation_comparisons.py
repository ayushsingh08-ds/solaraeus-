"""
Unit tests for numerical comparison metrics and verification tools.
"""

import math
import numpy as np
import pytest

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import create_single_box_scene
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.validation.comparisons import (
    compare_arrays, compare_results, format_comparison_summary, ComparisonMetrics
)
from urban_comfort.validation.metrics import (
    compute_shadow_iou, compute_utci_category_agreement, compute_error_percentiles
)


def test_compare_arrays_identity():
    arr = np.random.uniform(20.0, 50.0, size=(30, 30))
    metrics = compare_arrays(arr, arr, field_name="test_field", tolerance=1e-6)

    assert metrics.field_name == "test_field"
    assert math.isclose(metrics.max_absolute_error, 0.0, abs_tol=1e-12)
    assert math.isclose(metrics.mean_absolute_error, 0.0, abs_tol=1e-12)
    assert math.isclose(metrics.root_mean_squared_error, 0.0, abs_tol=1e-12)
    assert metrics.exceedance_count == 0
    assert metrics.exceedance_fraction == 0.0
    assert metrics.is_within_tolerance is True


def test_compare_arrays_known_perturbation():
    arr1 = np.full((20, 20), 30.0)
    arr2 = np.full((20, 20), 32.5)  # Offset by 2.5
    metrics = compare_arrays(arr2, arr1, field_name="perturbed", tolerance=1.0)

    assert math.isclose(metrics.max_absolute_error, 2.5, abs_tol=1e-12)
    assert math.isclose(metrics.mean_absolute_error, 2.5, abs_tol=1e-12)
    assert math.isclose(metrics.root_mean_squared_error, 2.5, abs_tol=1e-12)
    assert metrics.exceedance_count == 400
    assert metrics.exceedance_fraction == 1.0
    assert metrics.is_within_tolerance is False


def test_compare_results_full_pipeline():
    scene = create_single_box_scene(extent_m=40.0)
    weather = Weather(
        air_temperature=300.15, relative_humidity=50.0, wind_speed=2.0,
        wind_direction=180.0, direct_normal_irradiance=700.0, diffuse_horizontal_irradiance=150.0
    )
    config = SimulationConfig(
        latitude=40.7128, longitude=-74.0060, date="2024-07-15", local_time="12:00:00",
        sky_patch_configuration=16
    )

    res_ref = full_recompute(scene, weather, config)
    res_test = full_recompute(scene, weather, config)

    # Identical executions must pass all field checks
    comparisons = compare_results(res_test, res_ref, tmrt_tolerance=0.5)
    for field_name, m in comparisons.items():
        assert m.is_within_tolerance, f"Field '{field_name}' unexpectedly failed identity comparison!"

    summary_table = format_comparison_summary(comparisons)
    assert "PASS" in summary_table
    assert "FAIL" not in summary_table


def test_compare_results_perturbed_tmrt_detection():
    scene = create_single_box_scene(extent_m=30.0)
    weather = Weather(
        air_temperature=300.15, relative_humidity=50.0, wind_speed=2.0,
        wind_direction=180.0, direct_normal_irradiance=700.0, diffuse_horizontal_irradiance=150.0
    )
    config = SimulationConfig(sky_patch_configuration=16)

    res_ref = full_recompute(scene, weather, config)

    # Perturb Tmrt in test result by +1.5 K (tolerance = 0.5 K)
    perturbed_tmrt = res_ref.tmrt + 1.5
    res_perturbed = SimulationResult(
        shadow_mask=res_ref.shadow_mask.copy(),
        direct_irradiance=res_ref.direct_irradiance.copy(),
        visibility_fields=res_ref.visibility_fields.copy(),
        shortwave_flux=res_ref.shortwave_flux.copy(),
        longwave_flux=res_ref.longwave_flux.copy(),
        tmrt=perturbed_tmrt,
        utci=res_ref.utci.copy(),
        metadata=res_ref.metadata.copy()
    )

    comparisons = compare_results(res_perturbed, res_ref, tmrt_tolerance=0.5)
    assert comparisons["tmrt"].is_within_tolerance is False
    assert comparisons["tmrt"].exceedance_fraction == 1.0


def test_shadow_iou_metric():
    mask1 = np.ones((10, 10))
    mask2 = np.ones((10, 10))

    # Both empty of shade -> IoU = 1.0
    assert compute_shadow_iou(mask1, mask2) == 1.0

    # Half shaded in mask1, same half in mask2 -> IoU = 1.0
    mask1[:5, :] = 0.0
    mask2[:5, :] = 0.0
    assert compute_shadow_iou(mask1, mask2) == 1.0

    # Completely disjoint shades -> IoU = 0.0
    mask2[:5, :] = 1.0
    mask2[5:, :] = 0.0
    assert compute_shadow_iou(mask1, mask2) == 0.0


def test_utci_category_agreement_metric():
    utci_a = np.array([[22.0, 28.0], [35.0, 42.0]])
    utci_b = np.array([[24.0, 30.0], [36.0, 44.0]])

    # 22 & 24 -> No thermal stress
    # 28 & 30 -> Moderate heat stress
    # 35 & 36 -> Strong heat stress
    # 42 & 44 -> Very strong heat stress
    # 100% category agreement despite small numerical differences
    agreement = compute_utci_category_agreement(utci_a, utci_b)
    assert agreement == 1.0


def test_error_percentiles():
    err_map = np.arange(101, dtype=np.float64)  # 0 to 100
    p = compute_error_percentiles(err_map, percentiles=(50, 90, 99))
    assert math.isclose(p["p50"], 50.0)
    assert math.isclose(p["p90"], 90.0)
    assert math.isclose(p["p99"], 99.0)
