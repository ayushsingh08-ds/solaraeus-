## 9. Controlled Triangular-Mesh Generalization Stage (Milestones 1–12 Frozen)

### 9.1 Stage Objective & Scope Boundaries
The objective of this stage was to generalize the SOLARAEUS geometry representation from axis-aligned bounding boxes (AABBs) to controlled triangular meshes while preserving exact direct shadow correctness, SVF/radiation fidelity, conservative affected-region detection, and mathematically certified incremental recomputation.

**Enforced Claim Boundaries**:
- *"No certificate violations were observed in the evaluated synthetic configurations."*
- *"The mesh extension is an experimental CPU implementation evaluated on controlled synthetic geometries."*
- *"All certificates remain conditional on the documented discrete-grid, single-timestep, flat-terrain, fixed-material, and fixed-surface-temperature assumptions."*
- Prohibited out-of-scope technologies: No GPU/CUDA/OptiX, no external mesh file importers (OBJ/glTF/CityGML), no real-world LiDAR/GIS datasets, no vegetation, no CFD.

### 9.2 Architecture & Implementations
1. **Mesh Data Model** (`urban_comfort.geometry.mesh`):
   - `TriangleMesh`: Holds $(N_v, 3)$ float64 vertices and $(M, 3)$ int64 triangle indices. Computes face normals, bounding boxes, and surface areas.
   - 6 synthetic constructors: `create_box_mesh`, `create_rotated_box_mesh`, `create_pitched_roof_mesh`, `create_overhang_mesh`, `create_slanted_wall_mesh`, `create_l_shaped_mesh`.
2. **CPU Ray–Triangle Intersection** (`urban_comfort.visibility.mesh_ray_intersection`):
   - Vector-batch Möller–Trumbore ray casting with two-sided intersection testing and hierarchical mesh bounding box pre-culling.
3. **Mesh Direct Shadow Projection** (`urban_comfort.visibility.mesh_shadow`):
   - Receptors at pedestrian height ($z = 1.1\,\text{m}$) cast rays toward the sun. Dispatched transparently by `compute_direct_shadow_mask`.
4. **Directional Visibility & SVF** (`urban_comfort.visibility.mesh_visibility`):
   - Downward raycasting top-envelope DSM rasterization ($H_{\text{dsm}}(x, y)$) followed by 16-azimuth horizon scanning. Dispatched transparently by `compute_sky_view_factor`.
5. **Conservative Affected Regions & Incremental Safety** (`urban_comfort.incremental.mesh_affected_region`, `urban_comfort.incremental.mesh_update`):
   - Bounding volume shadow ray projection + SVF decay radius ($R_{\text{max}}$). Zero false negatives on all geometric modifications.
   - Mesh edit operations: `AddMeshEdit`, `RemoveMeshEdit`, `ReplaceMeshEdit`, `MoveMeshEdit`, `ChangeMeshHeightEdit`.

### 9.3 Comparative AABB vs Mesh Parity Benchmarks
Evaluated across 4 canonical scenes (`results/mesh_validation_20261006_092428/aabb_vs_mesh_comparison.csv`):

| Scene ID | Typology | AABB Bldgs | Mesh Tris | Shadow IoU | Mismatch Pixels | SVF MAE | $T_{\text{mrt}}$ MAE (K) | $T_{\text{mrt}}$ Max Diff (K) | UTCI Agreement | Runtime AABB (s) | Runtime Mesh (s) | Overhead Ratio |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `isolated_building` | 20x20x25m tower | 1 | 12 | 1.000000 | 0 | 0.000145 | 0.005894 | 0.042577 | 100.00% | 0.2431 | 0.2335 | 0.96x |
| `urban_canyon` | 2 parallel slabs (40x15x20m) | 2 | 24 | 1.000000 | 0 | 0.000285 | 0.011196 | 0.053181 | 100.00% | 0.3034 | 0.6341 | 2.09x |
| `enclosed_courtyard` | 4 perimeter blocks (18m) | 4 | 48 | 1.000000 | 0 | 0.000334 | 0.013033 | 0.092906 | 100.00% | 0.5348 | 0.7367 | 1.38x |
| `dense_3x3_grid` | 9 blocks (15-24m heights) | 9 | 108 | 1.000000 | 0 | 0.000269 | 0.010422 | 0.068890 | 100.00% | 0.7160 | 0.7175 | 1.00x |
| **Composite / Mean** | — | — | — | **1.000000** | **0** | **0.000258** | **0.010136** | **0.064389** | **100.00%** | **0.4493** | **0.5805** | **1.36x** |

### 9.4 Independent Certificate Audit Verification
Evaluated across 8 mesh typologies and 3 tolerances ($\tau \in [0.25, 0.5, 1.0]\,\text{K}$) in `results/mesh_validation_20261006_092428/mesh_dependency_audit.csv`:
- **Total Configurations**: 24 runs evaluated across 10,000 cells per run.
- **Certificate Violations**: **0 violations detected** ($e(x) \le B_T(x)$ on all cells).
- **Tolerance Violations**: **0 violations detected** ($e(x) \le \tau$ on all certified reused cells).
- **Mathematical Soundness**: **100.0% SOUND**.
- **Mean Reused Fraction**: 20.84% (up to 62.52%).

### 9.5 Non-Vacuous Mutation Testing
Tested in `tests/test_mesh_mutation_audit.py`:
- **Unmutated Control**: 0 violations, 100% sound.
- **Mutation A (Zeroed Error Bound)**: Audit flagged violations on 100% of reused cells with negative slack.
- **Mutation B (Unsafe Recompute Truncation)**: Audit detected actual errors exceeding $5.0\,\text{K}$ and failed tolerance compliance.

