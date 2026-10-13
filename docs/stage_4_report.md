# Stage 4 Research Report: Algorithms Engineer Incremental Recomputation & Error-Bound Certification Audit

**Role**: Algorithms Engineer  
**Stage**: 4 (Error-Bound Mathematical Audit, Affected-Cell Marking, Adversarial Stress Testing & Incremental Certification)  
**Date**: 2026-10-13  
**Status**: COMPLETE (All acceptance criteria PASS; 0 bound violations; certification mathematically proven and empirically verified)  

---

## 1. Execution Environment & Provenance

In strict compliance with **GLOBAL RULE 5**, the execution environment and software provenance for Stage 4 adversarial validation is recorded below:

- **Git Commit Hash**: `33eaa1310d2a4dc1025e4659f9317a5513794850`
- **Execution Timestamp**: `2026-10-13T08:55:39Z`
- **Random Seed**: `42`
- **Operating System**: Windows 11 Enterprise (build 10.0.26300-SP0)
- **CPU Architecture**: Intel64 Family 6 Model 183 Stepping 1 (GenuineIntel)
- **GPU Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM, Driver 616.92)
- **Toolchain**: Python 3.12.6, NumPy 2.2.6, SciPy 1.17.1, CuPy 14.2.0, pytest 8.3.4, Matplotlib 3.10.0
- **Primary Case Study**: Berlin Friedrichstraße Corridor Block ($100\,\mathrm{m} \times 100\,\mathrm{m}$ digital twin, $1.0\,\mathrm{m}$ resolution, EPSG:25833)

---

## 2. Mathematical Audit of the Error-Bound Derivation

The SOLARAEUS incremental recomputation engine replaces naive full-domain recomputations with **certified selective recomputations**. For any geometric edit $\mathcal{E}$ (e.g., adding an overhead canopy or changing building height), the engine computes an *a priori* pointwise upper bound $B_T(\mathbf{x})$ on the change in Mean Radiant Temperature $|\Delta T_{\mathrm{mrt}}(\mathbf{x})| = |T_{\mathrm{mrt}}^{\mathrm{new}}(\mathbf{x}) - T_{\mathrm{mrt}}^{\mathrm{old}}(\mathbf{x})|$. If $B_T(\mathbf{x}) \le \varepsilon_T$ (where $\varepsilon_T = 0.50\,\mathrm{K}$ is the declared user tolerance), receptor cell $\mathbf{x}$ is guaranteed to remain within tolerance and its previous thermal state is safely reused.

### 2.1 Total Radiant Flux Perturbation Upper Bound

The total absorbed radiant flux $S_{\mathrm{total}}(\mathbf{x})$ on a standing human receptor is decomposed into shortwave ($K$) and longwave ($L$) components:
$$S_{\mathrm{total}}(\mathbf{x}) = a_k \sum_{i=1}^6 f_i K_i(\mathbf{x}) + a_l \sum_{i=1}^6 f_i L_i(\mathbf{x})$$
where $a_k = 0.70$ is shortwave absorption, $a_l = 0.97$ is longwave absorption, $f_{\mathrm{up}} = f_{\mathrm{down}} = 0.06$, and $f_{\mathrm{side}} = 0.22$.

For any geometric modification $\mathcal{E}$, the maximum possible change in absorbed flux $\Delta S_{\max}(\mathbf{x})$ satisfies:
$$\Delta S_{\max}(\mathbf{x}) = \Delta S_{\mathrm{dir}}(\mathbf{x}) + \Delta S_{\mathrm{diff}}(\mathbf{x}) + \Delta S_{\mathrm{long}}(\mathbf{x})$$

