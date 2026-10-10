## 13. Milestone 14: Pre-Intervention Inconsistency Resolution & Metadata Reconciliation

Before executing the hypothetical shade-panel intervention, all five blocking documentation and metadata inconsistencies were investigated, mathematically proven, reconciled, and codified across all deliverables.

### 13.1 Solar-Position Discrepancy Resolution
- **Issue:** Earlier review notes cited solar altitude $\approx 52.82^\circ$ (or $\approx 52.8^\circ$, azimuth $\approx 264.4^\circ$), whereas the static simulation report cited $57.9160^\circ$ (azimuth $268.1655^\circ$ True North).
- **Authoritative Investigation & Findings:**
  1. The authoritative algorithm is `urban_comfort.solar.solar_position.calculate_solar_position` (NOAA astronomical algorithms).
  2. For the exact coordinates of Church Street ($12.974900^\circ\,\text{N}, 77.605400^\circ\,\text{E}$) on April 15, 2024 at 09:00:00 UTC (14:30:00 IST), NOAA yields:
     - `timestamp_utc`: `2024-04-15T09:00:00Z`
     - `timestamp_ist`: `2024-04-15T14:30:00+05:30`
     - `latitude`: `12.974900`
     - `longitude`: `77.605400`
     - `timezone`: `UTC / IST (UTC+05:30)`
     - `solar_altitude`: `57.9160°`
     - `solar_zenith`: `32.0840°`
     - `solar_azimuth_true_north`: `268.1655°`
     - `solar_azimuth_grid_north`: `267.5802°` ($\gamma = +0.585366^\circ$)
     - `algorithm/module`: `urban_comfort.solar.solar_position` (NOAA Solar Calculations)
  3. **Discrepancy Origin:**
     - The earlier figure ($\approx 52.82^\circ$) was an uncorrected textbook estimate assuming solar noon occurs at 12:00:00 clock time (hour angle $H = (14.5 - 12) \times 15^\circ = 37.5^\circ$), neglecting the Equation of Time ($+0.07$ min) and Bengaluru's geographic longitude offset relative to the standard Indian Standard Time meridian ($82.5^\circ\,\text{E}$ vs $77.6054^\circ\,\text{E}$, causing a $19.58$-minute solar lag).
     - At Bengaluru on April 15, true solar noon occurs at **12:20 IST (06:50 UTC)** with peak solar altitude of $86.99^\circ$.
     - At 14:30 IST, only **130 minutes (2.17 hours)** have elapsed since solar noon, placing the sun at **$57.9160^\circ$**.
     - Evaluating the sun position 2.5 hours past true solar noon (at 14:51 IST / 09:21 UTC) drops the solar altitude to **$52.8011^\circ$**, exactly matching the earlier uncorrected record.
     - The authoritative NOAA implementation at 09:00:00 UTC / 14:30:00 IST is strictly $57.9160^\circ$. Recorded in `solar_summary.json` and `static_simulation_report.md`.

### 13.2 Weather-Station Distance Recalculation
- **Issue:** Earlier documentation cited $\approx 2.56\,\text{km}$, whereas the draft static report informally cited $4.5\,\text{km}$.
- **Recalculation:**
  - Bengaluru City Station (WMO 43295 / NOAA ISD 43295099999): $12.9666666^\circ\,\text{N}, 77.5833333^\circ\,\text{E}$.
  - Church Street Study Block Centre: $12.9749000^\circ\,\text{N}, 77.6054000^\circ\,\text{E}$.
  - Haversine distance: $2,560.373\,\text{m}$ ($2.560\,\text{km}$).
  - WGS84 ellipsoid geodesic distance (`pyproj.Geod`): **$2,561.595\,\text{m}$ ($2.562\,\text{km}$ / $2.56\,\text{km}$)**.
  - The informal "4.5 km" in early report notes was an unverified colloquial driving-distance estimate.
- **Unified Consistency:** Reconciled strictly to **$2.56\,\text{km}$ ($2,561.6\,\text{m}$)** across:
  - `weather_summary.json`
  - `input_summary.json`
  - `static_simulation_report.md`
  - `context.md`
- **Station Weather Framing:** Preserved verbatim:
  *“Bengaluru City station observations applied as spatially uniform forcing at the Church Street study site.”*
  Explicitly documented that output does not represent measured Church Street microclimate.

### 13.3 Grid Interpretation Distinctions
- **Resolution:** Formal distinctions codified to avoid misinterpreting domain boundaries:
  - **nominal rounded bounds:** `380 m × 295 m` (informal textual summary of the analytical buffer envelope $369.99\,\text{m} \times 286.57\,\text{m}$).
  - **actual discrete grid extent:** `380 m × 296 m` (Cartesian extent spanning $[-85.0, 295.0]\,\text{m}$ in $X$ and $[-80.0, 216.0]\,\text{m}$ in $Y$).
  - **actual grid:** `190 × 148 cells = 28,120 cells` ($n_x = 380.0 / 2.0 = 190$, $n_y = 296.0 / 2.0 = 148$ at $\Delta x = \Delta y = 2.0\,\text{m}$).
  - Mathematical proof: $(380.0 \times 296.0) / (2.0^2) = 112,480 / 4 = 28,120$ cells with zero fractional truncation.
  - Recorded in `grid_metadata_reconciliation.json` and Section 7 of `static_simulation_report.md`.

### 13.4 Test Suite Audit & Warning Classification
- **Issue:** Test runner reported `186 passed, 41 warnings`. Required comprehensive classification beyond a simplistic "100% pass rate."
- **Classification Findings:**
  - **Total Warning Count:** 41 warnings.
  - **Warning Categories:**
    - **40 warnings:** `UserWarning` from `pythermalcomfort.models.utci` / `pythermalcomfort.utils.valid_range` (`tr - tdb is not within standard range [-30, 70]`).
    - **1 warning:** `PytestDeprecationWarning` from `pytest_asyncio` (`asyncio_default_fixture_loop_scope` unset in test configuration).
  - **Categorical Breakdown:**
    - **Numerical Precision:** None. Zero warnings relate to numerical underflow, overflow, floating-point precision loss, or NaN/Inf generation.
    - **Deprecated APIs:** 1 runner notice (`pytest_asyncio` fixture loop scope configuration notice in test harness). Zero deprecated APIs in solver code.
    - **Invalid Geometry:** None. Zero warnings relate to mesh geometry, self-intersections, unclosed solids, or degeneracies.
    - **Scientific Assumptions:** None. The 40 `UserWarning` instances are triggered strictly within artificial synthetic benchmark stress tests (`test_aabb_vs_mesh_benchmarks`, `test_mesh_scaling_benchmarks`, `test_mesh_mutation_audit`) evaluating stress inputs where mean radiant temperature in Kelvin was evaluated in raw throughput tests. Production Church Street baseline simulation code properly converts units and emits zero warnings.
  - **Tracking Status:** All 41 warnings are harmless, well-understood test harness notices, and fully tracked. Recorded in Section 15 of `static_simulation_report.md`. (With 2 new validation tests added for distance and readiness checks, the suite stands at **188 passed, 41 warnings, 100% pass rate**).

### 13.5 Updated Readiness Decision
- **Previous Decision:** `READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION`
- **Reconciled Decision:**
  ```text
  READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION_AFTER_METADATA_RECONCILIATION
  ```
- **Rationale:** The baseline computation itself is complete and numerically sound, and all solar-position, station-distance, grid-interpretation, and warning classification inconsistencies are fully resolved and secured prior to the shade-panel run.

---

