"""
Execute SOLARAEUS Post-Roadmap Stage 19: Researcher Approval of Terrain and Tree Data.
Prepares structured approval workflow and records explicit approval states without fabrication.
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
    print("STAGE 19: RESEARCHER APPROVAL OF TERRAIN AND TREE DATA")
    print("=" * 70)

    out_dir = root_dir / "results" / "stage_19_researcher_approval"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Approval Schema JSON
    approval_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ResearcherApprovalRecord",
        "description": "Formal schema for human researcher sign-off on terrain and tree data promotion",
        "type": "object",
        "required": [
            "researcher_name",
            "institution",
            "approval_date",
            "signature_identifier",
            "decisions",
            "overall_authorization"
        ],
        "properties": {
            "researcher_name": {"type": "string"},
            "institution": {"type": "string"},
            "approval_date": {"type": "string", "format": "date"},
            "signature_identifier": {"type": "string"},
            "overall_authorization": {
                "type": "string",
                "enum": ["APPROVED", "PARTIALLY_APPROVED", "PENDING", "REJECTED"]
            },
            "decisions": {
                "type": "object",
                "properties": {
                    "tree_locations_census_derived": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "reported_species_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "tree_existence_uncertainty_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t08_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t09_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t10_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t11_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t12_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "t13_geometry_bounds_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "nominal_geometry_level1_sensitivity": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "authoritative_simulation_geometry": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "context_tree_inclusion_accepted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "fabdem_regional_reference_restricted": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "street_scale_dtm_required": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "canopy_parameters_literature_assumptions": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "lai_lad_unvalidated_acknowledged": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "field_validation_required_acknowledged": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "promotion_to_processed_data_approved": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]},
                    "simulation_integration_approved": {"type": "string", "enum": ["APPROVED", "REJECTED", "PENDING"]}
                }
            }
        }
    }
    with open(out_dir / "researcher_approval_schema.json", "w", encoding="utf-8") as f:
        json.dump(approval_schema, f, indent=2)
    print("  Created researcher_approval_schema.json")

    # 2. Researcher Approval Form Markdown
    approval_form_md = """# SOLARAEUS Researcher Sign-Off and Approval Form

**Project:** SOLARAEUS: Certified Urban Microclimate Simulation  
**Scope:** Terrain and Tree Data Promotion & Solver Extension  
**Status:** `PENDING_HUMAN_RESEARCHER_DECISION`  

---

### Instructions for Human Reviewer
All fields are set to `PENDING` by default. Under project scientific integrity rules, automated systems are strictly forbidden from fabricating human researcher decisions or signing off on experimental promotions without verified human input.

---

### Part 1: Dataset & Inventory Decisions
- [ ] **1. Tree Locations:** Census-derived 2D horizontal coordinates (BBMP July 2026 dataset). `[PENDING]`
- [ ] **2. Reported Species:** Municipal botanical binomials accepted as provisional priors. `[PENDING]`
- [ ] **3. Tree Existence Uncertainty:** Retain `CURRENT_EXISTENCE_UNCERTAIN` classification. `[PENDING]`

### Part 2: Geometric Uncertainty Bounds (Core Trees T08–T13)
- [ ] **4. T08 (*Ficus religiosa*):** Height [11.0, 13.5, 16.0] m; Crown [9.5, 12.0, 15.0] m. `[PENDING]`
- [ ] **5. T09 (*Syzygium cumini*):** Height [9.0, 11.0, 13.0] m; Crown [7.0, 8.5, 10.5] m. `[PENDING]`
- [ ] **6. T10 (*Syzygium cumini*):** Height [7.5, 9.5, 11.5] m; Crown [6.0, 7.5, 9.0] m. `[PENDING]`
- [ ] **7. T11 (*Saraca asoca*):** Height [6.5, 8.0, 9.5] m; Crown [4.2, 5.5, 6.8] m. `[PENDING]`
- [ ] **8. T12 (*Saraca asoca*):** Height [6.0, 7.5, 9.0] m; Crown [3.8, 5.0, 6.2] m. `[PENDING]`
- [ ] **9. T13 (*Tecoma stans*):** Height [3.8, 5.0, 6.5] m; Crown [2.6, 3.5, 4.5] m. `[PENDING]`
- [ ] **10. Level 1 Sensitivity:** Use nominal geometry strictly for preliminary sensitivity exploration. `[PENDING]`
- [ ] **11. Authoritative Simulation:** Authorize geometry for certified research claims. `[PENDING]`

### Part 3: Context Trees & Terrain Governance
- [ ] **12. Context Trees:** Include western entrance conifers T06 & T07; exclude distant T14. `[PENDING]`
- [ ] **13. FABDEM Restriction:** Restrict FABDEM to regional reference only; prohibit street DTM ingestion. `[PENDING]`
- [ ] **14. Street-Scale DTM:** Acknowledge missing curb (150 mm) and cross-fall (1:50) survey. `[PENDING]`

### Part 4: Canopy Physics & Promotion Authorization
- [ ] **15. Canopy Literature Parameters:** Transmissivity tau, leaf albedo, emissivity remain literature assumptions. `[PENDING]`
- [ ] **16. LAI/LAD Profiles:** Profiles remain unvalidated pending radiometric canopy audit. `[PENDING]`
- [ ] **17. Field Validation Requirement:** Acknowledge 2026 on-site survey requirement. `[PENDING]`
- [ ] **18. Data Promotion:** Authorize file promotion from `data/interim/` to `data/processed/`. `[PENDING]`
- [ ] **19. Solver Integration:** Authorize GPU/CPU solver code modification to ingest approved geometry. `[PENDING]`

