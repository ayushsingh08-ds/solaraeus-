"""
Test suite for Scene Geometry & Trimesh Generation (Part 7, 16).
"""

from pathlib import Path
import trimesh
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCENE_DIR = ROOT / "results/final_3d_integrated_simulation/scene"


def test_scene_glb_exports_exist():
    expected_glbs = [
        "buildings.glb", "terrain.glb", "trees_provisional.glb",
        "interventions.glb", "map_context.glb", "solaraeus_integrated_scene.glb"
    ]
    for name in expected_glbs:
        p = SCENE_DIR / name
        assert p.exists(), f"Expected GLB {name} to exist"
        assert p.stat().st_size > 500, f"GLB {name} file is too small"


def test_integrated_scene_loading():
    scene_path = SCENE_DIR / "solaraeus_integrated_scene.glb"
    s = trimesh.load(scene_path)
    assert isinstance(s, trimesh.Scene)
    assert len(s.geometry) > 0
