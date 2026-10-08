"""
Test suite for Dynamic Heatmap Generation (Part 12, 16).
"""

from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
HM_DIR = ROOT / "results/final_3d_integrated_simulation/heatmaps"


def test_heatmap_manifest():
    m = HM_DIR / "heatmap_manifest.json"
    assert m.exists()
    with open(m, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "HEATMAPS_GENERATED_FROM_3D_SIMULATION"
    assert "tmrt" in data["fields"]
    assert "utci" in data["fields"]


def test_heatmap_rendered_views():
    view_dir = HM_DIR / "heatmap_rendered_views"
    assert view_dir.exists()
    expected_imgs = ["tmrt_baseline.png", "tmrt_intervention.png", "cooling_delta.png", "utci_baseline.png"]
    for img in expected_imgs:
        p = view_dir / img
        assert p.exists()
        assert p.stat().st_size > 1000
