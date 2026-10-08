# SOLARAEUS Interim Terrain and Vegetation Reconstruction Stage Report

**Study Site**: Bengaluru, Church Street Corridor (Karnataka, India)  
**Corridor Core Domain**: $218.5\text{ m} \times 135.1\text{ m}$ (EPSG:32643, UTM Zone 43N)  
**Documented Local Origin**: Easting $782,541.81\text{ m}$, Northing $1,435,736.11\text{ m}$  
**Audit Mode**: READ-ONLY Data Preparation and Independent Validation  
**Date of Audit**: October 7, 2026  
**Success Token**: `INTERIM_TERRAIN_AND_TREE_RECONSTRUCTION_COMPLETE`

---

## 1. Executive Summary

This report documents the completion of the interim terrain and vegetation reconstruction stage for Project **SOLARAEUS**. In strict accordance with scientific integrity guidelines:
- **Zero Physics Solvers or Optimization Code Were Modified**: The CPU full reference solver, CPU incremental solver, GPU full solver, GPU incremental solver, and surrogate optimization routines remain completely untouched and unmodified.
- **Zero Frozen Benchmarks Were Modified**: All 11 historical benchmark result directories (including `church_street_multi_intervention_optimization_20261007_114326`) remain cryptographically identical.
- **Zero Raw Supplement Files Were Modified**: All 197 raw files across the two delivered supplement packages and the handoff v2 baseline were cryptographically validated against SHA-256 digests.
- **Zero Unverified Geometry Ingested into Solver**: No synthetic curb heights, fake upsampled micro-DTMs, or uncalibrated tree canopies were created or ingested into the physics simulation pipeline.

All derived interim products have been placed strictly in `data/interim/` to provide an auditable, transparent baseline for subsequent researcher review.

---

## 2. Part 1 — Raw Data Protection & Cryptographic Verification

A complete cryptographic checksum audit was executed prior to and following all data preparation steps. 

### Audit Manifest Summary
- **BBMP Tree Census Supplement (`bengaluru_church_street_bbmp_trees_july2026_supplement`)**:
  - Total files audited: **25**
  - Mismatches / modifications: **0** (100% byte-identical)
- **Raw Sources Supplement (`bengaluru_church_street_raw_sources_2026-10-07`)**:
  - Total files audited: **83**
  - Mismatches / modifications: **0** (100% byte-identical)
- **Baseline Handoff Package (`bengaluru_church_street_manual_handoff_v2`)**:
  - Total files audited: **89**
  - Mismatches / modifications: **0** (100% byte-identical)
- **Frozen Result Directories**:
  - 11 verified directories: All result logs, certificate records, Pareto CSVs, and mesh definitions remain bitwise identical.

The complete audit record and file manifest is stored outside raw packages at:  
[raw_data_protection_report.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/raw_data_protection_report.json).

---

## 3. Part 2 — FABDEM Terrain Audit

### Technical Specification of FABDEM v1.2
- **Source File**: `N12E077_FABDEM_V1-2.tif` (Tile N12E077)
- **Product Type**: Forest and Buildings Removed Copernicus DEM (Machine Learning Bare-Earth DTM)
- **Raster Dimensions**: $3600 \times 3600$ pixels (1-degree tile)
- **Band Count**: 1
- **Data Type**: `Float32` (Cloud-Optimized GeoTIFF)
- **Coordinate Reference System**: EPSG:4326 (WGS 84 geographic 2D)
- **Resolution**: $0.000277777778^\circ$ per pixel ($\approx 30.87\text{ m}$ at Bengaluru latitude)
- **NoData Value**: `-9999.0`
- **Vertical Reference**: Orthometric height above the **EGM2008** geoid (metres)
- **Source DOI**: `10.5518/1109` (Hawker et al., University of Bristol)
- **License**: CC BY-NC-SA 4.0
- **SHA-256 Checksum**: `eb209c1fa6e3f36a54d5d95e0cba001851deae70e008ba8e340e42d78df13b2e`

