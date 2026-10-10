## 24. SOLARAEUS Solver Development Track: Stages 10 through 16 Execution (Milestone 24)

**Date**: October 8, 2026  
**Scope**: Sequential execution of authoritative solver roadmap Stages 10 through 16 without terrain/canopy extensions.  
**Execution Token Sequence**:
- `STAGE_10_COMPLETE`
- `STAGE_11_COMPLETE`
- `STAGE_12_COMPLETE`
- `STAGE_13_COMPLETE`
- `STAGE_14_COMPLETE`
- `STAGE_15_COMPLETE`
- `STAGE_16_COMPLETE`
- `STAGE_10_GPU_FULL_VS_CPU_VALIDATION_COMPLETE`
- `STAGE_11_GPU_INCREMENTAL_RECOMPUTATION_COMPLETE`
- `STAGE_12_GPU_RUNTIME_MEMORY_WORK_PROFILING_COMPLETE`
- `STAGE_13_GEOGRAPHIC_FEASIBILITY_AND_PARAMETERIZATION_COMPLETE`
- `STAGE_14_BASELINE_SEARCH_AND_CONSTRAINED_AI_OPTIMIZER_COMPLETE`
- `STAGE_15_FINAL_CANDIDATE_VALIDATION_AND_UNCERTAINTY_COMPLETE`
- `STAGE_16_ADDITIONAL_AREA_TESTING_AND_PUBLICATION_COMPLETE`
- **Master Success Token**: `STAGES_10_TO_16_EXECUTION_COMPLETE`

### 24.1 Stage 10: GPU Full-vs-CPU Full Validation
- **Execution Script**: [`scripts/execute_stage_10_gpu_full_vs_cpu.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_10_gpu_full_vs_cpu.py)
- **Output Artifacts Directory**: `results/stage_10_gpu_full_cpu_validation/`
- **Artifacts**: `inputs_manifest.json`, `gpu_full_outputs.json`, `cpu_full_outputs.json`, `parity_report.json`, `runtime_comparison.json`, `stage_10_test_results.json`
- **Hardware Platform**: NVIDIA GeForce RTX 4050 Laptop GPU (6.00 GB VRAM, Compute 8.9) via CuPy 14.2.0 and CUDA 12.8.
- **Verification against Frozen CPU Reference Oracle (`2.0.0-cpu-ref`)**:
  - Direct Shadow Mask Error: **$0.000000$** (0 differing cells, exact bit match).
  - Direct Shortwave Flux Error: **$0.000000\,\text{W/m}^2$** (0 differing cells, exact bit match).
  - SVF Error: Max **$1.0547 \times 10^{-14}$**, Mean **$3.93 \times 10^{-16}$** (tolerance $10^{-4}$).
  - Mean Radiant Temperature ($T_{\text{mrt}}$) Error: Max **$1.1368 \times 10^{-13}\,\text{K}$**, Mean **$1.62 \times 10^{-14}\,\text{K}$** (tolerance $0.05\,\text{K}$).
  - UTCI Error: **$0.000000\,^\circ\text{C}$** (0 differing cells).
  - Runtime Speedup: CPU full solve $5.71\,\text{s}$ vs GPU full solve $0.483\,\text{s}$ (**$11.83\times$ speedup**).
- **Test Suite**: `tests/test_stage_10_gpu_validation.py` (5 / 5 passed).

### 24.2 Stage 11: GPU Incremental Recomputation and Validation
- **Execution Script**: [`scripts/execute_stage_11_gpu_incremental.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_11_gpu_incremental.py)
- **Output Artifacts Directory**: `results/stage_11_gpu_incremental/`
- **Artifacts**: `inputs_manifest.json`, `gpu_incremental_outputs.json`, `affected_region_mask.json`, `parity_with_cpu_incremental.json`, `parity_with_gpu_full.json`, `gpu_incremental_certificate.json`, `runtime_metrics.json`, `stage_11_test_results.json`
- **Methodology & Mathematical Bounds**:
  - Maintained resident GPU device arrays for baseline static state.
  - Sliced active ROI to the candidate frustum, launching CUDA kernels exclusively over dirty cells.
  - Recomputed cells: **72 cells (0.26%)**; Reused cells: **28,048 cells (99.74%)**.
  - Certificate Violations: **0 across all 28,120 cells**.
  - Reused cell max actual $T_{\text{mrt}}$ error: **$0.028902\,\text{K}$**, strictly bounded by theoretical concave bound $B_T(x) = 0.081231\,\text{K} \le \varepsilon_T = 0.50\,\text{K}$.
  - Speedup: GPU incremental latency **$11.40\,\text{ms}$** (**$500.87\times$ speedup** vs CPU full, **$36.84\times$ speedup** vs CPU incremental).
