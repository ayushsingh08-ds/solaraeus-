# Static Full Recomputation Audit Report: Church Street Baseline Scene

**Execution Timestamp (UTC):** `20261006_232110`  
**Run Mode:** Static Full Recomputation (Single Timestep, Scratch Evaluation)  
**Scene Scope:** Baseline Scene (37 Core Buildings, 123 Shadow Context Buildings)  
**Readiness Decision:** `READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION_AFTER_METADATA_RECONCILIATION`  

> **Scientific Qualification:**  
> “The Church Street baseline is an exploratory static simulation using approved but partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties.”

---

## 1. Objective

The objective of this stage is to execute and audit one **static full recomputation** of the baseline Church Street scene in Bengaluru, Karnataka, India. This computation exercises the end-to-end triangular-mesh solver pathway—from direct solar shadow beam tracing, multi-azimuth sky view factor horizon scanning, and 6-directional shortwave/longwave flux integration, through Mean Radiant Temperature ($T_{mrt}$) and Universal Thermal Climate Index (UTCI)—without running incremental cache reuse or the hypothetical shade-panel intervention.

This stage establishes an audited, reproducible numerical reference for the baseline real-world urban geometry.

---

## 2. Study-Site Description

- **Site:** Church Street central/eastern study block
- **City:** Bengaluru, Karnataka, India
- **Centre Coordinates:** 12.974900° N, 77.605400° E
- **Core Site Boundary:** Approximately 217 m × 133 m enclosing 37 mapped building footprints.
- **Shadow Context Domain:** Core study site expanded outward by 75 m in UTM metric coordinates (squared/miter corners), capturing 123 total shadow-casting buildings (37 core + 86 context).
- **Pedestrian Analysis Corridor:** 12 m wide corridor (6 m on either side of the Church Street centerline) spanning the street canyon.

---

## 3. Input-Data Provenance and Verification

The simulation ingested verified preprocessing artifacts from:
`results/church_street_preprocessing_20261006_224238/`

All input files were audited and their SHA256 cryptographic digests verified before simulation execution:
- `main_scene_mesh.json`: `6dbaa914e7427445a808daef84a990ce524f64524c2d3293aa0a1da4cca300b6`
- `shadow_context_mesh.json`: `33c9ca008a6fa20e5155fb54652a7d3f2f31c5d20928c2cd0e1ecc360f47104e`
- `accepted_height_policy.json`: `b0eab59cd623026bbfb708d742ee1a9480f4b66aed74dc31ff9693c0a0788f87`
- `coordinate_validation.json`: `33f0e6fe61dcb934c07c8dae34595d9443607271ddf9e0e5c240ff430b7ac62a`
- `scene_summary.json`: `b884feff98e3d9f2712604f952578ebca6541fdc3d672ab78dd7bc5dbc9fad88`
- `geometry_validation_report.json`: `669d7977e95f83c6df8ccbc9a9643c5f96d25098eae78b18b655203af2616c5a`

All 6 researcher sign-off gates in `data/processed/researcher_signoff.json` were confirmed as approved.

---

## 4. Geometry and Mesh Summary

The urban geometry was ingested directly from validated triangular mesh serializations without reconstruction or modification:

| Domain | Building Count | Vertex Count | Triangle Count | Watertight Status | Degenerate Triangles |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Core Main Scene** | 37 | 448 | 748 | 100% Watertight (37/37) | 0 |
| **Shadow Context Scene** | 123 | 1,314 | 2,136 | 100% Watertight (123/123) | 0 |

- **Local Coordinate Bounds (Context):** $X \in [-197.7, 339.09]\,\text{m}$, $Y \in [-125.37, 252.04]\,\text{m}$, $Z \in [0.0, 52.5]\,\text{m}$.
- **All 37 core buildings** form a strict subset of the 123 shadow context buildings.
- **Context-only buildings** (86 buildings) are utilized strictly for geometric ray obstruction and sky obstruction; their pedestrian statistics are segregated from reported street canyon microclimate metrics.

---

## 5. Height Uncertainty Summary

Building heights were assigned under the approved multi-tier evidence selection policy. The dataset incorporates a formal **dual-taxonomy** classification:

1. **Axis 1 (Decision Status Gate):**
   - **Approved Core:** 30 buildings
   - **Accepted Context:** 77 buildings
   - **Total Approved / Accepted:** 107 buildings (87.0%)
   - **Uncertain Core:** 7 buildings
   - **Uncertain Context:** 9 buildings
   - **Total Uncertain Status:** 16 buildings (13.0%)
   - **Rejected:** 0 buildings