### Statistical Characteristics
- **Full Tile Extent ($12^\circ\text{–}13^\circ\text{N}, 77^\circ\text{–}78^\circ\text{E}$)**:
  - Valid Pixels: 12,960,000 (100% valid)
  - Minimum: $-15.11\text{ m}$ | Maximum: $1512.43\text{ m}$ | Mean: $715.31\text{ m}$ | Std Dev: $163.78\text{ m}$
- **Church Street Site Domain ($77.6035^\circ\text{–}77.6075^\circ\text{E}, 12.9735^\circ\text{–}12.9765^\circ\text{N}$)**:
  - Valid Pixels: 165
  - Minimum: **$910.12\text{ m}$** | Maximum: **$917.40\text{ m}$** | Mean: **$913.25\text{ m}$** | Std Dev: **$1.38\text{ m}$**

### Audit Classification & Suitability
- **Classification**: `FABDEM_AVAILABLE_FOR_REGIONAL_PREPROCESSING`
- **Why FABDEM is NOT a Street-Scale DTM**:
  1. **Spatial Resolution**: At $\approx 30\text{ m}$ ground sample distance (GSD), a single pixel spans more than twice the entire width of Church Street ($\approx 12\text{–}14\text{ m}$).
  2. **Micro-Topography Omission**: It cannot resolve curbs ($150\text{ mm}$ vertical step), pedestrian tactile paving, cross-slopes ($1:50$ drainage camber), road gutters, or building entrance thresholds.
  3. **Algorithm Nature**: FABDEM was trained using random forests on GEDI/ICESat-2 spaceborne LiDAR profiles to strip forest and building heights at regional scales. It provides an excellent regional baseline, but is not a terrestrial LiDAR or engineering-grade micro-topography model.

Full audit records:  
[fabdem_audit.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_audit.json)  
[fabdem_alignment_report.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_alignment_report.md)

---

## 4. Part 3 — FABDEM Clipping and Coordinate Reprojection

FABDEM was clipped to the Church Street site domain plus an outer $50\text{ m}$ buffer to encompass the full shadow-casting context:
- **Geographic Bounding Box**: $77.603348^\circ\text{–}77.607386^\circ\text{E}$, $12.973797^\circ\text{–}12.976214^\circ\text{N}$
- **Projected Bounds (EPSG:32643)**: Easting $782,491.81\text{ m}$ to $782,811.81\text{ m}$, Northing $1,435,686.11\text{ m}$ to $1,435,936.11\text{ m}$
- **Local Bounds**: $X \in [-50.0, 270.0]\text{ m}$, $Y \in [-50.0, 200.0]\text{ m}$

### Strict Preservation of Native Values
- No bilinear or bicubic upsampling was applied to fake sub-metre resolution.
- Both native CRS (`EPSG:4326`, $15 \times 9$ pixels) and projected UTM Zone 43N (`EPSG:32643`, $11 \times 9$ pixels at $30\text{ m}$ resolution) GeoTIFFs were generated with nearest-neighbour interpolation to preserve raw float values.
- A local reference raster aligned to the origin $(782541.81, 1435736.11)$ was generated without altering vertical heights.

Generated terrain assets:
- [fabdem_clipped_native.tif](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_clipped_native.tif)
- [fabdem_clipped_utm43.tif](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_clipped_utm43.tif)
- [fabdem_local_reference.tif](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_local_reference.tif)
- [fabdem_clip_metadata.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_clip_metadata.json)
- [fabdem_coordinate_alignment.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_coordinate_alignment.json)

---

## 5. Part 4 — FABDEM Comparison with Existing Skadi Terrain

An empirical, point-by-point comparison across 165 co-registered sample points within the Church Street study corridor yielded the following metrics:

