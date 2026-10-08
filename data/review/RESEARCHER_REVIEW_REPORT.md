# SOLARAEUS Researcher Review and Tree-Geometry Uncertainty-Bounds Report

**Project**: SOLARAEUS: High-Performance GPU Ray-Traced Urban Microclimate Simulation  
**Study Corridor**: Church Street, Bengaluru, Karnataka, India ($218.5\text{ m} \times 135.1\text{ m}$)  
**Local Coordinate Origin**: Easting $782,541.81\text{ m}$, Northing $1,435,736.11\text{ m}$ (EPSG:32643, UTM Zone 43N)  
**Stage**: Data-Review, Uncertainty-Bounding, and Sign-Off Preparation  
**Audit Date**: October 7, 2026  
**Operational Status**: `SIMULATION_INTEGRATION_BLOCKED` pending formal Researcher Sign-off  
**Success Token**: `RESEARCHER_REVIEW_AND_TREE_GEOMETRY_UNCERTAINTY_BOUNDS_COMPLETE`

---

## 1. Executive Summary

This report establishes the formal scientific review, uncertainty bounds, and sign-off preparation package for the terrain and vegetation assets of Project **SOLARAEUS**.

In strict adherence to scientific integrity and research protocol:
- **Physics Solvers & Optimization Codes Unmodified**: The CPU full reference solver, CPU incremental solver, GPU full solver, GPU incremental solver, and surrogate optimization routines remain completely untouched and unmodified.
- **Frozen Benchmark Directories Byte-Identical**: All 11 historical benchmark result directories (including the validated two-panel Pareto optimization run `church_street_multi_intervention_optimization_20261007_114326`) remain cryptographically verified.
- **Raw Supplements Unmodified**: All 202 raw supplement files across the BBMP tree census, raw source packages, and handoff v2 baseline remain identical against SHA-256 digests.
- **Interim Assets Protected**: All 26 interim assets generated in the prior data-preparation stage remain byte-identical.
- **Provisional Data Blocked From Physics Solver**: No tree geometry, canopy transmissivity, or coarse terrain elevations have been ingested into solver inputs or ray-tracing meshes.

---

## 2. Part 1 — Baseline Protection & Cryptographic Audit

A full cryptographic verification was performed prior to generating review products.
- **Raw Supplement Packages**:
  - `bengaluru_church_street_bbmp_trees_july2026_supplement`: 25 files audited, 0 mismatches.
  - `bengaluru_church_street_raw_sources_2026-10-07`: 88 files audited, 0 mismatches.
  - `bengaluru_church_street_manual_handoff_v2`: 89 files audited, 0 mismatches.
  - **Total Raw Files**: 202 files verified, **0 mismatches**.
- **Existing Interim Source Files**: 26 files verified, **0 mismatches**.
- **Frozen Result Directories**: 11 historical benchmark suites verified intact.
- **Git State**: Clean working tree for review stage with zero modifications to physics solver or optimization modules.

Audit Report: [tree_geometry_review_protection_report.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_geometry_review_protection_report.json).

---

## 3. Part 2 — Six Core Trees Review (T08 to T13)

The six core trees represent the municipal tree cohort located strictly within the primary Church Street study boundary ($X \in [0, 218.5]\text{ m}, Y \in [0, 135.1]\text{ m}$).

### Individual Tree Assessments

1. **Tree T08 (*Ficus Religiosa L.* - Sacred Fig / Peepal)**:
   - Census Identifiers: OBJECTID `554758`, KGISTreeID `GN8035CI5DUF001`.
   - Local Coordinates: $X = 20.07\text{ m}, Y = 81.14\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425142_2020-06-15_provider_processed.jpg` ($13.2\text{ m}$ distance); Wikimedia Commons `commons_72609328_original.jpg` (foreground subject).
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `HIGH`).
   - Visual Evidence: Massive broad spreading crown, distinct aerial roots, full trunk visibility. Scale reference provided by adjacent roadway width and bus/van clearance ($\approx 4.0\text{ m}$).
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN` (Historical photos from 2018/2020 do not prove 2026 survival).
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

