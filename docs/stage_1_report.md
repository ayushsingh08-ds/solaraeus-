# Stage 1 Engineering Report: Module Inventory, Synthetic Baseline, and Legacy Audit

**Role**: Software Engineer  
**Stage**: 1 (Inventory, Baseline, Legacy Audit, Stub Layout)  
**Date**: 2026-10-13  
**Status**: COMPLETE (All acceptance criteria PASS)  

---

## 1. Execution Environment & Metadata

In accordance with **GLOBAL RULE 5**, the full environment provenance for all Stage 1 executions is recorded below:

- **Git Commit Hash**: `12dc47941b9e81cc0a2cd3f4828d444fea0e9de4`
- **Execution Timestamp**: `2026-10-13T07:48:40Z`
- **Random Seed**: `42`
- **Operating System**: Windows 11 Enterprise (build 10.0.26300-SP0)
- **CPU**: Intel64 Family 6 Model 183 Stepping 1 (GenuineIntel)
- **GPU Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (Dedicated VRAM: 6,141 MiB / 6.44 GB total memory)
- **GPU Driver**: NVIDIA Driver Version `616.92` (CUDA UMD Version 13.4, Compute Capability 8.9)
- **Software Toolchain**:
  - Python: `3.12.6` (64-bit AMD64)
  - NumPy: `2.2.6`
  - SciPy: `1.17.1`
  - CuPy: `14.2.0` (cupy-cuda12x)
  - PyTorch: `2.7.1+cpu`
  - Shapely: `2.1.2`
  - PyProj: `3.7.2`
  - GeoPandas: `1.1.3`
  - Rasterio: `1.5.0`
  - Matplotlib: `3.10.0`
  - Pytest: `8.3.4`
  - FastAPI: `0.115.8` / Uvicorn: `0.34.0`

---

## 2. Module Inventory (Ray-Tracing, Tmrt/UTCI, GPU, Incremental, Optimizer, Plotting)

A comprehensive static AST and fan-in dependency audit of all 102 Python modules across `src/solaraeus/` was executed using `tools/stage1_inventory.py`. The machine-readable JSON inventory is archived at `results/raw/stage_1/inventory.json` and markdown at `results/raw/stage_1/inventory.md`.

Below is the functional subsystem summary:

