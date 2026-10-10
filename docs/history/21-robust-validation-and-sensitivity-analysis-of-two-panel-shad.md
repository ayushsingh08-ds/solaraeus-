## 21. Robust Validation and Sensitivity Analysis of Two-Panel Shade Optimization (Milestone 21)

### 21.1 Production Execution & Overview
- **Production Runner**: [`scripts/run_church_street_two_panel_robustness.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/run_church_street_two_panel_robustness.py)
- **Output Artifacts Directory**: `results/church_street_two_panel_robustness_20261007_122543/`
- **10 Study Dimensions Verified**:
  1. *Random-Seed Robustness*: Seeds 7, 42, 12345 evaluated. All seeds converge to dual structures separated by >20m that maximize pedestrian shade (Mean score = 56.4936 ± 0.0555).
  2. *Search Budget Sensitivity*: Budgets 25, 50, 100 evaluated. Budget 50 improved best objective to 56.4025; budget 100 to 56.3592 with diminishing returns beyond 50 evaluations.
  3. *Weather Perturbation Sensitivity*: Tested under 6 scenarios (nominal, hotter air, higher humidity, lower wind, lower direct, higher diffuse). Confirmed direct beam occlusion is primary driver of cooling efficacy (peak drop 12.68K nominal vs 9.04K lower direct).
  4. *Diurnal Solar Timestep Sensitivity*: Evaluated across 09:00, 11:00, 13:00, 15:00. Peak local $T_{\text{mrt}}$ drop reached 17.44K at 11:00 (high sun), confirming sustained multi-hour effectiveness.
  5. *Objective Formulation Sensitivity*: Re-ranked across comfort-focused, balanced, cost-focused, and coverage-focused formulations.
  6. *Constraint Geometry Sensitivity*: 500 candidate proposals screened per configuration. Building setback identified as most restrictive canyon constraint (yield dropped to 8.20% with 1.0m setback).
  7. *Cross-Intervention Comparison*: Baseline ($0\,\text{m}^2$, 0% coverage) vs Stage 1 Single ($8.82\,\text{m}^2$, 29.94% coverage) vs Stage 2 Single ($10.26\,\text{m}^2$, 59.88% coverage) vs Stage 3 Dual ($22.87\,\text{m}^2$, 74.85% coverage) vs 50-Budget Dual ($17.28\,\text{m}^2$, 59.88% coverage).
  8. *Three-Path Parity Verification*: Exact shadow/SVF equivalence and max $T_{\text{mrt}}$ difference $\le 0.0288\,\text{K}$ across CPU full, GPU full, and GPU incremental solvers (100% passed).
  9. *Certificate Validation*: 0 certificate violations across all evaluations.
  10. *Incremental Reuse Telemetry*: Sustained 98.76% average cell reuse across physical evaluations.
- **Visual Artifacts**: Generated 13 publication-quality figures in `plots/`.
- **Test Suite**: Added 16 tests in [`tests/test_two_panel_robustness.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_two_panel_robustness.py).
- **Success Token**: `ROBUST_TWO_PANEL_VALIDATION_COMPLETE`.

---