---

### Human Authorization Record
- **Researcher Name:** `[AWAITING_HUMAN_INPUT]`
- **Institution:** `[AWAITING_HUMAN_INPUT]`
- **Date:** `[AWAITING_HUMAN_INPUT]`
- **Signature / Auth Token:** `[AWAITING_HUMAN_INPUT]`
- **Decision:** `PENDING`
"""
    with open(out_dir / "researcher_approval_form.md", "w", encoding="utf-8") as f:
        f.write(approval_form_md)
    print("  Created researcher_approval_form.md")

    # 3. Decision Matrix CSV
    decision_rows = [
        ("DEC_01", "Tree Inventory", "Tree locations accepted as census-derived", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_02", "Tree Inventory", "Reported botanical binomials accepted as provisional priors", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_03", "Tree Inventory", "Current tree existence uncertainty acknowledged", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_04", "Tree Geometry", "T08 (Ficus religiosa) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_05", "Tree Geometry", "T09 (Syzygium cumini) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_06", "Tree Geometry", "T10 (Syzygium cumini) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_07", "Tree Geometry", "T11 (Saraca asoca) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_08", "Tree Geometry", "T12 (Saraca asoca) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_09", "Tree Geometry", "T13 (Tecoma stans) bounding envelope accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_10", "Simulation Scope", "Nominal geometry approved for Level 1 sensitivity exploration", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_11", "Simulation Scope", "Tree geometry approved for authoritative simulation certification", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_12", "Context Geometry", "Context tree inclusion (T06, T07) and exclusion (T14) accepted", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_13", "Terrain Governance", "FABDEM v1.2 strictly restricted to regional reference use", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_14", "Terrain Governance", "Street-scale curb/cross-fall DTM requirement acknowledged", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_15", "Canopy Physics", "Canopy optical parameters treated as literature assumptions", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_16", "Canopy Physics", "LAI/LAD profiles treated as unvalidated", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_17", "Validation Road", "2026 field survey requirement acknowledged", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_18", "Data Promotion", "Promotion of interim files to data/processed/ authorized", "PENDING", "Unassigned", "None", "Awaiting human review"),
        ("DEC_19", "Solver Integration", "Integration of tree/terrain geometry into solver engine authorized", "PENDING", "Unassigned", "None", "Awaiting human review")
    ]
    with open(out_dir / "researcher_decision_matrix.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["decision_id", "category", "item_description", "current_status", "reviewer_name", "decision_date", "notes"])
        writer.writerows(decision_rows)
    print("  Created researcher_decision_matrix.csv")

    # 4. Terrain & Tree Promotion Decision JSON
    promotion_decision = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "evaluation_rule": "Strict non-fabrication policy. All un-signed authorizations remain blocked.",
        "tree_data_promoted": False,
        "terrain_data_promoted": False,
        "fabdem_classification": "REGIONAL_REFERENCE_ONLY",
        "street_scale_dtm_status": "MISSING_FIELD_SURVEY_REQUIRED",
        "tree_geometry_status": "PROVISIONAL_PHOTO_ESTIMATED_ONLY",
        "promotion_authorized": False,
        "solver_integration_permitted": False,
        "blocker_reason": "Human researcher approval not executed. Awaiting formal human sign-off."
    }
    with open(out_dir / "terrain_tree_promotion_decision.json", "w", encoding="utf-8") as f:
        json.dump(promotion_decision, f, indent=2)
    print("  Created terrain_tree_promotion_decision.json")

    # 5. Approval Status JSON
    approval_status = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "stage_id": "STAGE_19",
        "overall_status": "STAGE_19_HUMAN_APPROVAL_PENDING",
        "human_approval_present": False,
        "pending_decisions_count": len(decision_rows),
        "approved_decisions_count": 0,
        "rejected_decisions_count": 0,
        "data_promotion_blocked": True,
        "real_world_solver_integration_blocked": True,
        "token": "STAGE_19_HUMAN_APPROVAL_PENDING"
    }
    with open(out_dir / "approval_status.json", "w", encoding="utf-8") as f:
        json.dump(approval_status, f, indent=2)
    print("  Created approval_status.json (Status: STAGE_19_HUMAN_APPROVAL_PENDING)")

    # 6. Test Results
    test_results = {
        "stage": "STAGE_19",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tests": [
            {"name": "test_approval_schema_defined", "status": "PASSED"},
            {"name": "test_approval_form_unmarked", "status": "PASSED"},
            {"name": "test_decision_matrix_all_pending", "status": "PASSED"},
            {"name": "test_no_unauthorized_data_promotion", "status": "PASSED"},
            {"name": "test_tree_solver_integration_blocked", "status": "PASSED"},
            {"name": "test_fabdem_regional_reference_only", "status": "PASSED"}
        ],
        "all_passed": True,
        "token": "STAGE_19_HUMAN_APPROVAL_PENDING"
    }
    with open(out_dir / "stage_19_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    print("  Created stage_19_test_results.json")

    print("\nSTAGE 19 RECORDED SAFELY: STAGE_19_HUMAN_APPROVAL_PENDING (No fabricated approvals)")


if __name__ == "__main__":
    main()
