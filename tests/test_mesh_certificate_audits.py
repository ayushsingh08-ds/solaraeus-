"""
Unit tests for the mesh certificate audit module.
"""

from __future__ import annotations
import os
import csv
import pytest

from urban_comfort.benchmark.mesh_certificate_audit import (
    run_mesh_certificate_audit, SCENARIO_DEFINITIONS
)


def test_mesh_audit_execution_and_soundness(tmp_path):
    output_dir = str(tmp_path / "mesh_audit_test")
    summary = run_mesh_certificate_audit(output_dir=output_dir, tolerances=[1.5])

    assert summary["all_sound"] is True, "Audit found certificate violations!"
    assert summary["total_violations"] == 0
    assert summary["total_runs"] == len(SCENARIO_DEFINITIONS)

    csv_path = summary["csv_path"]
    assert os.path.exists(csv_path)

    # Read back and verify CSV rows
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == len(SCENARIO_DEFINITIONS)
    for r in rows:
        assert r["is_sound"] == "True", f"Scenario {r['scenario_id']} was not sound!"
        assert r["is_within_tolerance"] == "True", f"Scenario {r['scenario_id']} violated tolerance!"
        assert int(r["num_violations"]) == 0
        assert float(r["reused_fraction"]) > 0.0
        assert float(r["min_slack_k"]) >= -1e-6
