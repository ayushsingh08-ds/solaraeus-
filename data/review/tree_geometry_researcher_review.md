# SOLARAEUS Tree-Geometry and Terrain Researcher Review

## 1. Executive Summary & Review Scope
This review constitutes the formal assessment of interim terrain and vegetation datasets prepared for Project **SOLARAEUS** covering the Church Street pedestrian corridor in Bengaluru, Karnataka, India.

- **Primary Objective**: Establish defensible uncertainty bounds for street trees, evaluate regional terrain suitability, and prevent premature ingestion of uncalibrated geometry into the validated GPU ray-tracing physics solver.
- **Protection Status**: 100% byte-identical preservation verified across all 197 raw files, 26 interim assets, and 11 frozen benchmark directories.
- **Current Operational Status**:
  - `TREE_LOCATIONS_VERIFIED`
  - `TREE_SPECIES_REPORTED`
  - `TREE_CURRENT_EXISTENCE_UNCERTAIN`
  - `TREE_DIMENSIONS_PROVISIONAL`
  - `TREE_GEOMETRY_BOUNDS_AVAILABLE`
  - `CANOPY_LEVEL_1_NOT_YET_APPROVED`
  - `CANOPY_LEVEL_2_PARAMETERS_NOT_VALIDATED`
  - `FABDEM_REGIONAL_REFERENCE_ONLY`
  - `MICROSCALE_DTM_MISSING`
  - `RESEARCHER_SIGNOFF_REQUIRED`
  - `SIMULATION_INTEGRATION_BLOCKED`

---

## 2. Six Core Trees Review (T08 to T13)
All six core trees are located strictly on the southern pedestrian sidewalk of Church Street within local coordinates $X \in [20.07, 97.09]\text{ m}, Y \in [65.54, 83.27]\text{ m}$.

| Tree ID | Census Species | Local Coord (X, Y) | Matched Imagery | Evidence Quality | Reviewer Decision | Key Observations |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| **T08** | *Ficus Religiosa L.* | (20.07m, 81.14m) | KV 814425142, Commons 72609328 | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Massive spreading sacred fig canopy. Vehicle clearance (~4.0m) and pavement width provide scale. |
| **T09** | *Syzygium Cumini (L.) Skeels* | (44.91m, 83.27m) | KV 814425130, KV 814425114 | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Dense mature jamun tree at direct 5.6m roadside capture. Upright rounded crown. |
| **T10** | *Syzygium Cumini (L.) Skeels* | (33.24m, 77.29m) | KV 814425138, KV 814425130 | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Semi-mature jamun tree between T08 and T09. Moderately dense canopy. |
| **T11** | *Saraca Asoca De Wilde* | (60.95m, 75.36m) | KV 814425114, KV 814425110, Mapillary | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Compact ovoid crown in sidewalk pit. Scaled against retail shopfront entry height (~3.0m). |
| **T12** | *Saraca Asoca De Wilde* | (78.32m, 74.65m) | KV 814425338, KV 814425110, Mapillary | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Companion Sita ashok tree at 7.5m capture distance. Compact upright foliage. |
| **T13** | *Techoma Stans* | (97.09m, 65.54m) | KV 814425266, KV 814425090 | APPROXIMATE_PHOTO | ACCEPT_WITH_WIDE_BOUNDS | Small yellow bells tree / shrub in raised planter. Lowest height in core cohort. |

---

## 3. Tree Dimension Uncertainty Envelope
To avoid false precision while enabling rigorous microclimate sensitivity analysis, three distinct geometric states have been formulated for each core tree:

