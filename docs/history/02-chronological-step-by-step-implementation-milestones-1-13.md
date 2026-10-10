## 2. Chronological Step-by-Step Implementation (Milestones 1 – 13)

### Milestone 1: Repository Inspection & Environment Baseline
- **Git State Verification**: Confirmed initial clean state on `main` branch (`1bb9ee0`).
- **Python Runtime & Toolchain**: Inspected local environment running Python 3.12.6 (Windows 64-bit).
- **Dependency Audit**: Verified installed scientific libraries:
  - `numpy` (vectorized multidimensional array algebra)
  - `scipy` (spatial mathematics and physical constants)
  - `pytest` (test execution framework)
  - `pythermalcomfort` (standard bio-meteorological thermal indices)
  - `shapely` (2D computational geometry and polygon clipping)
  - `matplotlib` (publication-grade scientific visualization)

---

### Milestone 2: Core Data Models & Canonical Geometric Scene Generation
- **Configuration & Constants ([config.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/config.py))**:
  - Implemented immutable data models: `Material`, `Weather`, and `SimulationConfig`.
  - Defined physical constants: Stefan-Boltzmann constant ($\sigma = 5.670374419 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$), human body shortwave absorptivity ($a_k = 0.70$), longwave emissivity ($a_l = 0.97$), default building wall albedo ($0.20$), and ground albedo ($0.15$).
- **Geometry Primitives ([primitives.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/geometry/primitives.py))**:
  - Created `BoundingBox2D` with interval overlap, intersection, and containment logic.
  - Implemented `Building` representing 3D axis-aligned rectangular prisms with footprint, height, position, and 3D bounds $(x_{\min}, x_{\max}, y_{\min}, y_{\max}, z_{\min}, z_{\max})$.
  - Created `GroundPlane` at $z = 0.0\,\text{m}$.
- **Scene Container & Synthetic Generators ([scene.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/geometry/scene.py))**:
  - Built `Scene` container managing collections of buildings, ground properties, and `PedestrianGridConfig`.
  - Added JSON serialization and deserialization (`Scene.to_dict`, `Scene.from_dict`, `Scene.save_json`, `Scene.load_json`).
  - Implemented synthetic scene generators: `create_single_box_scene`, `create_canyon_scene`, and `create_occlusion_scene`.
- **Baseline Configuration Artifact**:
  - Exported canonical baseline test scene: `configs/baseline_scene.json` (80m × 80m domain, 16m × 16m × 18m central building).
- **Tests**: Created `tests/test_geometry.py` (6 tests passing).

---

### Milestone 3: Astronomical Solar Positioning & Pedestrian Grid Infrastructure
- **Deterministic Solar Engine ([solar_position.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/solar/solar_position.py))**:
  - Implemented NOAA astronomical solar position algorithm.
  - Computes Julian Day, Julian Century, geometric mean longitude, mean anomaly, equation of the center, true/apparent solar longitude, obliquity of the ecliptic, solar declination, and equation of time.
  - Evaluates true solar time, hour angle, solar zenith angle, solar elevation angle (altitude $\alpha$), and solar azimuth angle $\phi$ (clockwise from True North).
  - Derived unit 3D sun vector $(s_x, s_y, s_z)$ in local Cartesian coordinates (East = $+X$, North = $+Y$, Up = $+Z$).
- **2D Pedestrian Grid Infrastructure ([pedestrian_grid.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/grid/pedestrian_grid.py))**:
  - Implemented `PedestrianGrid` over arbitrary bounding extents at pedestrian height $z_{\mathrm{ped}} = 1.1\,\text{m}$.
  - Provided bidirectional spatial mappings: continuous world coordinates $(u, v) \leftrightarrow$ discrete cell indices $(j, i)$.
  - Implemented vectorized 2D coordinate meshgrids (`grid.X`, `grid.Y`) and spatial bounding-box slicing helpers (`grid.bounding_box_slices`).
- **Tests**: Created `tests/test_solar_position.py` (4 tests) and `tests/test_pedestrian_grid.py` (5 tests).

