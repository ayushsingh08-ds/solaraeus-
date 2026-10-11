# Church Street Overhead Shade-Panel Full Recomputation Report

**Execution Timestamp (UTC):** 20261007_001600  
**Intervention Object:** `BLR_SHADE_001` / `CANOPY_001`  
**Execution Pipeline:** Pure Full Recomputation (Zero Incremental Computation, Zero Cache Reuse)  
**Readiness Status:** `READY_FOR_SHADE_PANEL_INCREMENTAL_COMPARISON`

---

## Scientific Qualification

> “The shade-panel result is an exploratory full-recomputation comparison using real-world building geometry, partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties.”

**Mandatory Terminology:**
- “Full-recomputation intervention comparison.”
- “Exploratory real-world geometry case study.”
- “Modeled difference under fixed assumptions.”

**Strict Boundary Definitions:**
- This study constitutes an “Exploratory real-world geometry case study.”
- All figures represent “Modeled difference under fixed assumptions,” not field measurements.
- Do not cite as measured Church Street thermal comfort, official SOLWEIG validation, or survey-accurate urban engineering.

---

## 1. Objective

The objective of this stage is to evaluate the microclimatic impact of introducing a single approved hypothetical overhead shade structure (`CANOPY_001`) into the Church Street pedestrian canyon using **independent full recomputations** of the baseline and intervention scenes. Incremental updates and cache reuse were strictly disabled.

---

## 2. Baseline Scene Description

- **Study Location:** Church Street central/eastern study block, Bengaluru, Karnataka, India (12.974900° N, 77.605400° E).
- **Core Building Footprints:** 37 buildings (28 interior, 9 boundary-intersecting).
- **Shadow Context Footprints:** 123 buildings (75 m metric buffer around main boundary, 2,136 triangles).
- **Receptor Grid:** Discrete Cartesian grid (380.0 m × 296.0 m at Δx = 2.0 m, 190 × 148 = **28,120 cells**).
- **Baseline Directory:** `C:\Users\AYUSH SINGH\Documents\GitHub\solaraeus\results\church_street_static_20261006_232110`.

---

## 3. Approved Shade-Panel Definition

- **Identifier:** `BLR_SHADE_001` (Object `CANOPY_001`).
- **Dimensions:** Length 6.0 m, Width 3.0 m, Thickness 0.10 m, Area 18.0 m².
- **Elevation:** Underside clearance z = 3.5 m, Top surface z = 3.6 m above ground (z = 0.0 m).
- **Orientation:** Long-axis bearing 103.028° True North (102.443° UTM Grid North).
- **Material Properties:** Assumed albedo α = 0.60, emissivity ε = 0.90, initial surface temperature 35.0°C (308.15 K), opaque (transmissivity 0.0).
- **Structural Framing:** Support columns omitted; non-structural geometric comparison.

---

## 4. Panel Mesh Validation

- **Mesh Construction:** Watertight 3D rectangular box mesh (`TriangleMesh`).
- **Vertex Count:** 8 vertices (4 base at z = 3.5 m, 4 top at z = 3.6 m).
- **Triangle Count:** 12 triangles (8 outward-pointing wall faces, 2 upward +Z roof faces, 2 downward -Z underside faces).
- **Watertightness:** Closed 2-manifold (every edge shared by exactly 2 triangles, 0 boundary edges).
- **Degeneracies:** 0 degenerate triangles (area > 1e-12 m²).
- **Collision Check:** 0 collisions with existing building footprints (clearance to nearest wall: 1.751 m).

---

## 5. Input and Provenance Summary

- **Execution Platform:** Python 3.12.6 on Windows 11.
- **Baseline Git Commit:** `487f275f6d146d69e8288d4ffebf5d330c975ef9`.
- **Incremental Computation Used:** **`false`** (both baseline and intervention evaluated via pure full recomputation).
- **Coordinate Reference System:** EPSG:32643 (UTM Zone 43N) relative to origin (782,541.81, 1,435,736.11, 0.0) m, grid convergence γ = +0.585366°.