| Metric | Existing Skadi DEM | New FABDEM v1.2 | Differential ($\Delta = \text{Skadi} - \text{FABDEM}$) |
| :--- | :---: | :---: | :---: |
| **Product Type** | Radar Surface Model (DSM) | ML Bare-Earth Model (DTM) | Building/Tree Bias Removal |
| **Stated Vertical Datum** | EGM96 Geoid | EGM2008 Geoid | $\approx 0.15\text{–}0.25\text{ m}$ geoid undulation |
| **Site Minimum** | $905.0\text{ m}$ | $910.12\text{ m}$ | $-5.12\text{ m}$ |
| **Site Maximum** | $934.0\text{ m}$ | $917.40\text{ m}$ | **$+16.60\text{ m}$ (Rooftop Spike)** |
| **Site Mean** | $920.35\text{ m}$ | $913.25\text{ m}$ | **$+7.10\text{ m}$ (Average Contamination)** |
| **Site Median** | $921.00\text{ m}$ | $913.38\text{ m}$ | **$+7.24\text{ m}$** |
| **Site Standard Deviation** | **$5.61\text{ m}$** | **$1.38\text{ m}$** | **$4.52\text{ m}$** |

### Physical Attribution of Differences
1. **Radar Rooftop Contamination in Skadi**: The Skadi DEM derives from SRTM C-band radar interferometry, which reflects off building rooftops and tree crowns. Commercial buildings on Church Street (4 to 7 stories, $12\text{–}22\text{ m}$ tall) caused positive radar spikes up to $+16.6\text{ m}$ above the true street ground.
2. **Variance Reduction in FABDEM**: FABDEM stripped building heights, dropping the site standard deviation from $5.61\text{ m}$ to $1.38\text{ m}$. The true Church Street terrain surface is a smooth, continuous gradient sloping down from Brigade Road ($917.4\text{ m}$) to Museum Road ($910.1\text{ m}$).
3. **Vertical Datum Shift**: Geoid undulation difference between EGM96 and EGM2008 in Bengaluru accounts for $\approx 0.2\text{ m}$.
4. **Cautionary Language**: FABDEM represents a *provisional regional elevation baseline* that *requires local vertical validation* and remains *insufficient for curb, gutter, and sidewalk geometry*.

Full comparison files:  
[fabdem_vs_skadi_comparison.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_vs_skadi_comparison.json)  
[fabdem_vs_skadi_comparison.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/fabdem_vs_skadi_comparison.md)

---

## 6. Part 5 — Tree Inventory Audit

The BBMP municipal tree census (July 2026 dataset) identifies **14 trees** in the Church Street scene: **6 core trees** within the primary study boundary, and **8 context trees** in the surrounding shadow-context buffer.

### Six Core Church Street Trees (Preserved IDs T08 to T13)

| Review ID | Census OBJECTID | KGISTreeID | Reported Species | Common Name | Local X (m) | Local Y (m) | Classification |
| :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| **T08** | 554758 | GN8035CI5DUF001 | *Ficus Religiosa L.* | Sacred Fig (Peepal) | $20.07$ | $81.14$ | CORE_STUDY_AREA |
| **T09** | 554765 | GN8035CI5EVO001 | *Syzygium Cumini (L.) Skeels* | Jamun (Java Plum) | $44.91$ | $83.27$ | CORE_STUDY_AREA |
| **T10** | 554768 | GN8035CI5DSH001 | *Syzygium Cumini (L.) Skeels* | Jamun (Java Plum) | $33.24$ | $77.29$ | CORE_STUDY_AREA |
| **T11** | 554783 | GN8035CI6AKO001 | *Saraca Asoca (Roxb.) De Wilde* | Sita Ashok | $60.95$ | $75.36$ | CORE_STUDY_AREA |
| **T12** | 554787 | GN8035CI6BKI001 | *Saraca Asoca (Roxb.) De Wilde* | Sita Ashok | $78.32$ | $74.65$ | CORE_STUDY_AREA |
| **T13** | 554795 | GN8035CI6BEG001 | *Techoma Stans* | Yellow Bells | $97.09$ | $65.54$ | CORE_STUDY_AREA |

### Eight Context Trees (Buffer Region)

