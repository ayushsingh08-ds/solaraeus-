# Urban Microclimate Dataset Review Report: Church Street, Bengaluru

**Study Site**: Church Street Central/Eastern Study Block, Bengaluru, Karnataka, India  
**Review Timestamp**: 2026-10-06T20:36:34.880051+00:00 (`20261006_203634`)  
**Dataset Package**: [bengaluru_church_street_manual_handoff_v2](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/bengaluru_church_street_manual_handoff_v2/bengaluru_church_street_manual_handoff_v2) (Version 2.0)  
**Overall Status**: **`NOT_READY_FOR_SIMULATION`**  
**Preprocessing Status**: **`READY_FOR_PREPROCESSING_ONLY`**  

---

## Executive Summary

This formal data quality audit reviews the manually prepared real-world urban microclimate dataset for the Church Street central/eastern study block in Bengaluru, India. 

The dataset provides building footprints from Overture Maps (`2026-09-23.1`), satellite elevation from Mapzen/Tilezen Skadi (EGM96 vertical datum), off-site meteorological forcing from the NOAA Bengaluru City station for April 15, 2024 at 09:00 UTC (14:30 IST), regional solar irradiance estimates from NASA POWER / CERES, four baseline material classes, and a proposed 6 m × 3 m overhead shade-panel intervention.

All **11 automated package integrity checks pass** and all **89 dataset files match their published SHA256 checksums exactly**. 

However, in accordance with scientific reproducibility standards, **the package is a review draft and is NOT simulation-ready**. Zero building heights are surveyed or approved (`model_height_m` is 100% unassigned), solar time-averaging conventions remain unaligned with the instantaneous station timestep, material properties are generic unmeasured assumptions, and the overhead shade panel is a hypothetical proposed scenario without physical footing verification.

**Under no circumstances should microclimate comfort simulations ($T_{\text{mrt}}$, $\text{UTCI}$) be executed until the researcher explicitly signs off on all blocking items in [researcher_signoff.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/data/processed/researcher_signoff.json).**

---

## 1. Dataset Inventory

An exhaustive file audit of the handoff package verified 89 registered files spanning raw observations, processed geospatial products, metadata manifests, and verification scripts.

| Category | File Count | Formats Present | SHA256 Verification | Classification |
| :--- | :---: | :--- | :---: | :---: |
| **Processed Data** | 27 | GeoJSON, CSV, JSON | 27 / 27 (100%) | `pass` |
| **Raw Data** | 30 | GeoParquet, GeoJSON, TIFF, HGT, CSV, JSON | 30 / 30 (100%) | `pass` |
| **Metadata & Docs** | 10 | Markdown, JSON, TXT, PNG | 10 / 10 (100%) | `pass` |
| **Preparation Scripts**| 12 | Python, Shell, DuckDB | 12 / 12 (100%) | `pass` |
| **Source Records** | 10 | JSON, Markdown, TXT | 10 / 10 (100%) | `pass` |
| **Total** | **89** | *All formats verified* | **89 / 89 (100%)** | **`pass`** |

Full file-by-file sizes, checksums, and role mappings are documented in [file_inventory.csv](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/file_inventory.csv).

---

## 2. Site and Boundary Verification

The study boundary represents a compact commercial block along Church Street between Brigade Road and Museum Road.

- **Site Identifier**: `BLR_CHURCH_STREET_01`
- **Geographic Bounding Box**: $[77.6044^\circ\text{E}, 12.9743^\circ\text{N}] \times [77.6064^\circ\text{E}, 12.9755^\circ\text{N}]$
- **Approximate Centre**: $12.974900^\circ\text{N}, 77.605400^\circ\text{E}$
- **Geodesic Extents**: $216.99\,\text{m}$ (East–West) $\times 132.76\,\text{m}$ (North–South)
- **Projected UTM Extents**: $218.46\,\text{m}$ (East–West) $\times 135.05\,\text{m}$ (North–South)
- **Projected Area**: $28,840.88\,\text{m}^2$ ($2.884\,\text{ha}$)
- **Boundary Ingestion Policy**: Buildings intersecting the boundary are retained in their entirety (not clipped at walls or rooflines).
- **Audit Result**: Boundary geometry is topologically valid, closed, non-self-intersecting, and correctly oriented.

**Classification**: `pass`

---

## 3. Shadow-Context Verification

To ensure that solar casting from tall adjacent buildings outside the study boundary is accurately captured, a shadow-context boundary was established.