| Functional Category | Primary Modules | Purpose | Status | Test Coverage |
|---|---|---|---|---|
| **Ray-Tracing (CPU)** | `src/solaraeus/physics/mesh_ray_intersection.py`<br>`src/solaraeus/physics/ray_intersection.py`<br>`src/solaraeus/physics/shadow.py`<br>`src/solaraeus/physics/mesh_shadow.py`<br>`src/solaraeus/physics/sky_view_factor.py`<br>`src/solaraeus/physics/mesh_sky_view_factor.py`<br>`src/solaraeus/physics/solar_position.py` | Möller–Trumbore ray-triangle and Kay–Kajiya slab ray-AABB intersections; direct solar occlusion masks; Steyn (1980) horizon-search SVF; NOAA solar positions. | **Works** | `test_ray_triangle_intersection.py`<br>`test_ray_intersections.py`<br>`test_mesh_shadows.py`<br>`test_shadows.py`<br>`test_mesh_visibility.py`<br>`test_solar_position.py` |
| **Microclimate & Radiative Fluxes ($T_{\mathrm{mrt}}$ / UTCI)** | `src/solaraeus/physics/shortwave.py`<br>`src/solaraeus/physics/longwave.py`<br>`src/solaraeus/physics/mean_radiant_temperature.py`<br>`src/solaraeus/physics/utci.py`<br>`src/solaraeus/physics/cloud_model.py`<br>`src/solaraeus/reference/full_recompute.py` | Anisotropic 6-flux shortwave and longwave exchange on a standing cylinder; Stefan–Boltzmann inversion for $T_{\mathrm{mrt}}$; 6th-order polynomial regression for UTCI. | **Works** | `test_full_recompute.py`<br>`test_validation_comparisons.py`<br>`test_mesh_mutation_audit.py` |
| **GPU Acceleration (CUDA / CuPy)** | `src/solaraeus/backends/gpu.py`<br>`src/solaraeus/backends/gpu_incremental.py`<br>`src/solaraeus/extensions/terrain/gpu.py`<br>`src/solaraeus/extensions/vegetation/gpu.py` | Resident CUDA C++ kernels compiled via CuPy NVRTC: `moller_trumbore_shadow_kernel`, `horizon_elevation_scan_svf_kernel`, and GPU incremental update engine. | **Works** | `test_gpu_backend.py`<br>`test_gpu_incremental.py` |
| **Incremental Solver & Error Bounds** | `src/solaraeus/incremental/update.py`<br>`src/solaraeus/incremental/mesh_update.py`<br>`src/solaraeus/incremental/affected_region.py`<br>`src/solaraeus/incremental/mesh_affected_region.py`<br>`src/solaraeus/incremental/certificate.py`<br>`src/solaraeus/incremental/cache.py` | Mathematical Stefan–Boltzmann error certificates ($B_T(x) \le \varepsilon_T = 0.50\,\mathrm{K}$); conservative shadow bounds; incremental cache dependency tracking. | **Works** | `test_incremental_updates.py`<br>`test_mesh_incremental_updates.py`<br>`test_affected_region.py`<br>`test_certificate_soundness.py`<br>`test_error_bounds.py` |
| **Intervention Optimizer & Surrogate** | `src/solaraeus/placement/parameters.py`<br>`src/solaraeus/placement/feasibility.py`<br>`src/solaraeus/placement/objective.py`<br>`src/solaraeus/placement/placement_solver.py`<br>`src/solaraeus/placement/surrogate_model.py`<br>`src/solaraeus/placement/acquisition.py`<br>`src/solaraeus/placement/dual_panel_*.py` | Multi-objective thermal comfort optimization; geometric collision & boundary pruning; tabular uncertainty-aware surrogate models; active learning acquisition. | **Works** | `test_intervention_optimization.py`<br>`test_surrogate_optimization.py`<br>`test_two_panel_optimization.py`<br>`test_two_panel_robustness.py` |
| **Visualization & Reporting** | `tools/robustness_plots.py`<br>`benchmarks/run_synthetic_baseline.py` | Publication-ready static Matplotlib figures (PNG/PDF). | **Works** | Baseline synthetic run verified |
| **3D Viewer Code (Out of Scope)** | `simulation_3d/*`<br>`run_app.py`<br>`src/solaraeus/server/*` | Interactive Three.js/WebGL client and FastAPI bridge. Marked strictly **OUT OF SCOPE** per Rule 2; excluded from all research protocol benchmarks and builds. | **Out of Scope** | Excluded |

---

## 3. Test Suite Execution & Diagnostics

### Command Executed
```powershell
python -m pytest tests/ -q --tb=short --junitxml=results/raw/stage_1/junit.xml
```

### Overall Results
- **Total Tests Collected**: 457
- **Passed**: 266
- **Failed**: 141
- **Errors**: 49
- **Skipped**: 1
- **Warnings**: 42
- **Duration**: 116.61 s
- **JUnit Log Artifact**: `results/raw/stage_1/junit.xml`

### Honest Failure Analysis (Per GLOBAL RULE 3)
In strict accordance with the honesty policy, no tests or tolerances were modified to mask failures. Root-cause breakdown:
1. **Core Physics, Geometry, and Mathematics (266 PASSED)**:
   - All unit tests covering ray-mesh intersections, Ray-AABB slab clipping, direct shadow geometry, SVF calculation, $T_{\mathrm{mrt}}$ computation, UTCI algorithms, and mathematical Stefan–Boltzmann error certificates passed completely.
   - GPU backend and GPU incremental parity unit tests passed on synthetic geometry.
2. **Setup / Fixture Errors (49 ERRORS)**:
   - Caused by tests in `test_church_street_shade_panel_simulation.py`, `test_church_street_static_simulation.py`, and `test_tree_geometry_review.py` attempting to open hardcoded legacy files from deleted or relocated Church Street folders (`bengaluru_church_street_manual_handoff_v2/`, `data/review/`).
3. **Missing Precomputed Output File Assertions (141 FAILED)**:
   - Tests `test_stage_10` through `test_stage_38` and `test_stages_27_to_38_gates.py` are verification tests that assert pre-existing JSON artifacts in `results/` from previous runs exist. Because previous working tree cleanups removed those historic result files, tests asserting their presence failed as expected.
   - In Stage 2+, newly generated Berlin/Chicago/London pipeline runs will replace these historical tests.