### 9.6 Scaling & Computational Performance
Evaluated across triangle counts ($M \in [12, 48, 192, 768, 3072]$) and resolutions ($dx \in [2.0, 1.0, 0.5]\,\text{m}$):
- **Runtime Scaling**: Subquadratic complexity; $256\times$ increase in triangle count produced only a $4.1\times$ runtime increase ($3.19\text{s} \to 13.18\text{s}$).
- **Peak Memory**: Bounded at **$\le 8.34\,\text{MB}$** across all configurations.
- **Selective Recomputation Speedup**: In dense configurations (3,072 triangles), incremental updates achieved **$15.14\times$ speedup** with $77.7\%$ cell reuse.

### 9.7 Adversarial & Edge-Case Robustness
Evaluated in `tests/test_mesh_adversarial.py` (8 suites):
- 500:1 sliver triangles, grazing sun at $6.6^\circ$, compounding 5-edit sequences, revert zero-drift ($< 10^{-10}\,\text{K}$), shared edge ray casting, near-pedestrian roofs ($1.15\,\text{m}$), and self-occluding concave geometries.

### 9.8 Generated Validation Artifacts
Directory: `results/mesh_validation_20261006_092428/`
- `mesh_dependency_audit.csv`: 24 audit runs across 8 scenarios and 3 tolerances (0 violations).
- `mesh_audit_summary.json`: Formal summary of audit soundness.
- `aabb_vs_mesh_comparison.csv`: 4-scene comparative parity metrics.
- `aabb_vs_mesh_summary.json`: High-level summary of parity (IoU 1.0, SVF MAE 0.00026, Tmrt MAE 0.010K, UTCI 100%).
- `mesh_scaling_results.csv`: 8 scaling trials across triangle counts and grid resolutions.
- `mesh_scaling_summary.json`: Scaling and memory boundedness summary.
- `mesh_validation_report.md`: Formal scientific validation report synthesizing all 12 milestones.

### 9.9 Regression Suite Status
- **Pre-Mesh Baseline**: 99 passing tests.
- **Post-Mesh Extension**: **173 passing automated tests** (+74 new tests covering geometry, ray intersection, shadows, visibility, affected regions, incremental updates, certificate audits, adversarial edge cases, AABB benchmarks, scaling benchmarks, and mutation audits).
- **Failures / Errors**: 0.
- **Status**: **COMPLETE AND AUDIT FROZEN**.

### 9.10 Architecture Map & Module Inventory
The triangular-mesh generalization was integrated seamlessly into the existing pipeline without architectural bifurcations:

```
src/urban_comfort/
├── geometry/
│   ├── primitives.py                     # AABB prisms, bounding boxes
│   ├── mesh.py                           # TriangleMesh data model & 6 synthetic constructors
│   └── scene.py                          # Unified scene container supporting both buildings & meshes
├── visibility/
│   ├── ray_intersection.py               # Kay-Kajiya slab ray-AABB intersection
│   ├── mesh_ray_intersection.py          # Vector-batch Möller-Trumbore ray-triangle intersection
│   ├── shadow.py                         # Unified shadow dispatcher (AABB / mesh)
│   ├── mesh_shadow.py                    # Direct solar raycasting for mesh geometry
│   ├── directional_visibility.py         # Unified SVF dispatcher (AABB / mesh)
│   └── mesh_visibility.py                # Top-envelope DSM rasterization & multi-azimuth horizon scan
├── incremental/
│   ├── affected_region.py                # Unified dirty region dispatcher
│   ├── mesh_affected_region.py           # Conservative bounding volume plume & horizon radius
│   ├── update.py                         # Certified incremental updates with ErrorCertificate
│   └── mesh_update.py                    # Mesh edit operations (Add, Remove, Replace, Move, ChangeHeight)
└── benchmark/
    ├── independent_audit.py              # Decoupled certificate audit engine
    ├── mesh_certificate_audit.py         # 24-run independent audit runner for meshes
    ├── aabb_vs_mesh_benchmark.py         # 4-scene canonical AABB vs mesh parity benchmark
    └── mesh_scaling_benchmark.py         # Triangle scaling & resolution scaling benchmark

tests/ (173 tests total: 99 baseline + 74 mesh extension)
├── test_mesh_geometry.py                 # 14 tests: data model, normals, areas, constructors
├── test_ray_triangle_intersection.py     # 10 tests: Möller-Trumbore, two-sided, backface, AABB culling
├── test_mesh_shadows.py                  # 8 tests: raycasting shadows, parity with AABB, night
├── test_mesh_visibility.py               # 7 tests: DSM rasterization, SVF parity, horizon occlusion
├── test_mesh_affected_region.py          # 7 tests: plume conservatism, zero false negatives
├── test_mesh_incremental_updates.py      # 7 tests: exact recompute zero drift, certified reuse > 84%
├── test_mesh_certificate_audits.py       # 1 test: end-to-end 24-configuration audit soundness
├── test_mesh_adversarial.py              # 8 tests: sliver triangles, grazing sun, revert drift < 1e-10K
├── test_aabb_vs_mesh_benchmarks.py       # 5 tests: 4-scene parity, IoU 1.0, SVF MAE < 0.005, Tmrt MAE < 0.05K
├── test_mesh_scaling_benchmarks.py       # 4 tests: M in [12..3072], dx in [0.5..2.0m], peak mem < 50MB
└── test_mesh_mutation_audit.py           # 3 tests: non-vacuous mutation audit (100% violation detection)
```

---

