# Static Full Recomputation Audit Report: Church Street Baseline Scene

**Execution Timestamp (UTC):** `20261006_232110`  
**Run Mode:** Static Full Recomputation (Single Timestep, Scratch Evaluation)  
**Scene Scope:** Baseline Scene (37 Core Buildings, 123 Shadow Context Buildings)  
**Readiness Decision:** `READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION`  

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

**Reconciliation Finding:**
The discrete simulation grid stored in `shadow_context_mesh.json` is strictly:
- Extent: $380.0\,\text{m} \times 296.0\,\text{m}$
- Cell Resolution: $\Delta x = \Delta y = 2.0\,\text{m}$
- Origin: $(-85.0, -80.0)\,\text{m}$
- Columns ($n_x$): $380.0 / 2.0 = 190$
- Rows ($n_y$): $296.0 / 2.0 = 148$
- Total Cells: $190 \times 148 = 28,120$ cells.
- Formula: $(380.0 \times 296.0) / (2.0^2) = 112,480 / 4 = 28,120$ cells with zero fractional truncation.

The citation of "295 m" in the textual summary was a rounded nominal description of the domain extent (analytical buffer height was $286.57\,\text{m}$). Because $295 / 2 = 147.5$ cells is fractional, the grid generator snapped $n_y$ to 148 rows ($296.0\,\text{m}$). The actual simulation grid was unaffected. Recorded in `grid_metadata_reconciliation.json`.

---

## 8. Weather Forcing

**Label:** *“Bengaluru City station observations applied as spatially uniform forcing at the Church Street study site.”*  
*(Off-site observation; not on-site microclimate measurement).*

- **Station:** Bengaluru City Station (NOAA ISD 43295099999)
- **Date & Time:** April 15, 2024 at 09:00 UTC / 14:30 IST
- **Air Temperature:** $35.0^\circ\text{C}$ ($308.15\,\text{K}$)
- **Dew Point:** $8.5^\circ\text{C}$
- **Relative Humidity:** $19.729\%$ (derived from air temperature and dew point)
- **Wind Speed:** $1.5\,\text{m/s}$ at pedestrian height
- **Wind Direction:** $90.0^\circ$ (from the east)

---

## 9. Solar Forcing and Time Convention

- **Source:** NASA POWER hourly solar radiation estimates for April 15, 2024.
- **Hourly Energy Interval:** 09:00–10:00 UTC (14:30–15:30 IST)
  - Global Horizontal Irradiance (GHI): $755.97\,\text{W/m}^2$
  - Direct Normal Irradiance (DNI): $728.31\,\text{W/m}^2$
  - Diffuse Horizontal Irradiance (DHI): $172.18\,\text{W/m}^2$
- **Sun Position (NOAA Solar Algorithm at 09:00 UTC):**
  - Altitude: $57.9160^\circ$
  - Zenith: $32.0840^\circ$
  - Azimuth (True North): $268.1655^\circ$
  - Azimuth (Grid North): $267.5802^\circ$
  - Unit Sun Vector (East, North, Up): $(-0.5309, -0.0170, 0.8473)$

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

## 15. Warnings and Unresolved Limitations

1. **Building Height Uncertainty:** 40 buildings (32.5% of total context) rely on uncorroborated floor counts or sparse ML pixel coverage. Height errors directly affect shadow boundaries and canyon SVF.
2. **Off-Site Weather Forcing:** Bengaluru City station is approximately 4.5 km from Church Street; local urban heat island and canyon wind channeling are not measured.
3. **Simplified Flat Ground:** Church Street has a gentle natural grade ($\approx 2.5\,\text{m}$ drop across the block) that is currently modeled as flat ($z = 0.0\,\text{m}$).
4. **Omission of Urban Canopy/Trees:** Church Street features ornamental trees and shop awnings that are not captured in the Overture building polygons.
5. **Static Evaluation:** This result represents a single snapshot at 14:30 IST on April 15, 2024 and does not depict diurnal thermal inertia.

---

## 16. Exact Files Generated

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

## 17. Reproduction Command

```powershell
python scripts/run_church_street_static_simulation.py
```

---

## 18. Decision for the Next Stage

```text
READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION
```

**Rationale:**  
The baseline static full recomputation completed with complete numerical integrity, zero NaNs or Infs, full physical consistency, verified radiation bounds, and all 179 pre-simulation tests passing. The baseline reference arrays are fully secured for the next stage: the full recomputation of the hypothetical shade-panel intervention.