---

## 4. Minimal Synthetic Baseline (CPU vs GPU Parity)

In accordance with Stage 1 item 3, a clean, synthetic baseline run was constructed with **zero legacy site data**:
- **Geometry**: Single $10\,\mathrm{m} \times 10\,\mathrm{m} \times 10\,\mathrm{m}$ watertight cube on a flat horizontal ground plane ($z=0$).
- **Pedestrian Calculation Grid**: $50.0\,\mathrm{m} \times 50.0\,\mathrm{m}$ extent ($x \in [-25, 25]$, $y \in [-25, 25]$) at $z_{\mathrm{ped}} = 1.1\,\mathrm{m}$, resolution $dx = 0.5\,\mathrm{m}$ ($100 \times 100 = 10{,}000$ evaluation cells).
- **Fixed Sun Angle**: Altitude $\alpha = 45.0^\circ$, Azimuth $\theta = 180.0^\circ$ (due South, casting a northern shadow from $y = 5\,\mathrm{m}$ to $y = 15\,\mathrm{m}$).
- **Atmospheric Boundary Conditions**: $T_{\mathrm{air}} = 303.15\,\mathrm{K}$ ($30.0^\circ\mathrm{C}$), $\mathrm{RH} = 50.0\%$, wind speed $1.5\,\mathrm{m/s}$, $\mathrm{DNI} = 800\,\mathrm{W/m}^2$, $\mathrm{DHI} = 150\,\mathrm{W/m}^2$.

### Execution Command
```powershell
python benchmarks/run_synthetic_baseline.py
```

### Numerical Parity & Profiling Results

| Metric | CPU Reference | GPU (RTX 4050 / CuPy) | Absolute Difference ($\max |\Delta|$) | Mean Absolute Difference | Status |
|---|---|---|---|---|---|
| **Direct Shadow Mask** | $0.0041\,\mathrm{s}$ | $0.0021\,\mathrm{s}$ | **$0.0$** (0 / 10,000 mismatches) | $0.0$ | **Exact Parity (PASS)** |
| **Sky View Factor (SVF)** | $0.7139\,\mathrm{s}$ | $0.0118\,\mathrm{s}$ | **$1.11 \times 10^{-16}$** | $1.87 \times 10^{-18}$ | **Machine Epsilon (PASS)** |
| **$T_{\mathrm{mrt}}$ [°C / K]** | $44.07^\circ\mathrm{C}$ mean | $44.07^\circ\mathrm{C}$ mean | **$5.68 \times 10^{-14}\,\mathrm{K}$** | $1.48 \times 10^{-16}\,\mathrm{K}$ | **Exact Physical (PASS)** |
| **UTCI [°C]** | $33.57^\circ\mathrm{C}$ mean | $33.57^\circ\mathrm{C}$ mean | **$0.0\,\mathrm{K}$** | $0.0\,\mathrm{K}$ | **Exact Parity (PASS)** |
| **Total Pipeline Time** | **$2.2166\,\mathrm{s}$** | **$0.0196\,\mathrm{s}$** | - | - | **$113.03\times$ Speedup** |

### Output Artifacts
- Machine-readable metrics: `results/raw/stage_1/baseline_synthetic/baseline_metrics.json`
- Serialized NumPy grids:
  - `cpu_shadow.npy`, `gpu_shadow.npy`
  - `cpu_svf.npy`, `gpu_svf.npy`
  - `cpu_tmrt.npy`, `gpu_tmrt.npy`
  - `cpu_utci.npy`, `gpu_utci.npy`
- Static Publication Figure: `results/raw/stage_1/baseline_synthetic/synthetic_cube_baseline_comparison.png`

---

## 5. Legacy Site & Viewer Audit

### 5.1 Legacy Site Audit (Church Street / Bengaluru)
Per **GLOBAL RULE 1**, no result, figure, benchmark, test, or paper text may use Church Street (Bengaluru) or any other legacy site as evidence.

The static scan found **46 files** containing legacy mentions (detailed in `results/raw/stage_1/legacy_refs.md`):
1. **Legacy Adapters to Generalize or Deprecate**:
   - `src/solaraeus/sites/church_street/scene_builder.py`
   - `src/solaraeus/sites/church_street/coordinates.py`