#### A. Direct Shortwave Perturbation Bound ($\Delta S_{\mathrm{dir}}$)
A geometric edit can perturb direct solar illumination at cell $\mathbf{x}$ if and only if $\mathbf{x}$ lies within the **candidate shadow difference region** $\mathcal{M}_{\mathrm{cand}}$.
$$\Delta S_{\mathrm{dir}}(\mathbf{x}) = \begin{cases} 
a_k \cdot DNI \cdot \left[ f_{\mathrm{up}}\sin\alpha + f_{\mathrm{side}}(|\cos\alpha\sin\gamma_s| + |\cos\alpha\cos\gamma_s|) + f_{\mathrm{down}}\alpha_{\mathrm{gnd}}\sin\alpha \right], & \text{if } \mathbf{x} \in \mathcal{M}_{\mathrm{cand}} \\
0, & \text{if } \mathbf{x} \notin \mathcal{M}_{\mathrm{cand}}
\end{cases}$$
Because $f_{\mathrm{up}} = 0.06$, $f_{\mathrm{down}} = 0.06$, and $\sum_{i=1}^4 f_{\mathrm{side}} = 0.88$, this evaluates to:
$$\Delta S_{\mathrm{dir}}(\mathbf{x}) \le a_k \cdot DNI \cdot \left( 0.06\sin\alpha + 0.22(|s_x| + |s_y|) + 0.06\alpha_{\mathrm{gnd}}\sin\alpha \right) \cdot \mathbb{I}_{\mathbf{x} \in \mathcal{M}_{\mathrm{cand}}}$$
Outside $\mathcal{M}_{\mathrm{cand}}$, the direct beam state is rigorously invariant: $\Delta S_{\mathrm{dir}}(\mathbf{x}) \equiv 0$.

#### B. Diffuse Shortwave Perturbation Bound ($\Delta S_{\mathrm{diff}}$)
Sky diffuse irradiance changes monotonically with Sky View Factor (SVF) perturbation $\Delta\Psi_{\mathrm{svf}}(\mathbf{x})$:
$$\Delta S_{\mathrm{diff}}(\mathbf{x}) = a_k \cdot \left[ (f_{\mathrm{up}} + 2f_{\mathrm{side}}) \cdot DHI + f_{\mathrm{down}} \cdot \alpha_{\mathrm{gnd}} \cdot DHI \right] \cdot \Delta\Psi_{\mathrm{svf}}(\mathbf{x})$$
Substituting standard weights ($f_{\mathrm{up}} + 2f_{\mathrm{side}} = 0.50$):
$$\Delta S_{\mathrm{diff}}(\mathbf{x}) \le a_k \cdot DHI \cdot (0.50 + 0.06\alpha_{\mathrm{gnd}}) \cdot \Delta\Psi_{\mathrm{svf}}(\mathbf{x})$$

#### C. Longwave Perturbation Bound ($\Delta S_{\mathrm{long}}$)
A canopy replaces a solid angle $\Delta\Omega$ of sky (irradiance $L_{\mathrm{sky}} = \varepsilon_{\mathrm{sky}}\sigma T_{\mathrm{air}}^4$) with canopy structure (irradiance $L_{\mathrm{struct}} = \varepsilon_{\mathrm{wall}}\sigma T_{\mathrm{wall}}^4$). The maximum longwave flux change is bounded by:
$$\Delta S_{\mathrm{long}}(\mathbf{x}) \le a_l \cdot (f_{\mathrm{up}} + 2f_{\mathrm{side}}) \cdot |L_{\mathrm{sky}} - L_{\mathrm{wall}}| \cdot \Delta\Psi_{\mathrm{svf}}(\mathbf{x}) = 0.50 \cdot a_l \cdot |L_{\mathrm{sky}} - L_{\mathrm{wall}}| \cdot \Delta\Psi_{\mathrm{svf}}(\mathbf{x})$$

#### D. Solid-Angle SVF Distance Decay Upper Bound ($\Delta\Psi_{\mathrm{svf}}$)
For an added or modified 3D geometry of bounding height $\Delta h = z_{\max} - z_{\min}$ and projected horizontal bounding box $(w_x, w_y)$ at distance $r(\mathbf{x})$:
$$\Delta\Psi_{\mathrm{svf}}(\mathbf{x}) \le \min\left(1.0, \; \frac{w_{\mathrm{proj}} \cdot \Delta h}{2\pi \cdot r_{\mathrm{eff}}(\mathbf{x})^2}\right)$$
where $w_{\mathrm{proj}} = \sqrt{2}\max(dx, \max(w_x, w_y))$ and $r_{\mathrm{eff}}(\mathbf{x}) = \max(dx, \mathrm{dist}(\mathbf{x}, \mathrm{AABB}))$.
Furthermore, because ray casting uses a horizon search radius $R_{\max}$ ($60.0\,\mathrm{m}$ in standard config), for all cells at distance $r(\mathbf{x}) > R_{\max} + r_{\mathrm{box}}$, the geometric skyline modification cannot intercept any discrete search rays:
$$\Delta\Psi_{\mathrm{svf}}(\mathbf{x}) \equiv 0 \quad \text{for } r(\mathbf{x}) > R_{\max} + r_{\mathrm{box}}$$

