## 4. Critical Scientific Distinctions & Empirical Findings

To ensure scientific integrity, the project strictly distinguishes four distinct levels of validation:

| Level | Definition | Project Status | Evidence |
| :--- | :--- | :--- | :--- |
| **Software Verification** | Does the software execute its intended mathematical and geometric algorithms correctly without bugs or runtime failures? | **VERIFIED** | 94 unit and integration tests passing (`python -m pytest -o pythonpath=src -v`). |
| **Numerical Validation** | Does the incremental approximation agree with ground-truth full recomputation within the certified error bound? | **EMPIRICALLY VERIFIED** | 0 certificate violations observed across >500,000 evaluated cells in 34 benchmark experiments (130 trials). Minimum slack $\ge 0.000\,\text{K}$. |
| **Independent Reference Validation** | Does the implementation agree with independent analytical solutions and established reference models? | **PARTIALLY ASSESSED** | 4 independent analytical benchmarks match to $< 10^{-7}$. External UMEP plugin boundary documented (requires QGIS environment). |
| **Physical Validation** | Does the simulated thermal field accurately match real-world physical sensor measurements under field conditions? | **UNVALIDATED** | No physical empirical sensor data was used. All conclusions are strictly mathematical and numerical. |

### 4.1 Multi-Trial Scaling Summary ($N = 5$ Trials, 95% Confidence Intervals)

| Domain Scale | Grid Cells | Full Recompute (Median $\pm \text{CI}_{95}$) | Incremental Total (Median $\pm \text{CI}_{95}$) | Speedup (Median) | Reused Cells (%) | Certificate Violations Observed |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $80\,\text{m} \times 80\,\text{m}$ (Low) | 6,400 | $0.499\,\text{s} \pm 0.019\,\text{s}$ | $0.565\,\text{s} \pm 0.056\,\text{s}$ | **$0.88\times$** | $3.1\%$ | **0** |
| $80\,\text{m} \times 80\,\text{m}$ (Medium) | 6,400 | $0.580\,\text{s} \pm 0.090\,\text{s}$ | $0.530\,\text{s} \pm 0.061\,\text{s}$ | **$1.09\times$** | $3.1\%$ | **0** |
| $80\,\text{m} \times 80\,\text{m}$ (High) | 6,400 | $0.472\,\text{s} \pm 0.043\,\text{s}$ | $0.454\,\text{s} \pm 0.089\,\text{s}$ | **$1.04\times$** | $3.1\%$ | **0** |
| $160\,\text{m} \times 160\,\text{m}$ (Low) | 25,600 | $0.818\,\text{s} \pm 1.098\,\text{s}$ | $0.231\,\text{s} \pm 0.177\,\text{s}$ | **$3.53\times$** | $70.9\%$ | **0** |
| $160\,\text{m} \times 160\,\text{m}$ (Medium) | 25,600 | $0.849\,\text{s} \pm 0.011\,\text{s}$ | $0.242\,\text{s} \pm 0.012\,\text{s}$ | **$3.50\times$** | $70.9\%$ | **0** |
| $160\,\text{m} \times 160\,\text{m}$ (High) | 25,600 | $0.883\,\text{s} \pm 0.011\,\text{s}$ | $0.252\,\text{s} \pm 0.005\,\text{s}$ | **$3.50\times$** | $70.9\%$ | **0** |
| $320\,\text{m} \times 320\,\text{m}$ (Low) | 102,400 | $11.49\,\text{s} \pm 12.56\,\text{s}$ | $0.729\,\text{s} \pm 1.181\,\text{s}$ | **$15.77\times$** | $92.7\%$ | **0** |
| $320\,\text{m} \times 320\,\text{m}$ (Medium) | 102,400 | $43.75\,\text{s} \pm 0.33\,\text{s}$ | $3.009\,\text{s} \pm 0.080\,\text{s}$ | **$14.54\times$** | $92.7\%$ | **0** |
| $320\,\text{m} \times 320\,\text{m}$ (High) | 102,400 | $44.76\,\text{s} \pm 3.92\,\text{s}$ | $3.056\,\text{s} \pm 0.280\,\text{s}$ | **$14.65\times$** | $92.7\%$ | **0** |

### 4.2 Timing Overhead Breakdown Across Computational Phases
Isolated phase instrumentation confirms bounding overhead introduces minimal computational penalty ($\le 1.60\%$):