---

### Milestone 4: Vectorized Visibility, Direct Shadows & Multi-Azimuth SVF
- **Vectorized Ray-AABB Slab Intersection ([ray_intersection.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/visibility/ray_intersection.py))**:
  - Implemented vectorized Kay-Kajiya slab ray-tracing test for axis-aligned bounding boxes.
  - Handled ray parallelisms, division-by-zero safeguards, and parametric intervals $[t_{\min}, t_{\max}]$.
- **Direct Solar Shadow Mask ([shadow.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/visibility/shadow.py))**:
  - Implemented `compute_direct_shadow_mask` tracing rays from pedestrian grid cells $(x, y, z_{\mathrm{ped}})$ toward the sun vector.
  - Added support for arbitrary bounding-box Regions of Interest (ROI) for targeted incremental updates.
- **Multi-Azimuth Horizon Search for Sky View Factor ([directional_visibility.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/visibility/directional_visibility.py))**:
  - Implemented `compute_sky_view_factor` across $N_{\mathrm{azimuth}}$ discrete angular directions (16, 32, 64 rays).
  - Scans horizon elevation angles $\gamma(\phi, x)$ up to configurable search distance $r_{\max} = 30.0\,\text{m}$.
  - Integrates unoccluded upper hemisphere view factor via:
    $$\psi_{\mathrm{svf}}(x) = \frac{1}{N} \sum_{k=1}^N \cos^2(\gamma(\phi_k, x))$$
  - Added directional view factor approximations for the 4 cardinal side walls.
- **Tests**: Created `tests/test_ray_intersections.py` (5 tests) and `tests/test_shadows.py` (5 tests).

---

### Milestone 5: Radiative Fluxes, Stefan-Boltzmann Inversion & Thermal Comfort
- **Shortwave Radiative Fluxes ([shortwave.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/radiation/shortwave.py))**:
  - Evaluated 6-directional shortwave components:
    - Direct solar radiation: $K_{\mathrm{dir}, i}(x) = I_{\mathrm{dir}} \cdot S_{\mathrm{shadow}}(x) \cdot \cos\theta_i$
    - Diffuse sky radiation: $K_{\mathrm{diff}, i}(x) = D_{\mathrm{diff}} \cdot \psi_{\mathrm{svf}, i}(x)$
    - Reflected shortwave from ground: $K_{\mathrm{refl, ground}}(x) = \alpha_g \cdot (I_{\mathrm{dir}} \sin\alpha \cdot S_{\mathrm{shadow}}(x) + D_{\mathrm{diff}})$
    - Reflected shortwave from walls: $K_{\mathrm{refl, wall}}(x) = \alpha_w \cdot (1 - \psi_{\mathrm{svf}}(x)) \cdot K_{\mathrm{avg}}$
  - Human angular weighting factors for standing cylinder: $F_{\mathrm{up}} = F_{\mathrm{down}} = 0.06$, $F_{\mathrm{side}} = 0.22$.
- **Longwave Radiative Fluxes ([longwave.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/radiation/longwave.py))**:
  - Atmospheric sky longwave with Brutsaert air emissivity: $\varepsilon_{\mathrm{air}} = 1.24 (e_{\mathrm{vap}} / T_{\mathrm{air}})^{1/7}$.
  - Building wall longwave emission: $L_{\mathrm{wall}}(x) = (1 - \psi_{\mathrm{svf}}(x)) \varepsilon_w \sigma T_{\mathrm{wall}}^4$.
  - Ground longwave emission: $L_{\mathrm{ground}}(x) = \varepsilon_g \sigma T_{\mathrm{ground}}^4$.
- **Stefan-Boltzmann $T_{\mathrm{mrt}}$ Inversion ([tmrt.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/radiation/tmrt.py))**:
  - Inverted Stefan-Boltzmann law across total absorbed flux density $S_{\mathrm{str}}$:
    $$T_{\mathrm{mrt}}(x) = \left( \frac{S_{\mathrm{str}}(x)}{\sigma} \right)^{1/4} - 273.15$$