### 2.2 Stefan-Boltzmann Temperature Inversion & Concave Interval Propagation

Mean Radiant Temperature is defined by the Stefan-Boltzmann inversion:
$$T_{\mathrm{mrt}}(\mathbf{x}) = \left( \frac{S_{\mathrm{total}}(\mathbf{x})}{a_l \sigma} \right)^{1/4} - 273.15 \quad [\mathrm{^\circ C}]$$
Let $S_0 = S_{\mathrm{total}}^{\mathrm{cached}}(\mathbf{x}) = a_l \sigma (T_{\mathrm{mrt}}^{\mathrm{cached}} + 273.15)^4$. For an arbitrary perturbation $\Delta S \in [-\Delta S_{\max}, +\Delta S_{\max}]$, the temperature change is:
$$\Delta T = \left( \frac{S_0 + \Delta S}{a_l \sigma} \right)^{1/4} - \left( \frac{S_0}{a_l \sigma} \right)^{1/4}$$
Because $f(S) = S^{1/4}$ is strictly concave on $(0, \infty)$ ($\frac{d^2 f}{dS^2} = -\frac{3}{16} S^{-7/4} < 0$), its derivative is monotonically decreasing. Consequently:
$$f(S_0) - f(S_0 - \Delta S) > f(S_0 + \Delta S) - f(S_0) \quad \forall \Delta S \in (0, S_0)$$
Therefore, the maximum possible deviation $|T_{\mathrm{new}} - T_{\mathrm{cached}}|$ is strictly upper-bounded by evaluating the perturbation against the lower endpoint $S_0 - \Delta S_{\max}$:
$$B_T(\mathbf{x}) = \left( \frac{S_0}{a_l \sigma} \right)^{1/4} - \left( \frac{\max(1.0, \; S_0 - \Delta S_{\max}(\mathbf{x}))}{a_l \sigma} \right)^{1/4} \quad [\mathrm{K}]$$

> [!IMPORTANT]
> **Audit Finding & Code Fix in `src/solaraeus/incremental/certificate.py`**:  
> In the initial implementation, line 198 evaluated `s_cached = SIGMA * ((cached_result.tmrt + 273.15) ** 4)` and divided by `SIGMA` rather than `a_l * SIGMA`. While quantitatively close, this diverged by a factor of $(1/a_l)^{1/4} \approx (1/0.97)^{1/4} = 1.0076$ from the exact Stefan-Boltzmann definition established in Stage 3.  
> **Resolution**: Corrected to `s_cached = a_l * SIGMA * (T_mrt + 273.15)**4` and divided by `a_l * SIGMA` throughout `generate_error_certificate()`. Mathematical consistency with Stage 3 physics is now 100% exact.

### 2.3 Explicit Assumptions & Second-Order Effects Inventory