| Review ID | Census OBJECTID | KGISTreeID | Reported Species | Local X (m) | Local Y (m) | Relative Location |
| :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **T01** | 554674 | GN8035CJ5FGG001 | *Artocarpus Heterophyllus Lam.* | $-34.72$ | $190.16$ | North parcel interior |
| **T02** | 554688 | GN8035CJ5BFF001 | *Michelia Longifolia Blume* | $-20.01$ | $169.95$ | North alley setback |
| **T03** | 554700 | GN8035CI5UGG001 | *Tabebuia Rosea (Bertol) Dc.* | $-34.60$ | $150.11$ | North setback near corner |
| **T04** | 554708 | GN8035CI5QWC001 | *Markhamia Lutea (Benth.)* | $-10.82$ | $140.23$ | North property line |
| **T05** | 554729 | GN8035CI5BXD001 | *Ficus Racemosa L.* | $-6.32$ | $80.78$ | West corridor approach |
| **T06** | 554737 | GN8035CI5BTO001 | *Araucaria Columnaris* | $-3.28$ | $79.03$ | West building entrance |
| **T07** | 554748 | GN8035CI5GDI001 | *Araucaria Columnaris* | $-9.26$ | $86.32$ | West companion conifer |
| **T14** | 554866 | GN8035CI6TVE001 | *Pongamia Pinnata (L.) Pierre* | $142.94$ | $141.82$ | North commercial rear |

### Spatial Distribution Insight
All 6 core trees are concentrated exclusively along the **southern pedestrian sidewalk** in the western half of the Church Street corridor ($X \in [20.07, 97.09]\text{ m}, Y \in [65.54, 83.27]\text{ m}$). The eastern segment ($X \in [105, 218.5]\text{ m}$) contains no census trees.
Crucially, the two-panel intervention optimizer previously placed shade panels (`CAND_4196_SURR`) at $X \in [124.0, 152.0]\text{ m}$—precisely within this unshaded canopy gap.

Generated inventory files:  
[tree_inventory_interim.geojson](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/tree_inventory_interim.geojson)  
[tree_inventory_interim.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/tree_inventory_interim.csv)

---

## 7. Part 6 — Photo-to-Tree Matching

### Imagery Corpus
- **KartaView 2020**: 29 sequential dashcam photographs captured on June 15, 2020 along Church Street ($4032 \times 3024$ px).
- **Wikimedia Commons**: 8 high-resolution photographs (2018–2024), including street-level pedestrian views and Barton Centre 22nd-floor aerial obliques.
- **Mapillary**: Crowdsourced 360-degree street capture sequence (October 2021).

### Trajectory and View Geometry
The KartaView sequence (`2394274`, indices 1363 to 1391) represents a westward drive from $X = 284.1\text{ m}$ to $X = -74.0\text{ m}$. With a front-facing camera looking forward along the vehicle heading ($282^\circ\text{–}285^\circ$ azimuth), all trees along the southern sidewalk ($Y \approx 75\text{–}83\text{ m}$) appear on the **driver's left-hand side** ahead of and beside the car.

### Match Results

| Tree ID | Closest Photo | Distance | Match Status | Confidence | Empirical Notes |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **T08** | `kartaview_814425142`<br>`commons_72609328` | $13.2\text{ m}$ | `MATCH_CONFIRMED` | HIGH | Massive spreading Ficus crown over pedestrian walkway; vehicle clearance scale observed. |
| **T09** | `kartaview_814425130` | $5.6\text{ m}$ | `MATCH_CONFIRMED` | HIGH | Direct $5.6\text{ m}$ roadside capture; trunk and dense rounded crown clearly resolved. |
| **T10** | `kartaview_814425138` | $14.5\text{ m}$ | `MATCH_CONFIRMED` | HIGH | Clear roadside perspective between T08 and T09; medium crown spread. |
| **T11** | `kartaview_814425114` | $11.1\text{ m}$ | `MATCH_CONFIRMED` | HIGH | Compact ovoid crown; tree grate and sidewalk curb clearly visible. |
| **T12** | `kartaview_814425338` | $7.5\text{ m}$ | `MATCH_CONFIRMED` | HIGH | Compact crown companion to T11; storefront heights provide scale reference. |
| **T13** | `kartaview_814425266` | $12.2\text{ m}$ | `MATCH_CONFIRMED` | MEDIUM | Small rounded tree/large shrub planted in raised roadside planter. |
| **T06/T07** | `kartaview_814425166` | $14.2\text{–}19.4\text{ m}$ | `MATCH_PROBABLE` | MEDIUM | Distinctive tall columnar Cook Pine conifer spires at western entrance. |
| **T05** | `kartaview_814425166` | $19.0\text{ m}$ | `MATCH_PROBABLE` | LOW | Western approach setback tree partially visible behind commercial signposts. |
| **T03/T04** | `commons_154346578` | $>60\text{ m}$ | `MATCH_POSSIBLE` | LOW | Distant canopy top texture visible in Barton Centre aerial obliques. |
| **T01/T02/T14**| None | $>90\text{ m}$ | `INSUFFICIENT_VIEW` | NONE | Obscured by multi-story commercial buildings in alleyways/rear parcels. |