- **Expansion Definition**: Outward expansion of the main study boundary by exactly $75.0\,\text{m}$ in metric coordinates with squared (mitre) corners.
- **Analytical Metric Expansion**:
  - Main UTM bounds: $[782539.69, 1435735.35] \text{ to } [782758.15, 1435870.40]$
  - 75m Buffered UTM bounds: $[782464.69, 1435660.35] \text{ to } [782833.15, 1435945.40]$
- **Mathematical Audit**: The symmetric difference between the handoff `shadow_context_boundary.geojson` and an analytical $75.000\,\text{m}$ mitre buffer in EPSG:32643 is **$2.01 \times 10^-7\,\text{m}^2$** (floating-point machine precision).
- **Building Ingestion**: Exactly **123 potential shadow-casting buildings** intersect the context envelope (all 37 core buildings + 86 external casters).
- **Pedestrian Receptor Policy**: Pedestrian microclimate receptors are strictly constrained to the core study boundary; context buildings are included solely as potential shadow and radiative obstruction casters.

**Classification**: `pass`

---

## 4. Building Geometry Review

Geospatial polygons from Overture Maps release `2026-09-23.1` were evaluated across both core and context domains. Detailed metrics for all 123 footprints are recorded in [geometry_review.csv](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/geometry_review.csv).

- **Core Footprints**: Exactly 37 building footprints.
- **Context Footprints**: Exactly 123 building footprints (including all 37 core buildings).
- **Topology & Validity**:
  - Invalid polygons: **0**
  - Self-intersections: **0**
  - Empty geometries: **0**
  - Duplicate Overture UUIDs: **0**
  - Vertex count: ranges from 4 to 86 vertices per footprint.
- **Area Distribution**:
  - Minimum area: $12.35\,\text{m}^2$ (Building B27, small kiosk/annex)
  - Maximum area: $1,719.79\,\text{m}^2$ (Spencer Building, B04)
  - Median area: $394.98\,\text{m}^2$
- **Overlap Audit**: Zero footprint pairs overlap by greater than $1.0\,\text{m}^2$.
- **Flags**:
  - Building B27 ($12.35\,\text{m}^2$) is flagged as a small structure (`warning`). It must not be deleted automatically.

**Classification**: `pass` (with 1 `warning` on small footprint B27)

---

## 5. Building-Height Evidence Review

The height review audit identified the most critical data gap in the entire handoff package. Records for all 37 buildings are logged in [height_evidence_review.csv](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/height_evidence_review.csv).

### Evidence Breakdown across 37 Core Buildings:
1. **Measured / Surveyed Metre Heights**: **0 / 37 (100% missing)**.
2. **Floor-Count Records**: **17 / 37 populated** (derived from OpenStreetMap via Overture; range 2 to 14 floors).
3. **Google Open Buildings 2.5D Temporal v1 (2023) ML Estimates**: **33 / 37 populated** (range 2.5 m to 52.5 m).
4. **Verified Model Heights**: **0 / 37 populated** (`model_height_m` is strictly null).

> [!CAUTION]
> **STRICT EVIDENCE ISOLATION ENFORCED**:
> The dataset maintains strict separation between source floors, unapproved floor extrapolations ($3.2\,\text{m/floor}$), satellite ML height predictions, and observed heights. 
> Under no circumstances have these evidence streams been silently merged, averaged, or promoted into model heights.

### High-Priority Review Cases (9 Buildings):
The following 9 buildings have been identified as high-priority review items requiring researcher inspection:
- **B02**: Floor tag indicates 3 floors ($9.6\,\text{m}$), but Google ML predicts $18.5\,\text{m}$ ($0.49$ pixel fraction). Large discrepancy.
- **B03**: Very small structure ($57.4\,\text{m}^2$), Google ML predicts $2.5\,\text{m}$ with low pixel fraction ($0.07$).
- **B17**: Floor tag indicates 3 floors ($9.6\,\text{m}$), Google ML predicts $16.0\,\text{m}$ with low pixel fraction ($0.21$).
- **B19**: **Missing Google ML estimate** ($0.0$ valid pixels). Has a 2-floor tag ($6.4\,\text{m}$).
- **B23**: **Missing Google ML estimate AND missing floor count**. Completely unconstrained geometry.
- **B31**: Floor tag indicates 3 floors ($9.6\,\text{m}$), Google ML predicts $16.5\,\text{m}$ ($0.48$ pixel fraction).
- **B32**: **Missing Google ML estimate AND missing floor count**. Completely unconstrained geometry.
- **B36**: **Missing Google ML estimate**. Has a 2-floor tag ($6.4\,\text{m}$).
- **B37**: Floor tag indicates 3 floors ($9.6\,\text{m}$), Google ML predicts $17.5\,\text{m}$ ($0.45$ pixel fraction).

