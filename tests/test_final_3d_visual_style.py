"""
Test suite for Cinematic Visual Styling & Physics Isolation (Part 15A, 16).
"""

from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
STYLE_DIR = ROOT / "results/final_3d_integrated_simulation/styling"


def test_style_manifest_and_presets():
    p = STYLE_DIR / "style_manifest.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "CINEMATIC_AERIAL_STYLE_APPLIED"
    assert "CINEMATIC_AERIAL" in data["presets"]
    assert "DAYLIGHT_CLEAR" in data["presets"]
    assert "ANALYSIS_NEUTRAL" in data["presets"]


def test_visual_only_elements_registry():
    p = STYLE_DIR / "visual_only_elements_registry.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "VISUAL_ONLY_ELEMENTS_EXCLUDED_FROM_PHYSICS"
    names = [el["name"] for el in data["elements"]]
    assert "corner_fog_wisps" in names
    assert "compass_rose" in names
    for el in data["elements"]:
        assert el["physics_participation"] == "VISUAL_ONLY"


def test_style_checklist_exists():
    p = STYLE_DIR / "style_checklist.md"
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    assert "Oblique Aerial Camera" in content
    assert "Dark Atmospheric Lighting" in content
    assert "Style/Physics Isolation" in content