### Integrity Safeguards
- **Existence Uncertainty**: Under project rules, historical photographs (2018–2020) **do NOT prove current 2026 existence**. All 14 trees retain `current_existence_status: CURRENT_EXISTENCE_UNCERTAIN`.
- **Camera Calibration**: None of the cameras possess geometric calibration. Dimensions derived from photos are strictly provisional relative estimates.

Full match log and report:  
[photo_tree_match_log.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/photo_tree_match_log.csv)  
[photo_tree_match_report.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/photo_tree_match_report.md)

---

## 8. Parts 7 & 8 — Interim Tree Dimensions & Parameter Separation

### Working Measurement Review Table
- **Strict Blank Field Rule**: Unknown measurements are left blank. No unknown value is set to zero.
- **Classification Status**: Core trees are marked `PHOTO_ESTIMATED`; unmeasured context trees are marked `MISSING`.

| Tree ID | Species | Height (m) | Crown Diam (m) | Crown Base (m) | DBH (m) | Measurement Status | Confidence |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T01** | *Artocarpus Heterophyllus* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | NONE |
| **T02** | *Michelia Longifolia* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | NONE |
| **T03** | *Tabebuia Rosea* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | LOW |
| **T04** | *Markhamia Lutea* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | LOW |
| **T05** | *Ficus Racemosa* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | LOW |
| **T06** | *Araucaria Columnaris* | $14.5$ | $3.8$ | $2.2$ | $0.35$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T07** | *Araucaria Columnaris* | $13.0$ | $3.5$ | $2.0$ | $0.32$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T08** | *Ficus Religiosa* | $13.5$ | $12.0$ | $4.2$ | $0.85$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T09** | *Syzygium Cumini* | $11.0$ | $8.5$ | $3.8$ | $0.55$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T10** | *Syzygium Cumini* | $9.5$ | $7.5$ | $3.2$ | $0.45$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T11** | *Saraca Asoca* | $8.0$ | $5.5$ | $2.8$ | $0.30$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T12** | *Saraca Asoca* | $7.5$ | $5.0$ | $2.6$ | $0.28$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T13** | *Techoma Stans* | $5.0$ | $3.5$ | $1.8$ | $0.18$ | `PHOTO_ESTIMATED` | MEDIUM |
| **T14** | *Pongamia Pinnata* | *[blank]* | *[blank]* | *[blank]* | *[blank]* | `MISSING` | NONE |

### Parameter Separation Matrix (Part 8)
1. **Category A (Observed or Census-Reported)**: Species name, coordinates (WGS84, UTM43N, Local X/Y), tree identity, municipal ward. Status: `VERIFIED_MUNICIPAL_RECORD_COORDINATES` ($100\%$ complete).
2. **Category B (Photo-Estimated)**: Approximate height, crown diameter, crown base height, DBH. Status: `PHOTO_ESTIMATED_PROVISIONAL_NON_CALIBRATED` (6/6 core, 2/8 context; 6/8 context MISSING).
3. **Category C (Literature-Assumed)**: Transmissivity ($\tau$), leaf albedo ($\alpha$), emissivity ($\varepsilon$), Leaf Area Index (LAI), Leaf Area Density (LAD), seasonal foliage factor. Status: `LITERATURE_ASSUMED_PENDING_RESEARCHER_SELECTION`. **Not assigned in this interim stage.**
4. **Category D (Missing)**: Field-measured tree heights, calibrated crown geometry, pyranometer transmissivity, hemispherical LAI, verified 2026 survival. Status: `MISSING_FIELD_VALIDATION_REQUIRED`.