- **Thermal Comfort & UTCI ([utci.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/comfort/utci.py))**:
  - Vectorized Universal Thermal Climate Index (UTCI) polynomial model.
  - Classified thermal sensation into 10 standardized categories (from Extreme Cold Stress to Extreme Heat Stress).
- **Ground-Truth Reference Pipeline ([full_recompute.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/reference/full_recompute.py))**:
  - Orchestrated full-domain calculation from scratch returning `SimulationResult`.
- **Tests**: Created `tests/test_full_recompute.py` (4 tests).

---

### Milestone 6: Reference Solver Verification & Statistical Comparisons
- **Array Comparison Utilities ([comparisons.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/validation/comparisons.py))**:
  - Implemented `compare_arrays` and `compare_results` evaluating Max Absolute Error (MAE), Root Mean Square Error (RMSE), Mean Bias Error (MBE), and Relative Error.
- **Spatial Validation Metrics ([metrics.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/validation/metrics.py))**:
  - Implemented direct shadow mask Intersection over Union (IoU).
  - Implemented UTCI thermal stress category concordance percentage.
- **Reference Example ([single_building.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/examples/single_building.py))**:
  - Standalone simulation script executing full recomputation on canonical scene.
- **Tests**: Created `tests/test_validation_comparisons.py` (7 tests).

---

### Milestone 7: Cache Management, State Hashing & Dependency Graph
- **Simulation Cache & State Hashing ([cache.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/cache.py))**:
  - Implemented `SimulationCache` with SHA-256 geometric state fingerprinting.
  - Implemented `FieldMetadata` tracking generation timestamps, invalidation states, and telemetry.
- **Dependency Graph Invalidation ([dependency_graph.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/dependency_graph.py))**:
  - Implemented physical DAG dependency graph:
    `Geometry -> [Shadow, SVF] -> Shortwave/Longwave -> Tmrt -> UTCI`.
  - Implemented reachability tracking to selectively invalidate only affected downstream fields.
- **Tests**: Created `tests/test_cache_and_dependencies.py` (6 tests).

---

### Milestone 8: Exact Incremental Update Engine
- **Atomic 3D Geometric Edits ([update.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/update.py))**:
  - `AddBuildingEdit`: Adds new building to scene.
  - `RemoveBuildingEdit`: Removes building from scene.
  - `ChangeHeightEdit`: Modifies building height $h_0 \to h_1$.
  - `MoveBuildingEdit`: Compound translation edit shifting building footprint.
- **Exact Incremental Solver (`incremental_update_exact`)**:
  - Computes exact footprint and shadow plume bounding boxes.
  - Evaluates shadow raycasting and SVF searches strictly within the affected region.
  - Merges recomputed patches with cached arrays.
  - Mathematically verified exact numerical equivalence ($\le 10^{-10}\,\text{K}$) against full recomputation.
- **Tests**: Created `tests/test_incremental_updates.py` (4 tests).

---

### Milestone 9: Candidate Affected Regions & Safety Frustum Envelopes
- **Candidate Affected Region Projection ([affected_region.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/affected_region.py))**:
  - Implemented `compute_candidate_affected_region` using directional shadow frustum projection.
  - Encompasses initial geometry footprint, modified geometry footprint, shadow projection envelopes, and a $2 \cdot \Delta x$ safety padding.
- **Low-Sun Stability Fallback**:
  - Automated detection of solar altitudes below numerical stability threshold ($\alpha < 5.0^\circ$).
  - Gracefully triggers clean fallback to full-domain recomputation (`is_fallback=True`).
- **Tests**: Created `tests/test_affected_region.py` (5 tests).

---

