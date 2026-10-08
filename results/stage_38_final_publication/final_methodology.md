# SOLARAEUS Project Final Methodology Report

**Document ID**: `SOLARAEUS-FINAL-METHODOLOGY`  
**Release Date**: October 8, 2026  
**Status**: `STAGE_38_FINAL_PUBLICATION_AND_ARCHIVAL_COMPLETE`  

---

## 1. Executive Summary
The core solver and GPU computational roadmap were completed and validated.

Terrain-aware and tree-aware extensions were executed using available synthetic, regional-reference, and provisional inputs.

FABDEM was not treated as a street-scale DTM.

Tree geometry was not treated as field-calibrated.

Canopy parameters were evaluated for sensitivity only.

Field calibration was not claimed unless observations were available.

Real-world terrain/tree conclusions remain limited by missing street-scale terrain, field tree validation, and canopy measurements.

---

## 2. Solver Architecture and Versioning
The SOLARAEUS computational suite implements an additive, strictly versioned multi-tier architecture:
- **`2.0.0-cpu-ref`**: Flat-ground authoritative CPU reference solver (SOLWEIG-aligned 6-flux radiative transfer, ray-cast shadow masking, directional sky-view factors).
- **`2.0.0-gpu`**: Resident CUDA CuPy backend executing direct shadow casting, ray-traced SVF, and instantaneous $T_{mrt}$ / UTCI evaluations.
- **`2.1.0-cpu-terrain` / `2.1.0-gpu-terrain`**: Terrain-aware computational extensions supporting Digital Terrain Models (DTMs) with receptor elevation matching $z(x, y) + h_{ped}$.
- **`2.2.0-cpu-tree` / `2.2.0-gpu-tree`**: Analytical Level 1 provisional tree geometry (cylinder trunks + ellipsoid crowns).

---

## 3. Data Classification Standard
All datasets and parameters across the project strictly adhere to the following taxonomy:
- `MEASURED`: Physical empirical ground truth (air temperature, humidity from Bengaluru METAR).
- `FIELD_VALIDATED`: Direct in-situ sensor verification (none claimed on Church Street).
- `CENSUS_DERIVED`: Municipal tree census records.
- `PHOTO_ESTIMATED`: Metric estimates derived from photographic imagery (tree crown radii, tree heights).
- `PROVISIONAL`: Working geometric bounds authorized for sensitivity analysis.
- `LITERATURE_ASSUMED`: Physiological parameters drawn from peer-reviewed literature (LAI, LAD, albedo).
- `SYNTHETIC`: Mathematical profiles used for solver mechanics (flat, 2.5% incline, 0.15m curb, swale).
- `REGIONAL_REFERENCE_ONLY`: FABDEM v1.2 elevation model (30m grid, Copernicus-derived).
- `MISSING`: Unacquired ground truth data (street-scale DTM, in-situ globe temperatures).
- `DEFERRED`: Explicitly postponed field campaigns.
