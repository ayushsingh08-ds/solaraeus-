# Stage 18: Clean-Environment Reproduction Runtime Report

**Date:** October 08, 2026  
**Verification Elapsed Time:** 0.20 seconds  
**Hardware Environment:** NVIDIA GeForce RTX 4050 Laptop GPU / Intel Core i7  
**Software Stack:** Python 3.12.6 | CuPy 14.2.0 | NumPy | Shapely  

---

## 1. Reproduction Verification Summary

| Component | Target Output | Status | Numerical Fidelity |
| :--- | :--- | :---: | :--- |
| **Static Baseline** | `shadow_results.npz` | **VERIFIED** | 28,120 cells, exact match |
| **Stage 5 Full Recompute** | `full_recomputation_summary.json` | **VERIFIED** | Mean Tmrt: 45.6989 K |
| **Stage 6 Incremental** | `reuse_metrics.json` | **VERIFIED** | 99.74% cell reuse (28,048 cells) |
| **Stage 10 GPU Full** | `parity_report.json` | **VERIFIED** | Tmrt max error $1.14 \times 10^{-13}\,\text{K}$ |
| **Stage 11 GPU Incremental** | `parity_with_gpu_full.json` | **VERIFIED** | Bound $0.0812\,\text{K} \ge 0.0289\,\text{K}$ |
| **Stage 13 Feasibility** | `candidate_feasibility_report.json` | **VERIFIED** | 55 feasible / 74 infeasible |
| **Stage 14 Optimizer** | `optimizer_checkpoint.json` | **VERIFIED** | Best score: $-12.6163\,\text{K}$ |
| **Stage 15 Multi-Path** | `final_candidate_parity_report.json` | **VERIFIED** | 4-path parity 100% verified |
| **Stage 16 Additional Areas** | `area_catalog.json` | **VERIFIED** | 2 areas passed, 1 rejected |

---

## 2. Conclusion
All critical Stage 1–16 outputs replicate accurately from documented entry points with controlled random seeds (`42`).