2. **Tree T09 (*Syzygium Cumini (L.) Skeels* - Jamun / Java Plum)**:
   - Census Identifiers: OBJECTID `554765`, KGISTreeID `GN8035CI5EVO001`.
   - Local Coordinates: $X = 44.91\text{ m}, Y = 83.27\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425130_2020-06-15_provider_processed.jpg` (direct $5.6\text{ m}$ roadside passage); `kartaview_814425114` ($12.7\text{ m}$).
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `HIGH`).
   - Visual Evidence: Dense rounded crown overhanging the southern sidewalk. Trunk, tree pit, and sidewalk curb clearly resolved.
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN`.
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

3. **Tree T10 (*Syzygium Cumini (L.) Skeels* - Jamun / Java Plum)**:
   - Census Identifiers: OBJECTID `554768`, KGISTreeID `GN8035CI5DSH001`.
   - Local Coordinates: $X = 33.24\text{ m}, Y = 77.29\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425138_2020-06-15_provider_processed.jpg` ($14.5\text{ m}$ distance).
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `HIGH`).
   - Visual Evidence: Semi-mature tree standing between T08 and T09. Moderately dense canopy scaled against adjacent 2-story commercial facade.
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN`.
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

4. **Tree T11 (*Saraca Asoca (Roxb.) De Wilde* - Sita Ashok)**:
   - Census Identifiers: OBJECTID `554783`, KGISTreeID `GN8035CI6AKO001`.
   - Local Coordinates: $X = 60.95\text{ m}, Y = 75.36\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425114_2020-06-15_provider_processed.jpg` ($11.1\text{ m}$); `kartaview_814425110` ($11.6\text{ m}$); Mapillary `860157968229406`.
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `HIGH`).
   - Visual Evidence: Upright, compact ovoid crown planted in a sidewalk pit. Scaled relative to ground-floor retail shopfront entry ($\approx 3.0\text{ m}$).
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN`.
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

5. **Tree T12 (*Saraca Asoca (Roxb.) De Wilde* - Sita Ashok)**:
   - Census Identifiers: OBJECTID `554787`, KGISTreeID `GN8035CI6BKI001`.
   - Local Coordinates: $X = 78.32\text{ m}, Y = 74.65\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425338_2020-06-15_provider_processed.jpg` ($7.5\text{ m}$ direct capture); `kartaview_814425110` ($11.7\text{ m}$); Mapillary `860157968229406`.
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `HIGH`).
   - Visual Evidence: Slender companion Sita ashok tree. Compact upright crown clearly visible against storefront facade.
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN`.
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

6. **Tree T13 (*Techoma Stans* - Yellow Bells)**:
   - Census Identifiers: OBJECTID `554795`, KGISTreeID `GN8035CI6BEG001`.
   - Local Coordinates: $X = 97.09\text{ m}, Y = 65.54\text{ m}$.
   - Matched Imagery: KartaView `kartaview_814425266_2020-06-15_provider_processed.jpg` ($12.2\text{ m}$); `kartaview_814425090` ($16.2\text{ m}$).
   - Match Classification: `MATCH_CONFIRMED` (Confidence: `MEDIUM`).
   - Visual Evidence: Small flowering ornamental tree / large multi-stem shrub growing in a raised masonry roadside planter. Scaled relative to planter wall ($\approx 0.6\text{ m}$) and pedestrian eye level.
   - Current Existence: `CURRENT_EXISTENCE_UNCERTAIN`.
   - Reviewer Decision: `ACCEPT_WITH_WIDE_BOUNDS`.

Review CSV: [core_tree_review.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/core_tree_review.csv).

---

## 4. Part 3 & 4 — Geometric Uncertainty Bounds Envelope

To prevent false precision while enabling rigorous microclimate sensitivity testing, three distinct geometric states have been formulated for each core tree:
1. **Conservative-Small**: Lower bound of tree height and crown spread; maximum crown base clearance. Minimizes potential tree shading impact.
2. **Nominal**: Central photo-estimated best estimate derived by proportion scaling against known storefront floor slabs ($\approx 3.5\text{ m}$) and vehicular clearances.
3. **Conservative-Large**: Upper bound of tree height and crown spread; lower crown base clearance. Maximizes potential tree shading impact.

### Uncertainty Table

