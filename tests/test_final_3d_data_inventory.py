"""
Test suite for Data Inventory & File Protection Audit (Part 2, 3, 16).
"""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/final_3d_integrated_simulation"


def test_data_inventory_manifest_exists():
    inv_file = OUT / "data_inventory.json"
    assert inv_file.exists(), "data_inventory.json must exist"
    with open(inv_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "total_files_audited" in data
    assert data["total_files_audited"] > 0
    assert len(data["files"]) > 0


def test_data_source_registry_and_limitations():
    reg_file = OUT / "data_source_registry.json"
    assert reg_file.exists(), "data_source_registry.json must exist"
    with open(reg_file, "r", encoding="utf-8") as f:
        reg = json.load(f)
    assert "buildings" in reg
    assert "trees_core" in reg
    assert "terrain_fabdem" in reg
    # Absence of observed cloud data explicitly stated
    assert "CLOUD_MODEL_PARAMETRIC_NOT_OBSERVED" in reg["cloud_data_status"]
    # No water body invented
    assert "NO_WATER_BODY_IN_PROJECT_DATA" in reg["water_data_status"]


def test_protection_audit_preserves_stages():
    audit_file = OUT / "final_3d_protection_audit.json"
    assert audit_file.exists()
    with open(audit_file, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["status"] == "PROTECTED_FILES_UNTOUCHED"
    assert audit["data_raw_preserved"] is True
    assert audit["data_review_preserved"] is True