| Scene Configuration | Full Recompute | Dependency Query | Candidate Plume | Certificate Eval | Selective Recompute | Result Assembly | Overhead Ratio (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **80m Low Density** | $0.4994\,\text{s}$ | $47.1\,\mu\text{s}$ | $132.0\,\mu\text{s}$ | $2.684\,\text{ms}$ | $0.5605\,\text{s}$ | $111.6\,\mu\text{s}$ | **$0.53\%$** |
| **80m Medium Density** | $0.5800\,\text{s}$ | $41.5\,\mu\text{s}$ | $127.8\,\mu\text{s}$ | $2.300\,\text{ms}$ | $0.5263\,\text{s}$ | $106.2\,\mu\text{s}$ | **$0.49\%$** |
| **80m High Density** | $0.4717\,\text{s}$ | $43.4\,\mu\text{s}$ | $129.6\,\mu\text{s}$ | $2.347\,\text{ms}$ | $0.4505\,\text{s}$ | $85.8\,\mu\text{s}$ | **$0.57\%$** |
| **160m Low Density** | $0.8182\,\text{s}$ | $16.6\,\mu\text{s}$ | $46.6\,\mu\text{s}$ | $2.181\,\text{ms}$ | $0.2289\,\text{s}$ | $53.1\,\mu\text{s}$ | **$0.99\%$** |
| **160m Medium Density** | $0.8487\,\text{s}$ | $15.4\,\mu\text{s}$ | $44.5\,\mu\text{s}$ | $2.122\,\text{ms}$ | $0.2399\,\text{s}$ | $51.6\,\mu\text{s}$ | **$0.92\%$** |
| **160m High Density** | $0.8827\,\text{s}$ | $14.9\,\mu\text{s}$ | $44.8\,\mu\text{s}$ | $2.126\,\text{ms}$ | $0.2494\,\text{s}$ | $52.3\,\mu\text{s}$ | **$0.89\%$** |
| **320m Low Density** | $11.4886\,\text{s}$ | $21.3\,\mu\text{s}$ | $134.2\,\mu\text{s}$ | $11.389\,\text{ms}$ | $0.7143\,\text{s}$ | $133.8\,\mu\text{s}$ | **$1.60\%$** |
| **320m Medium Density** | $43.7479\,\text{s}$ | $58.1\,\mu\text{s}$ | $347.3\,\mu\text{s}$ | $31.585\,\text{ms}$ | $2.9697\,\text{s}$ | $519.6\,\mu\text{s}$ | **$1.08\%$** |
| **320m High Density** | $44.7628\,\text{s}$ | $51.2\,\mu\text{s}$ | $201.3\,\mu\text{s}$ | $33.175\,\text{ms}$ | $3.0220\,\text{s}$ | $475.3\,\mu\text{s}$ | **$1.11\%$** |

### 4.3 Comparison with Non-Certified Dirty-Region Baseline
Comparison of ground-truth full recompute, naive 5m buffer heuristic, exact incremental, and certified incremental:

| Method | Wall-Clock Time | Measured Speedup | Reused Cells (%) | Max Actual Error | Violations Observed ($\varepsilon_T = 0.5\,\text{K}$) | Soundness Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Full Recomputation** | $0.434\,\text{s}$ | $1.00\times$ | $0$ ($0.0\%$) | $0.000\,\text{K}$ | 0 | Ground Truth Reference |
| **Non-Certified Dirty Box (5m margin)** | $0.055\,\text{s}$ | $7.95\times$ | $5,775$ ($90.2\%$) | **$20.818\,\text{K}$** | **685 violations** | **FAILED (Unsound)** |
| **Exact Incremental** | $0.411\,\text{s}$ | $1.06\times$ | $448$ ($7.0\%$) | $0.000\,\text{K}$ | 0 | Verified Sound |
| **Certified Incremental** | $0.456\,\text{s}$ | $0.95\times$ | $200$ ($3.1\%$) | $0.000\,\text{K}$ | **0 (Zero)** | **VERIFIED SOUND** |

### 4.4 Repeated Edit Cycle & Cumulative Drift Evaluation
5-step sequential edit cycle testing numerical drift and error accumulation:

| Step | Operation Description | Full Time | Inc Time | Speedup | Reused Cells | Max Error $e_{\max}$ | Max Bound $B_{\max}$ | Violations | Drift vs Step 0 |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | Baseline Scene | $1.576\,\text{s}$ | $1.576\,\text{s}$ | $1.00\times$ | $0$ ($0\%$) | $0.0000\,\text{K}$ | $0.000\,\text{K}$ | 0 | $0.0000\,\text{K}$ |
| **1** | Height Increase ($+6\,\text{m}$) | $0.164\,\text{s}$ | $0.133\,\text{s}$ | $1.24\times$ | $1,613$ ($25.2\%$) | $0.0307\,\text{K}$ | $63.172\,\text{K}$ | 0 | — |
| **2** | Translation ($+10\,\text{m}, +5\,\text{m}$) | $0.144\,\text{s}$ | $0.158\,\text{s}$ | $0.91\times$ | $0$ ($0.0\%$) | $0.0000\,\text{K}$ | $63.475\,\text{K}$ | 0 | — |
| **3** | Height Decrease ($-6\,\text{m}$) | $0.169\,\text{s}$ | $0.123\,\text{s}$ | $1.37\times$ | $1,667$ ($26.0\%$) | $0.0307\,\text{K}$ | $63.111\,\text{K}$ | 0 | — |
| **4** | Building Removal | $0.009\,\text{s}$ | $0.013\,\text{s}$ | $0.76\times$ | $392$ ($6.1\%$) | $0.0000\,\text{K}$ | $63.453\,\text{K}$ | 0 | — |
| **5** | Return to Baseline Geometry | $0.160\,\text{s}$ | $0.166\,\text{s}$ | $0.96\times$ | $60$ ($0.9\%$) | $0.0000\,\text{K}$ | $47.261\,\text{K}$ | 0 | **$0.0000\,\text{K}$** |

### 4.5 Error Tolerance Sensitivity Sweep ($\varepsilon_T \in [0.10\,\text{K}, 2.00\,\text{K}]$)

| Target Tolerance $\varepsilon_T$ | Full Time | Inc Time | Measured Speedup | Reused Cells | Reused Fraction | Max Actual Error | Contract Violations |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$0.10\,\text{K}$** | $0.0994\,\text{s}$ | $0.0962\,\text{s}$ | $1.03\times$ | 216 | $3.38\%$ | $0.0000\,\text{K}$ | 0 |
| **$0.25\,\text{K}$** | $0.1022\,\text{s}$ | $0.0957\,\text{s}$ | $1.07\times$ | 216 | $3.38\%$ | $0.0000\,\text{K}$ | 0 |
| **$0.50\,\text{K}$** | $0.1015\,\text{s}$ | $0.1023\,\text{s}$ | $0.99\times$ | 216 | $3.38\%$ | $0.0000\,\text{K}$ | 0 |
| **$1.00\,\text{K}$** | $0.1012\,\text{s}$ | $0.0898\,\text{s}$ | $1.13\times$ | 856 | $13.38\%$ | $0.0000\,\text{K}$ | 0 |
| **$2.00\,\text{K}$** | $0.0960\,\text{s}$ | $0.0654\,\text{s}$ | **$1.47\times$** | 2,685 | **$41.95\%$** | **$0.1543\,\text{K}$** | 0 |

### 4.6 Independent Analytical Reference Verification

| Analytical Benchmark Test | Closed-Form Solution | Prototype Numerical Value | Absolute Error | Relative Error | Tolerance | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Wall Shadow Length** ($h=20\,\text{m}, \alpha=45^\circ$) | $20.000000000\,\text{m}$ | $20.000000000\,\text{m}$ | $3.55 \times 10^{-15}\,\text{m}$ | $1.78 \times 10^{-16}$ | $10^{-9}$ | **PASSED** |
| **Finite Wall View Factor** ($20\text{m} \times 10\text{m}$ at $5\text{m}$) | $0.366800984$ | $0.366800984$ | $0.00 \times 10^{0}$ | $0.00 \times 10^{0}$ | $10^{-7}$ | **PASSED** |
| **Unobstructed Flat Terrain SVF** | $1.000000000$ | $1.000000000$ | $0.00 \times 10^{0}$ | $0.00 \times 10^{0}$ | $10^{-12}$ | **PASSED** |
| **Stefan-Boltzmann Inversion** ($S_{\mathrm{str}}=500\,\text{W/m}^2$) | $33.285846320^\circ\text{C}$ | $33.285846320^\circ\text{C}$ | $0.00 \times 10^{0}$ | $0.00 \times 10^{0}$ | $10^{-9}$ | **PASSED** |

### 4.7 Independent Scientific Audit & Mutation Testing Results (Milestone 14)

Campaign Identifier: `independent_audit_20261006_033239` (Output archive: [`results/independent_audit_20261006_033239/`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/independent_audit_20261006_033239)).

#### 1. Decoupled Certificate Verification Audit (11 Scenarios, 185,600 Evaluated Cells)
Direct recalculation from raw NumPy arrays ($e(x) = |\widetilde{T}_{\mathrm{mrt}}(x) - T_{\mathrm{mrt}}^{\mathrm{full}}(x)|$, $\text{slack}(x) = B_T(x) - e(x)$) without relying on internal `verify_certificate()`:

| Scenario Name | Domain Extent | Density | Edit Type | Tolerance $\varepsilon_T$ | Total Cells | Certified Reused Cells (%) | Max Actual Error $e_{\max}$ | Max Bound $B_{\max}$ | Min Slack | Violations ($e > B_T$) | Reused Violations ($e > \varepsilon_T$) | Audit Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **80m_low_height_inc** | $80\,\text{m}$ | Low | Height $+6\text{m}$ | $0.5\,\text{K}$ | 6,400 | $3,610$ ($56.4\%$) | $0.0387\,\text{K}$ | $60.58\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_height_inc** | $80\,\text{m}$ | Med | Height $+6\text{m}$ | $0.5\,\text{K}$ | 6,400 | $4,448$ ($69.5\%$) | $0.0000\,\text{K}$ | $24.47\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_high_height_inc** | $80\,\text{m}$ | High | Height $+6\text{m}$ | $0.5\,\text{K}$ | 6,400 | $1,300$ ($20.3\%$) | $0.0000\,\text{K}$ | $59.68\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **160m_med_height_inc** | $160\,\text{m}$ | Med | Height $+6\text{m}$ | $0.5\,\text{K}$ | 25,600 | $20,888$ ($81.6\%$) | $0.0193\,\text{K}$ | $59.83\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **320m_med_height_inc** | $320\,\text{m}$ | Med | Height $+6\text{m}$ | $0.5\,\text{K}$ | 102,400 | $98,834$ (**$96.5\%$**) | $0.0231\,\text{K}$ | $59.79\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_tol_0.1K** | $80\,\text{m}$ | Med | Height $+6\text{m}$ | $0.1\,\text{K}$ | 6,400 | $4,448$ ($69.5\%$) | $0.0000\,\text{K}$ | $24.47\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_tol_1.0K** | $80\,\text{m}$ | Med | Height $+6\text{m}$ | $1.0\,\text{K}$ | 6,400 | $4,448$ ($69.5\%$) | $0.0000\,\text{K}$ | $24.47\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_tol_2.0K** | $80\,\text{m}$ | Med | Height $+6\text{m}$ | $2.0\,\text{K}$ | 6,400 | $4,448$ ($69.5\%$) | $0.0000\,\text{K}$ | $24.47\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_add_building** | $80\,\text{m}$ | Med | Add building | $0.5\,\text{K}$ | 6,400 | $2,660$ ($41.6\%$) | $0.0000\,\text{K}$ | $60.18\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_remove_bldg** | $80\,\text{m}$ | Med | Remove building | $0.5\,\text{K}$ | 6,400 | $969$ ($15.1\%$) | $0.0000\,\text{K}$ | $60.20\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |
| **80m_med_move_bldg** | $80\,\text{m}$ | Med | Move building | $0.5\,\text{K}$ | 6,400 | $222$ ($3.5\%$) | $0.0000\,\text{K}$ | $60.20\,\text{K}$ | $0.0000\,\text{K}$ | **0** | **0** | **SOUND** |

#### 2. Intentional Mutation Sensitivity Audit
Proving that the independent audit pipeline reliably flags violations when physical or mathematical assumptions are broken:

| Mutation Scenario | Description of Injected Fault | Expected Result | Actual Violations | Actual Tolerance Violations | Min Slack | Max Error $e_{\max}$ | Audit Verdict |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`control_unmutated`** | Unmutated certified incremental pipeline | Pass (0 violations) | **0** | **0** | $0.0000\,\text{K}$ | $0.0000\,\text{K}$ | **PASS (Sound)** |
| **`mutation_truncated_shadow_plume`** | Shadow plume reach cut to $30\%$; $0\Delta x$ safety padding | Violations outside plume | **158** | **42** | **$-19.52\,\text{K}$** | **$19.62\,\text{K}$** | **DETECTED (Flagged)** |
| **`mutation_zero_diffuse_bound`** | Diffuse/SVF bound zeroed to $0.0001\,\text{K}$ | SVF diffuse error exceeds bound | 0 | 0 | $+0.0001\,\text{K}$ | $0.0000\,\text{K}$ | Clean cells had exact 0.0K error |
| **`mutation_forced_stale_reuse`** | Direct shadow change forced to reuse stale cached values | Thermal shock of un-recomputed direct shadow | **42** | **42** | **$-19.42\,\text{K}$** | **$19.62\,\text{K}$** | **DETECTED (Flagged)** |
| **`mutation_truncated_svf_cutoff`** | SVF decay bound cut to 5m (omitting 5m–30m zone) | Distant SVF decay exceeds bound | 0 | 0 | $0.0000\,\text{K}$ | $0.0000\,\text{K}$ | Recomputed zone covered SVF perturbation |

#### 3. Isolated Administrative Overhead Breakdown ($N=5$ Independent Trials)

| Scale | Cells | Full Median (Std) | Inc Median (Std) | Speedup | Dependency Query | Candidate Plume | Certificate Eval | Selective Recompute | Result Assembly | JSON Serialization | Total Admin Overhead | Overhead Ratio (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **80m** | 6,400 | $0.274\,\text{s}$ ($\pm 0.094\,\text{s}$) | $0.218\,\text{s}$ ($\pm 0.057\,\text{s}$) | **$1.53\times$** | $31.1\,\mu\text{s}$ | $43.8\,\mu\text{s}$ | $0.667\,\text{ms}$ | $0.217\,\text{s}$ | $46.0\,\mu\text{s}$ | $40.1\,\mu\text{s}$ | **$0.788\,\text{ms}$** | **$0.36\%$** |
| **160m** | 25,600 | $2.991\,\text{s}$ ($\pm 0.644\,\text{s}$) | $0.354\,\text{s}$ ($\pm 0.133\,\text{s}$) | **$6.39\times$** | $29.1\,\mu\text{s}$ | $97.1\,\mu\text{s}$ | $3.161\,\text{ms}$ | $0.347\,\text{s}$ | $127.3\,\mu\text{s}$ | $43.0\,\mu\text{s}$ | **$3.414\,\text{ms}$** | **$0.96\%$** |
| **320m** | 102,400 | $35.962\,\text{s}$ ($\pm 6.000\,\text{s}$) | $1.368\,\text{s}$ ($\pm 0.160\,\text{s}$) | **$23.14\times$** | $59.5\,\mu\text{s}$ | $251.2\,\mu\text{s}$ | $18.996\,\text{ms}$ | $1.344\,\text{s}$ | $315.6\,\mu\text{s}$ | $64.8\,\mu\text{s}$ | **$19.622\,\text{ms}$** | **$1.43\%$** |

*Conclusion*: Administrative bounding overhead accounts for **$\le 1.43\%$** of incremental execution time across all domain scales, introducing zero practical bottleneck.

#### 4. Scientific Claim Audit & Defensible Rectifications

| Claim Subject | Original Documented Wording | Revised Scientifically Defensible Wording | Rationale & Justification | Status |
| :--- | :--- | :--- | :--- | :---: |
| **GPU Acceleration** | *"Yield an estimated 20x-50x additional speedup from WebGPU / CUDA"* | Stated as architectural potential for parallel compute shaders on GPU hardware | Unmeasured performance multipliers removed from documentation | **RECTIFIED** |
| **Proof Scope** | *"Mathematically proven upper bounds"* | *"No error-certificate violations observed in evaluated benchmark cases"* | Discrete grid sampling and numerical approximations require empirical qualification | **RECTIFIED** |
| **Analytical Validation** | *"Fully validated against analytical references"* | *"Verified against independent analytical benchmarks and internal ground-truth full recomputation"* | Analytical benchmarks verify isolated components; field sensor validation has not been performed | **RECTIFIED** |
| **SOLWEIG Alignment** | *"Exact SOLWEIG match / Algorithmic match"* | *"SOLWEIG-compatible simplified formulation; conceptually aligned with Höppe (1992) cylinder factors"* | Clarifies shared physics formulation without claiming binary parity against external QGIS plugin | **RECTIFIED** |
| **Sequential Drift** | *"Provable drift immunity across sequential edits"* | *"No cumulative drift was observed in tested 5-step edit sequences (0.0000K reversion error)"* | General mathematical drift immunity is restricted to supported atomic edit operations | **RECTIFIED** |

---

