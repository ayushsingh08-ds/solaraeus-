"""
Test suite for Terrain Loading & Classification (Part 5, 16).
"""

import json
from pathlib import Path
import numpy as np
import pytest
from urban_comfort.integration.terrain_loader import terrain_loader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_terrain_manifest_and_labels():
    manifest = terrain_loader.get_terrain_manifest()
    assert "status" in manifest
    labels = manifest["mandatory_labels"]
    assert "FABDEM_REGIONAL_REFERENCE_ONLY" in labels
    assert "MEASURED_STREET_SCALE_DTM_NOT_AVAILABLE" in labels
    assert "SYNTHETIC_TERRAIN_ONLY" in labels


def test_terrain_elevation_sampling():
    # Flat
    assert terrain_loader.sample_elevation(50.0, 70.0, "flat") == 0.0

    # Inclined (5% slope)
    assert terrain_loader.sample_elevation(100.0, 70.0, "inclined") == pytest.approx(5.0)

    # Stepped
    assert terrain_loader.sample_elevation(50.0, 70.0, "stepped") == 0.0
    assert terrain_loader.sample_elevation(120.0, 70.0, "stepped") == 0.8


def test_terrain_mesh_generation():
    mesh = terrain_loader.generate_mesh(profile="flat", resolution=10.0)
    assert len(mesh.vertices) > 0
    assert len(mesh.faces) > 0
    assert np.all(mesh.vertices[:, 2] == 0.0)