| Tree ID | Geometry State | Total Height (m) | Crown Diam (m) | Crown Base (m) | Crown Top (m) | DBH (m) | Crown Area ($\text{m}^2$) | Simulation Approved |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T08** | Conservative-Small | $11.0$ | $9.5$ | $3.8$ | $11.0$ | $0.70$ | $70.88$ | `false` |
| **T08** | **Nominal** | **$13.5$** | **$12.0$** | **$4.2$** | **$13.5$** | **$0.85$** | **$113.10$** | `false` |
| **T08** | Conservative-Large | $16.0$ | $15.0$ | $4.5$ | $16.0$ | $1.00$ | $176.71$ | `false` |
| **T09** | Conservative-Small | $9.0$ | $7.0$ | $3.2$ | $9.0$ | $0.45$ | $38.48$ | `false` |
| **T09** | **Nominal** | **$11.0$** | **$8.5$** | **$3.8$** | **$11.0$** | **$0.55$** | **$56.75$** | `false` |
| **T09** | Conservative-Large | $13.0$ | $10.5$ | $4.2$ | $13.0$ | $0.65$ | $86.59$ | `false` |
| **T10** | Conservative-Small | $7.5$ | $6.0$ | $2.8$ | $7.5$ | $0.35$ | $28.27$ | `false` |
| **T10** | **Nominal** | **$9.5$** | **$7.5$** | **$3.2$** | **$9.5$** | **$0.45$** | **$44.18$** | `false` |
| **T10** | Conservative-Large | $11.5$ | $9.0$ | $3.6$ | $11.5$ | $0.55$ | $63.62$ | `false` |
| **T11** | Conservative-Small | $6.5$ | $4.2$ | $2.4$ | $6.5$ | $0.24$ | $13.85$ | `false` |
| **T11** | **Nominal** | **$8.0$** | **$5.5$** | **$2.8$** | **$8.0$** | **$0.30$** | **$23.76$** | `false` |
| **T11** | Conservative-Large | $9.5$ | $6.8$ | $3.2$ | $9.5$ | $0.36$ | $36.32$ | `false` |
| **T12** | Conservative-Small | $6.0$ | $3.8$ | $2.2$ | $6.0$ | $0.22$ | $11.34$ | `false` |
| **T12** | **Nominal** | **$7.5$** | **$5.0$** | **$2.6$** | **$7.5$** | **$0.28$** | **$19.63$** | `false` |
| **T12** | Conservative-Large | $9.0$ | $6.2$ | $3.0$ | $9.0$ | $0.34$ | $30.19$ | `false` |
| **T13** | Conservative-Small | $3.8$ | $2.6$ | $1.4$ | $3.8$ | $0.14$ | $5.31$ | `false` |
| **T13** | **Nominal** | **$5.0$** | **$3.5$** | **$1.8$** | **$5.0$** | **$0.18$** | **$9.62$** | `false` |
| **T13** | Conservative-Large | $6.5$ | $4.5$ | $2.2$ | $6.5$ | $0.22$ | $15.90$ | `false` |

Files:
- [tree_dimension_uncertainty_bounds.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_dimension_uncertainty_bounds.csv)
- [tree_geometry_uncertainty.geojson](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_geometry_uncertainty.geojson)
- [tree_geometry_uncertainty_envelopes.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/plots/tree_geometry_uncertainty_envelopes.png)
- [core_trees_spatial_uncertainty_plan.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/plots/core_trees_spatial_uncertainty_plan.png)

---

## 5. Part 5 — Species and Canopy-Parameter Decoupling

Physical radiative parameters are strictly separated from geometric bounds to prevent unvalidated physical assumptions from leaking into the solver.

### Species Canopy Parameter Review Matrix