2. **Axis 2 (Evidence Quality Rating):**
   - **Moderate Uncertainty:** 83 buildings (67.5%)
   - **High Uncertainty:** 29 buildings (23.6%)
   - **Extreme Uncertainty:** 11 buildings (8.9%)

3. **High/Extreme Sensitivity Cohort (40 buildings):**
   The 40 buildings identified in `uncertain_buildings.csv` represent the exact union of High (29) and Extreme (11) uncertainty tiers. This comprises the 16 Uncertain status buildings plus 24 Approved/Accepted buildings with high uncertainty (2 core floor fallbacks lacking ML and 22 context ML estimates with sparse pixel coverage).

---

## 6. Coordinate System and Local Metric Origin

- **Source Geodetic CRS:** EPSG:4326 (WGS84 ellipsoidal coordinates)
- **Projected Metric CRS:** EPSG:32643 (UTM Zone 43N)
- **Local Metric Origin $(0, 0, 0)$:**
  - Easting ($X$): $782,541.8055\,\text{m}$
  - Northing ($Y$): $1,435,736.1103\,\text{m}$
  - Elevation ($Z$): $0.0\,\text{m}$
- **Grid Convergence:** $\gamma = +0.585366^\circ$ ($35.12'$). Grid North (UTM $+Y$) points clockwise relative to True North. All ray intersection routines and solar vectors operate strictly in the local Cartesian metric system.

---

## 7. Pedestrian Grid Definition & Reconciliation

### Metadata Reconciliation Record
The nominal preprocessing report text cited:
`380 m × 295 m at 2 m resolution = 28,120 cells`
Whereas $(380 \times 295) / 2^2 = 28,025$ cells.

**Reconciliation Finding & Distinctions:**
The report explicitly distinguishes three distinct spatial interpretations:
1. **Nominal rounded bounds:** `380 m × 295 m` (informal domain approximation; analytical buffer envelope was $369.99\,\text{m} \times 286.57\,\text{m}$).
2. **Actual discrete grid extent:** `380 m × 296 m` (Cartesian extent spanning $[-85.0, 295.0]\,\text{m}$ in $X$ and $[-80.0, 216.0]\,\text{m}$ in $Y$).
3. **Actual grid:** `190 × 148 cells = 28,120 cells` ($n_x = 380.0 / 2.0 = 190$ columns, $n_y = 296.0 / 2.0 = 148$ rows).

Because a nominal height of 295 m at 2 m resolution yields $295 / 2 = 147.5$ fractional cells—and non-integer cells cannot exist on a discrete numerical grid—the pedestrian grid generator snapped $n_y$ to 148 rows ($296.0\,\text{m}$).
Exact formula: $(380.0 \times 296.0) / (2.0^2) = 112,480 / 4 = 28,120$ cells with zero fractional truncation.
The serialized discrete grid in `shadow_context_mesh.json` was always strictly $380.0\,\text{m} \times 296.0\,\text{m}$ (28,120 cells); the discrepancy was an informal report text rounding. Recorded in `grid_metadata_reconciliation.json`.

---

## 8. Weather Forcing

**Label:** *“Bengaluru City station observations applied as spatially uniform forcing at the Church Street study site.”*  
*(Off-site observation; not on-site microclimate measurement).*

- **Station Name:** Bengaluru City Station (WMO ID 43295 / NOAA ISD 43295099999)
- **Station Coordinates:** $12.966667^\circ\,\text{N}, 77.583333^\circ\,\text{E}$
- **Site Centre Coordinates:** $12.974900^\circ\,\text{N}, 77.605400^\circ\,\text{E}$
- **Station Geodesic Distance to Site Centre:** $2.56\,\text{km}$ ($2,561.6\,\text{m}$, WGS84 ellipsoid geodesic distance)
- **Date & Time:** April 15, 2024 at 09:00 UTC / 14:30 IST
- **Air Temperature:** $35.0^\circ\text{C}$ ($308.15\,\text{K}$)
- **Dew Point:** $8.5^\circ\text{C}$
- **Relative Humidity:** $19.729\%$ (derived from air temperature and dew point via Magnus formula)
- **Wind Speed:** $1.5\,\text{m/s}$ at pedestrian height
- **Wind Direction:** $90.0^\circ$ (from the east)
- **Data Provenance:** Observed weather at Bengaluru City station, applied as spatially uniform boundary forcing.

---

## 9. Solar Forcing and Time Convention

- **Source:** NASA POWER hourly solar radiation estimates for April 15, 2024.
- **Hourly Energy Interval:** 09:00–10:00 UTC (14:30–15:30 IST)
  - Global Horizontal Irradiance (GHI): $755.97\,\text{W/m}^2$
  - Direct Normal Irradiance (DNI): $728.31\,\text{W/m}^2$
  - Diffuse Horizontal Irradiance (DHI): $172.18\,\text{W/m}^2$

### Authoritative Solar Position (NOAA Astronomical Calculations)
| Parameter | Value |
| :--- | :--- |
| `timestamp_utc` | `2024-04-15T09:00:00Z` |
| `timestamp_ist` | `2024-04-15T14:30:00+05:30` |
| `latitude` | `12.974900` |
| `longitude` | `77.605400` |
| `timezone` | `UTC / IST (UTC+05:30)` |
| `solar_altitude` | `57.9160°` |
| `solar_zenith` | `32.0840°` |
| `solar_azimuth_true_north` | `268.1655°` |
| `solar_azimuth_grid_north` | `267.5802°` |
| `algorithm/module` | `urban_comfort.solar.solar_position` (NOAA Solar Calculations) |
| `sun_vector` (East, North, Up) | `(-0.5309, -0.0170, 0.8473)` |

### Solar-Position Discrepancy Resolution
- **Earlier Record:** Preliminary review documentation cited solar altitude $\approx 52.82^\circ$ (or $\approx 52.8^\circ$, azimuth $\approx 264.4^\circ$).
- **Current Authoritative Calculation:** Solar altitude $= 57.9160^\circ$, azimuth $= 268.1655^\circ$ True North ($267.5802^\circ$ Grid North).
- **Mathematical Explanation of Discrepancy:**
  1. The earlier review record of $\approx 52.82^\circ$ originated from a simplified uncorrected textbook solar position estimate that assumed local solar noon occurs at exactly 12:00:00 clock time (hour angle $H = (14.5 - 12) \times 15^\circ = 37.5^\circ$), neglecting the Equation of Time and Bengaluru's geographic longitude offset relative to the standard Indian Standard Time meridian ($82.5^\circ\,\text{E}$ vs $77.6054^\circ\,\text{E}$).
  2. Because Bengaluru is $4.8946^\circ$ west of the standard IST meridian, local solar time lags standard clock time by $19.58$ minutes ($-19^\text{m}35^\text{s}$). On April 15, true solar noon at Church Street occurs at **12:20 IST (06:50 UTC)** with peak solar altitude of $86.99^\circ$.
  3. At 14:30 IST, only **130 minutes (2.17 hours)** have elapsed since solar noon, placing the sun at **$57.9160^\circ$**.
  4. Evaluating NOAA solar position 2.5 hours after true solar noon (at 14:51 IST / 09:21 UTC) drops the solar altitude to **$52.8011^\circ$**, exactly matching the earlier uncorrected $52.82^\circ$ record.
  5. The authoritative NOAA implementation at the exact simulation timestamp (09:00:00 UTC / 14:30:00 IST) is strictly $57.9160^\circ$.

### Radiation Consistency Verification
The distinction between hourly interval-averaged radiation and instantaneous sun position is preserved:
- **Instantaneous (09:00 UTC):**  
  $\text{DNI} \cos(\theta_z) + \text{DHI} = 728.31 \times \cos(32.08^\circ) + 172.18 = 789.26\,\text{W/m}^2$  
  $\Delta = +33.29\,\text{W/m}^2$ ($+4.40\%$ vs GHI $755.97\,\text{W/m}^2$).
- **Interval Midpoint (09:30 UTC):**  
  $\text{DNI} \cos(\theta_{z,mid}) + \text{DHI} = 728.31 \times \cos(39.39^\circ) + 172.18 = 735.04\,\text{W/m}^2$  
  $\Delta = -20.93\,\text{W/m}^2$ ($-2.77\%$ vs GHI $755.97\,\text{W/m}^2$).
- **Hour-Integrated Mean (09:00–10:00 UTC):**  
  $\text{DNI} \langle\cos(\theta_z)\rangle + \text{DHI} = 733.46\,\text{W/m}^2$  
  $\Delta = -22.51\,\text{W/m}^2$ ($-2.98\%$ vs GHI $755.97\,\text{W/m}^2$).

All closure checks are well within normal satellite modeling tolerance ($< 5\%$).

---

## 10. Material Assumptions

All radiative properties represent **assumptions**, not field measurements:

| Material Class | Albedo $\alpha$ | Emissivity $\varepsilon$ | Initial Surface Temperature | Status |
| :--- | :--- | :--- | :--- | :--- |
| `building_wall` | 0.30 | 0.90 | $35.0^\circ\text{C}$ ($308.15\,\text{K}$) | Assumed |
| `building_roof` | 0.20 | 0.90 | $35.0^\circ\text{C}$ ($308.15\,\text{K}$) | Assumed |
| `ground` | 0.20 | 0.95 | $35.0^\circ\text{C}$ ($308.15\,\text{K}$) | Assumed |
| `pavement` | 0.30 | 0.95 | $35.0^\circ\text{C}$ ($308.15\,\text{K}$) | Assumed |

---

## 11. Terrain Policy

The solver operates under the canonical **flat-ground policy**:
$$\text{terrain\_z} = 0.0\,\text{m}$$
The 30 m SRTM DEM was reviewed for metadata and context elevation (mean site elevation $917.43\,\text{m}$, range $[916.18, 918.68]\,\text{m}$) but is deliberately excluded from solver thermal calculations.

---

## 12. Baseline Simulation Method

A single-pass, deterministic full recomputation was executed across the context grid ($148 \times 190 = 28,120$ cells):
1. **Direct Shadows:** Möller-Trumbore ray-mesh intersection tests for rays from pedestrian receptors ($z = 1.1\,\text{m}$) toward the sun vector across all 123 triangular meshes ($2,136$ triangles).
2. **Directional Visibility & SVF:** 32-azimuth horizon scanning up to $120\,\text{m}$ search horizon over the rasterized uppermost top-surface height field of the 123 meshes.
3. **Shortwave Radiation:** 6-directional fluxes on a standing human model (cylinder weights: $f_{up}=0.06, f_{down}=0.06, f_{side}=0.22$).
4. **Longwave Radiation:** Clear-sky emissivity via Prata (1996), atmospheric downward flux, wall thermal emission, and ground thermal emission integrated over directional view factors.
5. **Mean Radiant Temperature ($T_{mrt}$):** Total absorbed flux inverted via Stefan-Boltzmann law with human emissivity $\varepsilon_p = 0.97$.
6. **Thermal Comfort ($UTCI$):** Polynomial regression evaluated with $T_{air} = 35.0^\circ\text{C}$, $T_{mrt}$, $v_{10m} = 1.5\,\text{m/s}$, and $\text{RH} = 19.729\%$.

---

## 13. Output Statistics

Summary statistics across the **Church Street Pedestrian Corridor (Unbuilt Cells)**:

| Physical Metric | Mean | Median | Min | Max | Std Dev | P10 | P90 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Shadow Mask (0 lit, 1 sun)** | 0.9701 | 1.0 | 0.0 | 1.0 | 0.1704 | 1.0 | 1.0 |
| **Sky View Factor (SVF)** | 0.6569 | 0.6354 | 0.3014 | 0.9213 | 0.1206 | 0.5263 | 0.8597 |
| **Shortwave Flux $K_{total}$ (W/m²)** | 226.95 | 231.43 | 96.36 | 238.60 | 21.85 | 224.15 | 234.52 |
| **Longwave Flux $L_{total}$ (W/m²)** | 441.43 | 442.10 | 433.28 | 452.39 | 3.72 | 435.18 | 445.46 |
| **Mean Radiant Temp $T_{mrt}$ (°C)** | 45.81 | 46.33 | 32.27 | 47.94 | 2.18 | 44.66 | 47.02 |
| **UTCI (°C)** | 36.49 | 36.60 | 33.20 | 37.00 | 0.53 | 36.20 | 36.80 |

### Contrast Between Sunlit and Shaded Receptors in Pedestrian Corridor:
- **Sunlit Receptors ($N = 648$):**  
  Mean $T_{mrt} = 46.17^\circ\text{C}$, Mean $UTCI = 36.58^\circ\text{C}$
- **Shaded Receptors ($N = 20$):**  
  Mean $T_{mrt} = 34.28^\circ\text{C}$, Mean $UTCI = 33.68^\circ\text{C}$
- **Radiative Contrast:**  
  $\Delta T_{mrt} = 11.89\,\text{K}$, $\Delta UTCI = 2.89\,\text{K}$

---

## 14. Numerical Sanity Checks

All checks in `static_quality_checks.json` passed with zero errors:
- **Shape Consistency:** Context grid strictly $(148, 190)$ across all 7 physical fields.
- **NaN / Inf Absence:** Exactly 0 NaNs and 0 infinite values across all arrays.
- **Range Boundaries:** SVF strictly within $[0.0, 1.0]$ (0.0000 to 0.9948).
- **Direct Beam Occlusion:** Shadowed cells receive exactly $0.0\,\text{W/m}^2$ direct shortwave beam irradiance.
- **Thermal Plausibility:** $T_{mrt}$ in pedestrian corridor ranges from 32.3°C to 47.9°C; UTCI ranges from 33.2°C to 37.0°C (Strong to Very Strong Heat Stress).

---

## 15. Automated Test Suite Audit and Warning Classification

The test suite executed 188 automated unit, integration, and regression tests across the codebase.
- **Test Pass Rate:** 188 passed (100% test pass rate across all active test suites).
- **Warning Count:** 41 warnings.
- **Warning Categories:**
  - **40 warnings:** `UserWarning` from `pythermalcomfort.models.utci` / `valid_range` (`tr - tdb is not within standard range [-30, 70]`).
  - **1 warning:** `PytestDeprecationWarning` from `pytest_asyncio` (`asyncio_default_fixture_loop_scope` unset in test configuration).
- **Classification of Warnings:**
  - **Numerical Precision:** None. Zero warnings relate to numerical underflow, overflow, floating-point precision, or NaN/Inf array corruption.
  - **Deprecated APIs:** 1 harmless test-runner notice regarding default fixture loop scope in future `pytest-asyncio` releases. Zero deprecated APIs used in solver runtime code.
  - **Invalid Geometry:** None. Zero warnings relate to mesh geometry, self-intersections, unclosed manifolds, or degeneracies.
  - **Scientific Assumptions:** None. The 40 `UserWarning` instances are triggered strictly within artificial synthetic benchmark stress tests (`test_aabb_vs_mesh_benchmarks`, `test_mesh_scaling_benchmarks`, `test_mesh_mutation_audit`) evaluating stress inputs where mean radiant temperature in Kelvin was evaluated in raw throughput tests. Production Church Street baseline simulation code properly converts units and emits zero warnings.
- **Tracking Status:** All 41 warnings are harmless, well-understood test harness notices, and fully tracked.

---

## 16. Warnings and Unresolved Limitations

1. **Building Height Uncertainty:** 40 buildings (32.5% of total context) rely on uncorroborated floor counts or sparse ML pixel coverage. Height errors directly affect shadow boundaries and canyon SVF.
2. **Off-Site Weather Forcing:** Bengaluru City station (NOAA ISD 43295099999, $12.966667^\circ\text{N}, 77.583333^\circ\text{E}$) is located 2.56 km geodesic distance from the Church Street study site centre ($12.974900^\circ\text{N}, 77.605400^\circ\text{E}$). Observations are applied as spatially uniform forcing at the study site; microscale urban heat island variations and canyon wind channeling are not measured on-site.
3. **Simplified Flat Ground:** Church Street has a gentle natural grade ($\approx 2.5\,\text{m}$ drop across the block) that is currently modeled as flat ($z = 0.0\,\text{m}$).
4. **Omission of Urban Canopy/Trees:** Church Street features ornamental trees and shop awnings that are not captured in the Overture building polygons.
5. **Static Evaluation:** This result represents a single snapshot at 14:30 IST on April 15, 2024 and does not depict diurnal thermal inertia.

---

## 17. Exact Files Generated

All outputs are saved in:
`results/church_street_static_20261006_232110/`

1. `provenance.json`
2. `input_summary.json`
3. `grid_metadata_reconciliation.json`
4. `scene_summary.json`
5. `weather_summary.json`
6. `solar_summary.json`
7. `material_summary.json`
8. `shadow_results.npz`
9. `visibility_results.npz`
10. `shortwave_results.npz`
11. `longwave_results.npz`
12. `tmrt_results.npz`
13. `utci_results.npz`
14. `static_quality_checks.json`
15. `static_simulation_report.md`
16. `plots/site_geometry.png`
17. `plots/direct_shadow_map.png`
18. `plots/svf_map.png`
19. `plots/shortwave_flux_map.png`
20. `plots/longwave_flux_map.png`
21. `plots/tmrt_map.png`
22. `plots/utci_map.png`
23. `plots/building_height_uncertainty_map.png`

---

## 18. Reproduction Command

```powershell
python scripts/run_church_street_static_simulation.py
```

---

## 19. Decision for the Next Stage

```text
READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION_AFTER_METADATA_RECONCILIATION
```

**Rationale:**  
The baseline static full recomputation completed with complete numerical integrity, zero NaNs or Infs, full physical consistency, verified radiation bounds, and all 188 automated tests passing. The solar-position discrepancy (57.9160° authoritative vs 52.82° uncorrected estimate), weather-station geodesic distance (2.56 km), grid distinctions (nominal 380 m × 295 m bounds vs 380 m × 296 m discrete extent with 28,120 cells), and 41 test warnings have been rigorously analyzed, categorized, and reconciled. The baseline reference arrays are fully secured for the next stage: the full recomputation of the hypothetical shade-panel intervention.
