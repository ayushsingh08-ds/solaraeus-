# SOLARAEUS: Certified Incremental SOLWEIG-Compatible Urban Thermal-Comfort Simulation

An experimental, CPU-based research prototype for **Certified Incremental SOLWEIG-Compatible Urban Thermal-Comfort Updates**.

The engine determines whether urban thermal-comfort fields can be safely reused after local 3D building edits while guaranteeing a computable, model-specific error bound against full recomputation:

$$|\widetilde{T}_{\mathrm{mrt}}(x) - T_{\mathrm{mrt}}^{\mathrm{full}}(x)| \leq B_T(x) \leq \varepsilon_T$$

where:
- $\widetilde{T}_{\mathrm{mrt}}(x)$ is the incrementally updated Mean Radiant Temperature at pedestrian level ($z = 1.1\,\text{m}$).
- $T_{\mathrm{mrt}}^{\mathrm{full}}(x)$ is the ground-truth field produced by full-domain recomputation.
- $B_T(x)$ is a closed-form, conservative upper bound derived in $O(1)$ operations per cell *prior* to expensive recomputation.
- $\varepsilon_T$ is the user-specified maximum acceptable error tolerance (in Kelvin).

---

## 1. Scientific & Physical Formulation

SOLARAEUS implements the core physics of the **SOLWEIG** (Solar and LongWave Environmental Irradiance Geometry) model for a single timestep over a discrete horizontal pedestrian grid:

### 1.1 Stefan-Boltzmann Inversion
Mean Radiant Temperature $T_{\mathrm{mrt}}$ is calculated by inverting the Stefan-Boltzmann law across total absorbed radiation flux density $S_{\mathrm{str}}$:
$$T_{\mathrm{mrt}}(x) = \left( \frac{S_{\mathrm{str}}(x)}{\sigma} \right)^{1/4} - 273.15$$
where $\sigma = 5.670374419 \times 10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}$ is the Stefan-Boltzmann constant, and:
$$S_{\mathrm{str}}(x) = \sum_{i=1}^6 F_i \cdot \left( a_k K_i(x) + a_l L_i(x) \right)$$

### 1.2 Human Body Geometry & Absorption
- Standard rotationally symmetric standing human cylinder:
  - $F_{\mathrm{up}} = F_{\mathrm{down}} = 0.06$ (top and bottom horizontal view factors)
  - $F_{\mathrm{north}} = F_{\mathrm{south}} = F_{\mathrm{east}} = F_{\mathrm{west}} = 0.22$ (cardinal side view factors)
- Absorption coefficients:
  - Shortwave absorptivity: $a_k = 0.70$
  - Longwave emissivity: $a_l = 0.97$

### 1.3 Shortwave Fluxes $K_i(x)$
- **Direct Solar Radiation**:
  $$K_{\mathrm{dir}, i}(x) = I_{\mathrm{dir}} \cdot S_{\mathrm{shadow}}(x) \cdot \cos(\theta_i)$$
  where $S_{\mathrm{shadow}}(x) \in \{0, 1\}$ is the direct line-of-sight binary visibility mask evaluated via 3D ray-AABB slab intersection, and $\theta_i$ is the incident angle to surface normal $i$.
- **Diffuse Sky Radiation**:
  $$K_{\mathrm{diff}, i}(x) = D_{\mathrm{diff}} \cdot \psi_{\mathrm{svf}, i}(x)$$
  where $\psi_{\mathrm{svf}}(x) \in [0, 1]$ is the Sky View Factor computed via multi-azimuth horizon elevation search.
- **Reflected Shortwave from Ground and Walls**:
  $$K_{\mathrm{refl, ground}}(x) = \alpha_{\mathrm{ground}} \cdot (I_{\mathrm{dir}} \sin(\alpha_{\mathrm{sun}}) S_{\mathrm{shadow}}(x) + D_{\mathrm{diff}})$$
  $$K_{\mathrm{refl, wall}}(x) = \alpha_{\mathrm{wall}} \cdot (1 - \psi_{\mathrm{svf}}(x)) \cdot K_{\mathrm{avg}}$$

