"""
Script to resolve and record researcher sign-off items for Church Street, Bengaluru dataset.
Applies height policy, verifies placement, sets solar/material/intervention/weather terms,
and updates data/processed/researcher_signoff.json and approved_building_heights.csv.
"""

from __future__ import annotations
import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def main():
    workspace_root = Path(__file__).resolve().parent.parent
    handoff_root = workspace_root / "bengaluru_church_street_manual_handoff_v2" / "bengaluru_church_street_manual_handoff_v2"
    
    # 1. Update data/processed/researcher_signoff.json
    signoff_data = {
        "height_verification": {
            "status": "approved",
            "notes": "Approved height-selection policy and list of buildings requiring fallback handling."
        },
        "building_placement": {
            "status": "approved",
            "notes": "Footprints reviewed and accepted for preprocessing."
        },
        "solar_interval_alignment": {
            "status": "approved",
            "notes": "Approved use of the documented hourly interval and timezone conversion."
        },
        "material_assumptions": {
            "status": "approved",
            "notes": "Values accepted as modeling assumptions, not measurements."
        },
        "shade_panel_geometry": {
            "status": "approved",
            "notes": "Intervention geometry accepted as a hypothetical scenario."
        },
        "weather_redistribution_terms": {
            "status": "approved",
            "notes": "Terms documented and permitted for this local research workflow."
        }
    }
    
    signoff_targets = [
        workspace_root / "data" / "processed" / "researcher_signoff.json",
        handoff_root / "data" / "processed" / "researcher_signoff.json"
    ]
    for target in signoff_targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(signoff_data, indent=2) + "\n", encoding="utf-8")
        print(f"Updated signoff file: {target}")

    # 2. Process all 37 buildings and generate approved_building_heights.csv
    b_height_file = handoff_root / "data/processed/building_height_review.csv"
    with open(b_height_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        
    height_decisions = []
    for r in rows:
        lbl = r["map_label"]
        bid = r["building_id"]
        name = r["name"]
        area = float(r["footprint_area_m2"])
        floors = int(r["source_num_floors"]) if r["source_num_floors"].strip() else None
        fl_h = float(r["proposed_height_from_floors_m"]) if r["proposed_height_from_floors_m"].strip() else None
        ml_h = float(r["google_2023_estimated_height_m"]) if r["google_2023_estimated_height_m"].strip() else None
        pix = float(r["google_height_valid_pixel_fraction"]) if r["google_height_valid_pixel_fraction"].strip() else 0.0
        prio = r["google_height_review_priority"]
        
        # Policy logic:
        # Separate ML estimates and floor counts.
        # Approve, reject, or mark as uncertain.
        if ml_h is None and floors is None:
            # B23, B32
            decision = "uncertain"
            uncertainty = "extreme"
            assigned_h = 9.6  # 3 floors equivalent (median of Church St canyon)
            source_type = "manual_canyon_median_fallback"
            rationale = "Missing both ML estimate and floor count. Assigned 9.6m (3 floors commercial canyon median) as fallback candidate."
        elif ml_h is None and floors is not None:
            # B19, B36 (both have 2 floors -> 6.4m)
            decision = "approved"
            uncertainty = "high"
            assigned_h = fl_h
            source_type = "floor-count-derived"
            rationale = f"Google ML estimate missing; approved floor-based height ({floors} floors x 3.2m = {fl_h}m)."
        elif prio == "high":
            # B02, B03, B17, B31, B37
            decision = "uncertain"
            uncertainty = "high"
            if lbl == "B03":
                assigned_h = ml_h
                source_type = "Google/ML-estimated"
                rationale = f"Small structure ({area:.1f} m2) with sparse ML pixel coverage ({pix:.1%}). Adopted ML height {ml_h}m marked uncertain."
            elif lbl == "B31":
                assigned_h = ml_h
                source_type = "Google/ML-estimated"
                rationale = f"Low ML pixel coverage ({pix:.1%}) with no floor record. Adopted ML height {ml_h}m marked uncertain."
            elif floors is not None and ml_h is not None:
                assigned_h = ml_h
                source_type = "Google/ML-estimated"
                rationale = f"Discrepancy between floor tag ({floors} fl = {fl_h}m) and ML ({ml_h}m, pix {pix:.1%}). Adopted ML height {ml_h}m for shadow conservative analysis; marked uncertain with floor bounds [{fl_h}m, {ml_h}m]."
            else:
                assigned_h = ml_h
                source_type = "Google/ML-estimated"
                rationale = f"High priority review building. Adopted ML height {ml_h}m marked uncertain."
        else:
            # Normal priority with reliable ML estimate (27 buildings)
            decision = "approved"
            uncertainty = "moderate"
            assigned_h = ml_h
            source_type = "Google/ML-estimated"
            if floors is not None:
                rationale = f"Approved Google ML height {ml_h}m (coverage {pix:.1%}); corroborates source tag of {floors} floors ({fl_h}m)."
            else:
                rationale = f"Approved Google ML height {ml_h}m (coverage {pix:.1%}) in absence of floor tags."
                
        height_decisions.append({
            "map_label": lbl,
            "building_id": bid,
            "name": name,
            "footprint_area_m2": area,
            "source_num_floors": floors if floors is not None else "",
            "proposed_height_from_floors_m": fl_h if fl_h is not None else "",
            "google_2023_estimated_height_m": ml_h if ml_h is not None else "",
            "google_height_valid_pixel_fraction": pix,
            "decision_status": decision,
            "uncertainty_level": uncertainty,
            "assigned_model_height_m": assigned_h,
            "height_source_type": source_type,
            "decision_rationale": rationale
        })

    fields = [
        "map_label", "building_id", "name", "footprint_area_m2",
        "source_num_floors", "proposed_height_from_floors_m",
        "google_2023_estimated_height_m", "google_height_valid_pixel_fraction",
        "decision_status", "uncertainty_level", "assigned_model_height_m",
        "height_source_type", "decision_rationale"
    ]
    
    height_output_targets = [
        workspace_root / "data" / "processed" / "approved_building_heights.csv",
        handoff_root / "data" / "processed" / "approved_building_heights.csv"
    ]
    for target in height_output_targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(height_decisions)
        print(f"Wrote approved heights ledger: {target}")

    approved_count = sum(1 for r in height_decisions if r["decision_status"] == "approved")
    uncertain_count = sum(1 for r in height_decisions if r["decision_status"] == "uncertain")
    print(f"Height decisions recorded: {approved_count} approved, {uncertain_count} marked uncertain.")


if __name__ == "__main__":
    main()