| Tree ID | Dimension Metric | Conservative-Small | Nominal Estimate | Conservative-Large | Uncertainty Basis & Scaling Evidence |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **T08** | Height / Crown Diam / Base | 11.0m / 9.5m / 3.8m | **13.5m / 12.0m / 4.2m** | 16.0m / 15.0m / 4.5m | Scaled against 4-story commercial building floor slabs (~3.5m) and bus clearances. |
| **T09** | Height / Crown Diam / Base | 9.0m / 7.0m / 3.2m | **11.0m / 8.5m / 3.8m** | 13.0m / 10.5m / 4.2m | 5.6m roadside passage capture; street width and adjacent building facades. |
| **T10** | Height / Crown Diam / Base | 7.5m / 6.0m / 2.8m | **9.5m / 7.5m / 3.2m** | 11.5m / 9.0m / 3.6m | Scaled between T08 and adjacent storefront floor heights. |
| **T11** | Height / Crown Diam / Base | 6.5m / 4.2m / 2.4m | **8.0m / 5.5m / 2.8m** | 9.5m / 6.8m / 3.2m | Scaled relative to ground-floor retail facade and pedestrian bollards. |
| **T12** | Height / Crown Diam / Base | 6.0m / 3.8m / 2.2m | **7.5m / 5.0m / 2.6m** | 9.0m / 6.2m / 3.0m | Direct 7.5m lateral capture; companion to T11. |
| **T13** | Height / Crown Diam / Base | 3.8m / 2.6m / 1.4m | **5.0m / 3.5m / 1.8m** | 6.5m / 4.5m / 2.2m | Scaled against 0.6m masonry planter wall and pedestrian heights. |

---

## 4. Context Trees Evaluation (T01 to T07, T14)
- **T06 & T07 (*Araucaria columnaris*, Local X = -3.3m, -9.3m)**: Matched in KartaView photos `814425166` and `814425170`. Classified as `OPTIONAL_CONTEXT_GEOMETRY`. They cast narrow evening shadows into the western edge of Church Street.
- **T05 (*Ficus racemosa*, Local X = -6.3m)**: Partially visible behind signage; classified as `LOCATION_ONLY` (dimensions unmeasured).
- **T03 & T04 (Local Y = 140–150m)**: North setback trees near Brigade Road; crown tops visible in Barton Centre aerial obliques. Classified as `LOCATION_ONLY`.
- **T01 & T02 (Local Y = 170–190m)**: Rear parcel trees; obscured by commercial multi-story blocks. Classified as `INSUFFICIENT_DATA`.
- **T14 (Local X = 142.9m, Y = 141.8m)**: >70m north of corridor behind commercial blocks. Classified as `EXCLUDE_PENDING_REVIEW` (too distant to cast shadows on study area).

---

## 5. Regional FABDEM Terrain Evaluation
- **Native Resolution**: ~30.87m cell size.
- **Vertical Reference**: EGM2008 geoid orthometric height.
- **Topographic Gradient**: Smooth descent from West (917.4m) to East (910.1m), std dev 1.38m.
- **Comparison to Skadi DEM**: Skadi DEM is an uncorrected SRTM C-band radar DSM with positive building rooftop spikes up to **+16.6m** (mean difference +7.10m). FABDEM successfully stripped these rooftop artifacts.
- **Suitability Classification**: `REGIONAL_REFERENCE_ONLY`.
- **Prohibition**: FABDEM is strictly forbidden as a microscale street DTM. Curbs (150mm) and drainage cross-slopes (1:50) are missing.

---

## 6. Comprehensive Decision Matrix (Parts 8 & 9)

| Tree ID | Location | Species | Existence | Height | Crown Diam | Crown Base | Transmissivity | LAI/LAD | Ground Elevation | Simulation Approval |
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

## 7. Actionable Roadmap to Close Data Gaps
1. **2026 Field Ground Truth Walkthrough**: Perform a rapid pedestrian audit along Church Street to confirm current presence, tag tree trunks, and take georeferenced calibration photos.
2. **Optical / Laser Dimension Measurement**: Use a handheld TruPulse laser rangefinder to measure true total height, crown base clearance, and crown spread along two perpendicular axes.
3. **Under-Canopy Solar Radiometry**: Measure sub-canopy photosynthetic photon flux density (PPFD) or global shortwave irradiance under *Ficus religiosa* and *Syzygium cumini* to calibrate true transmissivity $\tau$.
4. **Engineering Curb Profile**: Obtain or survey a transverse curb cross-section to establish whether a 150mm step significantly affects pedestrian shadow boundaries.