### 1.4 Longwave Fluxes $L_i(x)$
- **Atmospheric Sky Longwave**:
  $$L_{\mathrm{sky}}(x) = \psi_{\mathrm{svf}}(x) \cdot \varepsilon_{\mathrm{air}} \sigma T_{\mathrm{air}}^4$$
  with air emissivity $\varepsilon_{\mathrm{air}} = 1.24 \cdot (e_{\mathrm{vap}} / T_{\mathrm{air}})^{1/7}$ (Brutsaert equation).
- **Building Wall Longwave**:
  $$L_{\mathrm{wall}}(x) = (1 - \psi_{\mathrm{svf}}(x)) \cdot \varepsilon_{\mathrm{wall}} \sigma T_{\mathrm{wall}}^4$$
- **Ground Longwave**:
  $$L_{\mathrm{ground}}(x) = \varepsilon_{\mathrm{ground}} \sigma T_{\mathrm{ground}}^4$$

### 1.5 Thermal Comfort
Universal Thermal Climate Index (UTCI) is computed from $T_{\mathrm{mrt}}$, $T_{\mathrm{air}}$, relative humidity, and 10m wind speed using the validated standard polynomial model, mapped into 10 thermal stress categories (from Extreme Cold Stress to Extreme Heat Stress).

---

## 2. Mathematical Error Certificate Formulation

The error certificate engine provides provable upper bounds on $\Delta T_{\mathrm{mrt}}(x)$ before recomputing any grid cells:

### 2.1 Total Radiation Perturbation Bound $\Delta S_{\max}(x)$
$$\Delta S_{\max}(x) = \Delta S_{\mathrm{dir},\max}(x) + \Delta S_{\mathrm{diff},\max}(x) + \Delta S_{\mathrm{long},\max}(x)$$

1. **Direct Shadow Error Bound $\Delta S_{\mathrm{dir},\max}(x)$**:
   Direct beam visibility $S_{\mathrm{shadow}}(x)$ can only change if a cell lies inside the **candidate shadow plume** (the Minkowski sum of the initial geometry shadow, the edited geometry shadow, and a $2 \cdot \Delta x$ safety margin).
   - If $x \notin \text{CandidatePlume}$: $\Delta S_{\mathrm{dir},\max}(x) = 0$.
   - If $x \in \text{CandidatePlume}$: $\Delta S_{\mathrm{dir},\max}(x) = a_k \cdot I_{\mathrm{dir}} \cdot (f_{\mathrm{up}} \sin\alpha + f_{\mathrm{side}} \cos\theta_{\max} + f_{\mathrm{down}} \alpha_g \sin\alpha)$.

2. **Sky View Factor Solid-Angle Distance Decay $\Delta \psi_{\mathrm{svf},\max}(x)$**:
   For any point $x$ at Euclidean distance $r = \operatorname{dist}(x, \Omega_{\mathrm{edit}})$ from the modified building envelope of projected width $W_{\mathrm{proj}}$ and differential height change $|\Delta h|$:
   $$\Delta \psi_{\mathrm{svf},\max}(x) \leq \min\left(1.0, \frac{W_{\mathrm{proj}} \cdot |\Delta h|}{2\pi r^2}\right)$$
   For cells beyond the maximum horizon search distance ($r > r_{\max} + r_{\mathrm{bbox}}$), $\Delta \psi_{\mathrm{svf},\max}(x) \equiv 0$.

3. **Diffuse and Longwave Bounds**:
   $$\Delta S_{\mathrm{diff},\max}(x) = a_k \cdot C_{\mathrm{diff}} \cdot \Delta \psi_{\mathrm{svf},\max}(x)$$
   $$\Delta S_{\mathrm{long},\max}(x) = a_l \cdot (f_{\mathrm{up}} + 2 f_{\mathrm{side}}) \cdot |\varepsilon_{\mathrm{air}} \sigma T_{\mathrm{air}}^4 - \varepsilon_w \sigma T_{\mathrm{wall}}^4| \cdot \Delta \psi_{\mathrm{svf},\max}(x)$$

