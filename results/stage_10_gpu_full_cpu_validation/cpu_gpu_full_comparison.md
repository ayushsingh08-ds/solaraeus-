# Stage 10: Complete GPU Full-vs-CPU Simulation Validation Report

**Date:** October 7, 2026  
**Reference Version:** `2.0.0-cpu-ref`  
**Execution Point:** `STAGE_10_GPU_FULL_VS_CPU_VALIDATION`  
**Device Platform:** NVIDIA GeForce RTX 4050 Laptop GPU (CUDA 8.9, 20 SMs, 6.00 GB VRAM)  
**Status:** **ALL TESTS PASSED**  

---

## 1. Executive Summary

This report delivers the rigorous numerical validation of the complete SOLARAEUS GPU simulation backend against the frozen CPU reference API (`2.0.0-cpu-ref`).
All 7 primary microclimate physical fields were compared array-by-array across the 28,120-cell Church Street domain ($148 \times 190$ grid, $\Delta x = 2.0\,\text{m}$, $z_{ped} = 1.1\,\text{m}$) with the approved overhead shade-panel (`BLR_SHADE_001`).

In accordance with strict verification rules:
- **Zero Coordinate or Mask Shifts**: Grid coordinates and valid masks are identical.
- **Exact Bit-Match Direct Shadow**: 0 differing cells out of 28,120 (0.000000 error).
- **Exact Bit-Match Direct Shortwave**: 0 differing cells out of 28,120 (0.000000 error).
- **Double-Precision SVF Parity**: Max absolute error is $1.05 \times 10^{-14}$ (well below $1.00 \times 10^{-4}$ tolerance).
- **Sub-Kelvin $T_{mrt}$ & UTCI Parity**: Max $T_{mrt}$ error is $1.14 \times 10^{-13}\,\text{K}$ ($< 0.05\,\text{K}$ tolerance).
- **Deterministic Repeatability**: Verified bit-identical across 3 consecutive GPU executions.

---

## 2. Pointwise Physical Field Parity Matrix (Church Street Shade-Panel Full)

| Physical Field | Unit | Tolerance | Differing Cells | Max Abs Error | Mean Abs Error | P95 Abs Error | P99 Abs Error | Max Rel Error | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Direct Shadow Mask** | fraction | 0.0 | **0** | **0.000000** | 0.000000 | 0.000000 | 0.000000 | 0.000000 | ✅ PASS |
| **Direct Shortwave Irradiance** | W/m² | 0.0 | **0** | **0.000000** | 0.000000 | 0.000000 | 0.000000 | 0.000000 | ✅ PASS |
| **Sky View Factor (SVF)** | fraction | 1.00e-4 | **0** | **1.05e-14** | 7.32e-17 | 2.22e-16 | 8.88e-16 | 1.62e-14 | ✅ PASS |
| **Total Shortwave Flux** | W/m² | 0.0100 | **0** | **3.41e-13** | 3.08e-15 | 2.84e-14 | 5.68e-14 | 1.48e-15 | ✅ PASS |
| **Total Longwave Flux** | W/m² | 0.0100 | **0** | **3.41e-13** | 7.25e-15 | 5.68e-14 | 1.14e-13 | 7.75e-16 | ✅ PASS |
| **Mean Radiant Temp ($T_{mrt}$)** | K | 0.0500 | **0** | **1.14e-13** | 1.17e-15 | 0.00e+00 | 5.68e-14 | 2.48e-15 | ✅ PASS |
| **Thermal Comfort (UTCI)** | °C | 0.0500 | **0** | **0.00e+00** | 0.00e+00 | 0.00e+00 | 0.00e+00 | 0.00e+00 | ✅ PASS |

---

## 3. Mandatory Test Suite Results

1. **Static Baseline CPU vs GPU**: **PASS** (0 differing shadow cells; Max SVF err: 1.05e-14; Max $T_{mrt}$ err: 1.14e-13 K).
2. **Shade-Panel Full CPU vs GPU**: **PASS** (All 7 fields passed within documented tolerance; 0 discrepant cells).
3. **Synthetic Scene CPU vs GPU**: **PASS** (Bit-identical shadow; SVF err: 2.78e-16; $T_{mrt}$ err: 5.68e-14 K).
4. **Edge-Case Scene CPU vs GPU**: **PASS** (Extreme zenith altitude 88°; tall tower; 0 shadow diffs; SVF err: 0.00e+00).
5. **Mask and Metadata Comparison**: **PASS** (Identical grid shapes [148, 190], coordinates match, solar angles within 1e-9 deg).
6. **Repeated GPU Run Determinism**: **PASS** (3 consecutive runs produced bit-identical outputs across all fields).

---

## 4. Verification Conclusion

```text
========================================================================
STATUS: STAGE_10_GPU_FULL_VS_CPU_VALIDATION_COMPLETE
ALL MANDATORY CRITERIA SATISFIED
ZERO DISCREPANCIES OUTSIDE TOLERANCE
========================================================================
```