- **Test Suite**: `tests/test_stage_11_gpu_incremental.py` (5 / 5 passed).

### 24.3 Stage 12: GPU Runtime, Memory, and Work Profiling
- **Execution Script**: [`scripts/execute_stage_12_gpu_profiling.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_12_gpu_profiling.py)
- **Output Artifacts Directory**: `results/stage_12_gpu_profiling/`
- **Artifacts**: `gpu_profiling_environment.json`, `gpu_runtime_summary.json`, `gpu_memory_summary.json`, `gpu_work_summary.json`, `gpu_benchmark_trials.csv`, `gpu_cpu_speedup_report.md`, `stage_12_test_results.json`
- **Profiling Outcomes**:
  - Benchmark Trials: 5 independent warm-up and timed trials across CPU Full, CPU Incremental, GPU Full, and GPU Incremental.
  - Peak GPU VRAM Allocation: **$1,089.45\,\text{MB}$** (well below 6.0 GB hardware capacity).
  - Ray-Work Reduction: **$99.74\%$** (925,584 rays avoided per timestep).
  - Host-to-Device Memory Overhead: $< 1.2\,\text{ms}$ for candidate parameter dispatch.
- **Test Suite**: `tests/test_stage_12_gpu_profiling.py` (4 / 4 passed).

### 24.4 Stage 13: Geographic Feasibility and Intervention Parameterization
- **Execution Script**: [`scripts/execute_stage_13_geographic_feasibility.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_13_geographic_feasibility.py)
- **Output Artifacts Directory**: `results/stage_13_geographic_feasibility/`
- **Artifacts**: `intervention_parameter_schema.json`, `feasibility_rules.json`, `candidate_feasibility_report.json`, `feasible_candidate_catalog.csv`, `infeasible_candidate_catalog.csv`, `stage_13_test_results.json`, `feasibility_plots/candidate_feasibility_screening.png`
- **Screening Rules & Physical Constraints**:
  - Formal parameter schema: length $[2.0, 15.0]\,\text{m}$, width $[1.0, 8.0]\,\text{m}$, height $[3.0, 6.0]\,\text{m}$, azimuth $[0, 360)^\circ$, tilt $[0, 45]^\circ$, albedo $[0.1, 0.9]$, emissivity $[0.7, 0.98]$.
  - Constraint rules: building collision intersection check, pedestrian domain polygon containment, pedestrian underside clearance ($h \ge 3.0\,\text{m}$, $h \le 5.5\,\text{m}$), maximum single footprint area ($A \le 60.0\,\text{m}^2$).
  - Evaluated 129 candidates: **55 feasible candidates** cataloged, **74 infeasible candidates** cataloged with detailed violation reasons.
- **Test Suite**: `tests/test_stage_13_geographic_feasibility.py` (3 / 3 passed).

### 24.5 Stage 14: Baseline Search and Constrained AI Optimizer
- **Execution Script**: [`scripts/execute_stage_14_constrained_optimizer.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_14_constrained_optimizer.py)
- **Output Artifacts Directory**: `results/stage_14_constrained_optimizer/`
- **Artifacts**: `baseline_search_results.csv`, `optimizer_configuration.json`, `optimizer_candidate_history.csv`, `optimizer_best_candidates.csv`, `optimizer_checkpoint.json`, `optimizer_reproducibility.json`, `optimizer_constraint_report.json`, `optimizer_certificate_summary.json`, `stage_14_test_results.json`
- **Optimization Search & Safety**:
  - Baseline Grid Search (Part A): 17 uniform candidate proposals systematically evaluated.
  - Constrained AI Optimizer (Part B): 29 proposal iterations driven by objective function maximizing thermal comfort relief while enforcing 100% feasibility constraints.
  - Top 5 candidates recorded; Best candidate `CAND_FINAL_BEST` ($x=120.0\,\text{m}, y=60.0\,\text{m}, L=6.0\,\text{m}, W=4.0\,\text{m}, H=4.0\,\text{m}$) achieved $-12.62\,\text{K}$ peak cooling.
  - Mathematical Guarantee: **100% of evaluations certified** with zero bound violations.
  - Checkpoint Recovery: Exactly verified state restoration from `optimizer_checkpoint.json`.
- **Test Suite**: `tests/test_stage_14_constrained_optimizer.py` (4 / 4 passed).

### 24.6 Stage 15: Final Candidate Validation and Uncertainty Analysis
- **Execution Script**: [`scripts/execute_stage_15_final_validation.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_15_final_validation.py)
- **Output Artifacts Directory**: `results/stage_15_final_validation/`
- **Artifacts**: `final_candidate_validation.json`, `final_candidate_validation.md`, `final_candidate_certificates.json`, `final_candidate_parity_report.json`, `final_candidate_uncertainty.csv`, `final_candidate_sensitivity.csv`, `final_candidate_constraint_report.json`, `final_candidate_reproducibility.json`, `stage_15_test_results.json`
- **4-Path Validation & Rigorous Uncertainty**:
  - Evaluated top 3 candidates: `CAND_FINAL_BEST`, `CAND_CANONICAL`, `CAND_ALT_LHS`.
  - 4-Path Parity (CPU Full, CPU Incremental, GPU Full, GPU Incremental): 100% parity verified across all physical fields.
  - Monte Carlo Uncertainty Analysis: 50 runs per candidate with weather perturbations ($\sigma_{\text{DNI}} = 25.0\,\text{W/m}^2$, $\sigma_{\text{Ta}} = 0.5\,\text{K}$, $\sigma_{\text{wind}} = 0.2\,\text{m/s}$).
  - Parameter Sensitivity Analysis: Computed first-order sensitivity gradients across solar angles, radiation components, and aerodynamic parameters.
  - Ranking Definitiveness Audit: In accordance with rigorous scientific integrity, because 95% confidence intervals overlap between candidate designs, the ranking is formally classified as **`NON_DEFINITIVE_OVERLAPPING_CI`** (empirical rank stability 35%), avoiding false claims of definitive superiority.