| Species Binomial | Taxon Confidence | Literature Baseline Source | Transmissivity Range ($\tau$) | LAI / LAD Status | Radiative Albedo / Emissivity | Parameter Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| *Ficus Religiosa L.* | HIGH | Konarska et al. (2014) / SOLWEIG dense broadleaf | $[0.05, 0.15]$ (nom: $0.10$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Syzygium Cumini Skeels*| HIGH | Vaz Monteiro et al. (2016) / tropical evergreen | $[0.08, 0.18]$ (nom: $0.12$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Saraca Asoca De Wilde* | HIGH | Tropical Urban Forestry Database (compact crown) | $[0.10, 0.20]$ (nom: $0.15$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Techoma Stans* | MEDIUM | Ornamental small tree / shrub (semi-open crown) | $[0.15, 0.30]$ (nom: $0.22$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Araucaria Columnaris* | HIGH | Conifer urban tree parameterization (narrow spire) | $[0.12, 0.25]$ (nom: $0.18$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Artocarpus Heterophyllus*| MEDIUM | Dense tropical evergreen fruit tree literature | $[0.06, 0.16]$ (nom: $0.10$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Michelia Longifolia* | MEDIUM | Magnoliaceae urban foliage literature | $[0.10, 0.22]$ (nom: $0.15$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Tabebuia Rosea* | HIGH | Bignoniaceae tropical flowering tree literature | $[0.10, 0.25]$ (nom: $0.18$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Markhamia Lutea* | MEDIUM | Bignoniaceae urban tree literature | $[0.12, 0.24]$ (nom: $0.17$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Ficus Racemosa L.* | MEDIUM | Ficus microclimate literature | $[0.08, 0.18]$ (nom: $0.12$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |
| *Pongamia Pinnata* | HIGH | Indian roadside tree literature; Leguminosae | $[0.12, 0.25]$ (nom: $0.18$) | LITERATURE_ASSUMED | LITERATURE_ASSUMED | CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED |

Review CSV: [species_canopy_parameter_review.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/species_canopy_parameter_review.csv).

---

## 6. Part 6 — Context-Tree Review (Buffer Region)

The eight context trees were audited independently from the core cohort:
- **T06 & T07 (*Araucaria columnaris*, Local X = -3.28m, -9.26m)**:
  - Inside 75m shadow-context boundary.
  - Distinctive tall Cook pine conifer silhouettes confirmed in KartaView photos `814425166` and `814425170`.
  - Cast narrow evening shadows into the western entrance of Church Street.
  - Classified as `OPTIONAL_CONTEXT_GEOMETRY`.
- **T05 (*Ficus racemosa*, Local X = -6.32m)**:
  - Partially visible behind commercial signage; dimensions unmeasured. Classified as `LOCATION_ONLY`.
- **T03 & T04 (Local Y = 140–150m)**:
  - Northern setback trees near Brigade Road corner. Distant upper crown texture visible in Barton Centre aerial obliques; road-level ground base obscured. Classified as `LOCATION_ONLY`.
- **T01 & T02 (Local Y = 170–190m)**:
  - Northern parcel alley trees obscured by commercial building masses. Classified as `INSUFFICIENT_DATA`.
- **T14 (*Pongamia pinnata*, Local X = 142.94m, Y = 141.82m)**:
  - Located >70m north of Church Street corridor behind properties along Rest House Crescent. Too distant to cast direct solar shadows onto pedestrian analysis area. Classified as `EXCLUDE_PENDING_REVIEW`.

Review CSV: [context_tree_review.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/context_tree_review.csv).

---

## 7. Part 7 — Regional FABDEM Terrain Evaluation

### Key Findings
1. **Bare-Earth Extraction Confirmed**: FABDEM v1.2 successfully stripped urban building radar reflections, lowering the mean elevation by **$7.10\text{ m}$** relative to the uncorrected Skadi DEM and eliminating positive rooftop spikes up to **$+16.60\text{ m}$**.
2. **Topographic Baseline**: FABDEM establishes a smooth, continuous regional slope across Church Street descending from West ($917.40\text{ m}$) to East ($910.12\text{ m}$).
3. **Classification & Constraints**:
   - `FABDEM: REGIONAL_REFERENCE_ONLY`
   - `Street-scale terrain: MISSING`
   - `Tree ground elevation status: FABDEM_REFERENCE_ONLY`
   - FABDEM's $\approx 30.87\text{ m}$ resolution is over double the width of the entire street; it cannot resolve $150\text{ mm}$ curb steps or $1:50$ transverse drainage cambers. It is strictly forbidden from being ingested as a microscale street DTM.

Decision File: [terrain_review_decision.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/terrain_review_decision.json).

---

## 8. Part 8 — Comprehensive 14-Tree Decision Matrix

Every field across all 14 census trees is categorized into exactly one auditable status:

| Tree ID | Location | Species | Existence | Height | Crown Diam | Crown Base | Transmissivity | LAI / LAD | Ground Z | Simulation Approval |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T01** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T02** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T03** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T04** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T05** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T06** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T07** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T08** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T09** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T10** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T11** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T12** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T13** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | PHOTO_ESTIMATED | PHOTO_ESTIMATED | PHOTO_ESTIMATED | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |
| **T14** | VERIFIED | PROVISIONAL | REQUIRES_FIELD_CHECK | MISSING | MISSING | MISSING | LITERATURE_ASSUMED | LITERATURE_ASSUMED | PROVISIONAL | REQUIRES_FIELD_CHECK |

---

## 9. Part 9 — Researcher Sign-Off Package

The complete manual sign-off package has been prepared for research leads:
1. Review Document: [tree_geometry_researcher_review.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_geometry_researcher_review.md)
2. Machine-Readable Review: [tree_geometry_researcher_review.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_geometry_researcher_review.json)
3. Formal Sign-Off Form: [tree_geometry_signoff_form.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_geometry_signoff_form.md)

All decision checkboxes on `tree_geometry_signoff_form.md` remain **unchecked (`[ ]`)** to ensure deliberate human authorization.

---

## 10. Part 10 — Promotion Policy & Candidate Manifest

No file has been promoted to `data/processed/`. Four candidate files have been logged in [promotion_candidates.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/promotion_candidates.json) with `approved_for_promotion: false`:
1. `tree_inventory_interim.geojson` $\rightarrow$ 2D point locations only.
2. `photo_tree_match_log.csv` $\rightarrow$ Empirical metadata catalog.
3. `fabdem_clipped_utm43.tif` $\rightarrow$ Regional macro-topography boundary baseline.
4. `tree_dimension_uncertainty_bounds.csv` $\rightarrow$ Level 1 provisional sensitivity envelope.

---

## 11. Part 11 — Test Suite & Quality Control Audit

A dedicated test suite [tests/test_tree_geometry_review.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_tree_geometry_review.py) was implemented covering the 15 required checks:
- All 6 core-tree IDs exist and are valid.
- All 14 census-tree IDs are unique without duplicate coordinates.
- Geodetic UTM transformations are accurate to $<1\text{ mm}$.
- Coordinates lie strictly within study domain and shadow-context buffer.
- 0 raw files altered; all 11 frozen benchmark directories byte-identical.
- Zero fake zeros in missing dimension fields.
- 100% of dimension bounds include explicit confidence labels and scaling evidence references.
- Historical imagery strictly decoupled from current 2026 survival claims.
- 0 records approved for simulation (`approved_for_simulation: false` across all records).
- Geometric bounds are strictly monotonic ($\text{Small} < \text{Nominal} < \text{Large}$).

**Test Suite Result: 15 Passed / 0 Failed in 0.12s.**

---

## 12. Final Readiness Decision Matrix

| Item | Classification Token | Status Rationale |
| :--- | :--- | :--- |
| **Tree Locations** | `TREE_LOCATIONS_VERIFIED` | 14 municipal census coordinates georeferenced and transformed. |
| **Tree Species** | `TREE_SPECIES_REPORTED` | Reported in municipal census; botanical voucher validation pending. |
| **Current Existence** | `TREE_CURRENT_EXISTENCE_UNCERTAIN` | 2018–2020 imagery does not prove 2026 ground-truth survival. |
| **Tree Dimensions** | `TREE_DIMENSIONS_PROVISIONAL` | Photo-estimated bounds; optical/laser survey required. |
| **Geometry Bounds** | `TREE_GEOMETRY_BOUNDS_AVAILABLE` | Conservative-Small, Nominal, and Conservative-Large states established. |
| **Canopy Level 1** | `CANOPY_LEVEL_1_NOT_YET_APPROVED` | Geometry ready for review, but simulation integration blocked. |
| **Canopy Level 2** | `CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED` | Radiative physics parameters decoupled as literature assumptions. |
| **Terrain (FABDEM)** | `FABDEM_REGIONAL_REFERENCE_ONLY` | Clean bare-earth macro-gradient; unsuitable for microscale DTM. |
| **Microscale DTM** | `MICROSCALE_DTM_MISSING` | Sub-metre curb, gutter, and sidewalk cross-slope data absent. |
| **Researcher Sign-Off**| `RESEARCHER_SIGNOFF_REQUIRED` | Awaiting explicit human completion of sign-off form. |
| **Simulation Pipeline**| `SIMULATION_INTEGRATION_BLOCKED` | Solvers locked against unapproved vegetation/terrain geometry. |

---

RESEARCHER_REVIEW_AND_TREE_GEOMETRY_UNCERTAINTY_BOUNDS_COMPLETE
