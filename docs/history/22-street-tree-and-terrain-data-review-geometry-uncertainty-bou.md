## 22. Street-Tree & Terrain Data Review, Geometry Uncertainty-Bounding, and Promotion-Readiness (Milestone 22)

**Date**: October 7, 2026  
**Study Corridor**: Church Street, Bengaluru ($218.5\,\text{m} \times 135.1\,\text{m}$ domain, EPSG:32643 UTM Zone 43N)  
**Deliverable Directory**: `data/review/`  
**Operational Status**: `RESEARCHER_SIGNOFF_PACKAGE_COMPLETE`, `SIMULATION_INTEGRATION_BLOCKED`, `AWAITING_HUMAN_APPROVAL`

### 22.1 Strict Scientific Review Principles
1. **Historical Imagery Is Not Proof of Current Existence**: Street photographs (KartaView 2021, Wikimedia Commons 2022–2023) verify historical presence at capture time but cannot prove 2026 tree existence.
2. **Photo-Estimated Dimensions Are Provisional Approximations**: Pixel-scaled heights and crown diameters carry substantial uncertainty ($\pm 20\%$) and are not validated measurements.
3. **Decoupling Geometry from Biophysical Parameters**: Verified tree coordinates and bounds must never be conflated with literature-assumed canopy properties (LAI, LAD, shortwave transmissivity $\tau$, leaf albedo, emissivity).
4. **Decoupling Elevation from Solver Inputs**: FABDEM bare-earth DTM confirms macro-topography but cannot resolve micro-scale urban curbs; direct ingestion into ray tracing is forbidden.
5. **No Automatic Sign-Off or Promotion**: All promotions to `data/processed/` and physics solver integration remain strictly locked pending human researcher authorization.

### 22.2 Core-Tree Decision Table (T08 to T13)
All six core trees are situated along the southern pedestrian sidewalk of Church Street ($X \in [20.07, 97.09]\,\text{m}, Y \in [65.54, 83.27]\,\text{m}$):

| Tree ID | Botanical Name | Local Coords $(X, Y)$ | Imagery Evidence | 2026 Existence Status | Height Bounds $[h_{\min}, h_{\mathrm{mid}}, h_{\max}]\,(\text{m})$ | Crown Diam $[D_{\min}, D_{\mathrm{mid}}, D_{\max}]\,(\text{m})$ | Recommended Policy |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T08** | *Ficus religiosa* | $(20.07, 81.14)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[11.0, 13.5, 16.0]$ | $[9.5, 12.0, 15.0]$ | `ACCEPT_BOUNDS_ONLY` |
| **T09** | *Syzygium cumini* | $(44.91, 83.27)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[9.0, 11.0, 13.0]$ | $[7.0, 8.5, 10.5]$ | `ACCEPT_BOUNDS_ONLY` |
| **T10** | *Syzygium cumini* | $(33.24, 77.29)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[7.5, 9.5, 11.5]$ | $[6.0, 7.5, 9.0]$ | `ACCEPT_BOUNDS_ONLY` |
| **T11** | *Saraca asoca* | $(60.95, 75.36)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[6.5, 8.0, 9.5]$ | $[4.2, 5.5, 6.8]$ | `ACCEPT_BOUNDS_ONLY` |
| **T12** | *Saraca asoca* | $(78.32, 74.65)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[6.0, 7.5, 9.0]$ | $[3.8, 5.0, 6.2]$ | `ACCEPT_BOUNDS_ONLY` |
| **T13** | *Tecoma stans* | $(97.09, 65.54)\,\text{m}$ | `MATCH_CONFIRMED` | `CURRENT_EXISTENCE_UNCERTAIN` | $[3.8, 5.0, 6.5]$ | $[2.6, 3.5, 4.5]$ | `ACCEPT_BOUNDS_ONLY` |

### 22.3 Context-Tree Decisions (8 Buffer Trees)
- **T06 & T07 (*Araucaria columnaris*)**: Western entrance conifers (Local $X = -3.28\,\text{m}, -9.26\,\text{m}$) confirmed in imagery. Recommended as `OPTIONAL_CONTEXT_GEOMETRY`.
- **T03, T04, T05**: Northern entrance and setback trees. Role: `LOCATION_ONLY`.
- **T01, T02**: Northern alley trees obscured by commercial building masses (`INSUFFICIENT_DATA`).
- **T14 (*Pongamia pinnata*)**: $>70\,\text{m}$ north of corridor behind commercial blocks (`EXCLUDE_PENDING_REVIEW`).

### 22.4 FABDEM Terrain Elevation & Street-Scale DTM Gap
- **Analysis**: FABDEM 30m bare-earth raster successfully eliminates the $+16.6\,\text{m}$ radar canopy/building bias present in Copernicus/Skadi DEM, confirming a gentle regional gradient ($917.40\,\text{m}$ West to $910.12\,\text{m}$ East, slope $\approx 3.3\%$).
- **Microscale Inadequacy**: Cell resolution ($\approx 30.87\,\text{m}$) cannot resolve $150\,\text{mm}$ curbs or $1:50$ road camber.
- **Classification**: Tagged as `REGIONAL_REFERENCE_ONLY`. Street-scale DTM remains `MISSING`. Flat ground model preserved for physical simulation.

### 22.5 Asset Protection & File Count Reconciliation
- **Protection Audit**: All 202 raw supplement files across the three packages (`bbmp_trees_july2026_supplement`: 26 files, `raw_sources_2026-10-07`: 84 files, `manual_handoff_v2`: 92 files) and 26 interim files verified 100% byte-identical.
- **Count Reconciliation**: Documented difference between 197 indexed package files vs 202 total disk files (accounting for package checksums and metadata files).
- **Key Artifacts Generated in `data/review/`**:
  - `FINAL_RESEARCHER_SIGNOFF_AND_PROMOTION_REPORT.md`
  - `RESEARCHER_REVIEW_REPORT.md`
  - `final_protection_audit.json`
  - `final_core_tree_decision_table.csv`
  - `final_context_tree_decision_table.csv`
  - `final_data_status_matrix.csv`
  - `tree_dimension_uncertainty_bounds.csv`
  - `tree_geometry_uncertainty.geojson`
  - `final_researcher_signoff_form.md`

---

