"""
Test suite for Tree Map Placement & Uncertainty Envelopes (Part 6, 16).
"""

import json
from pathlib import Path
import pytest
from urban_comfort.integration.tree_loader import tree_loader
from urban_comfort.integration.tree_geometry_builder import tree_geometry_builder

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_core_trees_loaded():
    core = tree_loader.get_core_trees()
    assert len(core) == 6, f"Expected 6 core trees (T08 to T13), got {len(core)}"
    ids = [t.tree_id for t in core]
    assert ids == ["T08", "T09", "T10", "T11", "T12", "T13"]


def test_tree_uncertainty_envelopes():
    t08 = tree_loader.get_tree("T08")
    assert t08 is not None
    # Nominal height should be between small and large
    h_s = t08.height_bounds["small"]
    h_n = t08.height_bounds["nominal"]
    h_l = t08.height_bounds["large"]
    assert h_s < h_n < h_l, f"Height envelope inverted: {h_s}, {h_n}, {h_l}"

    d_s = t08.crown_diameter_bounds["small"]
    d_n = t08.crown_diameter_bounds["nominal"]
    d_l = t08.crown_diameter_bounds["large"]
    assert d_s < d_n < d_l


def test_tree_mesh_generation():
    t08 = tree_loader.get_tree("T08")
    mesh = tree_geometry_builder.build_tree_mesh(t08, uncertainty_state="nominal")
    assert mesh.is_watertight or len(mesh.faces) > 0
    assert mesh.bounds[0][0] <= t08.local_x <= mesh.bounds[1][0]
    assert mesh.metadata["physics_participation"] == "PHYSICAL"