### Milestone 10: Closed-Form Computable Error Certificate Engine
- **Theoretical Bound Derivation ([certificate.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/certificate.py))**:
  - Direct shadow error bound: $\Delta S_{\mathrm{dir},\max}(x)$ via Minkowski shadow plume.
  - Solid-angle Sky View Factor distance decay:
    $$\Delta \psi_{\mathrm{svf},\max}(x) \leq \min\left(1.0, \frac{W_{\mathrm{proj}} \cdot |\Delta h|}{2\pi r^2}\right)$$
    with zero cutoff beyond maximum horizon search distance ($r > r_{\max} + r_{\mathrm{bbox}}$).
  - Diffuse and longwave flux sensitivity bounds.
  - **Concave Interval Stefan-Boltzmann Propagation**:
    $$B_T(x) = \left( \frac{S^{(0)}(x)}{\sigma} \right)^{1/4} - \left( \frac{\max(1.0, \, S^{(0)}(x) - \Delta S_{\max}(x))}{\sigma} \right)^{1/4}$$
    Strict concavity of $T(S) = (S/\sigma)^{1/4}$ ensures the lower-interval bound strictly dominates any upper-interval deviation, bounding both warming and cooling perturbations.
- **Certified Incremental Solver (`incremental_update_certified`)**:
  - Evaluates $B_T(x)$ in $O(1)$ operations per cell.
  - If $B_T(x) \le \varepsilon_T$: safely reuses cached cell.
  - If $B_T(x) > \varepsilon_T$: marks cell as dirty and recomputes.
- **Soundness Audit (`verify_certificate`)**:
  - Confirmed 0 violations across all 4 edits and multiple tolerance levels ($\varepsilon_T \in [0.1, 0.5, 1.0, 2.0]\,\text{K}$).
- **Tests**: Created `tests/test_error_bounds.py` (8 tests).

---

### Milestone 11: Adversarial Stress Testing & Comparative Benchmark
- **8 Adversarial Stress Test Cases ([test_adversarial_cases.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_adversarial_cases.py))**:
  1. *Small Height Delta ($20\,\text{m} \to 21\,\text{m}$)*: Verified differential height bound ($|\Delta h| = 1.0\,\text{m}$) yielding $>70\%$ certified reuse.
  2. *50m Perpendicular Wide Wall*: Bounded wide East-West obstacle shadow plume and broad SVF perturbation.
  3. *1m Thin Obstacle Aligned with Sun Vector*: Verified sub-cell raycasting stability without boundary leakage.
  4. *Occlusion Reveal*: Verified unmasked shadow capture when foreground building is removed.
  5. *Low Sun Altitude ($15.02^\circ$) Long Shadow*: Verified $>45\,\text{m}$ shadow plume projection across domain.
  6. *Ground Reflection/Diffuse Perturbation Outside Direct Shadow*: Verified non-zero diffuse/longwave delta bounded strictly by $B_T(x)$ where $\Delta S_{\mathrm{dir}} = 0$.
  7. *Grid Boundary Alignment*: Verified integer and half-integer coordinate alignment without edge artifacts.
  8. *Full-Domain Invalidation Fallback*: Verified massive obstacle edit triggering sound full-domain fallback.
- **Refinement in Height Bounds**:
  - Enhanced `ChangeHeightEdit.apply` to return the exact differential volume slice $[\min(h_0, h_1), \max(h_0, h_1)]$, yielding sound $\Delta h = |h_1 - h_0|$.
- **Initial Test Suite**: 82 unit and integration tests passing.
- **Initial Comparative Benchmark ([compare_full_incremental.py](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/examples/compare_full_incremental.py))**:
  - Evaluated on $80\,\text{m} \times 80\,\text{m}$ domain (6,400 cells) at $\varepsilon_T = 0.5\,\text{K}$.
  - Showed initial $1.22\times$ speedup with $27.6\%$ domain reused and zero certificate violations.

---

### Milestone 12: Baseline Documentation & Repository Hygiene
- **Repository Documentation (`README.md`)**:
  - Published comprehensive technical documentation covering mathematics, physics, directory structure, reproduction instructions, empirical findings, and limitations.
- **Security & Hygiene (`.gitignore`)**:
  - Added clean exclusion rules for virtual environments, secrets, caches, and binaries.
- **Initial Git Commit & Push**:
  - Staged and committed as `feat: implement certified incremental SOLWEIG microclimate simulation prototype` (`587e537`).

---

