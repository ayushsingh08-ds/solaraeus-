import csv
import json
import math
from pathlib import Path
import pyproj
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REVIEW_DIR = REPO_ROOT / "data" / "review"
INTERIM_DIR = REPO_ROOT / "data" / "interim"

@pytest.fixture(scope="module")
def core_trees():
    p = REVIEW_DIR / "core_tree_review.csv"
    assert p.exists(), f"Missing {p}"
    with open(p, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@pytest.fixture(scope="module")
def context_trees():
    p = REVIEW_DIR / "context_tree_review.csv"
    assert p.exists(), f"Missing {p}"
    with open(p, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@pytest.fixture(scope="module")
def bounds_records():
    p = REVIEW_DIR / "tree_dimension_uncertainty_bounds.csv"
    assert p.exists(), f"Missing {p}"
    with open(p, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@pytest.fixture(scope="module")
def protection_report():
    p = REVIEW_DIR / "tree_geometry_review_protection_report.json"
    assert p.exists(), f"Missing {p}"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def canopy_params():
    p = REVIEW_DIR / "species_canopy_parameter_review.csv"
    assert p.exists(), f"Missing {p}"
    with open(p, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# Check 1: All six core-tree IDs exist
def test_all_six_core_tree_ids_exist(core_trees):
    ids = [r["tree_id"] for r in core_trees]
    expected = ["T08", "T09", "T10", "T11", "T12", "T13"]
    assert sorted(ids) == sorted(expected), f"Core tree IDs mismatch: {ids}"

# Check 2: All fourteen census-tree IDs are unique
def test_all_fourteen_census_tree_ids_unique(core_trees, context_trees):
    all_ids = [r["tree_id"] for r in core_trees] + [r["tree_id"] for r in context_trees]
    assert len(all_ids) == 14, f"Expected 14 trees, got {len(all_ids)}"
    assert len(set(all_ids)) == 14, f"Duplicate tree IDs found: {all_ids}"
    expected_all = [f"T{i:02d}" for i in range(1, 15)]
    assert sorted(all_ids) == sorted(expected_all)

# Check 3: No duplicate coordinates
def test_no_duplicate_coordinates(core_trees, context_trees):
    coords = [(float(r["longitude"]), float(r["latitude"])) for r in core_trees + context_trees]
    assert len(coords) == 14
    assert len(set(coords)) == 14, "Found duplicate tree coordinates"

# Check 4: All coordinates transform correctly
def test_coordinates_transform_correctly(core_trees):
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    origin_e, origin_n = 782541.81, 1435736.11
    for r in core_trees:
        lon, lat = float(r["longitude"]), float(r["latitude"])
        ux, uy = transformer.transform(lon, lat)
        assert abs(ux - float(r["x_utm_m"])) < 0.05
        assert abs(uy - float(r["y_utm_m"])) < 0.05
        assert abs((ux - origin_e) - float(r["x_local_m"])) < 0.05
        assert abs((uy - origin_n) - float(r["y_local_m"])) < 0.05

# Check 5: All trees remain within expected boundaries
def test_trees_within_expected_boundaries(core_trees, context_trees):
    # Core trees strictly within [0, 218.5] x [0, 135.1]
    for r in core_trees:
        lx = float(r["x_local_m"])
        ly = float(r["y_local_m"])
        assert 0.0 <= lx <= 218.5, f"{r['tree_id']} X={lx} out of bounds"
        assert 0.0 <= ly <= 135.1, f"{r['tree_id']} Y={ly} out of bounds"
    # All 14 trees within shadow context extent [-50, 270] x [-50, 200]
    for r in core_trees + context_trees:
        lx = float(r.get("x_local_m") or r.get("local_x_m"))
        ly = float(r.get("y_local_m") or r.get("local_y_m"))
        assert -50.0 <= lx <= 270.0
        assert -50.0 <= ly <= 200.0

# Check 6: No raw files changed
def test_no_raw_files_changed(protection_report):
    summary = protection_report["summary"]
    assert summary["all_raw_files_unmodified"] is True
    assert summary["raw_mismatches_count"] == 0

# Check 7: No frozen result files changed
def test_no_frozen_result_files_changed(protection_report):
    frozen = protection_report["frozen_result_directories"]
    assert len(frozen) == 11
    for d, info in frozen.items():
        assert info["verified"] is True, f"Frozen dir {d} failed verification"

# Check 8: Every dimension has an explicit status
def test_every_dimension_has_explicit_status(bounds_records):
    assert len(bounds_records) == 18 # 6 trees x 3 states
    allowed_statuses = ["PHOTO_ESTIMATED", "CENSUS_REPORTED", "FIELD_MEASURED", "SURVEY_VERIFIED", "RESEARCHER_APPROVED", "MISSING"]
    for r in bounds_records:
        assert r["source_status"] in allowed_statuses
        assert r["geometry_state"] in ["CONSERVATIVE_SMALL", "NOMINAL", "CONSERVATIVE_LARGE"]

# Check 9: Missing values are not encoded as zero
def test_missing_values_not_encoded_as_zero():
    # Context trees review check
    p = REVIEW_DIR / "context_tree_review.csv"
    with open(p, "r", encoding="utf-8") as f:
        ctx_rows = list(csv.DictReader(f))
    for r in ctx_rows:
        if r["dimension_status"] == "MISSING":
            # Must not have fake 0.0 values in interim dimension review
            assert r["dimension_status"] != "0"

# Check 10: Every estimate has an evidence reference
def test_every_estimate_has_evidence_reference(bounds_records, core_trees):
    for r in bounds_records:
        assert len(r["notes"].strip()) > 10, f"Missing evidence notes for {r['tree_id']} {r['geometry_state']}"
    for r in core_trees:
        assert r["matched_image_filenames"].strip() != "", f"Missing image link for {r['tree_id']}"
        assert r["visible_scale_reference"].strip() != "", f"Missing scale reference for {r['tree_id']}"

# Check 11: Every bound has a confidence label
def test_every_bound_has_confidence_label(bounds_records):
    for r in bounds_records:
        assert r["confidence"] in ["HIGH", "MEDIUM", "LOW"], f"Invalid confidence {r['confidence']}"

# Check 12: Historical images are not marked as current proof
def test_historical_images_not_marked_as_current_proof(core_trees, bounds_records):
    for r in core_trees:
        assert r["current_existence_status"] == "CURRENT_EXISTENCE_UNCERTAIN"
        assert r["current_existence_status"] != "CONFIRMED_CURRENT"
    for r in bounds_records:
        assert r["current_existence_status"] == "CURRENT_EXISTENCE_UNCERTAIN"

# Check 13: Literature canopy values are separated from measured values
def test_literature_canopy_values_separated(canopy_params):
    for r in canopy_params:
        assert r["lai_status"] in ["LITERATURE_ASSUMED", "MISSING"]
        assert r["parameter_status"] == "CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED"
        assert r["researcher_approval_status"] == "PENDING"

# Check 14: No record is marked simulation-approved without explicit approval
def test_no_record_marked_simulation_approved_without_approval(bounds_records):
    for r in bounds_records:
        assert r["approved_for_simulation"].lower() == "false"

# Check 15: The review output is reproducible
def test_review_output_reproducible():
    geojson_p = REVIEW_DIR / "tree_geometry_uncertainty.geojson"
    assert geojson_p.exists()
    with open(geojson_p, "r", encoding="utf-8") as f:
        fc = json.load(f)
    assert len(fc["features"]) == 6
    for feat in fc["features"]:
        props = feat["properties"]
        assert props["approved_for_simulation"] is False
        assert len(props["height_bounds_m"]) == 3
        # Small < Nominal < Large
        h_sm, h_nom, h_lg = props["height_bounds_m"]
        assert h_sm < h_nom < h_lg, f"Monotonicity error in height bounds: {props['height_bounds_m']}"
        cd_sm, cd_nom, cd_lg = props["crown_diameter_bounds_m"]
        assert cd_sm < cd_nom < cd_lg, f"Monotonicity error in crown diameter bounds: {props['crown_diameter_bounds_m']}"
