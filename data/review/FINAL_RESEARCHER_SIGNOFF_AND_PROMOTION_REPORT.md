# SOLARAEUS Final Researcher Sign-Off and Promotion-Readiness Report

**Project**: SOLARAEUS: High-Performance GPU Ray-Traced Urban Microclimate Simulation  
**Study Corridor**: Church Street, Bengaluru, Karnataka, India ($218.5\text{ m} \times 135.1\text{ m}$)  
**Local Coordinate Origin**: Easting $782,541.81\text{ m}$, Northing $1,435,736.11\text{ m}$ (EPSG:32643, UTM Zone 43N)  
**Stage**: Final Researcher Sign-Off and Promotion Readiness  
**Date**: October 7, 2026  
**Success Token**: `RESEARCHER_SIGNOFF_PACKAGE_COMPLETE`  
**Operational Status**:  
```text
RESEARCHER_SIGNOFF_PACKAGE_COMPLETE
SIMULATION_INTEGRATION_BLOCKED
AWAITING_HUMAN_APPROVAL
```

---

## 1. Executive Summary

This report concludes the data-review and sign-off preparation stage for Project **SOLARAEUS**. All empirical datasets (BBMP municipal tree census, KartaView/Commons street-level imagery, and FABDEM bare-earth elevation) have been audited, cross-referenced, and structured into formal uncertainty bounds.

In accordance with strict scientific restrictions:
- **Zero Physics Solvers or Optimization Code Were Modified**: Solvers remain locked.
- **Zero Raw Supplement Files Were Modified**: All 202 raw physical files remain byte-identical.
- **Zero Interim Files Were Modified**: All 26 interim assets remain byte-identical.
- **Zero Unverified Geometry Ingested into Solver**: No tree geometry or canopy physics parameters have been added to solver inputs.
- **Zero Automatic Approvals**: Sign-off checkboxes and promotion manifests remain strictly unapproved pending human authorization.

---

## 2. Protection Audit Summary

The final protection audit verified the immutability of all repository assets:
- **Raw Supplements**:
  - `bengaluru_church_street_bbmp_trees_july2026_supplement`: 26 files (0 mismatches).
  - `bengaluru_church_street_raw_sources_2026-10-07`: 84 files (0 mismatches).
  - `bengaluru_church_street_manual_handoff_v2`: 92 files (0 mismatches).
  - **Total Raw Files Audited**: **202 files, 0 mismatches**.
- **Interim Source Files**: **26 files, 0 mismatches**.
- **Frozen Benchmark Directories**: **11 historical result suites verified intact**.
- **Git State**: Clean working tree; solvers and frozen directories untouched.

Audit File: [final_protection_audit.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_protection_audit.json).

---

## 3. Reconciled File Counts

Historical reports cited different file counts due to differing enumeration scopes. These have been formally reconciled in [protection_count_reconciliation.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/protection_count_reconciliation.json):
1. **197 Files (Package Manifest Enumeration)**: Count of files explicitly indexed across delivered `SHA256SUMS.txt` package manifests ($25 + 83 + 89 = 197$).
2. **202 Raw Files (Exhaustive Disk Enumeration)**: Total physical files on disk across the three raw package directories ($26 + 84 + 92 = 202$), accounting for the 3 checksum manifest files themselves and 2 package-level metadata files.
3. **26 Interim Files**: Total files in `data/interim/` (15 primary deliverables + 5 intermediate terrain files + 6 plot PNGs).
4. **11 Frozen Benchmark Suites**: Historical result suites preserved under `results/`.

---

## 4. Core-Tree Decision Table Summary (T08 to T13)

All six core trees are concentrated on the southern pedestrian sidewalk of Church Street ($X \in [20.07, 97.09]\text{ m}, Y \in [65.54, 83.27]\text{ m}$):

