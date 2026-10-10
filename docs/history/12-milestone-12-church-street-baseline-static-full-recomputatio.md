## 12. Milestone 12: Church Street Baseline Static Full Recomputation & Audit

**Execution Date:** 2026-10-06 / 2026-10-07  
**Artifact Directory:** `results/church_street_static_20261006_232110/`  
**Scientific Framing:**
> “The Church Street baseline is an exploratory static simulation using approved but partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties.”

### 12.1 Phase 0 Preflight Inspection & Grid Metadata Reconciliation

1. **Preprocessing Artifact Hashes Verified:**
   All 9 required files from `results/church_street_preprocessing_20261006_224238/` were cryptographically checked with SHA256:
   - `main_scene_mesh.json`: `6dbaa914e7427445a808daef84a990ce524f64524c2d3293aa0a1da4cca300b6`
   - `shadow_context_mesh.json`: `33c9ca008a6fa20e5155fb54652a7d3f2f31c5d20928c2cd0e1ecc360f47104e`
   - `accepted_height_policy.json`: `b0eab59cd623026bbfb708d742ee1a9480f4b66aed74dc31ff9693c0a0788f87`
   - `coordinate_validation.json`: `33f0e6fe61dcb934c07c8dae34595d9443607271ddf9e0e5c240ff430b7ac62a`
   - `scene_summary.json`: `b884feff98e3d9f2712604f952578ebca6541fdc3d672ab78dd7bc5dbc9fad88`
   - `geometry_validation_report.json`: `669d7977e95f83c6df8ccbc9a9643c5f96d25098eae78b18b655203af2616c5a`
2. **Researcher Sign-Off Confirmation:**
   All 6 gates confirmed `approved` in `data/processed/researcher_signoff.json`.
3. **Pre-Simulation Pytest Status:**
   Full test suite passed at 179/179.
4. **Grid Metadata Reconciliation ([grid_metadata_reconciliation.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_static_20261006_232110/grid_metadata_reconciliation.json)):**
   - Reconciled nominal report text citation of "$380\,\text{m} \times 295\,\text{m} = 28,120\,\text{cells}$" vs analytical $(380 \times 295)/4 = 28,025$.
   - **Finding:** The discrete simulation grid in `shadow_context_mesh.json` is strictly:
     - Origin: $(-85.0, -80.0)\,\text{m}$
     - Extent: $380.0\,\text{m} \times 296.0\,\text{m}$ at $\Delta x = 2.0\,\text{m}$
     - Dimensions: $n_x = 190, n_y = 148$
     - Discrete cell count: $190 \times 148 = \mathbf{28,120}\,\text{cells}$.
     - Formula: $(380.0 \times 296.0) / (2.0^2) = 112,480 / 4 = \mathbf{28,120}\,\text{cells}$ with zero fractional truncation.
   - The citation of "295 m" in the textual summary was an informal rounded description of the domain envelope (analytical buffer height was $286.57\,\text{m}$). The discrete grid generator snapped $n_y$ to 148 rows ($296.0\,\text{m}$) because non-integer cells cannot exist. The actual simulation grid was unaffected.

### 12.2 Phase 1 Input Validation

- **Geometry:** 37 core buildings, 123 context buildings, 2,136 triangles; all 100% watertight, 0 degeneracies, non-negative heights.
- **Coordinates:** EPSG:32643 local Cartesian coordinates relative to UTM origin $(782541.81, 1435736.11, 0.0)\,\text{m}$, grid convergence $\gamma = +0.585366^\circ$.
- **Weather Forcing:** Off-site Bengaluru City station observation: $T_{\text{air}} = 35.0^\circ\text{C}$ ($308.15\,\text{K}$), $T_{\text{dew}} = 8.5^\circ\text{C}$, $\text{RH} = 19.729\%$, wind speed $1.5\,\text{m/s}$ at $90^\circ$ True North.
- **Solar Forcing & Radiation Consistency Check:**
  - NASA POWER 09:00–10:00 UTC hourly interval: $\text{GHI} = 755.97\,\text{W/m}^2$, $\text{DNI} = 728.31\,\text{W/m}^2$, $\text{DHI} = 172.18\,\text{W/m}^2$.
  - Instantaneous sun position at 09:00 UTC: Altitude $\alpha = 57.9160^\circ$, Zenith $\theta_z = 32.0840^\circ$, Azimuth (True North) $= 268.1655^\circ$, Azimuth (Grid North) $= 267.5802^\circ$.
  - Radiation consistency:
    - At 09:00 UTC (instantaneous): $\text{DNI} \cos(\theta_z) + \text{DHI} = 789.26\,\text{W/m}^2$ vs $\text{GHI} = 755.97\,\text{W/m}^2$ ($\Delta = +33.29\,\text{W/m}^2$, $+4.40\%$).
    - At 09:30 UTC (interval midpoint): $\text{DNI} \cos(\theta_{z,mid}) + \text{DHI} = 735.04\,\text{W/m}^2$ ($\Delta = -20.93\,\text{W/m}^2$, $-2.77\%$).
    - Hour-integrated mean: $\text{DNI} \langle\cos(\theta_z)\rangle + \text{DHI} = 733.46\,\text{W/m}^2$ ($\Delta = -22.51\,\text{W/m}^2$, $-2.98\%$).
    - Verified well within normal satellite modeling tolerance ($< 5\%$).
