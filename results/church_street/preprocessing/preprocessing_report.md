# Bengaluru Church Street Exploratory Preprocessing Report

**Execution Timestamp**: `2026-10-06T23:03:08.908005+00:00`  
**Pipeline Run**: `results/church_street_preprocessing_20261006_230308`  
**Operational Status**: `READY_FOR_STATIC_FULL_SIMULATION`  
**Simulation Phase**: `PREPROCESSING_ONLY` (Zero comfort simulations performed)

> [!IMPORTANT]
> **Scientific Qualification**:  
> "The Church Street scene has been converted into an exploratory local-coordinate triangular-mesh representation using approved but partly uncertain building-height estimates."

---

## 1. Executive Summary & Site Specifications

This report documents the geometric preprocessing and validation of the real-world Church Street study site in Bengaluru, Karnataka, India into a fully validated, watertight 3D triangular-mesh scene ready for downstream solar and microclimatic modeling in **SOLARAEUS**.

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Study Site** | Church Street central/eastern study block | Mapped urban canyon in Bengaluru Central Business District |
| **Geographic Center** | 12.974900° N, 77.605400° E | WGS84 coordinates |
| **Main Boundary Extent** | 217.11 m × 135.05 m | Geodesic rectangle: Lon [77.6044, 77.6064], Lat [12.9743, 12.9755] |
| **Core Building Count** | **37 footprints** | Primary thermal comfort analysis buildings |
| **Shadow Context Extent** | 370.0 m × 286.57 m | Main boundary expanded outward by 75.0 m UTM with squared corners |
| **Total Shadow Buildings** | **123 footprints** | Complete footprints intersecting shadow context (no clipping) |
| **Source CRS** | `EPSG:4326` | WGS84 Geographic 2D |
| **Metric Projection** | `EPSG:32643` | UTM Zone 43N meters |
| **Local Cartesian Origin** | $(782541.81\,\text{m}, 1435736.11\,\text{m}, 0.0\,\text{m})$ | Southwest corner of main study block mapped to $(0, 0)$ |
| **UTM Grid Convergence** | $+0.585366^\circ$ ($+35.12'$) | Grid North is $+0.585^\circ$ clockwise from True North |
| **Model Ground Plane** | Flat horizontal surface at $z = 0.0\,\text{m}$ | Terrain samples ($917.43\pm 1.25\,\text{m}$) kept for metadata only |
| **Core Receptor Grid** | $230.0\,\text{m} \times 145.0\,\text{m}$ at $\Delta x = 1.0\,\text{m}$ | $n_x = 230, n_y = 145 \implies \mathbf{33,350}\,\text{cells}$ |
| **Context Shadow Grid** | $380.0\,\text{m} \times 296.0\,\text{m}$ at $\Delta x = 2.0\,\text{m}$ | $n_x = 190, n_y = 148 \implies \mathbf{28,120}\,\text{cells}$ (Exact integer grid) |

---

## 2. Receptor Grid Geometry & Exact Cell Count Verification

The study domain defines two distinct calculation and ray-tracing receptor grids:

### A. Core Pedestrian Analysis Grid
- **Bounding Extents**: Origin $(-10.0\,\text{m}, -5.0\,\text{m})$, Width $230.0\,\text{m}$, Height $145.0\,\text{m}$, bounds $X \in [-10.0, 220.0]\,\text{m}, Y \in [-5.0, 140.0]\,\text{m}$.
- **Resolution**: $\Delta x = 1.0\,\text{m}$, height $z = 1.1\,\text{m}$.
- **Cell Count**: $n_x = 230, n_y = 145 \implies 230 \times 145 = \mathbf{33,350}\,\text{cells}$.
- **Coverage**: Completely envelopes the $217.11\,\text{m} \times 135.05\,\text{m}$ main study boundary.

### B. Shadow-Context Calculation Grid
- **Bounding Extents**: Origin $(-85.0\,\text{m}, -80.0\,\text{m})$, Width $380.0\,\text{m}$, Height $296.0\,\text{m}$, bounds $X \in [-85.0, 295.0]\,\text{m}, Y \in [-80.0, 216.0]\,\text{m}$.
- **Resolution**: $\Delta x = 2.0\,\text{m}$, height $z = 1.1\,\text{m}$.
- **Exact Cell Count**:
  $$n_x = \frac{380.0\,\text{m}}{2.0\,\text{m}} = 190, \quad n_y = \frac{296.0\,\text{m}}{2.0\,\text{m}} = 148 \implies n_x \times n_y = 190 \times 148 = \mathbf{28,120}\,\text{cells}$$
  $$\frac{380.0\,\text{m} \times 296.0\,\text{m}}{(2.0\,\text{m})^2} = \frac{112,480\,\text{m}^2}{4.0\,\text{m}^2/\text{cell}} = \mathbf{28,120}\,\text{cells}$$

> [!NOTE]
> **Resolution of Dimensions vs. Cell Count**:  
> The nominal analytical 75 m buffer envelope has bounding dimensions of $369.99\,\text{m} \times 286.57\,\text{m}$ (local $[-77.12, 292.87]\,\text{m} \times [-75.76, 210.81]\,\text{m}$).  
> If an odd nominal dimension of $295.0\,\text{m}$ were used, dividing by $2.0\,\text{m}$ would yield a fractional $147.5$ cells (giving theoretical $(380 \times 295)/4 = 28,025$). Because discrete calculation grids require integer cell boundaries, the Y-extent is explicitly set to **$296.0\,\text{m}$** ($148$ cells $\times 2.0\,\text{m}$), yielding exactly **28,120 unclipped, uniform cells** with zero fractional-cell truncation.

---

## 3. Building Height Resolution & Dual-Taxonomy Clarification

To eliminate ambiguity between administrative simulation approval and empirical uncertainty, the 123 buildings are classified along two orthogonal axes:

### Axis 1: Formal Decision Status (Administrative Simulation Gate)
- **Approved (Core Study Block)**: **30 buildings** formally approved for baseline simulation based on corroborated Google ML estimates or verified floor counts.
- **Accepted (Context Domain)**: **77 buildings** accepted based on Google ML estimates for shadow-casting obstruction.
- **Total Approved / Accepted**: **107 buildings** (87.0% of total domain).
- **Uncertain**: **16 buildings** (13.0% of total domain):
  - 7 Core buildings (5 with floor/ML discrepancies or sparse pixel coverage; 2 canyon fallbacks).
  - 9 Context buildings (missing both ML and floor data; assigned commercial canyon fallback of $9.6\,\text{m}$).
- **Rejected**: **0 buildings** (0.0%).

### Axis 2: Physical Uncertainty Tier (Evidence Quality Level)
- **Moderate Uncertainty**: **83 buildings** (28 core + 55 context) — robust ML estimates corroborated with high valid pixel coverage ($\ge 50\%$).
- **High Uncertainty**: **29 buildings** (7 core + 22 context):
  - 2 Core buildings (B19, B36) approved from floor counts ($6.4\,\text{m}$) because ML was missing (floor-to-height ratio $3.2\,\text{m}$ is assumed).
  - 5 Core buildings (B02, B03, B17, B31, B37) marked uncertain due to floor-ML conflicts or sparse pixel coverage ($<50\%$).
  - 22 Context buildings accepted via ML but flagged due to low pixel coverage ($<50\%$).
- **Extreme Uncertainty**: **11 buildings** (2 core + 9 context) — zero empirical data, assigned $9.6\,\text{m}$ commercial canyon median fallback.

### Definition of the High-Risk Sensitivity Cohort (40 Buildings)
The **40 buildings** cataloged in [`uncertain_buildings.csv`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/uncertain_buildings.csv) represents the **union of the High (29) and Extreme (11) Uncertainty tiers**:
$$29 \,(\text{High}) + 11 \,(\text{Extreme}) = \mathbf{40\,\text{buildings}}$$
Of these 40 buildings:
- **16 buildings** have decision status `UNCERTAIN` (5 High + 11 Extreme).
- **24 buildings** have decision status `APPROVED` or `ACCEPTED` but carry elevated uncertainty flags (2 approved core floor tags + 22 accepted context ML estimates with low pixel coverage).

### Two-Dimensional Classification Cross-Tabulation Matrix

| Decision Status | Moderate Uncertainty | High Uncertainty | Extreme Uncertainty | Total by Status |
| :--- | :---: | :---: | :---: | :---: |
| **Approved (Core 37)** | 28 | 2 | 0 | **30** |
| **Accepted (Context 86)** | 55 | 22 | 0 | **77** |
| **Uncertain (Core 37)** | 0 | 5 | 2 | **7** |
| **Uncertain (Context 86)** | 0 | 0 | 9 | **9** |
| **Rejected (All)** | 0 | 0 | 0 | **0** |
| **Total by Uncertainty Tier** | **83** | **29** | **11** | **123** |

---

## 4. Geometric Auditing & Watertightness Verification

All 123 2D building footprints were projected into local coordinates and extruded into 3D triangular meshes using `mapbox_earcut` for base and roof triangulation and outward-facing quad-split walls.

### Geometric Validation Checklist

| Test Item | Verification Criteria | Observed Result | Status |
| :--- | :--- | :--- | :---: |
| **Watertight 2-Manifold** | Every edge incident to exactly 2 faces | **123 / 123 meshes pass** (0 boundary edges) | **PASSED** |
| **Degeneracy Elimination** | Triangle surface area $> 10^{-12}\,\text{m}^2$ | **0 degenerate triangles** across all meshes | **PASSED** |
| **Area Conservation** | $|A_{\text{roof}} - A_{\text{footprint}}| < 10^{-4}\,\text{m}^2$ | Max difference: **0.00000000 $\text{m}^2$** | **PASSED** |
| **Wall Face Normals** | $n_z = 0.0$ (horizontal, outward-facing) | **100% verified outward** | **PASSED** |
| **Roof Face Normals** | $n_z = +1.0$ (strictly upward) | **100% verified upward** | **PASSED** |
| **Floor Face Normals** | $n_z = -1.0$ (strictly downward) | **100% verified downward** | **PASSED** |
| **Z-Bounds Integrity** | $z_{\min} = 0.0\,\text{m}$, $z_{\max} = h\,\text{m}$ | All 123 meshes conform | **PASSED** |

### Mesh Complexity Metrics

- **Core Scene (37 buildings)**:
  - Total Vertices: **448**
  - Total Triangles: **748**
  - Total Footprint Area: **17,510.92 $\text{m}^2$**
  - Total Exterior Surface Area: **83,041.95 $\text{m}^2$**
  - Heights: Min **2.5 m**, Max **52.5 m**, Mean **13.0 m**, Median **12.0 m**
- **Shadow Context Scene (123 buildings)**:
  - Total Vertices: **1,314**
  - Total Triangles: **2,136**
  - Total Footprint Area: **49,875.81 $\text{m}^2$**
  - Total Exterior Surface Area: **208,225.96 $\text{m}^2$**
  - Heights: Min **1.5 m**, Max **52.5 m**, Mean **10.0 m**, Median **9.0 m**

---

## 5. Deliverables & Output Artifacts

The preprocessing run generated all mandatory structured deliverables in `results/church_street_preprocessing_20261006_230308/`:

1. [`provenance.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/provenance.json): Full execution environment, file hashes, sign-off confirmations.
2. [`scene_summary.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/scene_summary.json): Scene statistics, extents, and height distributions (`simulation_status: "preprocessing_only"`).
3. [`accepted_height_policy.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/accepted_height_policy.json): Detailed height assignment decisions, canyon fallbacks, and 2D taxonomy matrix.
4. [`coordinate_validation.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/coordinate_validation.json): CRS definitions, local origins, boundary polygons, grid convergence.
5. [`geometry_validation_report.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/geometry_validation_report.json): Per-mesh watertightness, area conservation, and normal checks.
6. [`mesh_statistics.csv`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/mesh_statistics.csv): Comprehensive tabular ledger of all 123 building meshes.
7. [`uncertain_buildings.csv`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/uncertain_buildings.csv): 40 buildings in the high-risk sensitivity cohort (High + Extreme uncertainty).
8. [`rejected_or_failed_features.csv`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/rejected_or_failed_features.csv): 0 failed features recorded.
9. [`main_scene_mesh.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/main_scene_mesh.json): Serialized `Scene` JSON for the 37 core study block buildings.
10. [`shadow_context_mesh.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/church_street_preprocessing_20261006_230308/shadow_context_mesh.json): Serialized `Scene` JSON for all 123 shadow context buildings.
11. Diagnostic Plots in `plots/`:
    - `site_boundary_local.png`: Main study boundary vs 75m shadow context buffer in local coordinates.
    - `building_footprints_local.png`: 2D building footprints classified by core vs context.
    - `building_height_map.png`: Height choropleth map highlighting uncertain buildings.
    - `mesh_scene_preview.png`: 3D perspective visualization of the extruded Church Street scene.

---

## 6. Downstream Simulation Readiness Decision

**Final Status**: `READY_FOR_STATIC_FULL_SIMULATION`

- **Completed**: Geometric extraction, CRS reprojection, local Cartesian referencing, watertight triangulation, area conservation auditing, height policy resolution, and scene serialization.
- **Strict Boundary Preservation**: Zero thermal comfort calculations ($T_{\text{mrt}}$, $\text{UTCI}$), zero ray-tracing solves, zero incremental updates, and zero intervention comparisons were conducted in this stage.
- **Next Stage**: Static full simulation of baseline microclimate using `main_scene_mesh.json` for receptor grids and `shadow_context_mesh.json` for solar obstruction ray tracing.
