## 10. Milestone 15: Real-World Urban Dataset Review & Manual Sign-off Resolution (Bengaluru Church Street Study Block)

### 10.1 Study Site & Spatial Boundary Definition
- **Site Name**: Church Street central/eastern study block, Bengaluru, Karnataka, India.
- **Geographic Centre**: $12.974900^\circ\,\text{N}, 77.605400^\circ\,\text{E}$.
- **Core Study Boundary**:
  - Longitude extents: $77.6044^\circ\,\text{E} \text{ to } 77.6064^\circ\,\text{E}$.
  - Latitude extents: $12.9743^\circ\,\text{N} \text{ to } 12.9755^\circ\,\text{N}$.
  - Geodesic dimensions: $216.99\,\text{m}$ (East–West) $\times 132.76\,\text{m}$ (North–South).
  - Projected UTM Zone 43N dimensions: $218.46\,\text{m} \times 135.05\,\text{m}$ (Area: $28,840.88\,\text{m}^2$).
  - Core building footprint count: **37 buildings** (28 centroids inside boundary, 9 intersecting edge buildings retained in full without clipping).
- **Shadow-Context Boundary**:
  - Definition: Main boundary expanded outward by exactly $75.0\,\text{m}$ in metric UTM coordinates with squared (mitre) corners.
  - Mathematical audit: Symmetric difference between handoff GeoJSON and analytical $75.0\,\text{m}$ mitre buffer is $2.01 \times 10^{-7}\,\text{m}^2$ (floating-point precision).
  - Context building footprint count: **123 buildings** (37 core + 86 external potential shadow-casters).
  - Receptor policy: Microclimate calculation and reporting are strictly confined to the core domain.