- **Approved Material Assumptions:**
  - `building_wall`: $\alpha = 0.30$, $\varepsilon = 0.90$, $T_{\text{init}} = 35.0^\circ\text{C}$ ($308.15\,\text{K}$).
  - `building_roof`: $\alpha = 0.20$, $\varepsilon = 0.90$, $T_{\text{init}} = 35.0^\circ\text{C}$ ($308.15\,\text{K}$).
  - `ground`: $\alpha = 0.20$, $\varepsilon = 0.95$, $T_{\text{init}} = 35.0^\circ\text{C}$ ($308.15\,\text{K}$).
  - `pavement`: $\alpha = 0.30$, $\varepsilon = 0.95$, $T_{\text{init}} = 35.0^\circ\text{C}$ ($308.15\,\text{K}$).
- **Terrain Policy:** Flat model ground plane $z = 0.0\,\text{m}$. SRTM DEM retained for metadata only.

### 12.3 Phase 2 Static Full Simulation Execution

- **Runner Script:** [`scripts/run_church_street_static_simulation.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/run_church_street_static_simulation.py).
- **Execution Pipeline:**
  1. Direct Shadows: Möller-Trumbore ray casting across 123 triangular meshes ($0.37\,\text{s}$).
  2. Directional Visibility / SVF: 32-azimuth horizon scanning up to $120\,\text{m}$ horizon ($2.81\,\text{s}$).
  3. Shortwave Radiation: 6-directional fluxes on human standing cylinder model ($< 0.01\,\text{s}$).
  4. Longwave Radiation: Clear-sky Prata formulation and directional view factor integration.
  5. Mean Radiant Temperature ($T_{\text{mrt}}$): Stefan-Boltzmann inversion ($\varepsilon_p = 0.97$).
  6. UTCI: Fiala polynomial regression with $T_{\text{air}} = 35.0^\circ\text{C}$, $v = 1.5\,\text{m/s}$, $\text{RH} = 19.729\%$ ($0.45\,\text{s}$).
- **Total Execution Time:** $3.64\,\text{s}$ across 28,120 grid cells.

### 12.4 Numerical Quality Checks & Microclimatic Output Statistics

**Quality Checks Summary ([static_quality_checks.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_static_20261006_232110/static_quality_checks.json)):**
- Status: **PASSED (17/17 automated audit criteria)**
- Array shape: strictly $(148, 190)$ across all 7 physical fields.
- Zero NaNs and zero infinite values across all arrays.
- SVF range: $\min = 0.0000, \max = 0.9948$ (strictly within $[0.0, 1.0]$).
- Direct horizontal beam irradiance on shadowed cells: strictly $0.0\,\text{W/m}^2$.
- $T_{\text{mrt}}$ range: $31.16^\circ\text{C}$ to $50.12^\circ\text{C}$ across unbuilt domain.
- UTCI range: $32.90^\circ\text{C}$ to $37.50^\circ\text{C}$.

**Church Street 12 m Pedestrian Corridor Statistics (668 unbuilt cells):**
- **Shadow Mask:** Mean $0.9701$, Lit receptors: 648 ($97.0\%$), Shaded receptors: 20 ($3.0\%$).
- **Sky View Factor (SVF):** Mean $0.6569 \pm 0.1206$, Range $[0.3014, 0.9213]$, Median $0.6354$.
- **Shortwave Flux $K_{\text{total}}$:** Mean $226.95 \pm 21.85\,\text{W/m}^2$, Range $[96.36, 238.60]\,\text{W/m}^2$.
- **Longwave Flux $L_{\text{total}}$:** Mean $441.43 \pm 3.72\,\text{W/m}^2$, Range $[433.28, 452.39]\,\text{W/m}^2$.
- **Mean Radiant Temperature $T_{\text{mrt}}$:** Mean $45.81 \pm 2.18^\circ\text{C}$, Range $[32.27, 47.94]^\circ\text{C}$.
- **UTCI:** Mean $36.49 \pm 0.53^\circ\text{C}$, Range $[33.20, 37.00]^\circ\text{C}$ (Strong Heat Stress).
- **Sunlit vs Shaded Receptor Contrast:**
  - Sunlit Receptors ($N = 648$): Mean $T_{\text{mrt}} = 46.17^\circ\text{C}$, Mean $\text{UTCI} = 36.58^\circ\text{C}$.
  - Shaded Receptors ($N = 20$): Mean $T_{\text{mrt}} = 34.28^\circ\text{C}$, Mean $\text{UTCI} = 33.68^\circ\text{C}$.
  - Radiative Contrast: $\Delta T_{\text{mrt}} = \mathbf{+11.89\,\text{K}}$, $\Delta \text{UTCI} = \mathbf{+2.89\,\text{K}}$.

### 12.5 Generated Deliverables & Publication Plots

**Directory:** `results/church_street_static_20261006_232110/`

1. `provenance.json`: Execution metadata, git commit, system specs, input hashes.
2. `input_summary.json`: Detailed inputs, boundaries, and forcing parameters.
3. `grid_metadata_reconciliation.json`: Formal derivation and reconciliation of discrete $380\,\text{m} \times 296\,\text{m}$ grid.
4. `scene_summary.json`: Mesh counts, coordinate bounds, pedestrian grid dimensions.
5. `weather_summary.json`: Station observations, dew point conversion, wind vectors.
6. `solar_summary.json`: Solar angles, unit vectors, radiation closure checks.
7. `material_summary.json`: Material classes, albedo, emissivity, initial surface temperatures.
8. `shadow_results.npz`: Compressed arrays of `shadow_mask`, `direct_horizontal_irradiance`, coordinates, masks.
9. `visibility_results.npz`: Compressed arrays of `svf`, coordinates, masks.
10. `shortwave_results.npz`: Compressed arrays of `k_total`, `direct_horizontal`, coordinates, masks.
11. `longwave_results.npz`: Compressed arrays of `l_total`, coordinates, masks.
12. `tmrt_results.npz`: Compressed arrays of `tmrt`, coordinates, masks.
13. `utci_results.npz`: Compressed arrays of `utci`, coordinates, masks.
14. `static_quality_checks.json`: 17 automated physical and numerical integrity checks.
15. `static_simulation_report.md`: Formal 18-section audit report.
16. **Diagnostic Plots (`plots/`):**
    - `site_geometry.png`: 123 building footprints colored by height with site and corridor boundaries.
    - `direct_shadow_map.png`: Binary direct beam illumination map at 14:30 IST sun position.
    - `svf_map.png`: Continuous Sky View Factor map (32 azimuths).
    - `shortwave_flux_map.png`: Total absorbed shortwave flux density $K_{\text{total}}$ on human model.
    - `longwave_flux_map.png`: Total absorbed longwave flux density $L_{\text{total}}$ on human model.
    - `tmrt_map.png`: Continuous Mean Radiant Temperature $T_{\text{mrt}}$ field ($30^\circ\text{C}$ to $75^\circ\text{C}$).
    - `utci_map.png`: Continuous Universal Thermal Climate Index field ($34^\circ\text{C}$ to $46^\circ\text{C}$).
    - `building_height_uncertainty_map.png`: Buildings categorized by Moderate (83), High (29), and Extreme (11) uncertainty tiers.

### 12.6 Unit Testing & Full Regression Status

- **Unit Test Suite:** [`tests/test_church_street_static_simulation.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_church_street_static_simulation.py) (9 comprehensive tests verifying mesh loading, grid reconciliation, solar consistency, NPZ integrity, SVF range, zero direct flux in shadow, sunlit vs shaded thermal contrast, station distance 2.56 km, and updated readiness decision).
- **Regression Result:** **188 passed** (173 baseline + 6 preprocessing + 9 static simulation, 41 warnings, 100% pass rate in $54.51\,\text{s}$).

---