---

## 6. Solar and Weather Forcing

- **Timestamp:** April 15, 2024 at 09:00:00 UTC (14:30:00 IST).
- **Solar Position (NOAA Authoritative):**
  - Altitude: 57.9160° (Zenith: 32.0840°)
  - Azimuth True North: 268.1655°
  - Azimuth Grid North: 267.5802°
- **Solar Irradiance (NASA POWER):** GHI = 755.97 W/m², DNI = 728.31 W/m², DHI = 172.18 W/m².
- **Weather Forcing (Bengaluru City Station ISD 43295099999):**
  - Distance to Site: **2.56 km**
  - Air Temperature: 35.0°C (308.15 K)
  - Relative Humidity: 19.729% (Dew point 8.5°C)
  - Wind Speed: 1.5 m/s from 90° True North
  - Framing: *“Bengaluru City station observations applied as spatially uniform forcing at the Church Street study site.”*

---

## 7. Full-Recomputation Method

1. **Independent Solves:** Baseline (123 meshes) and Intervention (124 meshes) were solved independently from scratch.
2. **Ray-Casting Shadows:** Vectorized Möller–Trumbore ray casting across all triangular meshes.
3. **Sky View Factor:** 32-azimuth horizon scanning over the uppermost envelope DSM up to 120 m horizon radius.
4. **Radiative Balance:** 6-directional shortwave and longwave integration on a standing human cylinder model (f_up = 0.06, f_down = 0.06, f_side = 0.22).
5. **Tmrt & UTCI:** Stefan-Boltzmann inversion (ε_p = 0.97) followed by UTCI regression polynomial.

---

## 8. Baseline Statistics (Church Street Corridor Unbuilt Cells, N = 668)

| Metric | Mean | Median | Min | Max | Std Dev |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shadow Mask (1=Sun, 0=Shade)** | 0.9701 | 1.0 | 0.0 | 1.0 | 0.1704 |
| **Sky View Factor (SVF)** | 0.6569 | 0.6354 | 0.3014 | 0.9213 | 0.1206 |
| **Shortwave Flux K_total (W/m²)** | 226.95 | 231.43 | 96.36 | 238.60 | 21.85 |
| **Longwave Flux L_total (W/m²)** | 441.43 | 442.10 | 433.28 | 452.39 | 3.72 |
| **Mean Radiant Temp Tmrt (°C)** | 45.81 | 46.33 | 32.27 | 47.94 | 2.18 |
| **UTCI (°C)** | 36.49 | 36.60 | 33.20 | 37.00 | 0.53 |

---

## 9. Intervention Statistics (Church Street Corridor Unbuilt Cells, N = 668)

| Metric | Mean | Median | Min | Max | Std Dev |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shadow Mask (1=Sun, 0=Shade)** | 0.9626 | 1.0 | 0.0 | 1.0 | 0.1898 |
| **Sky View Factor (SVF)** | 0.6509 | 0.6329 | 0.0000 | 0.9213 | 0.1357 |
| **Shortwave Flux K_total (W/m²)** | 226.15 | 231.43 | 96.36 | 251.08 | 23.90 |
| **Longwave Flux L_total (W/m²)** | 441.62 | 442.17 | 433.28 | 461.69 | 4.18 |
| **Mean Radiant Temp Tmrt (°C)** | 45.76 | 46.33 | 32.27 | 50.68 | 2.33 |
| **UTCI (°C)** | 36.48 | 36.60 | 33.20 | 37.70 | 0.57 |

---

## 10. Field-by-Field Difference Analysis

Differences are evaluated as: Δ = Intervention - Baseline.