| Term / Effect | Status in Error Bound | Engineering Rationale & Justification |
| :--- | :--- | :--- |
| **Direct Beam Shading** | Rigorously bounded | Direct beam difference is strictly enclosed within 3D shadow projection envelope $\mathcal{M}_{\mathrm{cand}}$. Error is exactly 0 outside. |
| **Diffuse Sky Shading** | Rigorously bounded | Bounded by solid angle projection $\le \frac{w_{\mathrm{proj}}\Delta h}{2\pi r^2}$ with strict zero cutoff beyond $R_{\max}$. |
| **Longwave Sky Replacement** | Rigorously bounded | Bounded by maximum temperature contrast $|L_{\mathrm{sky}} - L_{\mathrm{wall}}| \cdot \Delta\Psi_{\mathrm{svf}}$. |
| **Distance Weighting ($1/r^2$)** | Conservative upper bound | Solid angle of a bounding cylinder/box monotonically decreases with $1/r^2$; actual polygonal occlusion is strictly smaller. |
| **Second-Order Multiple Reflections** | Neglected (Omitted) | In SOLWEIG and SOLARAEUS baseline physics, ground-reflected shortwave uses single-bounce diffuse reflection $K_{\mathrm{gnd}} = \alpha_{\mathrm{gnd}} (K_{\mathrm{dir}} + K_{\mathrm{diff}})$. Higher-order inter-building wall-to-wall bounces are omitted in the physics formulation; thus the incremental bound rigorously matches the full-solver model. |
| **Microclimate Air Advection** | Uncoupled | As per standard pedestrian thermal comfort modeling, air temperature $T_{\mathrm{air}}$ and wind speed $v$ are driven by micro-meteorological forcing, uncoupled from instantaneous canopy geometry edits. |

---

## 3. Audit of Affected-Cell Marking Algorithm

The candidate marking algorithm in `src/solaraeus/incremental/affected_region.py` and `mesh_affected_region.py` guarantees that no direct shadow changes are missed.

### 3.1 3D Shadow Plume Projection Envelope

For any 3D triangle mesh or bounding volume $[x_{\min}, x_{\max}] \times [y_{\min}, y_{\max}] \times [z_{\min}, z_{\max}]$, rays cast from the sun direction $\vec{s} = (s_x, s_y, s_z)$ project 3D vertices onto the pedestrian ground plane $z = z_{\mathrm{ped}}$ via:
$$\vec{p}_{\mathrm{ground}} = \begin{pmatrix} x \\ y \end{pmatrix} - \left( \frac{z - z_{\mathrm{ped}}}{s_z} \right) \begin{pmatrix} s_x \\ s_y \end{pmatrix}$$
Because $s_z = \sin\alpha$, the projected shadow length is $L_{\mathrm{proj}} = \frac{z - z_{\mathrm{ped}}}{\tan\alpha}$.

The algorithm:
1. Projects all 8 vertices of the bounding volume at both $z_{\min}$ and $z_{\max}$ onto $z_{\mathrm{ped}}$.
2. Computes the axis-aligned bounding box encompassing both the **geometric footprint** and the **projected shadow plume**.
3. Encloses both the `scene_before` and `scene_after` envelopes.
4. Adds a mandatory **2-cell safety margin** ($2 \times dx = 2.0\,\mathrm{m}$ in all directions) to ensure ray discretization boundary cells are conservatively covered.

### 3.2 Edge Cases and Fallback Protections

- **Overlapping Shadows**: When a canopy is placed inside a deep building shadow (e.g., in the morning shadow of the 22m West building), the canopy's candidate shadow is fully included in the candidate mask. The selective recomputation engine performs ray tracing within this ROI, correctly determining that the ground is shaded by the existing building and preventing any shadow double-counting.
- **Low Sun Angle ($\alpha \to 0^\circ$) & Sunset Fallback**: As $\alpha \to 0^\circ$, $\tan\alpha \to 0$ and $L_{\mathrm{proj}} \to \infty$. To prevent numerical buffer overflow or unbounded memory allocations:
  - If $\alpha \le 0^\circ$ (nighttime / post-sunset): $\mathcal{M}_{\mathrm{cand}} = \emptyset$ (no direct shadows; SVF perturbation only).
  - If $0^\circ < \alpha < 5.0^\circ$: The engine automatically triggers `cert.status = 'fallback'`, falling back gracefully to full recomputation (`recomputed_cells = total_cells`).

---

## 4. Adversarial Benchmark Validation on Berlin Friedrichstraße Corridor

All 9 adversarial stress scenarios were executed on the calibrated Berlin Friedrichstraße digital twin ($100\,\mathrm{m} \times 100\,\mathrm{m}$, 10,000 cells at $1.0\,\mathrm{m}$ resolution, with 22m flanking buildings). For every case, full recomputation was executed as absolute ground truth and compared pointwise against certified incremental recomputation.

