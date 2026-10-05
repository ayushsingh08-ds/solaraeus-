"""
Tests for Mutation Audits in SOLARAEUS.

Asserts that intentional algorithmic and certificate mutations break safety invariants,
trigger detectable certificate violations and negative slack, and are correctly labeled
as effective.
"""

from __future__ import annotations
import pytest
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.benchmark.scenes import create_scaling_scene
from urban_comfort.benchmark.independent_audit import run_mutation_tests


@pytest.fixture
def standard_setup():
    scene = create_scaling_scene(80.0, "medium")
    weather = Weather(
        air_temperature=301.15,
        relative_humidity=50.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=160.0
    )
    config = SimulationConfig(
        latitude=31.2304,
        longitude=121.4737,
        date="2026-06-21",
        local_time="08:00:00",
        tmrt_tolerance=0.5,
        max_svf_search_dist_m=30.0
    )
    return scene, weather, config


def test_mutation_suite_execution_and_schema(standard_setup):
    scene, weather, config = standard_setup
    mutations = run_mutation_tests(scene, weather, config)
    assert len(mutations) == 5
    
    required_keys = [
        "mutation_id", "description", "dependency_affected", "scene_id",
        "full_result_changed", "incremental_result_changed", "actual_error",
        "predicted_bound", "minimum_slack", "certificate_violations",
        "tolerance_violations", "status"
    ]
    for m in mutations:
        for k in required_keys:
            assert k in m, f"Key '{k}' missing from mutation record {m.get('mutation_id')}"
        assert m["status"] in ("effective", "ineffective", "inconclusive")


def test_control_unmutated_produces_zero_violations(standard_setup):
    scene, weather, config = standard_setup
    mutations = run_mutation_tests(scene, weather, config)
    ctrl = next(m for m in mutations if m["mutation_id"] == "control_unmutated")
    
    assert ctrl["certificate_violations"] == 0
    assert ctrl["tolerance_violations"] == 0
    assert ctrl["minimum_slack"] >= -1e-9
    assert ctrl["status"] == "effective"


def test_all_mutations_are_effective_and_detected(standard_setup):
    scene, weather, config = standard_setup
    mutations = run_mutation_tests(scene, weather, config)
    mutated_cases = [m for m in mutations if m["mutation_id"] != "control_unmutated"]
    
    assert len(mutated_cases) == 4
    for m in mutated_cases:
        m_id = m["mutation_id"]
        assert m["status"] == "effective", f"Mutation {m_id} was expected to be 'effective', got '{m['status']}'"
        assert m["certificate_violations"] > 0, f"Mutation {m_id} produced 0 certificate violations"
        assert m["minimum_slack"] < 0.0, f"Mutation {m_id} did not produce negative slack (slack={m['minimum_slack']})"
        assert m["full_result_changed"] is True, f"Mutation {m_id} did not perturb full result"


def test_mutation_zero_diffuse_bound_specifically(standard_setup):
    scene, weather, config = standard_setup
    mutations = run_mutation_tests(scene, weather, config)
    m2 = next(m for m in mutations if m["mutation_id"] == "mutation_zero_diffuse_bound")
    
    # Deliberately zeroed diffuse bound with un-recomputed SVF decay
    assert m2["actual_error"] > 0.15, "Expected un-recomputed SVF to create > 0.15K Tmrt error"
    assert m2["certificate_violations"] > 1000, "Expected >1000 cells to violate zero diffuse bound"
    assert m2["minimum_slack"] < -0.15


def test_mutation_truncated_svf_cutoff_specifically(standard_setup):
    scene, weather, config = standard_setup
    mutations = run_mutation_tests(scene, weather, config)
    m4 = next(m for m in mutations if m["mutation_id"] == "mutation_truncated_svf_cutoff")
    
    # Truncated 5m cutoff leaving 5m-30m un-recomputed
    assert m4["actual_error"] > 0.15, "Expected un-recomputed SVF outside 5m to create > 0.15K error"
    assert m4["certificate_violations"] > 1000, "Expected >1000 cells to violate 0.0K bound beyond 5m"
    assert m4["minimum_slack"] < -0.15