Additionally, **B10 (Barton Centre)** is the tallest building in the domain (14 floors = $44.8\,\text{m}$ floor estimate vs $52.5\,\text{m}$ Google ML estimate), casting extensive shadows across the afternoon canyon.

**Classification**: **`requires_researcher_signoff`** (**`blocking`**)

---

## 6. Coordinate-System Review

The dataset establishes clean, reproducible geodetic-to-metric transformations. Complete transformation parameters are archived in [coordinate_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/coordinate_review.json).

- **Source CRS**: EPSG:4326 (WGS84 ellipsoidal 2D coordinates, longitude/latitude).
- **Calculation CRS**: EPSG:32643 (UTM Zone 43N, transverse Mercator, metres).
- **Projection Transformation**: Enforces `always_xy=True` across all pyproj pipelines to prevent axis-order inversion bugs.
- **Round-Trip Transformation Precision**: Maximum roundtrip error is **$3.55 \times 10^-15$ degrees** (well below millimeter precision).
- **Local Scene Origin**:
  - Easting: $782,541.805538\,\text{m}$
  - Northing: $1,435,736.110343\,\text{m}$
- **Grid Convergence**:
  - Central meridian of UTM Zone 43N: $\lambda_0 = 75.0^\circ\text{E}$
  - Longitude of Church Street: $\lambda = 77.6054^\circ\text{E}$ ($\Delta \lambda = +2.6054^\circ$)
  - Latitude: $\phi = 12.9749^\circ\text{N}$
  - Grid convergence angle: $\gamma = \Delta \lambda \sin(\phi) = +0.5854^\circ$ ($+35.12\text{ arcminutes}$)
  - **Implication**: True North and Grid North diverge by $+0.585^\circ$. Astronomical solar azimuths must be rotated by $-\gamma$ when casting rays in UTM coordinate space.

**Classification**: `pass`

---

## 7. Terrain Review

Elevation data is preserved from the Mapzen / Tilezen Skadi product (tile `N12E077`). Full metadata is archived in [terrain_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/terrain_review.json).

- **Original Format**: gzip-compressed SRTM-style signed 16-bit big-endian integer grid (`.hgt.gz`).
- **Converted Product**: GeoTIFF (`N12E077.tif`), losslessly converted preserving pixel alignment and values.
- **Horizontal Resolution**: 1.0 arcsecond ($pprox 30.14\,\text{m}$ East–West $\times 30.73\,\text{m}$ North–South).
- **Vertical Reference**: EGM96 orthometric height in metres.
- **NoData Identifier**: `-32768`.
- **Site Samples**: 32 sample points lie within the site boundary; 0 missing samples.
- **Site Elevation Bounds**: Minimum $916\,\text{m}$, Maximum $934\,\text{m}$, Median $922.0\,\text{m}$.
- **Elevation Classification**: `composite_elevation_DEM_not_certified_bare_earth`.
- **Critical Limitations**:
  - The $30\,\text{m}$ raster sampling cannot resolve street curbs, gutters, sidewalk edges, or individual building foundations.
  - Radar interferometry captures reflections from tree canopies and building rooftops.
- **Solver Treatment**: The microclimate solver currently assumes flat ground at model-relative $z = 0\,\text{m}$. Terrain elevation is excluded from solver computations for this phase.

**Classification**: `pass` (with `warning` on coarse resolution and non-bare-earth classification)

---

## 8. Weather and Timestamp Review

Meteorological forcing represents a single afternoon timestep during hot dry pre-monsoon conditions. Full metrics are archived in [weather_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/weather_review.json).

- **Timestamp UTC**: `2024-04-15T09:00:00Z`
- **Timestamp Local IST**: `2024-04-15T14:30:00+05:30` (UTC $+05:30$)
- **Station**: Bengaluru City station (WMO ID `43295099999`, "BANGALORE, IN")
  - Station Location: $12.9667^\circ\text{N}, 77.5833^\circ\text{E}$, elevation $921.0\,\text{m}$
  - Distance to Site Centre: $2.562\,\text{km}$ south-southwest
- **Observed & Derived Variables**:
  - Air Temperature: $35.0^\circ\text{C}$ (Observed off-site, NOAA QC code 1)
  - Dew Point: $8.5^\circ\text{C}$ (Observed off-site, NOAA QC code 1)
  - Relative Humidity: $19.729\%$ (Derived from $T$ and $T_{\text{dew}}$ via Magnus formulation)
  - Wind Speed: $1.5\,\text{m/s}$ (Observed off-site, NOAA QC code 1)
  - Wind Direction: $90^\circ$ True North (Observed off-site, East wind)
  - Anemometer Height: Undocumented in source file (standard synoptic $10\,\text{m}$ assumed)