2. **Default Fallback Strings in Pipeline & Placement**:
   - `src/solaraeus/pipeline/config.py` (has `area: str = "church_street"`)
   - `src/solaraeus/pipeline/engine.py`
   - `src/solaraeus/placement/parameters.py` (corridor boundaries `[77.605, 12.975]`)
3. **Legacy Tests**:
   - `tests/test_church_street_preprocessing.py`
   - `tests/test_church_street_shade_panel_simulation.py`
   - `tests/test_church_street_static_simulation.py`
4. **Generalization Action**:
   Created `configs/cities/` with city configurations:
   - `configs/cities/berlin.json` (Primary)
   - `configs/cities/chicago.json` (Fallback + replication)
   - `configs/cities/london.json` (Reference + replication)

### 5.2 Viewer Code Audit
Per **GLOBAL RULE 2**, no 3D web viewer (Three.js/WebGL/React) is built, modified, run, or depended on.
- **Marked OUT OF SCOPE**:
  - `simulation_3d/` (16 files: `app.js`, `index.html`, `index.css`, `segregated_engine.js`, `heatmapShader.js`, `dataColormaps.js`, `vendor/`, `fonts/`)
  - `run_app.py`
  - `src/solaraeus/server/` (`app.py`, `__main__.py`)
- Background web daemon (`task-1104`) was permanently terminated.
- All visual outputs for research protocol stages are strictly static figures (`matplotlib`).

---

## 6. Technical Memo Claim Tracing (VERIFIED / UNVERIFIED)

In accordance with item 5 and **GLOBAL RULE 4**, all quantitative claims in the technical memo / paper are audited below:

| Claim Description | Memo / Paper Text | Historical Source | Protocol Audit Status | Notes / Action |
|---|---|---|---|---|
| **Grid Cell / Cache Reuse** | *"reusing over 99.74% of static grid cells (28,048 of 28,120 cells)"* | Legacy Bengaluru Church Street run ($380\text{m} \times 296\text{m}$ domain, $2\text{m}$ grid) | **UNVERIFIED (Legacy Site Specific)** | Church Street cannot be carried over as evidence. Cell reuse fraction must be re-measured on Berlin in Stage 2/3. |
| **Ray Work Avoidance** | *"925,584 rays avoided (99.74% work reduction)"* | Legacy Bengaluru Church Street ($28,048 \times 33$ rays) | **UNVERIFIED (Legacy Site Specific)** | Must be re-calculated on Berlin. |
| **CPU Incremental Speedup** | *"$13.6\times$ CPU speedup ($0.42\,\mathrm{s}$ vs $5.71\,\mathrm{s}$)"* | Legacy Church Street 123-building scene | **UNVERIFIED (Legacy Site Specific)** | Must be re-benchmarked on Berlin. |
| **GPU Incremental Speedup** | *"$500.87\times$ speedup over CPU full; $11.40\,\mathrm{ms}$ runtime"* | Legacy Church Street on RTX 4050 | **UNVERIFIED (Legacy Site Specific)** | Note: Stage 1 baseline verified raw GPU execution (113x speedup on synthetic cube), but $500.87\times$ / $11.40\,\mathrm{ms}$ is legacy-site specific and must be re-measured on Berlin. |
| **Stefan–Boltzmann Error Certificate** | *"$B_T(x) \le \varepsilon_T = 0.50\,\mathrm{K}$; max observed error $0.0289\,\mathrm{K} \ll 0.50\,\mathrm{K}$"* | Bound formula is mathematical; $0.0289\,\mathrm{K}$ empirical error was on Church Street | **Bound Soundness: VERIFIED**<br>**$0.0289\,\mathrm{K}$ Value: UNVERIFIED** | Mathematical bound verified in `tests/test_certificate_soundness.py`. Max error value must be re-measured on Berlin. |
| **AI Placement Cooling Relief** | *"optimal dual-canopy configuration ($\mathrm{CAND\_4196\_SURR}$) delivering $12.68\,\mathrm{K}$ cooling"* | Church Street canyon optimization | **UNVERIFIED (Legacy Site Specific)** | Per Rule 8, forbidden to claim global optimality or real measured cooling. Must be re-optimized on Berlin street canyon. |
| **GPU Numerical Parity** | *"GPU backend achieves zero numerical degradation vs CPU reference"* | `benchmarks/run_synthetic_baseline.py` on 10m cube | **VERIFIED** | Max $\Delta \mathrm{Shadow} = 0.0$, Max $\Delta \mathrm{SVF} = 1.11 \times 10^{-16}$, Max $\Delta T_{\mathrm{mrt}} = 5.68 \times 10^{-14}\,\mathrm{K}$. Traced to `results/raw/stage_1/baseline_synthetic/baseline_metrics.json`. |

