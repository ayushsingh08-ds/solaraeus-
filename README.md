# SOLARAEUS

> **A Physics-Based 3D Urban Microclimate Digital Twin with Certified Incremental Radiative Transfer, GPU Acceleration, and an AI Solver for Optimal Intervention Placement**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![CUDA Accelerated](https://img.shields.io/badge/cuda-12.x-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Table of Contents
1. [Overview & Core Motivation](#1-overview--core-motivation)
2. [Physics & Biometeorological Formulation](#2-physics--biometeorological-formulation)
3. [Certified Incremental Radiative Transfer (Theorem 1)](#3-certified-incremental-radiative-transfer-theorem-1)
4. [Dual-Backend Architecture (CPU & CUDA GPU)](#4-dual-backend-architecture-cpu--cuda-gpu)
5. [AI Placement Solver & Active Learning](#5-ai-placement-solver--active-learning)
6. [Real-World Case Study: Church Street, Bengaluru Digital Twin](#6-real-world-case-study-church-street-bengaluru-digital-twin)
7. [Terrain (DTM) & Vegetation Extensions](#7-terrain-dtm--vegetation-extensions)
8. [Interactive 3D WebGL Digital Twin](#8-interactive-3d-webgl-digital-twin)
9. [Mathematical Symbol ↔ Code Token Trace](#9-mathematical-symbol--code-token-trace)
10. [Repository Structure & Module Inventory](#10-repository-structure--module-inventory)
11. [Installation & Requirements](#11-installation--requirements)
12. [Quickstart & Execution Workflows](#12-quickstart--execution-workflows)
13. [Documented Limitations & Scientific Boundaries](#13-documented-limitations--scientific-boundaries)

---

## 1. Overview & Core Motivation

Pedestrian heat stress poses an escalating public health crisis in rapidly densifying tropical metropolises. Traditional urban microclimate simulation packages suffer from fundamental computational bottlenecks:
- **CFD Suites (e.g., ENVI-met)**: Simulate coupled Navier–Stokes turbulence and vegetative biology, but require hours to days of CPU processing for a single diurnal cycle, precluding iterative exploration.
- **Decoupled Radiation Models (e.g., SOLWEIG / UMEP, RayMan, Ladybug)**: Substantially accelerate ray calculations, yet operate as monolithic batch programs: whenever a localized architectural alteration (e.g., a shade canopy or tree planting) is introduced, the engine discards the domain and recalculates all grid cells from scratch.
- **Lack of Certified Error Bounds**: Heuristic spatial clipping methods lack a mathematically rigorous guarantee that untouched cells do not exceed an acceptable thermal tolerance ($|\widetilde{T}_{\mathrm{mrt}}(x) - T_{\mathrm{mrt}}^{\mathrm{full}}(x)| \le \varepsilon_T$).
- **Absence of Autonomous AI Solvers**: Urban planners rely on manual trial-and-error placement because the multi-parameter combinatorial search space of 3D canopy coordinates, dimensions, orientations, and clearance constraints cannot be practically traversed by brute-force simulations.

**SOLARAEUS** resolves these challenges by providing:
1. **Certified Incremental Solver**: Formulates and proves a closed-form error bound ($B_T(x) \le \varepsilon_T = 0.50\,\mathrm{K}$) grounded in concave Stefan–Boltzmann linearization and solid-angle horizon truncation decay, reusing over **99.74%** of static grid cells.
2. **Resident GPU Acceleration**: Executes high-throughput double-precision (FP64) CUDA C++ ray-triangle and horizon reduction kernels directly in GPU VRAM (NVIDIA RTX 4050), executing incremental updates in **$11.40\,\mathrm{ms}$** (**$500.87\times$ speedup** over full CPU recomputation; **$36.84\times$** over CPU incremental recomputation).
3. **Active Learning AI Placement Solver**: Couples 5-stage geometric feasibility screening ($94.9\%$ pruning rate), a 20-dimensional permutation-invariant feature embedding, multi-target decision-tree ensembles (Random Forest / Extra-Trees), and Upper Confidence Bound (UCB) acquisition to autonomously discover Pareto-optimal shade installations.
4. **Interactive 3D WebGL Digital Twin**: Connects typed JSON data contracts to a modern Three.js r128 browser runtime with real-time GLSL thermal shaders, diurnal timeline scrubbing, and pedestrian comfort HUDs.

---

## 2. Physics & Biometeorological Formulation

SOLARAEUS models outdoor radiative transfer and human energy exchange across a discrete 2D pedestrian grid ($z_{\mathrm{ped}} = 1.1\,\mathrm{m}$ eye level):

```
       +-----------------------------------------------------------+
       |             Astronomical Solar Vector Tracking            |
       |                  (Altitude α_s, Azimuth φ_s)              |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |           Möller-Trumbore 3D Ray-Mesh Occlusion           |
       |                Direct Shadow Mask S(u, v) ∈ {0, 1}        |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |             Steyn (1980) Sky View Factor (SVF)            |
       |                32/36-Azimuth Radial Ray-Marching          |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |            6-Flux Shortwave (K_i) & Longwave (L_i)         |
       |                Fanger Rotationally Symmetric Cylinder     |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |               Stefan-Boltzmann Inversion Law              |
       |              Mean Radiant Temperature T_mrt (K)           |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |                 UTCI Biometeorological Stress             |
       |                Universal Thermal Climate Index            |
       +-----------------------------------------------------------+
```

### 2.1 Astronomical Solar Vector Tracking
Using NOAA astronomical solar position algorithms, local solar altitude ($\alpha_s$) and True North solar azimuth ($\phi_s$) are evaluated for given timestamps, geographic coordinates, and local UTM grid convergence angles ($\gamma$).

### 2.2 3D Möller–Trumbore Ray-Traced Direct Shadows
Line-of-sight occlusions between each receptor point and the unit sun vector $\vec{s}$ are evaluated via double-precision Möller–Trumbore ray-triangle intersection:
$$\begin{bmatrix} t \\ u_b \\ v_b \end{bmatrix} = \frac{1}{\vec{P} \cdot \vec{E}_1} \begin{bmatrix} \vec{Q} \cdot \vec{E}_2 \\ \vec{P} \cdot \vec{T} \\ \vec{Q} \cdot \vec{D} \end{bmatrix}$$
yielding binary shadow mask $\mathcal{S}(u, v) \in \{0, 1\}$.

### 2.3 Steyn (1980) Sky View Factor (SVF)
Sky View Factor $\Psi_{\mathrm{svf}}(u, v) \in [0, 1]$ is computed across $N_\phi$ discrete azimuth search radials:
$$\Psi_{\mathrm{svf}}(u, v) = \frac{1}{N_\phi} \sum_{j=1}^{N_\phi} \bigl(1 - \sin \beta(u, v, \phi_j)\bigr)$$
where $\tan \beta(u, v, \phi_j) = \max_{r \in (0, R_{\max}]} \frac{z_{\mathrm{mesh}}(u_r, v_r) - z_{\mathrm{ped}}}{r}$.

### 2.4 Six-Flux Human Radiation Balance
Radiant flux density absorbed by a pedestrian is resolved on Fanger's cylindrical human geometry:
$$\Phi_{\mathrm{tot}}(u, v) = \alpha_p \sum_{i=1}^6 F_i K_i(u, v) + \varepsilon_p \sum_{i=1}^6 F_i L_i(u, v)$$
- Geometric view factors: $F_{\mathrm{up}} = F_{\mathrm{down}} = 0.06$, $F_{\mathrm{sides}} = 0.22$.
- Human absorption properties: Shortwave absorptivity $\alpha_p = 0.70$, Longwave emissivity $\varepsilon_p = 0.97$.
- Shortwave components ($K_i$): Direct beam $K_{\mathrm{dir}} = I_{\mathrm{dir}} \mathcal{S}$, diffuse sky $K_{\mathrm{diff}} = I_{\mathrm{diff}} \Psi_{\mathrm{svf}}$, and reflected fluxes from walls and ground pavements.
- Longwave components ($L_i$): Atmospheric sky emission $L_{\mathrm{down}} = \Psi_{\mathrm{svf}} \varepsilon_{\mathrm{air}} \sigma T_{\mathrm{air}}^4 + (1 - \Psi_{\mathrm{svf}}) \varepsilon_{\mathrm{wall}} \sigma T_{\mathrm{wall}}^4$.

### 2.5 Mean Radiant Temperature ($T_{\mathrm{mrt}}$)
Inverting the Stefan–Boltzmann law across total absorbed radiant flux yields:
$$T_{\mathrm{mrt}}(u, v) = \left( \frac{\Phi_{\mathrm{tot}}(u, v)}{\sigma} \right)^{1/4}$$
where $\sigma = 5.670374419 \times 10^{-8}\,\mathrm{W/(m^2\,K^4)}$.

### 2.6 Universal Thermal Climate Index (UTCI)
Calculated via the operational multi-node human thermoregulation model polynomial from `pythermalcomfort`:
$$\mathrm{UTCI} = f_{\mathrm{poly}}(T_a, T_{\mathrm{mrt}}, v_{1.1}, \mathrm{RH})$$

---

## 3. Certified Incremental Radiative Transfer (Theorem 1)

When an urban intervention $\mathcal{P}$ (e.g., shade canopy or building alteration) is introduced, SOLARAEUS partitions the simulation domain into dirty cells $\Omega_{\mathrm{dirty}}$ and invariant clean cells $\Omega_{\mathrm{clean}} = \Omega \setminus \Omega_{\mathrm{dirty}}$ using closed-form error certificates.

### Definition: Thermal Error Certificate
An incremental update is **certified safe** with user tolerance $\varepsilon_T$ if:
$$|\widetilde{T}_{\mathrm{mrt}}(x) - T_{\mathrm{mrt}}^{\mathrm{full}}(x)| \le B_T(x) \le \varepsilon_T, \quad \forall x \in \Omega_{\mathrm{clean}}$$

### Theorem 1 (Closed-Form Stefan–Boltzmann Bound)
Let $\Delta \Phi_{\max}(x)$ be an upper bound on radiant flux perturbation at cell $x$ caused by intervention $\mathcal{P}$, and let $T_{\min} \ge 273.15\,\mathrm{K}$. Then:
$$B_T(x) = \frac{\Delta \Phi_{\max}(x)}{4 \sigma T_{\min}^3} \le \varepsilon_T$$

**Proof:** Let $\Phi_1, \Phi_2$ denote baseline and intervention radiant fluxes at $x$. By the Mean Value Theorem on $g(\Phi) = (\Phi/\sigma)^{1/4}$:
$$|T_{\mathrm{mrt}, 2} - T_{\mathrm{mrt}, 1}| = \frac{|\Delta \Phi|}{4 \sigma^{1/4} \xi^{3/4}} \le \frac{|\Delta \Phi_{\max}(x)|}{4 \sigma T_{\min}^3}$$
since $\xi \ge \sigma T_{\min}^4$. Setting $\Delta \Phi_{\max}(x) \le 4 \sigma T_{\min}^3 \varepsilon_T$ guarantees the certificate. $\blacksquare$

### Solid-Angle Horizon Distance Decay
The flux perturbation decays quadratically with Euclidean distance $r(x) = \mathrm{dist}(x, \mathcal{P})$ according to the solid-angle horizon cutoff:
$$\Delta \Psi_{\mathrm{svf}}(x) \le \min\left(1.0, \frac{W_{\mathcal{P}} H_{\mathcal{P}}}{2\pi r(x)^2}\right)$$

Cells where $B_T(x) > \varepsilon_T$ or where direct solar rays intersect $\mathcal{P}$ form $\Omega_{\mathrm{dirty}}$; all remaining cells retain baseline values with certified zero error.

### Empirical Parity & Work Avoidance (Church Street Intervention)
| Evaluated Field | Unit | Documented Tolerance | Observed Max Error | Observed Mean Error | Parity Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Direct Shadow Mask** | - | $0.00$ | **$0.000000$** | $0.000000$ | **PASS (Bitwise Exact)** |
| **Direct SW Flux** | $\mathrm{W/m^2}$ | $0.00$ | **$0.000000$** | $0.000000$ | **PASS (Bitwise Exact)** |
| **Sky View Factor ($\Psi_{\mathrm{svf}}$)** | - | $0.01$ | **$0.004195$** | $2.01 \times 10^{-6}$ | **PASS** |
| **Total Shortwave Flux** | $\mathrm{W/m^2}$ | $0.50$ | **$0.128809$** | $6.17 \times 10^{-5}$ | **PASS** |
| **Total Longwave Flux** | $\mathrm{W/m^2}$ | $0.50$ | **$0.129326$** | $6.19 \times 10^{-5}$ | **PASS** |
| **Mean Radiant Temp ($T_{\mathrm{mrt}}$)** | $\mathrm{K}$ | $0.50$ | **$0.028902$** | $1.39 \times 10^{-5}$ | **PASS** |
| **UTCI Thermal Comfort** | $^{\circ}\mathrm{C}$ | $0.50$ | **$0.100000$** | $3.56 \times 10^{-6}$ | **PASS** |

- **Recomputed Dirty Cells**: $72$ cells ($0.26\%$)
- **Reused Clean Cells**: $28{,}048$ cells ($99.74\%$)
- **Ray Work Avoidance**: $925{,}584$ rays avoided ($99.74\%$ reduction)
- **Certificate Violations**: **0 (Zero across all audited proposals)**

---

## 4. Dual-Backend Architecture (CPU & CUDA GPU)

The SOLARAEUS computational engine implements a clean backend abstraction (`solaraeus.backends`):

```
                      +------------------------+
                      |    SimulationConfig    |
                      | (backend: cpu/gpu/auto)|
                      +-----------+------------+
                                  |
                                  v
                      +------------------------+
                      |   SimulationBackend    |
                      +-----------+------------+
                                  |
               +------------------+------------------+
               |                                     |
               v                                     v
      +-----------------+                   +-----------------+
      |   CPUBackend    |                   |   GPUBackend    |
      | (NumPy Ref.)    |                   | (CUDA C++ JIT)  |
      +-----------------+                   +-----------------+
               |                                     |
               |                                     v
               |                            +-----------------+
               |                            | CuPy RawModule  |
               |                            | - MT Shadow     |
               |                            | - SVF Horizon   |
               |                            +-----------------+
               |                                     |
               +------------------+------------------+
                                  |
                                  v
                      +------------------------+
                      |    SimulationResult    |
                      +------------------------+
```

### 4.1 Backend Engine Details
- **`CPUBackend`**: Vectorized NumPy and CPU Möller–Trumbore ray intersection. Serves as trusted reference ground truth.
- **`GPUBackend`**: High-performance CUDA C++ ray-tracing engine executed via CuPy `RawModule` and JIT compilation. Employs full IEEE-754 64-bit Double Precision (`double` / FP64) inside kernels to maintain machine-level numerical parity ($10^{-14}$) with CPU reference.
- **`GPUIncrementalEngine`**: Maintains static scene geometry (123 buildings, 2,136 triangles) and baseline fields permanently resident in device VRAM. Dynamic intervention meshes upload in $< 18\,\mathrm{ms}$. Active thread blocks evaluate CUDA kernels strictly over $\Omega_{\mathrm{dirty}}$.

### 4.2 Multi-Trial Benchmark Telemetry (NVIDIA GeForce RTX 4050 Laptop GPU)
| Execution Pathway | Total Pipeline (s) | Kernel Latency (ms) | Speedup vs CPU Full | Speedup vs CPU Incr | Work Avoided |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **CPU Full Recompute** | $5.71 \pm 0.04\,\mathrm{s}$ | - | $1.0\times$ (base) | - | $0.0\%$ |
| **CPU Incremental** | $0.42 \pm 0.01\,\mathrm{s}$ | - | **$13.6\times$** | $1.0\times$ (base) | $99.74\%$ |
| **GPU Full Recompute** | $0.133 \pm 0.01\,\mathrm{s}$ | $54.43\,\mathrm{ms}$ | **$69.1\times$** | $3.16\times$ | $0.0\%$ |
| **GPU Incremental** | **$0.0114 \pm 0.001\,\mathrm{s}$** | **$11.40\,\mathrm{ms}$** | **$500.87\times$** | **$36.84\times$** | **$99.74\%$** |

- **Peak Device VRAM**: $1{,}089.45\,\mathrm{MB}$

---

## 5. AI Placement Solver & Active Learning

Identifying optimal shade structure coordinates, orientations, and dimensions across complex urban corridors constitutes a non-convex, constrained optimization problem. SOLARAEUS couples multi-target decision-tree ensembles with an active learning search loop.

```
+--------------------------------------------------------------------------+
|                  1. Candidate Proposal Generation                        |
|   Single-Panel (p ∈ R^7) or Dual-Panel Multi-Intervention (p ∈ R^14)     |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                  2. 5-Stage Geometric Feasibility Filter                 |
|  Corridor Polygon, Facade Setback ≥ 1m, Clearance ≥ 3.5m, Sep ≥ 2m       |
|                 (Prunes 94.9% of invalid candidates)                     |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|            3. Permutation-Invariant 20-D Feature Embedding               |
|      Canonical Lexicographical Sorting + Interaction Metrics             |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|             4. Multi-Target Decision-Tree Ensemble Surrogate             |
|        Random Forest / Extra-Trees (100 trees, 7 physical targets)        |
|               Uncertainty σ^(p) without O(N^3) Matrix Inversion          |
+------------------------------------+-------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|             5. Active Learning Acquisition & GPU Verification            |
|       Upper Confidence Bound (UCB): α(p) = J^(p) + 1.96 · σ(p)           |
|            Dispatches to Resident GPU Kernel (11.4 ms/eval)              |
+--------------------------------------------------------------------------+
```

### 5.1 Canonical Lexicographical Parameterization
For dual-canopy configurations ($\mathbf{p} = [\mathbf{p}_1, \mathbf{p}_2] \in \mathbb{R}^{14}$), swapping panel indices $(\mathbf{p}_1 \leftrightarrow \mathbf{p}_2)$ represents identical physical reality. To eliminate combinatorial symmetry, the AI solver enforces canonical ordering ($x_1 < x_2$, or $y_1 < y_2$ when $|x_1 - x_2| < 0.1\,\mathrm{m}$).

### 5.2 Geometric Feasibility Screening
Before physical ray tracing, proposals undergo 5-stage geometric validation:
1. **Corridor Polygon Containment**: All 4 vertices must lie inside the street boundary.
2. **Facade Setback**: Minimum clearance to building walls $d_{\mathrm{facade}} \ge 1.0\,\mathrm{m}$ for emergency egress.
3. **Vehicle Clearance**: Underside height $H_k \ge 3.5\,\mathrm{m}$.
4. **Mutual Separation**: Panel centroids must maintain $d_{\mathrm{sep}} \ge 2.0\,\mathrm{m}$.
5. **Area Budget**: Combined canopy footprint $A_1 + A_2 \le 30.0\,\mathrm{m}^2$.
*Rejection rate: over **94.9%** of proposals are pruned upfront.*

### 5.3 20-Dimensional Feature Embedding
$$\mathbf{z}(\mathbf{p}) = [x_1, y_1, L_1, W_1, H_1, \theta_1, \alpha_1, A_1, x_2, y_2, L_2, W_2, H_2, \theta_2, \alpha_2, A_2, A_{\mathrm{tot}}, d_{\mathrm{center}}, d_{\mathrm{sep}}, \Delta H]^\top$$

### 5.4 Multi-Target Ensemble Architecture
Replaces $\mathcal{O}(N^3)$ Gaussian process inversion with randomized tree ensembles ($N_{\mathrm{trees}} = 100$, $D_{\max} = 12$) predicting 7 simultaneous physical metrics: composite score $\mathcal{J}$, corridor mean $T_{\mathrm{mrt}}$, 90th-percentile UTCI, mean UTCI, $\Delta T_{\mathrm{mrt}}$, peak localized cooling, and construction cost. Ensemble variance directly quantifies spatial epistemic uncertainty:
$$\widehat{\sigma}^2(\mathbf{p}) = \frac{1}{N_{\mathrm{trees}}} \sum_{t=1}^{N_{\mathrm{trees}}} \bigl(\widehat{y}_t(\mathbf{p}) - \overline{y}(\mathbf{p})\bigr)^2$$

### 5.5 Optimal Intervention Discovery
Across $4{,}401$ evaluated dual-canopy proposals on Church Street:
- **Optimal Dual-Canopy Winner (`CAND_4196_SURR`)**:
  - Panel 1: Centroid $(124.02\,\mathrm{m}, 59.63\,\mathrm{m})$, $6.76\,\mathrm{m} \times 2.07\,\mathrm{m}$ at $3.79\,\mathrm{m}$ height, orientation $113.8^\circ$ ($14.01\,\mathrm{m}^2$).
  - Panel 2: Centroid $(151.94\,\mathrm{m}, 59.04\,\mathrm{m})$, $3.85\,\mathrm{m} \times 2.30\,\mathrm{m}$ at $4.16\,\mathrm{m}$ height, orientation $93.7^\circ$ ($8.86\,\mathrm{m}^2$).
  - Total Area: $22.87\,\mathrm{m}^2$, Mutual Separation: $22.45\,\mathrm{m}$.
  - **Mutual Shadow Overlap**: **$0.0\,\mathrm{m}^2$ (Zero overlap)**.
  - **Peak Localized $T_{\mathrm{mrt}}$ Reduction**: **$12.68\,\mathrm{K}$**.
  - **Composite Objective Score $\mathcal{J}$**: **$56.57$**.

---

## 6. Real-World Case Study: Church Street, Bengaluru Digital Twin

To evaluate SOLARAEUS on an authentic, high-density tropical pedestrian corridor, Church Street in central Bengaluru ($12.9749^\circ\,\mathrm{N}, 77.6054^\circ\,\mathrm{E}$) was selected.

### 6.1 Geospatial Digital Twin Parameters
| Parameter | Symbol | Value | Unit |
| :--- | :---: | :---: | :---: |
| Coordinate Reference System | CRS | UTM Zone 43N | EPSG:32643 |
| Local Origin Coordinates | $(X_0, Y_0)$ | $(782{,}541.81, 1{,}435{,}736.11)$ | $\mathrm{m}$ |
| Grid Convergence Angle | $\gamma$ | $+0.5854$ | $\mathrm{deg}$ |
| Simulation Domain Extent | $\Omega$ | $380.0 \times 296.0$ | $\mathrm{m}$ |
| Grid Resolution | $\Delta x, \Delta y$ | $2.0 \times 2.0$ | $\mathrm{m}$ |
| Active Receptors | $N_{\mathrm{grid}}$ | $28{,}120$ | cells |
| Total Buildings | $N_{\mathrm{bldg}}$ | 123 (37 core, 86 context) | structures |
| Triangulated Watertight Meshes | $N_{\mathrm{tri}}$ | $2{,}136$ | triangles |
| Solar Altitude | $\alpha_s$ | $57.9160$ | $\mathrm{deg}$ |
| Solar Azimuth (Grid North) | $\phi_{\mathrm{grid}}$ | $267.5802$ | $\mathrm{deg}$ |
| Ambient Air Temperature | $T_a$ | $35.0$ | $^{\circ}\mathrm{C}$ |
| Relative Humidity | $\mathrm{RH}$ | $19.73$ | $\%$ |
| Pedestrian Wind Speed ($1.1\,\mathrm{m}$) | $v_{1.1}$ | $1.1$ | $\mathrm{m/s}$ |
| Global Horizontal Irradiance | $\mathrm{GHI}$ | $755.97$ | $\mathrm{W/m^2}$ |
| Direct Normal Irradiance | $\mathrm{DNI}$ | $728.31$ | $\mathrm{W/m^2}$ |
| Diffuse Horizontal Irradiance | $\mathrm{DHI}$ | $172.18$ | $\mathrm{W/m^2}$ |

### 6.2 Baseline Heat Stress vs. Single Intervention Impact
- **Baseline Corridor Conditions**: $97.0\%$ of corridor cells receive direct unshaded sun, yielding mean $T_{\mathrm{mrt}} = 45.81^\circ\mathrm{C}$ and UTCI $= 36.49^\circ\mathrm{C}$ (*Strong Heat Stress*).
- **Single-Canopy Intervention (`BLR_SHADE_001`, $6.0\,\mathrm{m} \times 3.0\,\mathrm{m}$)**: Delivers average localized cooling of $-10.03\,\mathrm{K}$ $T_{\mathrm{mrt}}$ (peak **$-12.62\,\mathrm{K}$**) and average UTCI relief of $-2.43\,\mathrm{K}$ (peak **$-3.10\,\mathrm{K}$**), downgrading pedestrian sensation to *Moderate Heat Stress*.

---

## 7. Terrain (DTM) & Vegetation Extensions

SOLARAEUS includes extensible scientific modules for non-flat topography and urban tree canopies:
- **Digital Terrain Models (`solaraeus.extensions.terrain`)**: The [`TerrainGrid`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/solaraeus/extensions/terrain/dtm.py) class supports regular elevation rasters, bilinear height interpolation, slope/aspect evaluation, and synthetic/FABDEM regional topography on both CPU and GPU backends.
- **Level 1 Vegetation Geometry (`solaraeus.extensions.vegetation`)**: Street trees cataloged from Bruhat Bengaluru Mahanagara Palike (BBMP) census data are modeled in [`tree.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/solaraeus/extensions/vegetation/tree.py) as cylindrical trunks and ellipsoidal crowns, incorporating Beer–Lambert shortwave canopy extinction priors.

---

## 8. Interactive 3D WebGL Digital Twin

Located in [`simulation_3d/`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/simulation_3d/):
- **Core Engine**: Three.js (r128) WebGL application with OrbitControls.
- **Custom Shaders**: Real-time GLSL thermal fragment shaders ([`heatmapShader.js`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/simulation_3d/heatmapShader.js)) rendering continuous $T_{\mathrm{mrt}}$, UTCI, and cooling delta fields.
- **Interactive Controls**: Diurnal solar timeline scrubber (06:00 to 18:00), scenario comparison toggles (`baseline`, `trees`, `panels`, `combined`), point-of-interest (POI) 3D pins, and avatar microclimate HUD.
- **Serving the Viewer**:
  ```bash
  python -m http.server 8000 --directory simulation_3d
  ```
  Navigate to `http://localhost:8000` in any modern WebGL-compatible browser.

---

## 9. Mathematical Symbol ↔ Code Token Trace

To ensure scientific transparency between publication manuscripts and software implementation, the following reconciliation table traces authoritative mathematical definitions to active source code tokens:

| Paper Symbol | Formal Description | Code Location | Active Token Name |
| :--- | :--- | :--- | :--- |
| $\varepsilon_T$ | Thermal error tolerance (K) | `solaraeus/core/config.py` | `SimulationConfig.tmrt_tolerance_k` |
| $B_T(x)$ | Closed-form error certificate bound (K) | `solaraeus/incremental/certificate.py` | `ErrorCertificate.predicted_error_bound_k` |
| $\Psi_{\mathrm{svf}}$ | Sky View Factor in $[0, 1]$ | `solaraeus/physics/sky_view_factor.py` | `compute_sky_view_factor()` / `svf` |
| $\vec{s}$ | 3D unit sun vector $(s_x, s_y, s_z)$ | `solaraeus/physics/solar_position.py` | `SolarPosition.sun_vector` |
| $\mathcal{S}(u,v)$ | Direct binary shadow mask | `solaraeus/physics/shadow.py` | `compute_direct_shadow_mask()` |
| $K_i, L_i$ | Shortwave / Longwave directional fluxes | `solaraeus/physics/shortwave.py`, `longwave.py` | `compute_shortwave_fluxes()`, `compute_longwave_fluxes()` |
| $\Phi_{\mathrm{tot}}$ | Total absorbed radiant flux density ($S_{\mathrm{str}}$) | `solaraeus/physics/mean_radiant_temperature.py` | `RadiantState.s_str` |
| $T_{\mathrm{mrt}}$ | Mean Radiant Temperature (Kelvin / Celsius) | `solaraeus/physics/mean_radiant_temperature.py` | `mean_radiant_temperature()` (`tmrt_k`, `tmrt_c`) |
| $\mathrm{UTCI}$ | Universal Thermal Climate Index ($^{\circ}\mathrm{C}$) | `solaraeus/physics/utci.py` | `compute_utci()` |
| $\Omega_{\mathrm{dirty}}$ | Candidate recomputation cells | `solaraeus/incremental/affected_region.py` | `AffectedRegionResult.candidate_mask` |
| $\mathbf{p}_k$ | 7-D single-panel parameter vector | `solaraeus/placement/parameters.py` | `ShadePanelParams` |
| $\mathbf{p}$ | 14-D dual-panel parameter vector | `solaraeus/placement/dual_panel_parameters.py`| `DualPanelParams` |
| $\mathbf{z}(\mathbf{p})$ | 20-D permutation-invariant embedding | `solaraeus/placement/dual_panel_surrogate_model.py`| `extract_dual_panel_features()` |
| $\mathcal{J}$ | Composite optimization objective score | `solaraeus/placement/dual_panel_objective.py` | `compute_dual_panel_objective()` |
| $\alpha_{\mathrm{ucb}}$ | Upper Confidence Bound acquisition | `solaraeus/placement/acquisition.py` | `compute_lcb_score()` (sign-flipped UCB) |

---

## 10. Repository Structure & Module Inventory

```text
solaraeus/
├── configs/                         # Canonical simulation and scene configurations
│   └── baseline_scene.json          # Canonical test scene (80m × 80m domain)
├── data/                            # Curated geospatial and environmental datasets
│   ├── benchmark/                   # Benchmark elevation profiles & test geometries
│   ├── processed/                   # Approved building footprints, heights, & signoffs
│   └── review/                      # Municipal census datasets & uncertainty records
├── examples/                        # Standalone evaluation & demonstration scripts
│   ├── single_building.py           # Full reference simulation demonstration
│   ├── compare_full_incremental.py  # Comparative CPU benchmark runner
│   └── run_publication_validation.py# Multi-trial publication verification runner
├── research_paper_sol/              # IEEE conference publication package
│   ├── solaraeus.tex                # Authoritative IEEE 2-column LaTeX manuscript
│   ├── fig1_architecture.png / .tex# System architecture diagram & TikZ vector source
│   ├── fig2_incremental.png         # Certified incremental workflow diagram
│   ├── fig3_gpu_engine.png          # GPU resident-memory acceleration diagram
│   └── fig4_optimization.png        # AI solver active learning workflow diagram
├── results/                         # Frozen benchmarks, audit logs, & stage reports
├── scripts/                         # Stage execution pipelines (Stages 05–38) & tooling
│   ├── run_church_street_*.py       # High-resolution Church Street simulation workflows
│   └── generate_ieee_figures.py     # Publication figure generation script
├── simulation_3d/                   # Interactive Three.js 3D WebGL Digital Twin viewer
│   ├── index.html                   # Cinematic WebGL web application entry point
│   ├── index.css                    # Design system (typography, glassmorphism, HUD)
│   ├── app.js                       # Scene controller, Three.js shaders, & avatar HUD
│   ├── heatmapShader.js             # Custom GLSL fragment thermal shader
│   ├── church_street_data.json      # Church Street 3D meshes & simulation payload
│   └── fonts/ & vendor/             # Self-contained web fonts and Three.js libraries
├── src/solaraeus/                   # Core physics and simulation package
│   ├── core/                        # Configs, materials, meshes, and pedestrian grids
│   │   ├── config.py                # Weather, SimulationConfig, and Material schemas
│   │   ├── geometry/                # TriangleMesh, Primitives, Scene data structures
│   │   ├── pedestrian_grid.py       # Receptor grid coordinate mapping
│   │   └── serialization_compat.py  # Backward-compatible physical unit alias shim
│   ├── physics/                     # Physical transfer & biometeorological solvers
│   │   ├── solar_position.py        # Astronomical solar vector equations
│   │   ├── ray_intersection.py      # Möller–Trumbore ray-triangle & ray-AABB tests
│   │   ├── shadow.py                # Direct solar shadow mask computation
│   │   ├── sky_view_factor.py       # Steyn multi-azimuth SVF horizon search
│   │   ├── shortwave.py             # 6-flux shortwave solar balance
│   │   ├── longwave.py              # Atmospheric & surface longwave balance
│   │   ├── mean_radiant_temperature.py # Stefan–Boltzmann inversion
│   │   └── utci.py                  # Universal Thermal Climate Index
│   ├── backends/                    # Dual-backend execution abstractions
│   │   ├── base.py                  # SimulationBackend abstract base class
│   │   ├── cpu.py                   # CPU reference backend (NumPy)
│   │   ├── gpu.py                   # CUDA C++ kernels & CuPy backend
│   │   └── gpu_incremental.py       # Resident VRAM GPU incremental engine
│   ├── pipeline/                    # Unified 5-Stage Microclimate Pipeline Architecture
│   │   ├── config.py                # Pipeline execution dataclass & area settings
│   │   ├── stage1_data_ingestion.py # Ingestion: GIS vectors, heights, terrain, & grids
│   │   ├── stage2_calculation.py    # Calculation: Baseline solar raytracing, Tmrt, & UTCI
│   │   ├── stage3_intervention.py   # Intervention: Urban shade structures & cooling deltas
│   │   ├── stage4_incremental_solver.py # Incremental: Certified spatial cone & horizon bounding
│   │   ├── stage5_ai_solver.py      # AI Solver: Surrogate-assisted Pareto optimization
│   │   └── runner.py                # End-to-end multi-stage pipeline orchestrator
│   ├── incremental/                 # Certified incremental recomputation engine
│   │   ├── certificate.py           # Closed-form error bounds & audit contracts
│   │   ├── affected_region.py       # Candidate shadow plume & horizon decay masks
│   │   └── update.py                # Scene edit operations (Add, Remove, Height, Move)
│   ├── placement/                   # AI Placement Solver & Active Learning
│   │   ├── parameters.py            # Single- and dual-panel parameter schemas
│   │   ├── feasibility.py           # 5-stage geometric and corridor feasibility filters
│   │   ├── surrogate_model.py       # Multi-target decision-tree ensembles (RF/ExtraTrees)
│   │   ├── acquisition.py           # Upper Confidence Bound acquisition policies
│   │   ├── dual_panel_placement_solver.py # Dual-panel multi-intervention engine
│   │   └── robustness.py            # Multi-seed & sensitivity evaluation suite
│   ├── server/                      # FastAPI engine REST backend & static mount
│   │   ├── app.py                   # REST endpoints (/api/areas, /api/process, /api/optimize)
│   │   └── __main__.py              # Server CLI entrypoint
│   └── sites/                       # Real-world site adapters & builders
│       └── church_street/           # Bengaluru Church Street coordinate transforms
├── data/                            # Segregated Data Root
│   ├── input/                       # Unified Input Data (case area named folders only)
│   │   └── church_street/           # GIS vectors, heights, trees, terrain rasters, weather
│   ├── processed/                   # Segregated Processed Data (<case_area>/<timestamp>/)
│   │   └── church_street/           # 3D scene meshes, pedestrian grids, baseline Tmrt & UTCI
│   └── optimized/                   # Segregated Optimization Data (<case_area>/<timestamp>/)
│       └── church_street/           # Optimal canopies, cooling deltas, 3D intervention meshes
├── simulation_3d/                   # Interactive 3D WebGL Digital Twin Web Interface
│   ├── app.js                       # Three.js 3D viewport, shaders, & scene orchestration
│   ├── segregated_engine.js         # Client-side engine controller & 3-data layer switcher
│   ├── index.html                   # Observatory UI with 3-data controls & canopy prompt modal
│   └── index.css                    # Modern glassmorphism theme & styling tokens
├── run_app.py                       # Root launcher for engine server & interactive UI
└── tools/                           # Plotting & analysis utilities
    └── robustness_plots.py          # Reporting & visualization plot utilities
```

---

## 11. Installation & Requirements

### 11.1 Prerequisites
- **Python**: 3.10+ (Tested on Python 3.12.6)
- **Host OS**: Linux, macOS, or Windows 10/11
- **GPU (Optional for GPU Backend)**: NVIDIA GPU with Compute Capability $\ge 6.0$ (Pascal through Ada Lovelace / Blackwell) with modern NVIDIA drivers ($\ge 525.60$).

### 11.2 Environment Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/ayushsingh08-ds/solaraeus.git
cd solaraeus
pip install numpy scipy shapely pythermalcomfort scikit-learn matplotlib pyproj trimesh fastapi uvicorn
```

---

## 12. Quickstart & Execution Workflows

### 12.1 Interactive 3D Digital Twin Engine Web App (Recommended)
Launch the unified server and web interface:
```bash
python run_app.py --port 8000
```
Open `http://localhost:8000` in any web browser to interact with the full engine:
1. **Select Data & Timestamp**: Choose your case area (e.g. `church_street`) from `data/input/` and specify a custom timestamp.
2. **Process Data**: Click `⚡ Process Data` to construct 3D scene meshes, discrete pedestrian grids, and calculate baseline microclimate ($T_{\mathrm{mrt}}$, UTCI, SVF, shadows) into `data/processed/<area>/<timestamp>/`.
3. **Canopy & Shade Optimization Prompt**: The UI prompts for the number of shade canopies (1–10), dimensions (length, width, height), and transmissivity. Click `🚀 Calculate Best Position Across Map` to run the AI solver, placing canopies at optimal coordinates and saving outputs to `data/optimized/<area>/<timestamp>/`.
4. **Display 3 Data Layers**: Switch between:
   - **`1. Baseline`**: Baseline $T_{\mathrm{mrt}}$ ($38^\circ\text{C}-58^\circ\text{C}$), UTCI thermal stress, baseline shadows.
   - **`2. Canopies`**: 3D placed canopy structures rendered at optimal coordinates with tension fabric and support posts.
   - **`3. Best Reduction`**: Cooling delta heatmap ($\Delta T_{\mathrm{mrt}}$ up to $-12.8\text{ K}$) and reduction scorecard.
   - **`All 3 Layers`**: Simultaneous 3D buildings, placed canopies, and cooled thermal relief overlay.
3. **Intervention** (`03_intervention/`): Integrates 3D urban canopy interventions and executes forward simulation to evaluate pedestrian cooling deltas.
4. **Incremental Solver** (`04_incremental_solver/`): Executes certified incremental recomputation bounding the affected spatial cone and radiative horizon (typically achieving $\mathbf{10\times\text{--}30\times}$ speedup and $>99\%$ cell reuse with analytical error certificates $\le \varepsilon_T$).
5. **AI Solver** (`05_ai_solver/`): Runs surrogate-assisted multi-objective optimization to discover Pareto-optimal shade interventions.

All stage artifacts, arrays (`.npz`), geometries, and executive audit reports are generated cleanly inside the designated destination directory with an overarching `pipeline_manifest.json` and `pipeline_report.md`.

You can also run specific stages or adjust resolution/evaluations:
```bash
# Run only stages 1 and 2
python scripts/run_pipeline.py --stages 1,2 --output results/my_baseline_run

# Run full pipeline with custom optimization budget
python scripts/run_pipeline.py --stages 1,2,3,4,5 --evals 25 --output results/full_study
```

### 12.2 Single Building Simulation Example
Run the reference simulation over an 80m canonical scene:
```bash
python examples/single_building.py
```
Outputs solar position, shadow fraction, mean $T_{\mathrm{mrt}}$ in sun vs. shade, and UTCI comfort stress distributions.

### 12.2 Comparative Incremental Benchmark
Compare full-domain recomputation against certified incremental updates:
```bash
python examples/compare_full_incremental.py
```
Audits computational speedup, verified cell-reuse percentage, and certificate upper bounds.

### 12.3 Church Street GPU Simulation
Execute the full GPU simulation over Church Street, Bengaluru:
```bash
python scripts/run_church_street_gpu_simulation.py
```

### 12.4 AI Intervention Placement Discovery
Run the surrogate-assisted dual-canopy placement solver:
```bash
python scripts/run_church_street_two_panel_optimization.py
```

---

## 13. Documented Limitations & Scientific Boundaries

In adherence to scientific integrity, the following boundaries and assumptions are formally documented:
1. **Flat-Ground Datum Baseline**: Primary benchmarks evaluate terrain at flat datum $z = 0.0\,\mathrm{m}$ because measured, street-scale curb-and-gutter elevation surveys were unavailable (`FABDEM_REGIONAL_REFERENCE_ONLY`).
2. **Provisional Tree Geometries**: Street vegetation models utilize Level 1 cylinder trunks and ellipsoid crowns parameterized from municipal BBMP counts and photographic estimation (`TREE_GEOMETRY_PHOTO_ESTIMATED_ONLY`), pending on-site laser scanning.
3. **Decoupled Boundary Forcing**: Simulations evaluate modeled physical differences under fixed atmospheric boundary forcing rather than continuous multi-point in-situ sensor measurements (`FIELD_CALIBRATION_NOT_PERFORMED`).
4. **Low-Sun Zenith Fallback**: At solar altitudes $\alpha_s < 5.0^\circ$, geometric shadow lengths grow towards infinity ($h / \tan\alpha_s$), triggering an automated, sound fallback to full-domain recomputation.
5. **Fluid Dynamics Coupling**: Convective microscale wind flow fields are evaluated at fixed pedestrian reference velocities ($v_{1.1} = 1.1\,\mathrm{m/s}$) rather than coupled CFD Navier–Stokes equations.

---

## Citation

If you use SOLARAEUS in your research, please cite:

```bibtex
@inproceedings{singh2026solaraeus,
  author    = {Singh, Ayush and Thomas, Jobin},
  title     = {Solaraeus: A Physics-Based 3D Urban Microclimate Digital Twin with Certified Incremental Radiative Transfer, GPU Acceleration, and an AI Solver for Optimal Intervention Placement},
  booktitle = {Proceedings of the IEEE Conference on Urban Informatics and Computing},
  year      = {2026},
  url       = {https://github.com/ayushsingh08-ds/solaraeus}
}
```