> [!IMPORTANT]
> **MANDATORY FRAMING REQUIREMENT**:
> Bengaluru City station observations are applied as spatially uniform forcing at the Church Street study site. 
> These observations must NEVER be described as site-measured Church Street weather.

**Classification**: `pass` (with `warning` regarding off-site synoptic anemometer vs pedestrian street-canyon wind)

---

## 9. Solar-Data Review

Solar radiation data is obtained from NASA POWER / CERES hourly satellite assimilation. Complete documentation is archived in [solar_timestamp_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/solar_timestamp_review.json).

- **Irradiance Quantities**:
  - Global Horizontal Irradiance (GHI): $755.97\,\text{W/m}^2$ ($755.97\,\text{Wh/m}^2$ over 1 hour)
  - Direct Normal Irradiance (DNI): $728.31\,\text{W/m}^2$ ($728.31\,\text{Wh/m}^2$ over 1 hour)
  - Diffuse Horizontal Irradiance (DHI): $172.18\,\text{W/m}^2$ ($172.18\,\text{Wh/m}^2$ over 1 hour)
- **Solar Classification**: `Regional satellite/model estimate, not Church Street measurements`.
- **Timestamp Interval Discrepancy**:
  - NASA POWER hourly radiation records represent integrated hourly energy fluxes.
  - The provider hour label `2024041509` does not explicitly declare whether the aggregation interval is $[08:00, 09:00]$ UTC (hour-ending), $[09:00, 10:00]$ UTC (hour-beginning), or $[08:30, 09:30]$ UTC (hour-centered).
  - Pairing time-averaged irradiance with instantaneous astronomical sun position ($14:30\,\text{IST}$, solar altitude $\approx 52.8^\circ$, solar azimuth $\approx 264.4^\circ$) requires explicit researcher protocol approval.

**Classification**: **`requires_researcher_signoff`** (**`blocking`**)

---

## 10. Shade-Panel Intervention Review

A single proposed overhead shade panel has been defined as a reversible pedestrian intervention scenario. Full geometry and metadata are recorded in [intervention_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/intervention_review.json).

- **Intervention ID**: `BLR_SHADE_001` (Object `CANOPY_001`)
- **Type**: Overhead shade panel
- **Geometry**:
  - Length: $6.0\,\text{m}$
  - Width: $3.0\,\text{m}$
  - Footprint Area: $18.0\,\text{m}^2$
  - Underside Height: $3.5\,\text{m}$
  - Panel Thickness: $0.10\,\text{m}$
  - Top Height: $3.6\,\text{m}$
  - Opacity: $1.0$ (Completely opaque)
  - Support Columns: **Omitted** (floating panel pilot simplification)
- **Orientation**:
  - Bearing from True North: $103.028^\circ$ (parallel to local Church Street centerline tangent)
  - Bearing from UTM Grid North: $102.443^\circ$
- **Clearance**:
  - Offset from centerline: $4.5\,\text{m}$ north
  - Minimum clearance to nearest building footprint: $1.751\,\text{m}$
  - Footprint collisions: **0**
- **Material Assumptions**:
  - Albedo: $0.60$ (assumed)
  - Emissivity: $0.90$ (assumed)
  - Initial Surface Temperature: $35.0^\circ\text{C}$ (assumed initial condition)
- **Status & Limitations**: The intervention is a purely hypothetical simulation scenario. Physical footing feasibility, tree branch collisions, and municipal installation permissions are unverified.

**Classification**: **`requires_researcher_signoff`** (**`blocking`**)

---

## 11. Material-Assumption Review

Five material classes are defined with assumed radiative and initial thermal boundary conditions:

| Material Class | Albedo | Emissivity | Initial Surface Temp | Status | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **building_wall** | 0.30 | 0.90 | $35.0^\circ\text{C}$ | `assumed` | Generic masonry/plaster; unmeasured |
| **building_roof** | 0.20 | 0.90 | $35.0^\circ\text{C}$ | `assumed` | Generic bituminous/concrete; unmeasured |
| **ground** | 0.20 | 0.95 | $35.0^\circ\text{C}$ | `assumed` | Generic soil/unpaved surface |
| **pavement** | 0.30 | 0.95 | $35.0^\circ\text{C}$ | `assumed` | Church Street granite pavers; unmeasured |
| **shade_panel** | 0.60 | 0.90 | $35.0^\circ\text{C}$ | `assumed` | High-reflectance canopy membrane |

