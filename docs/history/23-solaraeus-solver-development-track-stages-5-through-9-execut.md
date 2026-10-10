## 23. SOLARAEUS Solver Development Track: Stages 5 through 9 Execution (Milestone 23)

**Date**: October 7, 2026  
**Scope**: Sequential execution of authoritative solver roadmap Stages 5 through 9 without terrain/canopy extensions.  
**Execution Token Sequence**:
- `STAGE_5_SHADE_PANEL_FULL_RECOMPUTATION_COMPLETE`
- `STAGE_6_SHADE_PANEL_INCREMENTAL_RECOMPUTATION_COMPLETE`
- `STAGE_7_CERTIFICATE_AUDIT_AND_CPU_EFFICIENCY_COMPLETE`
- `STAGE_8_CPU_REFERENCE_API_FROZEN`
- `STAGE_9_GPU_DIRECT_SHADOW_SVF_BACKEND_COMPLETE`
- **Master Success Token**: `STAGES_05_TO_09_EXECUTION_COMPLETE`

### 23.1 Stage 5: Shade-Panel Full Recomputation
- **Execution Script**: [`scripts/execute_stage_05_shade_panel_full.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_05_shade_panel_full.py)
- **Output Artifacts Directory**: `results/stage_05_shade_panel_full/`
- **Methodology**: Pure, non-incremental, ground-truth solve across all 28,120 cells ($148 \times 190$ domain, $\Delta x = 2.0\,\text{m}$, receptor height $z_{\mathrm{ped}} = 1.1\,\text{m}$) with the overhead shade-panel (`BLR_SHADE_001` / `CANOPY_001`: $6.0\,\text{m} \times 4.0\,\text{m} \times 0.2\,\text{m}$, height $4.0\,\text{m}$, albedo $0.30$, emissivity $0.90$) placed at $(120.0\,\text{m}, 60.0\,\text{m})$.
- **Solar Forcing**: April 15, 2024 at 09:00:00 UTC (Solar altitude $57.916^\circ$, Azimuth $268.1655^\circ$, direct normal irradiance $850\,\text{W/m}^2$, diffuse horizontal $150\,\text{W/m}^2$).
- **Key Metrics**:
  - Direct shadow coverage: $15,108 / 28,120$ cells ($53.73\%$)
  - Mean SVF: $0.463784$ (Min: $0.098418$, Max: $0.985652$)
  - Mean $T_{\text{mrt}}$: $45.6989\,\text{K}$ (Min: $33.6405\,\text{K}$, Max: $55.0865\,\text{K}$)
  - Mean UTCI: $36.4678\,^\circ\text{C}$ (Min: $31.8000\,^\circ\text{C}$, Max: $38.9000\,^\circ\text{C}$)
  - Solver Runtime: $5.71\,\text{s}$ (CPU vectorized)
- **Validation**: Passed all 10 required consistency and physical plausibility tests.

### 23.2 Stage 6: Shade-Panel Incremental Recomputation
- **Execution Script**: [`scripts/execute_stage_06_shade_panel_incremental.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_06_shade_panel_incremental.py)
- **Output Artifacts Directory**: `results/stage_06_shade_panel_incremental/`
- **Methodology**: Reused baseline static fields for all unaffected cells, dispatching ray tracing exclusively to the conservative affected shadow frustum:
  - Recomputed cells: **72 cells (0.26%)**
  - Reused cells: **28,048 cells (99.74%)**
  - Ray-work reduction: **99.74%** (925,584 rays avoided out of 927,960)
  - Incremental runtime: **0.42 s** ($13.6\times$ wall-clock speedup vs full solve)
- **Soundness & Certificate Guarantees**:
  - Evaluated pointwise Stefan-Boltzmann concave upper bound $B_T(x) \le \varepsilon_T = 0.50\,\text{K}$.
  - Recomputed cells: $B_T(x)$ peaked at $49.95\,\text{K}$ under the panel, forcing exact recomputation.
  - Reused cells: Max bound $B_T(x) = 0.083\,\text{K} \le 0.50\,\text{K}$.
  - Certificate violations: **0 across all 28,120 cells**.
  - Reused cell max actual $T_{\text{mrt}}$ error: **$0.028902\,\text{K}$** (strictly $\le 0.50\,\text{K}$).

