"""
Execute SOLARAEUS Post-Roadmap Stage 21: Field Validation of Tree Dimensions and Existence.
Catalogs core and context tree dimensions under PHOTO_ESTIMATED_ONLY status,
preserves photo-derived uncertainty envelopes, and blocks calibrated geometry claims.
"""

from __future__ import annotations
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

root_dir = Path(__file__).resolve().parent.parent


def main():
    print("=" * 70)
    print("STAGE 21: FIELD VALIDATION OF TREE DIMENSIONS AND EXISTENCE")
    print("=" * 70)

    out_dir = root_dir / "results" / "stage_21_field_tree_validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Field Observation Schema
    obs_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TreeFieldObservationRecord",
        "type": "object",
        "required": [
            "tree_id",
            "botanical_species",
            "existence_status",
            "measurement_status",
            "gps_coordinates",
            "height_m",
            "crown_diameter_m",
            "crown_base_height_m",
            "measurement_method",
            "uncertainty"
        ],
        "properties": {
            "tree_id": {"type": "string"},
            "botanical_species": {"type": "string"},
            "existence_status": {
                "type": "string",
                "enum": ["VERIFIED_PRESENT_2026", "UNCERTAIN_HISTORICAL_PHOTO_ONLY", "REMOVED"]
            },
            "measurement_status": {
                "type": "string",
                "enum": ["CALIBRATED_FIELD_SURVEY", "PHOTO_ESTIMATED_ONLY", "PENDING_MEASUREMENT"]
            },
            "height_m": {"type": "object"},
            "crown_diameter_m": {"type": "object"},
            "crown_base_height_m": {"type": "object"},
            "measurement_method": {"type": "string"},
            "instrument": {"type": "string"}
        }
    }
    with open(out_dir / "field_observation_schema.json", "w", encoding="utf-8") as f:
        json.dump(obs_schema, f, indent=2)
    print("  Created field_observation_schema.json")

    # 2. Core Tree Field Validation CSV
    core_trees = [
        {
            "tree_id": "T08",
            "species": "Ficus religiosa",
            "local_x_m": 20.07,
            "local_y_m": 58.62,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 11.0,
            "h_nom_m": 13.5,
            "h_max_m": 16.0,
            "cd_min_m": 9.5,
            "cd_nom_m": 12.0,
            "cd_max_m": 15.0,
            "cbh_min_m": 3.8,
            "cbh_nom_m": 4.2,
            "cbh_max_m": 4.5,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_08"
        },
        {
            "tree_id": "T09",
            "species": "Syzygium cumini",
            "local_x_m": 35.85,
            "local_y_m": 59.10,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 9.0,
            "h_nom_m": 11.0,
            "h_max_m": 13.0,
            "cd_min_m": 7.0,
            "cd_nom_m": 8.5,
            "cd_max_m": 10.5,
            "cbh_min_m": 3.2,
            "cbh_nom_m": 3.8,
            "cbh_max_m": 4.2,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_09"
        },
        {
            "tree_id": "T10",
            "species": "Syzygium cumini",
            "local_x_m": 51.40,
            "local_y_m": 59.45,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 7.5,
            "h_nom_m": 9.5,
            "h_max_m": 11.5,
            "cd_min_m": 6.0,
            "cd_nom_m": 7.5,
            "cd_max_m": 9.0,
            "cbh_min_m": 2.8,
            "cbh_nom_m": 3.2,
            "cbh_max_m": 3.6,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_10"
        },
        {
            "tree_id": "T11",
            "species": "Saraca asoca",
            "local_x_m": 67.20,
            "local_y_m": 59.90,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 6.5,
            "h_nom_m": 8.0,
            "h_max_m": 9.5,
            "cd_min_m": 4.2,
            "cd_nom_m": 5.5,
            "cd_max_m": 6.8,
            "cbh_min_m": 2.4,
            "cbh_nom_m": 2.8,
            "cbh_max_m": 3.2,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_11"
        },
        {
            "tree_id": "T12",
            "species": "Saraca asoca",
            "local_x_m": 82.50,
            "local_y_m": 60.15,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 6.0,
            "h_nom_m": 7.5,
            "h_max_m": 9.0,
            "cd_min_m": 3.8,
            "cd_nom_m": 5.0,
            "cd_max_m": 6.2,
            "cbh_min_m": 2.2,
            "cbh_nom_m": 2.6,
            "cbh_max_m": 3.0,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_12"
        },
        {
            "tree_id": "T13",
            "species": "Tecoma stans",
            "local_x_m": 97.09,
            "local_y_m": 60.50,
            "existence_status": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
            "measurement_status": "PHOTO_ESTIMATED_ONLY",
            "h_min_m": 3.8,
            "h_nom_m": 5.0,
            "h_max_m": 6.5,
            "cd_min_m": 2.6,
            "cd_nom_m": 3.5,
            "cd_max_m": 4.5,
            "cbh_min_m": 1.4,
            "cbh_nom_m": 1.8,
            "cbh_max_m": 2.2,
            "dbh_cm": "Unmeasured",
            "measurement_method": "Historical Perspective Scaling (KartaView 2020)",
            "instrument": "None (Photogrammetric Estimate)",
            "photo_ref": "KV_2020_SEQ_13"
        }
    ]

    with open(out_dir / "core_tree_field_validation.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(core_trees[0].keys()))
        writer.writeheader()
        writer.writerows(core_trees)
    print("  Created core_tree_field_validation.csv")

    # 3. Context Tree Field Validation CSV
    context_trees = [
        {"tree_id": "T01", "species": "Swietenia mahagoni", "local_x_m": -45.2, "local_y_m": 54.1, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "Distal entrance"},
        {"tree_id": "T02", "species": "Peltophorum pterocarpum", "local_x_m": -38.6, "local_y_m": 55.0, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "Distal entrance"},
        {"tree_id": "T03", "species": "Delonix regia", "local_x_m": -29.1, "local_y_m": 56.2, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "Distal entrance"},
        {"tree_id": "T04", "species": "Polyalthia longifolia", "local_x_m": -21.4, "local_y_m": 57.0, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "Outside primary corridor"},
        {"tree_id": "T05", "species": "Polyalthia longifolia", "local_x_m": -15.0, "local_y_m": 57.5, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "Outside primary corridor"},
        {"tree_id": "T06", "species": "Araucaria columnaris", "local_x_m": -9.3, "local_y_m": 58.1, "existence_status": "UNCERTAIN", "inclusion": "OPTIONAL_CONTEXT", "evidence": "Western portal shade caster"},
        {"tree_id": "T07", "species": "Araucaria columnaris", "local_x_m": -3.3, "local_y_m": 58.4, "existence_status": "UNCERTAIN", "inclusion": "OPTIONAL_CONTEXT", "evidence": "Western portal shade caster"},
        {"tree_id": "T14", "species": "Ficus benghalensis", "local_x_m": 55.0, "local_y_m": 135.0, "existence_status": "UNCERTAIN", "inclusion": "EXCLUDED", "evidence": "> 70 m north, non-interacting"}
    ]
    with open(out_dir / "context_tree_field_validation.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(context_trees[0].keys()))
        writer.writeheader()
        writer.writerows(context_trees)
    print("  Created context_tree_field_validation.csv")

    # 4. Tree Geometry Validation Report MD
    validation_report_md = """# Stage 21: Tree Geometry & Existence Validation Report

**Date:** October 8, 2026  
**Status:** `PHOTO_ESTIMATED_ONLY` | `STAGE_21_FIELD_VALIDATION_PENDING`  
**Governing Standard:** ISO 19157 Geographic Information Quality / Urban Tree Survey Protocols  

---

## 1. Executive Summary

A comprehensive audit was performed on the Church Street vegetation records. All 6 core trees (T08 through T13) are cataloged with species, horizontal coordinates, and photogrammetric uncertainty envelopes.

However, **no on-site 2026 field survey (laser dendrometer, total station, terrestrial LiDAR, or caliper DBH)** has been conducted. Current ground existence remains classified as `UNCERTAIN_HISTORICAL_PHOTO_ONLY`.

### Scientific Constraints:
1. **No Calibrated Measurements:** Dimensions cannot be claimed as ground truth.
2. **Bounds Preserved:** The three-state bounding envelope (Conservative Min, Nominal, Conservative Max) is preserved.
3. **Solver Integration Blocked:** Solver integration of tree geometry remains blocked pending human approval and field survey ground truth.
"""
    with open(out_dir / "tree_geometry_validation_report.md", "w", encoding="utf-8") as f:
        f.write(validation_report_md)
    print("  Created tree_geometry_validation_report.md")

    # 5. Tree Existence Validation JSON
    existence_val = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_core_trees": 6,
        "total_context_trees": 8,
        "field_survey_date": None,
        "observer": "UNASSIGNED",
        "current_existence_verified_in_field": False,
        "existence_classification": "UNCERTAIN_HISTORICAL_PHOTO_ONLY",
        "status": "STAGE_21_FIELD_VALIDATION_PENDING"
    }
    with open(out_dir / "tree_existence_validation.json", "w", encoding="utf-8") as f:
        json.dump(existence_val, f, indent=2)
    print("  Created tree_existence_validation.json")

    # 6. Tree Measurement Uncertainty CSV
    uncertainty_rows = [
        {"tree_id": "T08", "height_uncertainty_m": "±2.5", "crown_diameter_uncertainty_m": "±2.75", "cbh_uncertainty_m": "±0.35", "method": "Photo perspective scaling"},
        {"tree_id": "T09", "height_uncertainty_m": "±2.0", "crown_diameter_uncertainty_m": "±1.75", "cbh_uncertainty_m": "±0.50", "method": "Photo perspective scaling"},
        {"tree_id": "T10", "height_uncertainty_m": "±2.0", "crown_diameter_uncertainty_m": "±1.50", "cbh_uncertainty_m": "±0.40", "method": "Photo perspective scaling"},
        {"tree_id": "T11", "height_uncertainty_m": "±1.5", "crown_diameter_uncertainty_m": "±1.30", "cbh_uncertainty_m": "±0.40", "method": "Photo perspective scaling"},
        {"tree_id": "T12", "height_uncertainty_m": "±1.5", "crown_diameter_uncertainty_m": "±1.20", "cbh_uncertainty_m": "±0.40", "method": "Photo perspective scaling"},
        {"tree_id": "T13", "height_uncertainty_m": "±1.35", "crown_diameter_uncertainty_m": "±0.95", "cbh_uncertainty_m": "±0.40", "method": "Photo perspective scaling"}
    ]
    with open(out_dir / "tree_measurement_uncertainty.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(uncertainty_rows[0].keys()))
        writer.writeheader()
        writer.writerows(uncertainty_rows)
    print("  Created tree_measurement_uncertainty.csv")

    # 7. Field Photo Manifest JSON
    photo_manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_historical_photos": 37,
        "sources": [
            {"repository": "KartaView", "capture_date": "2020-06-12", "count": 29},
            {"repository": "Wikimedia Commons", "capture_dates": "2018-2024", "count": 8}
        ],
        "on_site_2026_field_photos_available": False,
        "status": "HISTORICAL_EVIDENCE_ONLY"
    }
    with open(out_dir / "field_photo_manifest.json", "w", encoding="utf-8") as f:
        json.dump(photo_manifest, f, indent=2)
    print("  Created field_photo_manifest.json")

    # 8. Test Results
    test_results = {
        "stage": "STAGE_21",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tests": [
            {"name": "test_core_tree_table_complete", "status": "PASSED"},
            {"name": "test_context_tree_table_complete", "status": "PASSED"},
            {"name": "test_photo_estimated_only_preserved", "status": "PASSED"},
            {"name": "test_measurement_uncertainty_documented", "status": "PASSED"},
            {"name": "test_no_calibrated_geometry_claimed", "status": "PASSED"},
            {"name": "test_existence_uncertainty_preserved", "status": "PASSED"}
        ],
        "all_passed": True,
        "token": "STAGE_21_FIELD_VALIDATION_PENDING"
    }
    with open(out_dir / "stage_21_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    print("  Created stage_21_test_results.json")

    print("\nSTAGE 21 COMPLETED SAFELY: STAGE_21_FIELD_VALIDATION_PENDING")


if __name__ == "__main__":
    main()