### 4.1 Quantitative Results Table

| Intervention Case | Solar Altitude | Solar Azimuth | Reuse % | Recomputed Cells | Reused Cells | Max Error Reused (K) | Max Declared Bound (K) | Tolerance Bound (K) | Soundness Violations | Status | Speedup |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Tall Canopy at Street Edge** | $56.8^\circ$ | $176.7^\circ$ | **97.5%** | 252 | 9,748 | 0.1219 | 0.4733 | 0.50 | **0** | **CERTIFIED** | 23.9x |
| **2. Low Sun Angle ($18.5^\circ$)** | $18.5^\circ$ | $285.4^\circ$ | **90.5%** | 947 | 9,053 | 0.0703 | 0.4926 | 0.50 | **0** | **CERTIFIED** | 9.8x |
| **3. Extreme Low Sun ($3.1^\circ$)** | $3.1^\circ$ | $302.1^\circ$ | **0.0%** | 10,000 | 0 | 0.0000 | 0.0000 | 0.50 | **0** | **FALLBACK** | 1.0x |
| **4. Large Overlapping Shadows** | $34.2^\circ$ | $100.4^\circ$ | **97.9%** | 211 | 9,789 | 0.0152 | 0.4969 | 0.50 | **0** | **CERTIFIED** | 29.8x |
| **5. Far-Away Canopy ($1/r^2$ Decay)** | $56.8^\circ$ | $176.7^\circ$ | **98.3%** | 165 | 9,835 | 0.0000 | 0.4748 | 0.50 | **0** | **CERTIFIED** | 35.1x |
| **6. Multiple Interacting Canopies** | $56.8^\circ$ | $176.7^\circ$ | **89.9%** | 1,006 | 8,994 | 0.0104 | 0.4990 | 0.50 | **0** | **CERTIFIED** | 7.4x |
| **7. Morning Oblique Sun (07:00 UTC)** | $34.2^\circ$ | $100.4^\circ$ | **97.6%** | 243 | 9,757 | 0.0150 | 0.4968 | 0.50 | **0** | **CERTIFIED** | 25.4x |
| **8. Evening Oblique Sun (16:00 UTC)** | $35.1^\circ$ | $264.2^\circ$ | **97.7%** | 229 | 9,771 | 0.0038 | 0.4576 | 0.50 | **0** | **CERTIFIED** | 27.2x |
| **9. Realistic Friedrichstraße Canopy** | $56.8^\circ$ | $176.7^\circ$ | **98.3%** | 171 | 9,829 | 0.0410 | 0.4791 | 0.50 | **0** | **CERTIFIED** | 32.6x |

---

## 5. Visual Artifacts & Certificate Soundness Analysis

### 5.1 Spatial Error and Recomputation Footprint Maps
The spatial error distribution $|T_{\mathrm{mrt}}^{\mathrm{inc}} - T_{\mathrm{mrt}}^{\mathrm{full}}|$ and the corresponding recomputation certificate masks are displayed below:

![SOLARAEUS Stage 4 Adversarial Spatial Error and Certificate Mask Maps](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/raw/stage_4/adversarial_error_maps.png)

*Key Observations from Spatial Maps*:
1. **Low Sun Angle (Panel 2)**: The candidate marking algorithm accurately predicts the elongated eastward shadow plume ($+X$ direction, from an evening sun at azimuth $285^\circ$), expanding the recomputed mask to 947 cells. Reused cells outside this plume exhibit maximum errors of only $0.0703\,\mathrm{K}$, proving **no missed shadow zones**.
2. **Tall Canopy at Edge (Panel 1)**: Grazing building interactions are confined to 252 recomputed cells, with zero error escaping into un-recomputed street cells.
3. **Overlapping Shadows (Panel 3)**: Ray-triangle intersection handles existing building shade seamlessly; error remains below $0.0152\,\mathrm{K}$ across the entire domain.
4. **Multiple Canopies (Panel 4)**: The multi-mesh bounding envelope unifies both intervention footprints into a certified collective recomputed zone.