### 23.3 Stage 7: Certificate Audit and CPU Efficiency Analysis
- **Execution Script**: [`scripts/execute_stage_07_certificate_and_cpu_audit.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_07_certificate_and_cpu_audit.py)
- **Output Artifacts Directory**: `results/stage_07_certificate_and_cpu_audit/`
- **18-Certificate Audit**:
  - 16 Authoritative certificates: input manifest integrity, scene metadata, coordinate consistency, valid-cell masks, direct shadow bounds, SVF bounds, radiation bounds, thermal comfort bounds, full/incremental parity, affected-region correctness, determinism, provenance, reproducibility, watertightness, collision avoidance, certificate slack.
  - 2 Diagnostic certificates: asymptotic invariance, corridor sensitivity.
  - Audit outcome: **18 / 18 PASSED (100% pass rate, 0 violations)**.
- **5-Trial CPU Efficiency Benchmark**:
  - Baseline Full: Wall-clock $5.71 \pm 0.04\,\text{s}$ | CPU time $5.68 \pm 0.03\,\text{s}$
  - Stage 5 Full: Wall-clock $5.71 \pm 0.05\,\text{s}$ | CPU time $5.67 \pm 0.04\,\text{s}$
  - Stage 6 Incremental: Wall-clock $0.42 \pm 0.01\,\text{s}$ | CPU time $0.41 \pm 0.01\,\text{s}$
  - Speedup: **$13.6\times$**
  - Peak Heap Memory: Bounded strictly under $10\,\text{MB}$.
- **Numerical Parity across Solvers**:

| Field | Tolerance | Max Error | Mean Error | Differing Cells | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Direct Shadow Mask** | $0.0$ | **$0.000000$** | $0.000000$ | $0$ | **PASS** |
| **Direct Shortwave Irradiance** | $0.0\,\text{W/m}^2$ | **$0.000000$** | $0.000000$ | $0$ | **PASS** |
| **Sky View Factor (SVF)** | $0.01$ | **$0.004195$** | $2.01 \times 10^{-6}$ | $0$ | **PASS** |
| **Total Shortwave Flux** | $0.50\,\text{W/m}^2$ | **$0.128809$** | $6.17 \times 10^{-5}$ | $0$ | **PASS** |
| **Total Longwave Flux** | $0.50\,\text{W/m}^2$ | **$0.129326$** | $6.19 \times 10^{-5}$ | $0$ | **PASS** |
| **Mean Radiant Temp ($T_{\text{mrt}}$)** | $0.50\,\text{K}$ | **$0.028902$** | $1.39 \times 10^{-5}$ | $0$ | **PASS** |
| **Thermal Comfort (UTCI)** | $0.50\,^\circ\text{C}$ | **$0.100000$** | $3.56 \times 10^{-6}$ | $0$ | **PASS** |

### 23.4 Stage 8: Freeze Stable CPU Reference API
- **Execution Script**: [`scripts/execute_stage_08_cpu_reference_freeze.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_08_cpu_reference_freeze.py)
- **Output Artifacts Directory**: `results/stage_08_cpu_reference_freeze/`
- **Frozen Version**: `2.0.0-cpu-ref` (`FROZEN_STABLE`)
- **Reference Oracle Role**: Established as the immutable ground-truth oracle against which GPU, mobile, and web backends must validate.
- **Formal JSON Schemas Exported**:
  - `Scene`, `Weather`, `SimulationConfig`, `SimulationResult`, `IncrementalUpdateResult`, `ErrorCertificate`.
- **10 Mandatory Regression Tests**: 10 / 10 passed (baseline regression, full regression, incremental regression, parity, certificate, synthetic, invalid input, determinism, serialization, API compatibility).

### 23.5 Stage 9: GPU Direct-Shadow and SVF Backend
- **Execution Script**: [`scripts/execute_stage_09_gpu_direct_shadow_svf.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_09_gpu_direct_shadow_svf.py)
- **Output Artifacts Directory**: `results/stage_09_gpu_direct_shadow_svf/`
- **Hardware Platform**: NVIDIA GeForce RTX 4050 Laptop GPU (CUDA Compute Capability 8.9, 20 SMs, 6.00 GB VRAM, Driver 576.88).
- **Kernels**:
  - `moller_trumbore_shadow_kernel`: CUDA C++ triangle ray intersection.
  - `compute_svf_horizon_kernel`: CUDA C++ horizon elevation angular integration.
- **Verification against Frozen CPU Reference API**:
  - Direct Shadow Mask Error: **$0.000000$** (0 differing cells, exact bit match).
  - SVF Error: Max **$1.05 \times 10^{-14}$**, Mean **$3.93 \times 10^{-16}$** (0 differing cells at $10^{-4}$ tolerance, IEEE-754 double-precision limit).
  - GPU validation suite: 12 / 12 tests passed.

### 23.6 Multi-Stage Cross-Verification & Repository Protection Audit
- **Master Final Report**: [`results/STAGES_05_TO_09_FINAL_REPORT.md`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/STAGES_05_TO_09_FINAL_REPORT.md)
- **Validation Report**: [`results/stages_05_to_09_validation_report.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/stages_05_to_09_validation_report.json)
- **Protection Audit**: [`results/stages_05_to_09_protection_audit.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/stages_05_to_09_protection_audit.json)
  - Verified 14 critical historical benchmark files across `results/church_street_static_20261006_232110/`, `results/church_street_shade_full_20261007_001600/`, and `results/church_street_shade_incremental_20261007_081114/`.
  - All 14 files confirmed **100% INTACT AND UNMODIFIED**.
- **Pytest Suite**: Complete run via `pytest -o pythonpath=src` passing at **294 / 294 passed** (0 failures).

---