Full measurement and parameter files:  
[tree_measurement_review_working.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/tree_measurement_review_working.csv)  
[canopy_parameter_status.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/canopy_parameter_status.json)

---

## 9. Part 9 — Terrain/Tree Vertical Alignment

For each of the 14 trees, the FABDEM bare-earth elevation was sampled at the tree coordinates:
- All 14 trees lie strictly inside the valid raster coverage.
- Nearest-neighbour elevation ranges from **$912.42\text{ m}$ to $915.22\text{ m}$** (EGM2008) for core trees, with bilinear diagnostics within $\pm 0.12\text{ m}$.
- In accordance with Part 9 rules: **FABDEM elevation was NOT merged into tree geometry as authoritative ground_z.**
- Ground Z status is explicitly set to: `FABDEM_REFERENCE_ONLY`.

Full alignment file:  
[tree_fabdem_alignment.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/tree_fabdem_alignment.csv)

---

## 10. Part 10 — Quality Control Summary

The automated Quality Control suite evaluated 16 integrity checks across all interim assets:
- **Duplicate tree IDs**: 0 duplicates (**PASSED**)
- **Duplicate coordinates**: 0 duplicates (**PASSED**)
- **Invalid geometries**: 0 invalid (**PASSED**)
- **Core study boundary compliance**: 6/6 core trees within $[0, 218.5]\text{ m} \times [0, 135.1]\text{ m}$ (**PASSED**)
- **Shadow-context extent compliance**: 14/14 trees within $[-50, 270]\text{ m} \times [-50, 200]\text{ m}$ (**PASSED**)
- **Coordinate axis ordering**: Verified Easting/Northing order (**PASSED**)
- **UTM transformation accuracy**: $< 1\text{ mm}$ discrepancy (**PASSED**)
- **Local origin consistency**: Preserved exact origin $(782541.81, 1435736.11)$ (**PASSED**)
- **Species completeness**: 14/14 complete (**PASSED**)
- **Core image cross-links**: 6/6 linked (**PASSED**)
- **Image match validity**: 0 invalid confirmed matches (**PASSED**)
- **Current existence integrity**: 14/14 flagged `CURRENT_EXISTENCE_UNCERTAIN` (**PASSED**)
- **Source record conflicts**: 0 conflicts (**PASSED**)
- **CRS uniformity**: Uniform EPSG:4326 and EPSG:32643 (**PASSED**)
- **Physical bounds on dimensions**: All estimates physically plausible (**PASSED**)
- **Raw file immutability**: 0 mismatches across 197 files (**PASSED**)

**Total Checks Passed: 16 / 16 (100%)**

Full QC reports:  
[quality_control_report.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/quality_control_report.json)  
[quality_control_report.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/quality_control_report.md)

---

## 11. Part 11 — Review Package & Visualizations

Six high-resolution review figures were generated strictly from derived interim data and saved under interim plots directories:

1. **Six Core Church Street Trees Map**: Sidewalk locations, photo-estimated canopy extents, and study boundary:  
   [core_trees_map.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/plots/core_trees_map.png)
2. **Fourteen-Tree Context Inventory Map**: Complete spatial distribution of core vs context trees within the shadow-context buffer:  
   [context_trees_inventory_map.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/plots/context_trees_inventory_map.png)
3. **KartaView Trajectory & Proximity Alignment**: Camera waypoints, westward driving route, and proximity sightlines:  
   [photo_tree_matching_trajectory.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/plots/photo_tree_matching_trajectory.png)
4. **Tree Dimensions Comparison Profile**: Vertical height spans, crown clearances, and horizontal spread:  
   [tree_dimensions_comparison.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/vegetation/plots/tree_dimensions_comparison.png)
5. **FABDEM Elevation Reference Surface**: Macro-scale topographic gradient across Church Street:  
   [fabdem_elevation_surface.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/plots/fabdem_elevation_surface.png)
6. **Skadi vs FABDEM Cross-Section Profile**: Longitudinal elevation profile demonstrating removal of building radar spikes:  
   [fabdem_vs_skadi_elevation_profile.png](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/interim/terrain/plots/fabdem_vs_skadi_elevation_profile.png)