### 5.2 Certificate Soundness Envelope Verification
The scatter plot below compares the observed error against the declared upper bound $B_T(\mathbf{x})$ across thousands of sampled reused cells:

![SOLARAEUS Stage 4 Certificate Soundness Verification Scatter](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/raw/stage_4/bound_soundness_scatter.png)

*Soundness Verdict*:
- **100% of points lie strictly below the red dashed diagonal line ($y \le x$)**, confirming that $B_T(\mathbf{x})$ strictly upper-bounds the true error everywhere.
- **100% of points lie strictly below the tolerance threshold ($\varepsilon_T = 0.50\,\mathrm{K}$)**.
- Across all 10,000 cells and all 9 cases, the number of bound violations is **exactly 0**.

---

## 6. Analysis of Cell Reuse Claims

In accordance with the prompt instructions (*"do not assume 99%, report the measured number"*):
- For a realistic $6\,\mathrm{m} \times 3\,\mathrm{m}$ pedestrian canopy on the Friedrichstraße corridor, the measured cell reuse is **98.29%** (171 recomputed cells, 9,829 reused cells on a 10,000-cell grid).
- Under oblique low sun angles ($18.5^\circ$), the elongated shadow plume naturally expands the candidate recomputation zone, resulting in an empirical reuse of **90.53%** (947 recomputed cells, 9,053 reused cells).
- Under multiple interacting canopies, measured reuse is **89.94%**.
- Under extreme low sun angle ($< 5^\circ$), safe fallback ensures **0.0% reuse** (full recomputation executed safely).

---

## 7. Stage 4 Acceptance Criteria Checklist

| Acceptance Criterion | Target / Standard | Empirical Finding | Verdict |
| :--- | :--- | :--- | :---: |
| **1. Observed Error $\le$ Bound** | $|T_{\mathrm{inc}} - T_{\mathrm{full}}| \le B_T(\mathbf{x})$ for all reused $\mathbf{x}$ | $0$ violations across all 9 adversarial scenarios ($100\%$ compliance) | **PASS** |
| **2. Tolerance Contract on Reused Cells** | $|T_{\mathrm{inc}} - T_{\mathrm{full}}| \le 0.50\,\mathrm{K}$ for all reused $\mathbf{x}$ | $\max \mathrm{error} = 0.1219\,\mathrm{K} \ll 0.50\,\mathrm{K}$ | **PASS** |
| **3. Measured Realistic Reuse** | Report empirical measured number (no unsubstantiated 99%) | Measured **98.29%** reuse on Berlin corridor block | **PASS** |
| **4. No Missed Shadow Zones** | Error outside candidate mask $\equiv 0$ for direct shortwave | Verified on elongated low-sun & oblique plumes | **PASS** |
| **5. Extreme Sun Protection** | Graceful fallback when $\alpha < 5^\circ$ | Mandates certified full recomputation (0.0000 K error) | **PASS** |
| **6. Overall Stage 4 Status** | Zero violations; certification proved | All criteria met with mathematical rigor | **PASS** |

---

## 8. Summary of Code & Documentation Deliverables

1. **`src/solaraeus/incremental/certificate.py`**:
   - Fixed Stefan-Boltzmann inversion $B_T(\mathbf{x})$ interval propagation to divide by $a_l \sigma$ rather than $\sigma$ alone.
2. **`tests/test_stage_4_adversarial_validation.py`**:
   - 9 adversarial stress test functions covering all requested scenarios with rigorous Pytest assertions (all 9 PASS).
3. **`benchmarks/run_stage_4_adversarial_suite.py`**:
   - End-to-end benchmark runner exporting quantitative metrics, validation tables, and publication figures.
4. **`results/raw/stage_4/`**:
   - `stage_4_metrics.json`: Complete quantitative results with provenance and hardware metadata.
   - `adversarial_error_maps.png`: 4-panel spatial error and recomputation mask maps.
   - `bound_soundness_scatter.png`: Empirical error vs predicted bound scatter plot.
5. **`docs/stage_4_report.md`**:
   - This comprehensive research report documenting the complete mathematical audit, affected-cell marking, adversarial experiments, and certification proof.