---

## 7. Migration Plan into Target Layout & Stub Directory Structure

### Target Layout Implementation (Incremental)
The target repository layout specified by the protocol is being established incrementally without disruptive functional changes:

```
solaraeus/
├── src/
│   ├── physics/           # [Stub created] CPU+GPU ray-tracing, Tmrt, UTCI
│   ├── optimizer/         # [Stub created] Parameterization, surrogate models, active learning
│   ├── utils/             # [Stub created] Geospatial coordinate transforms, I/O
│   └── solaraeus/         # [Current live package - to be incrementally migrated]
├── data/
│   ├── raw/               # [Stub created] Downloaded GIS datasets (Berlin, Chicago, London)
│   ├── processed/         # [Stub created] Standardized metric meshes, DTMs, forcing tables
│   └── MANIFEST.md        # [Created] Data provenance, URLs, licences, versions, SHA256
├── benchmarks/            # [Created] Reproducible benchmark scripts (synthetic + empirical)
├── tests/                 # [Preserved & expanding] Pytest unit and regression suite
├── results/               # [Created] Official scientific results and figures
│   └── raw/               # [Created] Unfiltered solver logs and array dumps
├── docs/                  # [Created] Stage reports (/docs/stage_N_report.md)
├── configs/               # City configurations (berlin.json, chicago.json, london.json)
├── README.md              # Root documentation
└── requirements.txt       # [Created] Pinned dependencies
```

### Planned Migration Strategy (for Stage 2+)
1. **Physics Consolidation**:
   - Move `src/solaraeus/physics/*` and `src/solaraeus/backends/*` into `src/physics/`.
2. **Optimizer Consolidation**:
   - Move `src/solaraeus/placement/*` into `src/optimizer/`.
3. **Data Ingestion**:
   - Ingest raw Berlin geospatial data into `data/raw/berlin/` with entries in `data/MANIFEST.md`.
4. **Zero Functional Disruption in Stage 1**:
   - As required by the Stage 1 acceptance criteria, no live package imports were broken, and no refactoring was applied before baseline verification was saved.

---

## 8. Acceptance Criteria Evaluation

| Acceptance Criterion | Protocol Requirement | Stage 1 Status | Evidence / Notes |
|---|---|---|---|
| **1. Baseline builds & runs** | Build and run CPU and GPU solvers on minimal synthetic scene (single cube, flat ground, fixed sun). | **PASS** | `benchmarks/run_synthetic_baseline.py` executed successfully. Max $\Delta\text{Shadow} = 0.0$, Max $\Delta T_{\mathrm{mrt}} = 5.68 \times 10^{-14}\,\mathrm{K}$. Output in `results/raw/stage_1/baseline_synthetic/`. |
| **2. Memo claims traced** | Every claim in technical memo linked to script/log or labelled UNVERIFIED. | **PASS** | All 7 claims forensically audited; legacy Church Street numbers explicitly marked UNVERIFIED per Rule 1. |
| **3. Refactor list written** | Proposed migration into target layout with stub folders created. | **PASS** | Stub folders created; layout defined in §7; `data/MANIFEST.md` and `requirements.txt` generated. |
| **4. No functional code changes** | Preserve existing code without functional regressions. | **PASS** | No existing core library code was altered. Only read-only inventory, benchmarks, configs, and reports were added. |

---

## 9. Open Issues & Next Steps

1. **Stage 2 Ingestion**: Download and ingest Berlin primary case study data (ALKIS/LoD2 building footprints, DGM1 terrain, tree inventory) into `data/raw/berlin/`, compute SHA256 checksums, and update `data/MANIFEST.md`.
2. **City-Config Integration**: Update data ingestion pipeline to read directly from `configs/cities/berlin.json`.
3. **Legacy Test Clean-up**: Isolate legacy tests into an archived directory or adapt them to synthetic/Berlin configurations so test suite runs with 100% pass rate.
