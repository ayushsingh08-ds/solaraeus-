## 14. Milestone 15: Church Street Overhead Shade-Panel Intervention Full Recomputation & Audit

**Execution Date:** 2026-10-06 / 2026-10-07  
**Artifact Directory:** `results/church_street_shade_full_20261007_001600/`  
**Scientific Framing:**
> “The shade-panel result is an exploratory full-recomputation comparison using real-world building geometry, partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties.”

**Enforced Safe Terminology:**
- “Full-recomputation intervention comparison.”
- “Exploratory real-world geometry case study.”
- “Modeled difference under fixed assumptions.”

### 14.1 Phase 0 Preflight Inspection & Baseline Reference Integrity
- **Frozen Baseline Directory:** `results/church_street_static_20261006_232110/`.
- **Baseline Integrity:** All 11 baseline reference files verified with SHA-256 (0 mismatches).
- **Meteorological & Solar Alignment:** Verified identical inputs between baseline and intervention:
  - Timestamp: `2024-04-15 09:00:00 UTC` (`14:30:00 IST`).
  - Solar angles: Altitude $57.9160^\circ$, Zenith $32.0840^\circ$, Azimuth True North $268.1655^\circ$, Azimuth Grid North $267.5802^\circ$.
  - Station distance: $2.56\,\text{km}$ ($2,561.6\,\text{m}$) southwest of site.
  - Discrete calculation grid: $380.0\,\text{m} \times 296.0\,\text{m}$ at $\Delta x = 2.0\,\text{m}$ ($190 \times 148 = 28,120$ cells).
  - Material assumptions: Walls ($\alpha = 0.30, \varepsilon = 0.90$), Roofs ($\alpha = 0.20, \varepsilon = 0.90$), Ground ($\alpha = 0.20, \varepsilon = 0.95$), Pavement ($\alpha = 0.30, \varepsilon = 0.95$).

### 14.2 Phase 1 Intervention Mesh Validation (`BLR_SHADE_001` / `CANOPY_001`)
- **Dimensions:** Length $6.0\,\text{m}$, Width $3.0\,\text{m}$, Thickness $0.10\,\text{m}$, Footprint Area $18.0\,\text{m}^2$.
- **Elevation:** Underside clearance $z = 3.5\,\text{m}$, Top surface $z = 3.6\,\text{m}$ above flat ground ($z = 0.0\,\text{m}$).
- **Orientation:** Long-axis bearing $103.028^\circ$ True North ($102.443^\circ$ UTM Grid North).
- **Material Assignment:** `SHADE_PANEL_ASSUMED_001` ($\alpha = 0.60, \varepsilon = 0.90$, initial surface temperature $35.0^\circ\text{C} / 308.15\,\text{K}$, opaque, transmissivity $0.0$).
- **Mesh Topology:**
  - Vertices: 8 vertices (4 base at $z = 3.5\,\text{m}$, 4 top at $z = 3.6\,\text{m}$).
  - Triangles: 12 triangles (8 outward wall faces, 2 upward $+Z$ roof faces, 2 downward $-Z$ underside faces).
  - Watertightness: 100% closed 2-manifold (every edge shared by exactly 2 triangles, 0 boundary edges).
  - Degenerate triangles: 0 ($A > 10^{-12}\,\text{m}^2$).
  - Footprint collisions: 0 collisions with the 123 existing building footprints (clearance to nearest wall: $1.751\,\text{m}$).
- Serialized record: `panel_validation.json` (SHA-256 recorded in provenance).

### 14.3 Phase 2 Pure Full Recomputation Execution
- **Pipeline:** Executed independent full recomputations from scratch for both scenes:
  - Baseline scene: 123 buildings ($2,136$ triangles), run time $6.23\,\text{s}$.
  - Intervention scene: 124 meshes (123 buildings + shade panel, $2,148$ triangles), run time $6.04\,\text{s}$.
- **Strict Methodological Constraint:** Zero cache reuse, zero incremental invalidation, zero certificate evaluations. `"incremental_computation_used": false` explicitly validated.

### 14.4 Phase 3 Spatial Disaggregation & Difference Analysis
Evaluated across 4 distinct spatial zones:
1. `all_grid_cells`: Entire $380\,\text{m} \times 296\,\text{m}$ context domain ($28,120$ cells).
2. `main_analysis_cells`: Core study block boundary ($7,225$ cells).
3. `unbuilt_pedestrian_cells`: Main boundary unbuilt receptor domain ($3,837$ cells).
4. `church_street_corridor_cells`: Designated 12 m pedestrian walkway corridor ($668$ cells).

#### Corridor Output Summary (Church Street Corridor Unbuilt Cells, N = 668):
- **Direct Solar Shading:** Exactly **6 discrete grid cells** ($24.0\,\text{m}^2$) cast into direct shadow by the canopy at 14:30 IST.
  - Shaded cell coordinates: $x \in [132.0, 136.0]\,\text{m}, y \in [63.0, 65.0]\,\text{m}$.
  - Geometric consistency: At sun azimuth $267.58^\circ$ Grid North and altitude $57.92^\circ$, direct rays cast shadows East-Northeast from the panel ($x \in [128.5, 135.0]\,\text{m}$), exactly falling on cells $x \in [132.0, 136.0]\,\text{m}$.