| Tree ID | Species | Local Coord (X, Y) | Image Match | Current Existence | Height Bounds (m) | Crown Diam Bounds (m) | Recommended Decision |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T08** | *Ficus religiosa* | (20.07m, 81.14m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[11.0, 13.5, 16.0]$ | $[9.5, 12.0, 15.0]$ | `ACCEPT_BOUNDS_ONLY` |
| **T09** | *Syzygium cumini* | (44.91m, 83.27m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[9.0, 11.0, 13.0]$ | $[7.0, 8.5, 10.5]$ | `ACCEPT_BOUNDS_ONLY` |
| **T10** | *Syzygium cumini* | (33.24m, 77.29m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[7.5, 9.5, 11.5]$ | $[6.0, 7.5, 9.0]$ | `ACCEPT_BOUNDS_ONLY` |
| **T11** | *Saraca asoca* | (60.95m, 75.36m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[6.5, 8.0, 9.5]$ | $[4.2, 5.5, 6.8]$ | `ACCEPT_BOUNDS_ONLY` |
| **T12** | *Saraca asoca* | (78.32m, 74.65m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[6.0, 7.5, 9.0]$ | $[3.8, 5.0, 6.2]$ | `ACCEPT_BOUNDS_ONLY` |
| **T13** | *Tecoma stans* | (97.09m, 65.54m) | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[3.8, 5.0, 6.5]$ | $[2.6, 3.5, 4.5]$ | `ACCEPT_BOUNDS_ONLY` |

Decision File: [final_core_tree_decision_table.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_core_tree_decision_table.csv).

---

## 5. Context-Tree Decision Summary (8 Buffer Trees)

- **T06 & T07 (*Araucaria columnaris*, Local X = -3.28m, -9.26m)**: Western entrance conifers confirmed in KartaView photos. Role: `OPTIONAL_CONTEXT_GEOMETRY`.
- **T03, T04, T05**: Northern setback and entrance setback trees. Role: `LOCATION_ONLY`.
- **T01, T02**: Northern rear parcel alley trees obscured by commercial building masses. Role: `INSUFFICIENT_DATA`.
- **T14 (*Pongamia pinnata*, Local X = 142.94m, Y = 141.82m)**: >70m north of corridor behind commercial blocks. Role: `EXCLUDE_PENDING_REVIEW`.

Decision File: [final_context_tree_decision_table.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_context_tree_decision_table.csv).

---

## 6. Geometry and Canopy-Parameter Decoupling

Data elements have been segregated into four strict categories in [final_data_status_matrix.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_data_status_matrix.csv):
1. **Verified**: Census tree identity, census coordinates, reported species, spatial classification.
2. **Provisional**: Photo-estimated heights, crown diameters, crown base heights, trunk diameters, FABDEM regional elevation baseline.
3. **Literature-Assumed**: Shortwave transmissivity ($\tau \in [0.05, 0.30]$), LAI, LAD, leaf albedo, leaf emissivity, seasonal foliage state.
4. **Missing**: Current 2026 tree existence, field-measured dimensions, calibrated optical data, street-scale DTM, empirical microclimate validation.

---

## 7. FABDEM Terrain Decision & Street-Scale DTM Gap

- **Classification**: `REGIONAL_REFERENCE_ONLY`.
- **Finding**: FABDEM bare-earth raster successfully stripped $+16.6\text{ m}$ commercial building radar reflections present in the Skadi DEM, confirming a regional longitudinal descent from West ($917.40\text{ m}$) to East ($910.12\text{ m}$).
- **Microscale Inadequacy**: Cell size ($\approx 30.87\text{ m}$) is over double the width of Church Street; it cannot resolve $150\text{ mm}$ curb steps or $1:50$ transverse drainage slopes.
- **Policy**: FABDEM is restricted to macro-topography reference. Street-scale DTM remains classified as `MISSING`. Direct raster ingestion into ray tracing is forbidden.

Decision File: [final_terrain_promotion_decision.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_terrain_promotion_decision.json).

---

## 8. Promotion Candidates & Human Decisions Required

Six candidate files have been logged in [final_promotion_manifest.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_promotion_manifest.json) with default `approved_for_promotion: false`.

The 10 governing human decisions documented in [human_decisions_required.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/human_decisions_required.md) require formal researcher determination before promotion or simulation integration may proceed.

---

## 9. Sign-Off Instructions & Blockers

To authorize promotion or Level 1 sensitivity testing:
1. Review the uncertainty envelopes and decision tables.
2. Complete the checkboxes and sign [final_researcher_signoff_form.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/final_researcher_signoff_form.md).
3. Record researcher name, institution, date, approval identifier, and scope restrictions.

### Explicit Simulation Blockers
- `approved_for_simulation: false` across all records.
- `approved_for_promotion: false` across all candidates.
- `researcher_approval_status: PENDING` across all canopy parameters.
- `current_existence_status: CURRENT_EXISTENCE_UNCERTAIN` across all 14 trees.
- `microscale_dtm: MISSING`.

---

## 10. Final Project Status

```text
TREE_LOCATIONS_VERIFIED
TREE_SPECIES_REPORTED
TREE_CURRENT_EXISTENCE_UNCERTAIN
TREE_DIMENSIONS_PROVISIONAL
TREE_GEOMETRY_BOUNDS_AVAILABLE
CANOPY_LEVEL_1_NOT_YET_APPROVED
CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED
FABDEM_REGIONAL_REFERENCE_ONLY
MICROSCALE_DTM_MISSING
RESEARCHER_SIGNOFF_REQUIRED
SIMULATION_INTEGRATION_BLOCKED
```

RESEARCHER_SIGNOFF_PACKAGE_COMPLETE