| Physical Field | Corridor Min Diff | Corridor Max Diff | Domain-wide Changed Cells | Physical Mechanism |
| :--- | :--- | :--- | :---: | :--- |
| **Shadow Mask** | -1.0 | 0.0 | 6 | Direct beam obstruction by the elevated canopy. |
| **Sky View Factor** | -0.6441 | 0.0000 | 238 | Obstruction of upper sky hemisphere by solid panel. |
| **Direct Shortwave** | -617.90 W/m² | 0.00 W/m² | 6 | Complete occlusion of direct solar beam in shadow. |
| **Total Shortwave** | -129.61 W/m² | +19.78 W/m² | 39 | Direct beam loss vs diffuse reflection from α = 0.60 panel. |
| **Total Longwave** | 0.00 W/m² | +19.86 W/m² | 238 | Replacement of cool sky emission with 35°C panel emission. |
| **Mean Radiant Temp** | **-12.62 K** | +4.39 K | 39 | Sharp cooling in direct shadow; slight warming in sunlit unshaded cells under panel. |
| **UTCI** | **-3.10 K** | +1.10 K | 39 | Significant thermal stress reduction under panel. |

---

## 11. Pedestrian-Area Results & Corridor Impact

- **Direct Shading Extent:** Exactly **6 discrete grid cells** (24 m²) are cast into new direct shadow at 14:30 IST.
- **Shadow Geometry:** Sun azimuth of 267.58° Grid North casts the shadow towards local East-Northeast (x in [132.0, 136.0] m, y in [63.0, 65.0] m).
- **Peak Shaded Cell Cooling:**
  - Receptor at (x = 136.0, y = 63.0) m: ΔTmrt = **-12.62 K**, ΔUTCI = **-3.10 K**.
  - Receptor at (x = 136.0, y = 65.0) m: ΔTmrt = **-12.28 K**, ΔUTCI = **-3.00 K**.
  - Average shaded cell thermal relief: ΔTmrt = -10.03 K, ΔUTCI = -2.43 K.
- **Localized Secondary Warming:** Unshaded cells directly under or adjacent to the panel that remain illuminated experience modest local warming (up to +4.39 K Tmrt) due to trapped thermal radiation emitted from the 35°C panel underside and shortwave reflection.

---

## 12. Quality Checks Summary

All checks in `quality_checks.json` passed with zero errors:
- **Array Shape Equality:** Both baseline and intervention strictly (148, 190) across all fields.
- **NaN / Infinite Values:** Exactly 0 NaNs and 0 infinite values.
- **SVF Range:** Valid within [0.0000, 0.9948].
- **Shadow Mask:** Valid binary values in [0.0, 1.0].
- **Configuration Parity:** Baseline and intervention inputs match identically except for the panel.
- **Incremental Computation:** `"incremental_computation_used": false`.

---

## 13. Uncertainty and Limitations

See `uncertainty_notes.md` for complete discussion. Key factors:
1. 40 context buildings have high/extreme height uncertainty.
2. Station weather forcing is off-site (2.56 km).
3. Single timestep (14:30 IST) does not represent diurnal performance.
4. Support columns and street trees are omitted.
5. Surfaces are assumed isothermal at 35.0°C.

---

## 14. Unsupported Claims

The following claims are **explicitly unsupported**:
- "Church Street pedestrians will experience 3.1°C cooler comfort." (Unvalidated off-site forcing, omitted microclimate physics).
- "The shade panel design is structurally feasible." (Support posts were omitted).
- "SOLWEIG officially validates this model." (Compatibility check only, no official cross-validation run).
- "Survey-accurate urban comfort mapping." (Building heights are estimated, terrain is flat).

---

## 15. Reproduction Command

```powershell
python scripts/run_church_street_shade_panel_simulation.py
```

---

## 16. Decision for the Next Stage

```text
READY_FOR_SHADE_PANEL_INCREMENTAL_COMPARISON
```

**Rationale:**  
1. Baseline and intervention configurations match identically except for the shade panel.
2. Panel geometry is fully validated, watertight, and non-colliding.
3. Both simulations were executed as independent full recomputations with zero cache reuse.
4. All output arrays are valid, shape-compatible, and free of NaNs/Infs.
5. The direct shadow and radiative response behave with strict physical consistency.
6. All sources of uncertainty are documented and bounded.
7. Quality checks and test suite pass completely.
The reference intervention dataset is fully secured to benchmark the certified incremental update engine in the next stage.