### Baseline Vegetation Policy:
- Existing mature street trees and shopfront awnings along Church Street are **unmapped** in this baseline dataset.
- A canopy-free baseline is an unverified simplifying assumption. The researcher must formally accept this baseline simplification before results are published.

**Classification**: **`requires_researcher_signoff`** (**`blocking`**)

---

## 12. Provenance and Licensing Review

Provenance documentation tracks all upstream datasets, download timestamps, and licensing terms. Detailed assessment is logged in [provenance_review.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/provenance_review.json).

| Dataset | Provider / Version | License | Downstream Distribution Terms | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Buildings** | Overture Maps `2026-09-23.1` | ODbL-1.0 | Attribution required; share-alike | `pass` |
| **Roads** | Overture Maps `2026-09-23.1` | ODbL-1.0 | Attribution required; share-alike | `pass` |
| **ML Heights** | Google Open Buildings Temporal v1 | CC-BY-4.0 / ODbL | Attribution to Google Research required | `pass` |
| **Terrain** | Mapzen / Tilezen Skadi | USGS Public Domain | Mapzen / USGS attribution required | `pass` |
| **Solar Forcing** | NASA POWER / CERES | CC-BY-4.0 | Open access; citation required | `pass` |
| **Weather** | NOAA ISD Bengaluru City (`43295099999`) | Open Data | International partner station data terms lack explicit SPDX license | **`requires_researcher_signoff`** (`warning`) |

**Classification**: `requires_researcher_signoff` (`warning` on NOAA international station records)

---

## 13. Unresolved Researcher Decisions

To ensure full scientific integrity, six formal sign-off gates remain open in [researcher_signoff.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/data/processed/researcher_signoff.json):

```json
{
  "height_verification": {
    "status": "pending",
    "notes": ""
  },
  "building_placement": {
    "status": "pending",
    "notes": ""
  },
  "solar_interval_alignment": {
    "status": "pending",
    "notes": ""
  },
  "material_assumptions": {
    "status": "pending",
    "notes": ""
  },
  "shade_panel_geometry": {
    "status": "pending",
    "notes": ""
  },
  "weather_redistribution_terms": {
    "status": "pending",
    "notes": ""
  }
}
```

Detailed decision summaries are archived in [unresolved_items.json](file:///C:/Users/AYUSH SINGH/Documents/GitHub/solaraeus/results/church_street_data_review_20261006_203634/unresolved_items.json).

| Gate ID | Area | Severity | Required Researcher Action |
| :--- | :--- | :---: | :--- |
| `height_verification` | Building Heights | **`blocking`** | Review `building_height_review.csv`, resolve B19/B23/B32/B36, populate approved `model_height_m`. |
| `building_placement` | Footprint Registration | **`blocking`** | Verify Overture footprints against independent aerial imagery; inspect edge-crossing structures. |
| `solar_interval_alignment`| Solar Time Averaging | **`blocking`** | Formally approve integration interval definition and instantaneous sun angle pairing protocol. |
| `material_assumptions` | Radiative & Vegetation | **`blocking`** | Accept default albedos, initial $35^\circ\text{C}$ surface temperatures, and tree-free baseline simplification. |
| `shade_panel_geometry` | Shade Intervention | **`blocking`** | Approve hypothetical 6x3m canopy dimensions, 3.5m clearance, and no-posts structural model. |
| `weather_redistribution_terms`| Weather Licensing | `warning` | Review institutional redistribution terms for NOAA international partner station data. |

---

## 14. Simulation-Readiness Decision

```text
================================================================================
                           FINAL DECISION
================================================================================
                      NOT_READY_FOR_SIMULATION
================================================================================
```

### Alternative Preprocessing Determination:
`READY_FOR_PREPROCESSING_ONLY`

### Formal Declaration:
The Bengaluru Church Street handoff dataset package satisfies all structural, geodetic, topological, and hash-integrity verification checks. Automated preprocessing pipelines (footprint cleaning, coordinate conversions, and bounding box validations) may proceed.

However, **because zero building heights are approved, solar integration intervals are unresolved, material properties are uncalibrated assumptions, and the intervention geometry is hypothetical, the dataset is strictly UNFIT FOR SIMULATION**.

No thermal-comfort simulations ($T_{\text{mrt}}$, $\text{UTCI}$), ray-tracing recomputations, or certificate generations may be executed until the researcher transitions all blocking gates in `researcher_signoff.json` from `"pending"` to `"approved"`.

---
*Report generated by SOLARAEUS Data Review Protocol v2.0*
