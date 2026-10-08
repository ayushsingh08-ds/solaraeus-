"""
Test suite for 3D Feasibility Checking (Part 14, 16).
"""

from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_feasibility_manifest():
    p = OUT / "feasibility_manifest.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "3D_FEASIBILITY_ACTIVE"
    assert len(data["constraints_checked"]) >= 5
    assert data["verified_clearance_m"] >= 4.0
