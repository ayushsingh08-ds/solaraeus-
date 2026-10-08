"""
Test suite for Final 3D Exports & Reports (Part 17, 18, 16).
"""

from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_final_simulation_status():
    p = OUT / "FINAL_3D_SIMULATION_STATUS.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["success_token"] == "SOLARAEUS_DATA_DRIVEN_3D_SIMULATION_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
    summary = data["validation_summary"]
    for k, v in summary.items():
        assert v is True, f"Validation failure for: {k}"


def test_final_report_markdown():
    p = OUT / "FINAL_3D_SIMULATION_REPORT.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "SOLARAEUS_DATA_DRIVEN_3D_SIMULATION_COMPLETE_WITH_DOCUMENTED_LIMITATIONS" in content
    assert "FABDEM_REGIONAL_REFERENCE_ONLY" in content
    assert "CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED" in content