- **Thermal Comfort Relief in Shaded Cells:**
  - Peak $T_{\text{mrt}}$ cooling: $\mathbf{-12.62\,\text{K}}$ (at $x=136.0\,\text{m}, y=63.0\,\text{m}$).
  - Peak UTCI relief: $\mathbf{-3.10\,\text{K}}$ (from $36.70^\circ\text{C}$ to $33.60^\circ\text{C}$).
  - Mean thermal relief across shaded cohort: $\Delta T_{\text{mrt}} = -10.03\,\text{K}$, $\Delta \text{UTCI} = -2.43\,\text{K}$.
- **Sky View Factor (SVF):** Decreased by up to **$-0.6441$** directly under the solid overhead panel; 104 cells exhibit $|\Delta \text{SVF}| > 10^{-4}$.
- **Localized Secondary Warming:** Unshaded cells directly adjacent to or under the panel that remain sunlit experience slight local warming (up to $+4.39\,\text{K}$ $T_{\text{mrt}}$, $+1.10\,\text{K}$ UTCI) due to reduced cold sky view factor and thermal longwave emission from the $35.0^\circ\text{C}$ panel underside combined with diffuse reflection from the $\alpha = 0.60$ panel.

### 14.5 Phase 4 Quality Checks & Sanity Verification
- **Status:** **PASSED** (17/17 automated criteria in `quality_checks.json`).
- **Array Shape Parity:** All 12 output arrays strictly $(148, 190)$.
- **NaN / Infinite Values:** Exactly 0 NaNs and 0 infinities across all fields.
- **Physical Boundaries:** SVF strictly in $[0.0, 1.0]$ ($0.0000$ to $0.9948$). Shadow mask strictly binary $\{0.0, 1.0\}$.
- **Configuration Equality:** 100% identical configurations between baseline and intervention.
- **Incremental Flag:** `"incremental_computation_used": false`.

### 14.6 Generated Deliverables & Publication Plots
**Directory:** `results/church_street_shade_full_20261007_001600/` (25 files total)
1. `provenance.json`: Tool versions, Git commit, input file hashes, panel mesh hash, `"incremental_computation_used": false`.
2. `baseline_reference.json`: Baseline directory reference and corridor metrics.
3. `intervention_summary.json`: Intervention geometry, panel specs, timing breakdown, changed cell counts.
4. `panel_validation.json`: Watertightness, normal vectors, dimensions, area, 0 degeneracies.
5. `configuration_comparison.json`: Side-by-side configuration audit confirming equality.
6. `baseline_statistics.json` & `intervention_statistics.json`: 4-domain statistics across all physical fields.
7. `difference_statistics.csv`: Complete tabular difference summary (mean, median, min, max, std, P10, P90, changed counts).
8. `changed_cell_summary.csv`: Cell-by-cell ledger for all 39 cells with $|\Delta T_{\text{mrt}}| > 0.01\,\text{K}$.
9. `quality_checks.json`: 17 numerical and physical sanity checks.
10. `uncertainty_notes.md`: Formal documentation of the 5 major microclimatic uncertainty dimensions.
11. `shade_panel_full_recomputation_report.md`: Comprehensive 16-section scientific evaluation report.
12. **Compressed NPZ Archives (13 files):** `baseline_shadow.npz`, `intervention_shadow.npz`, `baseline_visibility.npz`, `intervention_visibility.npz`, `baseline_shortwave.npz`, `intervention_shortwave.npz`, `baseline_longwave.npz`, `intervention_longwave.npz`, `baseline_tmrt.npz`, `intervention_tmrt.npz`, `baseline_utci.npz`, `intervention_utci.npz`, `difference_fields.npz`.
13. **High-Resolution Plots (`plots/`, 12 files):**
    - `baseline_geometry.png`, `intervention_geometry.png`, `panel_location.png`
    - `baseline_shadow_map.png`, `intervention_shadow_map.png`, `shadow_difference.png`
    - `svf_difference.png`, `shortwave_difference.png`, `longwave_difference.png`
    - `tmrt_difference.png`, `utci_difference.png`, `changed_cells_map.png`

### 14.7 Testing & Full Regression Status
- **New Test Suite:** [`tests/test_church_street_shade_panel_simulation.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_church_street_shade_panel_simulation.py) (7 comprehensive tests verifying mesh construction, configuration equality, pure full recomputation flag, difference arrays, quality checks, diagnostic plot generation, and readiness decision).
- **Regression Result:** **195 passed, 41 warnings** (173 baseline + 6 preprocessing + 9 static simulation + 7 shade panel simulation, 100% pass rate in $112.89\,\text{s}$).

### 14.8 Completion Decision
```text
READY_FOR_SHADE_PANEL_INCREMENTAL_COMPARISON
```
**Rationale:**  
All baseline and intervention configurations match identically except for the panel. The panel mesh geometry is verified watertight and non-colliding. Both simulations were executed as independent full recomputations with zero cache reuse. Output arrays are valid, shape-compatible, free of NaNs/Infs, and exhibit expected physical cooling. All uncertainty sources are documented and bounded. The full test suite passes at 100%. The reference intervention dataset is fully frozen and ready to benchmark the certified incremental update engine in the next stage.

---