### 2.2 Concave Interval Stefan-Boltzmann Propagation
Because the function $T(S) = (S/\sigma)^{1/4}$ is strictly concave on $S > 0$, its derivative $T'(S) = \frac{1}{4 \sigma^{1/4} S^{3/4}}$ is monotonically decreasing.
Therefore, the downward interval perturbation strictly exceeds the upward perturbation:
$$T(S^{(0)}) - T(S^{(0)} - \Delta S) \geq T(S^{(0)} + \Delta S) - T(S^{(0)})$$
Thus, evaluating the lower interval endpoint yields a guaranteed upper bound for both warming and cooling perturbations:
$$B_T(x) = \left( \frac{S^{(0)}(x)}{\sigma} \right)^{1/4} - \left( \frac{\max(1.0, \, S^{(0)}(x) - \Delta S_{\max}(x))}{\sigma} \right)^{1/4}$$

### 2.3 Decision Rule for Selective Recomputation
For each grid cell $x$:
- If $B_T(x) \leq \varepsilon_T$: **Reuse cached $T_{\mathrm{mrt}}(x)$** (Certificate holds; zero recomputation).
- If $B_T(x) > \varepsilon_T$: **Mark cell as dirty** (Recompute direct shadow, SVF, and fluxes only on dirty region).

---

## 3. Supported 3D Geometric Edits

The engine natively supports 4 atomic 3D geometric operations:
1. **`AddBuildingEdit`**: Inserts a new opaque rectangular prism building into the scene.
2. **`RemoveBuildingEdit`**: Removes an existing building, unmasking previously occluded sky and solar rays.
3. **`ChangeHeightEdit`**: Modifies building height $h_0 \to h_1$, computing the exact differential volume slice $\Delta h = |h_1 - h_0|$.
4. **`MoveBuildingEdit`**: Compound translation edit that shifts building footprint by $(\Delta x, \Delta y)$, updating both source and destination regions.

---

## 4. Repository Architecture

```text
solaraeus/
├── configs/
│   └── baseline_scene.json          # Canonical baseline scene configuration
├── examples/
│   ├── single_building.py           # Full reference simulation demonstration
│   └── compare_full_incremental.py  # End-to-end comparative benchmark script
├── results/                         # Generated benchmark artifacts (.npz, .png, .json)
├── src/
│   └── urban_comfort/
│       ├── config.py                # Data classes for Materials, Weather, SimulationConfig
│       ├── geometry/
│       │   ├── primitives.py        # BoundingBox2D, Building, GroundPlane
│       │   └── scene.py             # Scene container and synthetic scene generators
│       ├── solar/
│       │   └── solar_position.py    # NOAA astronomical solar position calculation
│       ├── grid/
│       │   └── pedestrian_grid.py   # Discrete 2D pedestrian grid mappings
│       ├── visibility/
│       │   ├── ray_intersection.py  # Vectorized Kay-Kajiya slab ray-AABB intersections
│       │   ├── shadow.py            # Direct beam solar shadow mask calculation
│       │   └── directional_visibility.py # Multi-azimuth horizon search for Sky View Factor
│       ├── radiation/
│       │   ├── shortwave.py         # 6-directional shortwave radiation fluxes
│       │   ├── longwave.py          # Sky, wall, and ground longwave fluxes
│       │   └── tmrt.py              # Stefan-Boltzmann inversion and Tmrt calculation
│       ├── comfort/
│       │   └── utci.py              # Vectorized UTCI polynomial & thermal stress categories
│       ├── reference/
│       │   └── full_recompute.py    # Ground-truth reference recomputation pipeline
│       ├── incremental/
│       │   ├── update.py            # Geometric edits, exact update, and certified update
│       │   ├── affected_region.py   # Minkowski shadow plume candidate region & safety padding
│       │   ├── certificate.py       # Computable error certificate engine & verification
│       │   ├── cache.py             # SHA-256 state hashing & simulation cache
│       │   └── dependency_graph.py  # DAG reachability and selective invalidation
│       ├── benchmark/
│       │   ├── baseline_comparison.py # Non-certified dirty box vs certified comparative harness
│       │   ├── harness.py           # Multi-trial statistical benchmarking engine (N=5, 95% CI)
│       │   ├── repeated_edits.py    # Sequential edit sequence and drift evaluation
│       │   ├── tightness.py         # Cell-by-cell certificate slack and ratio analysis
│       │   └── independent_reference.py # Analytical and external reference test harness
│       └── validation/
│           ├── comparisons.py       # Pointwise array comparison and error statistics
│           └── metrics.py           # Shadow IoU, UTCI agreement, percentiles
└── tests/                           # 94 automated tests (unit, integration, adversarial)
    ├── test_adversarial_cases.py    # 8 canonical adversarial stress test cases
    ├── test_adversarial_suite.py    # Parameterized adversarial suites
    ├── test_extended_adversarial.py # 12 extended stress test cases
    ├── test_certificate_soundness.py# Empirical certificate bounds verification
    ├── test_error_bounds.py         # Mathematical soundness unit tests
    ├── test_incremental_updates.py  # Exact zero-error update tests
    ├── test_affected_region.py      # Shadow plume projection and fallback tests
    ├── test_cache_and_dependencies.py # Cache hashing and DAG reachability tests
    ├── test_validation_comparisons.py # Statistical comparison metric tests
    ├── test_full_recompute.py       # End-to-end reference solver tests
    ├── test_geometry.py             # Bounding box and scene construction tests
    ├── test_pedestrian_grid.py      # Grid index and coordinate mapping tests
    ├── test_ray_intersections.py    # Vectorized ray-AABB intersection tests
    ├── test_shadows.py              # Direct shadow raycasting tests
    ├── test_solar_position.py       # Astronomical solar position verification tests
    └── test_solweig_reference.py    # Analytical reference comparisons
```