- **Test Suite**: `tests/test_stage_15_final_validation.py` (4 / 4 passed).

### 24.7 Stage 16: Additional Area Testing and Publication Package
- **Execution Script**: [`scripts/execute_stage_16_additional_areas_and_publication.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/execute_stage_16_additional_areas_and_publication.py)
- **Output Artifacts Directories**:
  - `results/stage_16_additional_areas/`: `area_catalog.json`, `area_input_validation_report.json`, `cross_area_summary.csv`, `cross_area_limitations.md`, `stage_16_test_results.json`, along with subdirectories `area_baseline_results/`, `area_intervention_results/`, `area_parity_reports/`, `area_certificate_reports/`, `area_uncertainty_reports/`.
  - `results/stage_16_publication_package/`: `publication_methodology.md`, `publication_results_summary.md`, `publication_limitations.md`, `reproducibility_guide.md`, `data_and_code_availability.md`, `license_and_provenance.md`, `figure_manifest.json`, `table_manifest.json`, `final_project_status.json`, `stage_16_test_results.json`.
- **Multi-Area Verification & Negative Control**:
  - `AREA_BRIGADE_ROAD_EXT` ($120\times 150\,\text{m}$ domain, 84 buildings): Baseline and intervention validated; 100% certificate compliance.
  - `AREA_MG_ROAD_PLAZA` ($160\times 160\,\text{m}$ domain, 62 buildings): Baseline and intervention validated; 100% certificate compliance.
  - `AREA_HILLSIDE_COMPLEX` (negative control): Slope of $18.5\%$ correctly detected and rejected by input validation engine as violating flat ground assumptions ($z=0.0\,\text{m}$).
- **Publication Bundle**: Complete scientific manuscript documentation, figure/table manifests, and open-access data and code availability declarations frozen.
- **Test Suite**: `tests/test_stage_16_publication_package.py` (4 / 4 passed).

### 24.8 Multi-Stage Cross-Verification & Repository Protection Audit
- **Master Final Report**: [`results/STAGES_10_TO_16_FINAL_REPORT.md`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/STAGES_10_TO_16_FINAL_REPORT.md)
- **Validation Report**: [`results/stages_10_to_16_validation_report.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/stages_10_to_16_validation_report.json) & [`results/stages_10_to_16_validation_report.md`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/stages_10_to_16_validation_report.md)
- **Protection Audit**: [`results/stages_10_to_16_protection_audit.json`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/results/stages_10_to_16_protection_audit.json)
  - Verified all 14 critical historical benchmark files and raw zip archives via SHA-256 hashes.
  - All 14 files confirmed **100% INTACT AND UNMODIFIED**.
- **Physics Decoupling Compliance**:
  - Street-tree geometries (BBMP dataset) were **NOT** integrated into the solver.
  - FABDEM terrain elevation rasters were **NOT** integrated into the solver.
- **Full Pytest Test Suite**:
  - Ran `python -m pytest -o pythonpath=src` across all 32 test files: **323 passed**, 0 failures in 108.55s.

---

