"""
Test suite for 3D Ray Tracing & Certificates (Part 9, 16).
"""

from pathlib import Path
import pandas as pd
import json
import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_ray_intersection_records():
    p = OUT / "ray_tracing/ray_intersection_records.parquet"
    assert p.exists()
    df = pd.read_parquet(p)
    assert len(df) > 0
    assert "origin_x" in df.columns
    assert "sun_azimuth_deg" in df.columns
    assert "primary_occluder" in df.columns
    assert "direct_visibility" in df.columns


def test_ray_tracing_manifest_and_certificates():
    m = OUT / "ray_tracing/ray_tracing_manifest.json"
    assert m.exists()
    with open(m, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "SHADOWS_RAY_TRACED_IN_3D"
    assert "parity_error_kelvin" in data
    assert data["parity_error_kelvin"] < 0.05
