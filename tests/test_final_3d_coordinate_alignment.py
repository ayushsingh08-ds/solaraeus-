"""
Test suite for Authoritative Coordinate Alignment (Part 4, 16).
"""

import json
from pathlib import Path
import pytest
from urban_comfort.integration.coordinates import transformer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_coordinate_transform_manifest():
    p = OUT / "coordinate_transform_manifest.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["coordinate_system"]["source_crs"] == "EPSG:4326"
    assert data["coordinate_system"]["projected_crs"] == "EPSG:32643"
    assert data["status"] == "AUTHORITATIVE_COORDINATE_PIPELINE_VALIDATED"


def test_reversible_roundtrip_precision():
    # Test point at Church Street
    lon, lat = 77.6045925, 12.9750311
    res = transformer.validate_roundtrip(lon, lat)
    assert res["error_lon_deg"] < 1e-7, "Longitude roundtrip precision error"
    assert res["error_lat_deg"] < 1e-7, "Latitude roundtrip precision error"


def test_threejs_coordinate_mapping():
    # Local: X East, Y North, Z Up
    # Three.js: X East, Y Up, Z -North
    lx, ly, lz = 10.0, 20.0, 5.0
    tx, ty, tz = transformer.local_to_threejs(lx, ly, lz)
    assert tx == 10.0
    assert ty == 5.0
    assert tz == -20.0

    rx, ry, rz = transformer.threejs_to_local(tx, ty, tz)
    assert (rx, ry, rz) == (lx, ly, lz)