---

## 5. Installation & Requirements

### 5.1 Environment Prerequisites
- Python 3.10+ (Tested on Python 3.12.6)
- Core dependencies: `numpy`, `scipy`, `pytest`, `pythermalcomfort`, `shapely`, `matplotlib`

### 5.2 Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/ayushsingh08-ds/solaraeus.git
cd solaraeus
pip install numpy scipy pytest pythermalcomfort shapely matplotlib
```

---

## 6. How to Run Tests and Examples

### 6.1 Run the Full Test Suite (94 Tests)
To execute all 94 unit, integration, adversarial, and reference tests:
```bash
python -m pytest -o pythonpath=src -v
```
*Expected result: 94 passed with zero errors or failures.*

### 6.2 Run the Master Publication Validation Suite
To execute the comprehensive multi-trial benchmarking and validation suite (evaluates 34 experiments, 130 trials, repeated edits, baseline comparison, and tightness analysis):
```bash
python examples/run_publication_validation.py
```
Outputs complete CSV telemetry, JSON audit logs, and 9 publication-grade figures in `results/publication_validation_<timestamp>/`.

### 6.3 Run the Single-Building Reference Example
```bash
python examples/single_building.py
```
Outputs solar altitude, azimuth, direct shadow ratio, mean sunlit vs. shaded $T_{\mathrm{mrt}}$, UTCI thermal comfort categories, and execution timing breakdowns.

### 6.4 Run the Comparative Benchmark Experiment
```bash
python examples/compare_full_incremental.py
```
This script executes the baseline comparative protocol on an $80\,\text{m} \times 80\,\text{m}$ urban domain, comparing full recomputation against certified incremental updates, auditing empirical soundness, and exporting evaluation artifacts into `results/`.

---

## 7. Empirical Benchmark Results & Canonical Reconciliation

### 7.1 Canonical Benchmark Reconciliation Across Experimental Campaigns

Performance speedups and safe cell-reuse fractions depend directly on the geometric perturbation footprint relative to the overall domain size. Across the three experimental campaigns conducted on the prototype, results reconcile as follows:

| Experiment ID | Domain Size | Grid Cells | Edit Type & Magnitude | Reused Cells (%) | Full Recompute (s) | Incremental (s) | Measured Speedup | Max Error (K) | Violations |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`exp_80m_corner_infill`** | 80m x 80m | 6,400 | AddBuilding (corner quadrant) | 27.6% | 0.434s | 0.411s | **1.22x** | 0.000K | 0 |
| **`exp_80m_central_infill`** | 80m x 80m | 6,400 | AddBuilding (18m center infill) | 3.1% | 0.580s | 0.530s | **1.09x** | 0.000K | 0 |
| **`exp_80m_height_delta`** | 80m x 80m | 6,400 | ChangeHeight (20m -> 26m) | 69.5% | 0.274s | 0.218s | **1.53x** | 0.000K | 0 |
| **`exp_160m_central_infill`** | 160m x 160m | 25,600 | AddBuilding (18m center infill) | 70.9% | 0.849s | 0.242s | **3.50x** | 0.000K | 0 |
| **`exp_160m_height_delta`** | 160m x 160m | 25,600 | ChangeHeight (20m -> 26m) | 81.6% | 2.991s | 0.354s | **6.39x** | 0.019K | 0 |
| **`exp_320m_central_infill`** | 320m x 320m | 102,400 | AddBuilding (18m center infill) | 92.7% | 43.75s | 3.009s | **14.54x** | 0.000K | 0 |
| **`exp_320m_height_delta`** | 320m x 320m | 102,400 | ChangeHeight (20m -> 26m) | 96.5% | 35.96s | 1.368s | **23.14x** | 0.023K | 0 |

> **No certificate violations were observed in the evaluated configurations.**

#### Physical Cause of Performance Variations:
1. **Corner vs. Central Infill (80m)**: Placing an infill building at the domain boundary directs its shadow plume outside the evaluated mesh, leaving 27.6% of cells unperturbed (1.22x speedup). Placing the identical building at the center allows its 39.5m shadow plume and 30m SVF decay envelope to sweep across 96.9% of the compact grid, reducing clean cells to 3.1% (1.09x speedup).
2. **Central Infill vs. Height Delta (80m–320m)**: Modifying the height of an existing building ($\Delta h = +6\,\text{m}$) modifies a smaller differential volume than inserting a completely new 18m structure from ground level. As a result, height deltas retain substantially larger clean fractions (69.5% on 80m, 96.5% on 320m), yielding speedups from **1.53x** up to **23.14x**.
3. **Domain Expansion Amortization**: Because direct shadow and SVF horizon decays are bounded physical phenomena, expanding the domain quadratically expands the clean boundary area, scaling speedups from ~1.1x–1.5x at 80m to **14.5x–23.1x at 320m**.

### 7.2 Multi-Trial Timing Overhead Breakdown
The incremental pipeline records isolated wall-clock overhead across all phases:
- **Dependency & Candidate Region**: $\le 0.0003\,\text{s}$ ($< 0.01\%$ of runtime).
- **Certificate Evaluation**: $0.002\,\text{s} - 0.033\,\text{s}$ ($0.36\% - 1.43\%$ of incremental execution time).
- **Result Assembly & Verification**: $< 0.0005\,\text{s}$ ($< 0.02\%$ of runtime).
- **Total Overhead Ratio**: Total overhead constitutes **$\le 1.6\%$** of incremental execution time, confirming that bounding calculations introduce minimal computational penalty.

### 7.3 Comparison with Non-Certified Dirty-Region Baseline

| Method | Wall-Clock Time | Measured Speedup | Reused Cells | Max Actual Error | Violations Observed ($\varepsilon_T = 0.5\,\text{K}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full Recomputation** | $0.434\,\text{s}$ | $1.00\times$ | $0$ ($0\%$) | $0.000\,\text{K}$ | 0 |
| **Non-Certified Dirty Box (5m margin)** | $0.055\,\text{s}$ | $7.95\times$ | $5,775$ ($90.2\%$) | **$20.818\,\text{K}$** | **685 violations** |
| **Exact Incremental** | $0.411\,\text{s}$ | $1.06\times$ | $448$ ($7.0\%$) | $0.000\,\text{K}$ | 0 |
| **Certified Incremental** | $0.456\,\text{s}$ | $0.95\times$ | $200$ ($3.1\%$) | $0.000\,\text{K}$ | **0 (Zero)** |

---

## 8. Documented Assumptions, Verification Tiers & Known Limitations

### 8.1 5-Tier Verification & Validation Taxonomy
1. **Tier 1: Analytical Benchmark Verification**: Completed and passing. Geometric shadow length ($H/\tan\alpha$), Siegel & Howell finite vertical wall view factors, unobstructed SVF ($1.0$), and Stefan-Boltzmann radiant flux inversion match closed-form analytical solutions with errors $\le 10^{-7}$.
2. **Tier 2: Internal Numerical Validation**: Completed and passing across 11 scaling and edit configurations (>185,000 cells checked). Maximum observed actual error is $\le 0.023\,\text{K}$, strictly bounded by certificates with zero violations.
3. **Tier 3: External Compatibility Assessment**: Completed. The prototype formulation is conceptually aligned with SOLWEIG/UMEP v2023a conventions (Hoppe 1992 cylinder factors $0.06/0.06/0.22$, Brutsaert atmospheric emissivity), with input raster DSM adapters documented.
4. **Tier 4: External Numerical Validation**: Not performed. Numerical cross-validation against official QGIS UMEP outputs requires installing QGIS and UMEP plugin desktop environments.
5. **Tier 5: Field Validation**: Not performed. No in-situ microclimate sensor instrumentation or physical weather station campaigns have been conducted.

### 8.2 Strict Scientific Boundaries & Limitations
> **The certificate is conditional on the documented discrete grid, supported geometry, fixed materials, fixed surface temperatures, single timestep, and configured visibility horizon.**

> **The prototype is compatible with selected SOLWEIG conventions but has not been numerically cross-validated against official SOLWEIG outputs.**

> **UTCI is recomputed from the updated Tmrt under fixed air temperature, humidity, and wind inputs.**

> **The core modules were exercised by the automated test suite.**

1. **CPU-Only Execution**: The current prototype is implemented in pure Python with NumPy/SciPy vectorization.
2. **Single Timestep**: Boundary weather conditions and solar astronomical angles are evaluated at a single static instant.
3. **Flat Terrain & Axis-Aligned Prisms**: Ground elevation is currently modeled at $z = 0.0\,\text{m}$, and building footprints are axis-aligned rectangular bounding boxes.
4. **Low-Sun Fallback**: At solar altitudes $\alpha < 5.0^\circ$, shadow lengths grow towards infinity ($h / \tan\alpha$), triggering an automatic, sound fallback to full-domain recomputation.
5. **Physical Exclusions**: The model currently excludes computational fluid dynamics (CFD) wind fields, dynamic facade thermal mass, evapotranspiration, and vegetative canopies.
6. **Artifact Provenance**: The historical artifact `results/independent_audit_20261006_033239/` was generated under Indian Standard Time (UTC+05:30), where local time crossed midnight into October 6, 2026, while UTC was October 5, 2026. It is preserved untouched, and the official cleaned audit is established under `results/audit_cleanup_<timestamp_utc>/` with full UTC and Git provenance.

---

## 9. Future Acceleration Pathways

- **WebGPU / CUDA Acceleration**: Multi-azimuth horizon elevation searches and shadow raycasting are embarrassingly parallel; migrating grid sweeps to compute shaders offers significant parallel acceleration potential on GPU hardware.
- **Bounding Volume Hierarchies (BVH)**: Implementing a 2D/3D BVH (R-tree) will reduce shadow and SVF intersection tests from $O(N_{\mathrm{buildings}})$ to $O(\log N_{\mathrm{buildings}})$.
- **Multi-Timestep Temporal Caching**: Extending the certificate bound across diurnal solar trajectories to reuse microclimate calculations across adjacent time steps.
- **Non-Flat Topography & Arbitrary Meshes**: Generalizing the shadow frustum projection to digital elevation models (DEM) and arbitrary 3D triangular meshes.