---

## 12. Part 12 — Final Readiness Decision Matrix

Every audited item is classified into exactly one required readiness state:

| # | Audited Domain / Asset | Assigned Classification | Scientific Justification |
| :---: | :--- | :---: | :--- |
| 1 | **FABDEM Regional Terrain Reference** | `READY_FOR_INTERIM_RECONSTRUCTION` | Bare-earth ML DTM verified; unpolluted macro-gradient baseline across study domain. |
| 2 | **Street-Scale Terrain DTM** | `MISSING` | $\approx 30\text{ m}$ FABDEM does not resolve curbs ($150\text{ mm}$), road crowns, or thresholds; engineering DTM is absent. |
| 3 | **Six Core Tree Locations** | `READY_FOR_INTERIM_RECONSTRUCTION` | Coordinates verified in municipal census, cross-referenced to street photos, within study boundary. |
| 4 | **Fourteen-Tree Context Inventory** | `READY_FOR_INTERIM_RECONSTRUCTION` | Complete municipal census cohort audited and mapped within shadow-context extent. |
| 5 | **Tree Species** | `PRESENT_BUT_UNVERIFIED` | Reported in BBMP census, but lacks independent on-site botanical herbarium validation. |
| 6 | **Tree Heights** | `PHOTO_ESTIMATED_ONLY` | Estimated from uncalibrated consumer dashcam photographs; no laser clinometer measurement exists. |
| 7 | **Crown Diameters** | `PHOTO_ESTIMATED_ONLY` | Estimated from uncalibrated street photographs; no crown spread tape survey exists. |
| 8 | **Crown Base Heights** | `PHOTO_ESTIMATED_ONLY` | Visual clearance estimation above vehicular traffic; no vertical ground survey exists. |
| 9 | **Current Tree Existence** | `PRESENT_BUT_UNVERIFIED` | Photographs date from 2018–2020; current 2026 survival on Church Street requires field check. |
| 10 | **LAI / LAD** | `MISSING` | No hemispherical canopy photography or plant canopy analyzer data exists. |
| 11 | **Canopy Transmissivity** | `MISSING` | No sub-canopy pyranometer radiation measurements exist. |
| 12 | **Field Validation** | `MISSING` | No on-site survey team ground-truth inspection has been performed. |
| 13 | **Researcher Sign-Off** | `NOT_READY_FOR_SIMULATION` | Interim stage is complete, but data must not be ingested into physics solver without explicit review. |

---

## 13. Policy on Promotion and Forbidden Simulation Inputs

### Files Eligible for Eventual Promotion to `data/processed/` (Following Researcher Approval)
1. `data/interim/terrain/fabdem_clipped_utm43.tif`: Suitable as a **regional boundary elevation baseline**.
2. `data/interim/vegetation/tree_inventory_interim.geojson` & `.csv`: Suitable as **verified 2D tree point locations**.
3. `data/interim/vegetation/photo_tree_match_log.csv`: Suitable as an **empirical reference catalog**.

### Files That Must NEVER Be Ingested as Authoritative Simulation Inputs
1. `data/raw/terrain/elevation_original.tif` (Skadi DEM): **Contains $+16.6\text{ m}$ commercial building rooftop spikes.** Ingesting this into ray tracing would create massive fictitious terrain shadows across Church Street.
2. `data/interim/vegetation/tree_measurement_review_working.csv`: **Contains uncalibrated photo-estimates.** Must not be treated as true 3D CAD tree geometry without sensitivity analysis and researcher sign-off.
3. Uncalibrated literature radiative defaults (LAI/transmissivity): Must not be hard-coded into GPU/CPU solvers as empirical ground truth.

---

## 14. Verification Summary Statement

The interim terrain and vegetation reconstruction stage for Project SOLARAEUS is complete. All 15 required deliverables, 5 intermediate terrain rasters/metadata files, and 6 high-resolution review figures have been generated and cryptographically audited. All physics solvers and benchmark result directories remain untouched.

`INTERIM_TERRAIN_AND_TREE_RECONSTRUCTION_COMPLETE`
