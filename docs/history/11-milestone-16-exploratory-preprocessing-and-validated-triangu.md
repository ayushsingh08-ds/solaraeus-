## 11. Milestone 16: Exploratory Preprocessing & Validated Triangular-Mesh Representation (Bengaluru Church Street)

### 11.1 Scope, Boundaries & Scientific Framing
- **Phase Status**: Exploratory preprocessing only. **Zero thermal comfort simulations ($T_{\text{mrt}}$, $\text{UTCI}$) performed.**
- **Strict Boundary Preservation**:
  - No ray-tracing comfort solves or incremental updates executed.
  - No intervention scenario comparisons run.
  - No solver modification or terrain elevation variation introduced (flat model ground $z = 0.0\,\text{m}$).
  - No vegetation, CFD, or GPU dependencies.
- **Mandatory Scientific Framing**:
  > *"The Church Street scene has been converted into an exploratory local-coordinate triangular-mesh representation using approved but partly uncertain building-height estimates."*

### 11.2 Preprocessing Architecture & Adapter Implementation
- **Adapter Module**: [`src/urban_comfort/preprocessing/church_street_adapter.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/preprocessing/church_street_adapter.py)
  - `ChurchStreetAdapter`: End-to-end data loader, CRS projector, ear-clipping triangulator, 3D extruder, and audit validator.
  - `PreprocessingConfig`: Configurable parameters for file paths, local Cartesian origin, CRS codes, convergence angle, fallback heights, and optical properties.
  - `PreprocessedSceneResult`: Typed container holding the core `Scene` (37 buildings), shadow context `Scene` (123 buildings), mesh collections, statistics, and audit reports.
- **Triangulation & Extrusion Engine**:
  - Footprint ear-clipping via `mapbox_earcut` on 2D polygon base vertices.
  - Extrudes 2D polygon into a **watertight closed 2-manifold TriangleMesh**:
    - $N$ base vertices at $z = 0.0\,\text{m}$ ($0 \dots N-1$).
    - $N$ roof vertices at $z = h\,\text{m}$ ($N \dots 2N-1$).
    - Side wall quads triangulated as $[i, j, j+N]$ and $[i, j+N, i+N]$ with outward-pointing horizontal face normals ($n_z = 0.0$).
    - Roof triangulated as $[a+N, b+N, c+N]$ with strictly upward vertical face normals ($n_z = +1.0$).
    - Bottom floor triangulated as $[a, c, b]$ with strictly downward vertical face normals ($n_z = -1.0$) ensuring manifold closure.
    - Total vertices = $2N$; Total triangles = $4N - 4$.

### 11.3 Geometric Audit & Quality Metrics
Across all 123 building meshes:
- **Watertightness**: 123 / 123 meshes verified as closed 2-manifolds (every internal edge shared by exactly 2 triangles, 0 boundary edges).
- **Degenerate Area Elimination**: 0 degenerate triangles ($A > 10^{-12}\,\text{m}^2$) detected across all 2,136 triangles.
- **Area Conservation**: $|A_{\text{roof}} - A_{\text{footprint}}| = 0.00000000\,\text{m}^2$ maximum discrepancy across all 123 meshes.
- **Face Normal Orientation**: 100% of wall normals verified horizontal and outward; 100% of roof normals verified upward $+Z$; 100% of floor normals verified downward $-Z$.
- **Z-Bounds**: $z_{\min} = 0.0\,\text{m}$, $z_{\max} = h\,\text{m}$ strictly verified for all meshes.

### 11.4 Coordinate Transformation & Georeferencing
- **Source CRS**: `EPSG:4326` (WGS84 lon, lat).
- **Metric Calculation CRS**: `EPSG:32643` (UTM Zone 43N meters) with `always_xy=True`.
- **Local Cartesian Origin**:
  $$x_0 = 782,541.805538\,\text{m}, \quad y_0 = 1,435,736.110343\,\text{m}, \quad z_0 = 0.0\,\text{m}$$
  Maps the southwest corner of the main study block ($77.6044^\circ\,\text{E}, 12.9743^\circ\,\text{N}$) to local $(0.0, 0.0)\,\text{m}$.
- **UTM Grid Convergence**:
  $$\gamma = +0.585366^\circ \quad (+35.12')$$
  Grid North is rotated $+0.585^\circ$ clockwise relative to True North. Downstream solar ray azimuths will adjust by $-0.585^\circ$.
- **Terrain Handling**: Coarse Skadi DEM terrain samples ($917.43\,\text{m} \pm 1.25\,\text{m}$) retained for metadata and validation only. Model ground plane is flat at $z = 0.0\,\text{m}$.

### 11.5 Building Height Dual-Taxonomy & Uncertainty Rollup
To eliminate ambiguity between administrative simulation approval and empirical uncertainty, the 123 buildings are classified along two orthogonal axes:

1. **Formal Decision Status (Administrative Simulation Gate)**:
   - **Approved (Core Study Block)**: **30 buildings** formally approved for baseline simulation based on corroborated Google ML estimates or verified floor counts.
   - **Accepted (Context Domain)**: **77 buildings** accepted based on Google ML estimates for shadow-casting obstruction.
   - **Total Approved / Accepted**: **107 buildings** (87.0% of total domain).
   - **Uncertain**: **16 buildings** (13.0% of total domain):
     - 7 Core buildings (5 with floor/ML discrepancies or sparse pixel coverage; 2 canyon fallbacks).
     - 9 Context buildings (missing both ML and floor data; assigned commercial canyon fallback of $9.6\,\text{m}$).
   - **Rejected**: **0 buildings** (0.0%).

2. **Physical Uncertainty Tier (Evidence Quality Level)**:
   - **Moderate Uncertainty**: **83 buildings** (28 core + 55 context) — robust ML estimates corroborated with high valid pixel coverage ($\ge 50\%$).
   - **High Uncertainty**: **29 buildings** (7 core + 22 context):
     - 2 Core buildings (B19, B36) approved from floor counts ($6.4\,\text{m}$) because ML was missing (floor-to-height ratio $3.2\,\text{m}$ is assumed).
     - 5 Core buildings (B02, B03, B17, B31, B37) marked uncertain due to floor-ML conflicts or sparse pixel coverage ($<50\%$).
     - 22 Context buildings accepted via ML but flagged due to low pixel coverage ($<50\%$).
   - **Extreme Uncertainty**: **11 buildings** (2 core + 9 context) — zero empirical data, assigned $9.6\,\text{m}$ commercial canyon median fallback.

3. **High-Risk Sensitivity Cohort (40 Buildings)**:
   - The figure of **40 buildings** refers specifically to the union of all buildings in the **High Uncertainty (29)** and **Extreme Uncertainty (11)** tiers ($29 + 11 = 40$).
   - It comprises:
     - All **16 buildings** with `UNCERTAIN` status (5 High + 11 Extreme).
     - **24 buildings** with `APPROVED` or `ACCEPTED` status that carry elevated uncertainty flags (2 approved core floor fallbacks + 22 accepted context ML estimates with low pixel coverage).
   - This 40-building subset forms the designated cohort for parameter perturbation and sensitivity bounds in subsequent microclimatic uncertainty propagation.

#### Two-Dimensional Classification Cross-Tabulation Matrix

| Decision Status | Moderate Uncertainty | High Uncertainty | Extreme Uncertainty | Total by Status |
| :--- | :---: | :---: | :---: | :---: |
| **Approved (Core 37)** | 28 | 2 | 0 | **30** |
| **Accepted (Context 86)** | 55 | 22 | 0 | **77** |
| **Uncertain (Core 37)** | 0 | 5 | 2 | **7** |
| **Uncertain (Context 86)** | 0 | 0 | 9 | **9** |
| **Rejected (All)** | 0 | 0 | 0 | **0** |
| **Total by Uncertainty Tier** | **83** | **29** | **11** | **123** |

### 11.6 Scene Complexity & Exact Receptor Grid Verification

| Scene | Buildings | Vertices | Triangles | Footprint Area ($\text{m}^2$) | Surface Area ($\text{m}^2$) | Min Height ($\text{m}$) | Max Height ($\text{m}$) | Mean Height ($\text{m}$) | Median Height ($\text{m}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Core Main Scene** | **37** | **448** | **748** | **17,510.92** | **83,041.95** | 2.5 | 52.5 | 13.01 | 12.0 |
| **Shadow Context Scene** | **123** | **1,314** | **2,136** | **49,875.81** | **208,225.96** | 1.5 | 52.5 | 10.04 | 9.0 |

#### Receptor Grid Geometry & Exact Cell Count Verification:
- **Core Main Scene Grid**:
  - Domain extents: $X \in [-10.0, 220.0]\,\text{m}, Y \in [-5.0, 140.0]\,\text{m}$ (Width $230.0\,\text{m}$, Length $145.0\,\text{m}$).
  - Resolution: $\Delta x = 1.0\,\text{m}$, receptor height $z = 1.1\,\text{m}$.
  - Discrete cell count: $n_x = 230, n_y = 145 \implies 230 \times 145 = \mathbf{33,350}\,\text{cells}$.
- **Shadow Context Grid**:
  - Domain extents: $X \in [-85.0, 295.0]\,\text{m}, Y \in [-80.0, 216.0]\,\text{m}$ (Width $380.0\,\text{m}$, Length $296.0\,\text{m}$).
  - Resolution: $\Delta x = 2.0\,\text{m}$, receptor height $z = 1.1\,\text{m}$.
  - Discrete cell count:
    $$n_x = \frac{380.0\,\text{m}}{2.0\,\text{m}} = 190, \quad n_y = \frac{296.0\,\text{m}}{2.0\,\text{m}} = 148 \implies n_x \times n_y = 190 \times 148 = \mathbf{28,120}\,\text{cells}$$
    $$\frac{380.0\,\text{m} \times 296.0\,\text{m}}{(2.0\,\text{m})^2} = \frac{112,480\,\text{m}^2}{4.0\,\text{m}^2/\text{cell}} = \mathbf{28,120}\,\text{cells}$$
  - **Clarification on Nominal vs Discrete Extents**:
    The analytical $75\,\text{m}$ shadow-context buffer envelope has bounding dimensions of $369.99\,\text{m} \times 286.57\,\text{m}$ (local $[-77.12, 292.87]\,\text{m} \times [-75.76, 210.81]\,\text{m}$). An odd nominal dimension of $295.0\,\text{m}$ divided by $2.0\,\text{m}$ yields $147.5$ cells (giving theoretical $(380 \times 295)/4 = 28,025$). Because discrete calculation grids require integer cell boundaries, the Y-extent is explicitly set to **$296.0\,\text{m}$** ($148$ cells $\times 2.0\,\text{m}$), yielding exactly **28,120 unclipped, uniform cells** with zero fractional-cell truncation.

### 11.7 Preprocessing Deliverables & Artifacts
All deliverables generated in `results/church_street_preprocessing_20261006_230308/`:
1. `provenance.json`: Tool versions, input file SHA256 hashes, sign-off confirmations.
2. `scene_summary.json`: Scene statistics, bounding boxes, height metrics, exact discrete grid derivations (`simulation_status: "preprocessing_only"`).
3. `accepted_height_policy.json`: Detailed height decisions, canyon fallback parameters, and 2D taxonomy matrix.
4. `coordinate_validation.json`: CRS parameters, local origins, boundary polygons, grid convergence angle.
5. `geometry_validation_report.json`: Per-mesh watertightness, area conservation, and normal checks (all 123 pass).
6. `mesh_statistics.csv`: Complete 123-building tabular ledger with 18 geometry and uncertainty attributes.
7. `uncertain_buildings.csv`: Detailed ledger of 40 buildings in the high-risk sensitivity cohort (High + Extreme uncertainty).
8. `rejected_or_failed_features.csv`: 0 failed features recorded.
9. `main_scene_mesh.json`: Serialized `Scene` JSON for 37 core study block buildings.
10. `shadow_context_mesh.json`: Serialized `Scene` JSON for 123 shadow context buildings.
11. `preprocessing_report.md`: Formal engineering report certifying `READY_FOR_STATIC_FULL_SIMULATION`.
12. Diagnostic Plots (`plots/`):
    - `site_boundary_local.png`: Local Cartesian extents and grid convergence notation.
    - `building_footprints_local.png`: 2D floor plans categorized by core (37) vs context (86).
    - `building_height_map.png`: Height choropleth map highlighting uncertain buildings with hatching.
    - `mesh_scene_preview.png`: 3D perspective visualization of the extruded Church Street urban canyon.

### 11.8 Testing & Test Suite Regression
- **Unit Tests**: [`tests/test_church_street_preprocessing.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_church_street_preprocessing.py) (6 tests verifying config, coordinate transforms, height loaders, ear-clipping extrusion, full pipeline execution, discrete grid math, and scene JSON serialization).
- **Test Suite Regression**: **179 passed** (173 baseline tests + 6 new preprocessing tests, 100% pass rate).

---

