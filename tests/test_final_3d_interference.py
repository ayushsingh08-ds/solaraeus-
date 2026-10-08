"""
Test suite for Multi-Scenario Interference Logic (Part 13, 16).
"""

from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_interference_manifest():
    p = OUT / "interference_manifest.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "INTERFERENCE_LOGIC_ACTIVE"
    scenarios = data["scenarios"]
    assert "BASELINE" in scenarios
    assert "TREES_ONLY" in scenarios
    assert "PANELS_ONLY" in scenarios
    assert "TREES_AND_PANELS" in scenarios
    assert "combined_delta_k" in data["decomposition"]