- **Coordinate Systems & Projection**:
  - Source CRS: EPSG:4326 (WGS84 lon, lat).
  - Calculation CRS: EPSG:32643 (UTM Zone 43N, metres).
  - Transformation convention: `always_xy=True` strictly enforced. Roundtrip precision error $< 3.55 \times 10^{-15}$ degrees.
  - Local origin: Easting $782,541.81\,\text{m}$, Northing $1,435,736.11\,\text{m}$.
  - Grid convergence angle: $\gamma = +0.5854^\circ$ ($+35.12'$). Solar ray azimuths must account for grid convergence relative to True North.

### 10.2 Strict Review Phase & Audit Deliverables
A comprehensive, non-destructive audit of `bengaluru_church_street_manual_handoff_v2` was completed prior to any simulation execution. Zero thermal calculations ($T_{\text{mrt}}$, $\text{UTCI}$) were run.
- **SHA256 Hash Verification**: 89 / 89 handoff files matched `SHA256SUMS.txt` byte-identically (0 mismatches, 0 missing).
- **Review Artifact Directory**: `results/church_street_data_review_20261006_203634/` containing all 12 required files:
  1. `review_report.md`: 14-section formal report establishing `NOT_READY_FOR_SIMULATION` (`READY_FOR_PREPROCESSING_ONLY`).
  2. `file_inventory.csv`: Full catalog of 89 audited files.
  3. `geometry_review.csv`: Footprint metrics for all 123 buildings (validity, vertex count, area, bounding box).
  4. `height_evidence_review.csv`: 37 core buildings keeping source floors, ML estimates, and model heights separate.
  5. `coordinate_review.json`: CRS parameters, origin, grid convergence, and transformation precision.
  6. `terrain_review.json`: Skadi DEM metadata, EGM96 datum, and flat-ground solver policy.
  7. `weather_review.json`: Bengaluru City station observations and derived Magnus RH ($19.729\%$).
  8. `solar_timestamp_review.json`: NASA POWER hourly fluxes and interval alignment analysis.
  9. `intervention_review.json`: Proposed 6m × 3m overhead shade panel geometry and assumptions.
  10. `provenance_review.json`: Upstream licensing audit and NOAA international station terms flag.
  11. `unresolved_items.json`: Detailed registry of 6 open researcher sign-off gates.
  12. `summary.json`: Machine-readable audit rollup.

### 10.3 Resolution of the Six Researcher Sign-off Items
In Phase 2, all six manual sign-off items were formally resolved and approved in `data/processed/researcher_signoff.json`:

1. **Building Heights (`height_verification`)**:
   - Status: `approved`.
   - Policy: Separate evidence streams preserved. 30 buildings approved (28 Google ML moderate uncertainty, 2 floor tags high uncertainty); 7 marked uncertain (5 floor/ML conflicts or sparse pixels, 2 commercial canyon median fallbacks of $9.6\,\text{m}$ for B23 and B32).
   - Dedicated ledger created in `data/processed/approved_building_heights.csv`.
2. **Building Placement (`building_placement`)**:
   - Status: `approved`.
   - Rationale: All 123 Overture footprints verified topologically valid, non-self-intersecting, non-overlapping ($>1\,\text{m}^2$), and suitable for 3D extrusion preprocessing.
3. **Solar Interval Alignment (`solar_interval_alignment`)**:
   - Status: `approved`.
   - Convention: NASA POWER hour label `2024041509` ($755.97\,\text{W/m}^2$ GHI, $728.31\,\text{W/m}^2$ DNI, $172.18\,\text{W/m}^2$ DHI) represents the 09:00–10:00 UTC (14:30–15:30 IST) hourly interval. It is explicitly adopted as time-averaged representative forcing paired with the instantaneous 09:00 UTC astronomical sun position (altitude $52.82^\circ$, True North azimuth $264.40^\circ$, UTM Grid North azimuth $263.81^\circ$).
4. **Material Assumptions (`material_assumptions`)**:
   - Status: `approved`.
   - Parameters: Accepted as modeling assumptions: walls ($\alpha = 0.30, \varepsilon = 0.90$), roofs ($\alpha = 0.20, \varepsilon = 0.90$), ground ($\alpha = 0.20, \varepsilon = 0.95$), pavement ($\alpha = 0.30, \varepsilon = 0.95$), shade panel ($\alpha = 0.60, \varepsilon = 0.90$). Initial surface temperature $35.0^\circ\text{C}$ (308.15 K). Simplified unmapped street-tree baseline accepted.
5. **Shade-Panel Intervention Geometry (`shade_panel_geometry`)**:
   - Status: `approved`.
   - Parameters: Single overhead panel (`BLR_SHADE_001` / `CANOPY_001`), $6.0\,\text{m} \times 3.0\,\text{m} \times 0.10\,\text{m}$, underside clearance $3.5\,\text{m}$, top height $3.6\,\text{m}$, bearing $103.028^\circ$ True North / $102.443^\circ$ Grid North, opaque, support columns omitted. Accepted as a hypothetical sensitivity scenario.
6. **Weather Redistribution Terms (`weather_redistribution_terms`)**:
   - Status: `approved`.
   - Terms: NOAA Bengaluru City station (`43295099999`) open observations ($35.0^\circ\text{C}$, $19.729\%\text{ RH}$, $1.5\,\text{m/s}$ wind at $90^\circ$) are archived locally for reproducible research. Permitted for local research workflow; mandatory framing applied: *"Bengaluru City station observations are applied as spatially uniform forcing at the Church Street study site."*

### 10.4 Complete Building Height Decision Ledger (37 Core Buildings)

| ID | Name / Description | Area ($\text{m}^2$) | Floors | Floor Est ($\text{m}$) | ML Est ($\text{m}$) | Pix Frac | Status | Uncertainty | Assigned Height ($\text{m}$) | Source Type & Rationale |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **B01** | Commercial block | 595.4 | — | — | 19.0 | 71.5% | `approved` | moderate | 19.0 | Google ML (coverage 71.5%) |
| **B02** | Commercial block | 933.2 | 3 | 9.6 | 18.5 | 49.4% | `uncertain` | high | 18.5 | Google ML ($\Delta = 8.9\text{m}$ vs 3 floors) |
| **B03** | Small structure | 57.4 | — | — | 2.5 | 7.4% | `uncertain` | high | 2.5 | Google ML (sparse coverage 7.4%) |
| **B04** | Spencer Building | 1719.8 | 5 | 16.0 | 18.0 | 93.4% | `approved` | moderate | 18.0 | Google ML (corroborates 5 floors) |
| **B05** | Commercial building | 128.7 | 3 | 9.6 | 7.5 | 62.3% | `approved` | moderate | 7.5 | Google ML (corroborates 3 floors) |
| **B06** | Commercial block | 1160.2 | — | — | 18.0 | 88.7% | `approved` | moderate | 18.0 | Google ML (coverage 88.7%) |
| **B07** | Commercial building | 292.3 | — | — | 11.0 | 58.1% | `approved` | moderate | 11.0 | Google ML (coverage 58.1%) |
| **B08** | Commercial building | 356.9 | — | — | 12.0 | 77.2% | `approved` | moderate | 12.0 | Google ML (coverage 77.2%) |
| **B09** | Low-rise commercial | 211.3 | — | — | 5.5 | 51.4% | `approved` | moderate | 5.5 | Google ML (coverage 51.4%) |
| **B10** | Barton Centre | 1433.4 | 14 | 44.8 | 52.5 | 86.2% | `approved` | moderate | 52.5 | Google ML (tallest building, 14 floors) |
| **B11** | Commercial building | 453.2 | — | — | 13.0 | 80.2% | `approved` | moderate | 13.0 | Google ML (coverage 80.2%) |
| **B12** | Asha Enclave | 261.7 | — | — | 13.5 | 82.8% | `approved` | moderate | 13.5 | Google ML (coverage 82.8%) |
| **B13** | Commercial building | 741.4 | — | — | 12.0 | 78.1% | `approved` | moderate | 12.0 | Google ML (coverage 78.1%) |
| **B14** | Commercial building | 244.6 | 7 | 22.4 | 21.0 | 80.7% | `approved` | moderate | 21.0 | Google ML (corroborates 7 floors) |
| **B15** | Brigade Gardens | 1344.8 | — | — | 13.5 | 86.1% | `approved` | moderate | 13.5 | Google ML (coverage 86.1%) |
| **B16** | Commercial building | 1547.8 | 3 | 9.6 | 10.5 | 83.9% | `approved` | moderate | 10.5 | Google ML (corroborates 3 floors) |
| **B17** | Commercial building | 365.1 | 3 | 9.6 | 16.0 | 21.0% | `uncertain` | high | 16.0 | Google ML (sparse 21% / conflict) |
| **B18** | Shrungar Shopping Ctr | 395.0 | 4 | 12.8 | 15.5 | 76.0% | `approved` | moderate | 15.5 | Google ML (corroborates 4 floors) |
| **B19** | Commercial building | 396.0 | 2 | 6.4 | — | 0.0% | `approved` | high | 6.4 | Floor-derived (ML missing) |
| **B20** | Commercial building | 152.7 | — | — | 7.0 | 75.4% | `approved` | moderate | 7.0 | Google ML (coverage 75.4%) |
| **B21** | Commercial building | 382.5 | — | — | 8.5 | 52.9% | `approved` | moderate | 8.5 | Google ML (coverage 52.9%) |
| **B22** | Raymonds | 507.1 | 3 | 9.6 | 12.0 | 86.9% | `approved` | moderate | 12.0 | Google ML (corroborates 3 floors) |
| **B23** | Commercial footprint | 45.8 | — | — | — | 0.0% | `uncertain` | extreme | 9.6 | Canyon median fallback (no data) |
| **B24** | Commercial building | 140.9 | 5 | 16.0 | 12.5 | 87.0% | `approved` | moderate | 12.5 | Google ML (corroborates 5 floors) |
| **B25** | Commercial building | 144.7 | — | — | 13.0 | 89.4% | `approved` | moderate | 13.0 | Google ML (coverage 89.4%) |
| **B26** | Commercial block | 381.0 | — | — | 20.0 | 93.5% | `approved` | moderate | 20.0 | Google ML (coverage 93.5%) |
| **B27** | Small commercial kiosk | 15.3 | — | — | 12.0 | 100.0% | `approved` | moderate | 12.0 | Google ML (small footprint, 15.3 m2) |
| **B28** | Commercial building | 115.1 | 2 | 6.4 | 10.0 | 94.8% | `approved` | moderate | 10.0 | Google ML (corroborates 2 floors) |
| **B29** | Commercial building | 146.4 | — | — | 19.0 | 73.5% | `approved` | moderate | 19.0 | Google ML (coverage 73.5%) |
| **B30** | Commercial building | 480.3 | — | — | 10.5 | 86.8% | `approved` | moderate | 10.5 | Google ML (coverage 86.8%) |
| **B31** | Commercial building | 287.0 | — | — | 4.5 | 31.2% | `uncertain` | high | 4.5 | Google ML (sparse coverage 31.2%) |
| **B32** | Commercial footprint | 130.6 | — | — | — | 0.0% | `uncertain` | extreme | 9.6 | Canyon median fallback (no data) |
| **B33** | Commercial building | 298.0 | 2 | 6.4 | 11.0 | 92.9% | `approved` | moderate | 11.0 | Google ML (corroborates 2 floors) |
| **B34** | Higginbotham's | 419.8 | 2 | 6.4 | 6.5 | 65.5% | `approved` | moderate | 6.5 | Google ML (corroborates 2 floors) |
| **B35** | Commercial building | 592.5 | 5 | 16.0 | 15.5 | 88.1% | `approved` | moderate | 15.5 | Google ML (corroborates 5 floors) |
| **B36** | Commercial building | 172.1 | 2 | 6.4 | — | 0.0% | `approved` | high | 6.4 | Floor-derived (ML missing) |
| **B37** | Commercial building | 330.6 | 5 | 16.0 | 8.0 | 85.1% | `uncertain` | high | 8.0 | Google ML ($\Delta = 8.0\text{m}$ vs 5 floors) |

### 10.5 Artifacts & Reproducibility Scripts
- **Review Generation Script**: `scripts/generate_church_street_review.py`
- **Sign-off Resolution Script**: `scripts/resolve_researcher_signoff.py`
- **Output Sign-off Record**: `data/processed/researcher_signoff.json` (mirrored in handoff)
- **Approved Height Decisions Ledger**: `data/processed/approved_building_heights.csv` (mirrored in handoff)
- **Regression Pass Status**: **173 tests passing** (100% pass rate).

---

