# CPU Reference API Regression Suite Report

**API Version:** `2.0.0-cpu-ref`  
**Status:** `FROZEN_STABLE`  
**Execution Timestamp:** `2026-10-07 18:33:20 UTC`  
**Commit Hash:** `909f9db1c6188995ae32b378a2642ac5247d643a`  
**Suite Result:** **10/10 TESTS PASSED (100% REGRESSION CLOSURE)**  
**Acceptance Token:** `STAGE_8_CPU_REFERENCE_API_FROZEN`  

---

## 1. Regression Test Results

| # | Test Name | Description | Target Metric | Error Observed | Status |
| :-: | :--- | :--- | :---: | :---: | :-: |
| 1 | **Baseline Regression** | Verifies that recomputed baseline matches static baseline reference identically | `shadow_mask_identity` | `0.00e+00` | ✅ **PASS** |
| 2 | **Shade-Panel Full Regression** | Verifies that full recompute matches Stage 5 frozen outputs within machine precision | `max_abs_error_tmrt_k` | `0.00e+00` | ✅ **PASS** |
| 3 | **Shade-Panel Incremental Regression** | Verifies that incremental update matches Stage 6 frozen outputs within machine precision | `max_abs_error_tmrt_k` | `0.00e+00` | ✅ **PASS** |
| 4 | **Full/Incremental Parity Regression** | Verifies that incremental and full solvers satisfy documented 0.50 K tolerance | `max_abs_error_tmrt_k` | `0.02890152869707663` | ✅ **PASS** |
| 5 | **Certificate Soundness Regression** | Verifies that mathematical error certificate has 0 violations and non-negative slack | `certificate_violations_count` | `0` | ✅ **PASS** |
| 6 | **Synthetic-Scene Regression** | Verifies clean execution and physical plausibility on synthetic box obstruction scene | `synthetic_grid_shape_and_no_nan` | `0.00e+00` | ✅ **PASS** |
| 7 | **Invalid-Input Behavior** | Verifies that invalid geometries, negative resolutions, and bad dates raise exceptions | `exception_raised_on_invalid_input` | `0.00e+00` | ✅ **PASS** |
| 8 | **Determinism Regression** | Verifies that two consecutive independent runs produce bit-identical results | `repeat_trial_max_error` | `0.00e+00` | ✅ **PASS** |
| 9 | **Serialization/Deserialization** | Verifies that Scene and TriangleMesh objects round-trip via JSON dictionary losslessly | `roundtrip_mesh_equality` | `0.00e+00` | ✅ **PASS** |
| 10 | **API Backward Compatibility** | Verifies that legacy get_backend('cpu') and functional signatures remain intact | `legacy_api_availability` | `0.00e+00` | ✅ **PASS** |

---

## 2. API Invariance and Freeze Contract

1. **Deterministic Guarantees:** All CPU reference routines are certified deterministic. Repeat runs produce exact bit-identical floating-point matrices.
2. **Correctness Invariance:** The CPU reference solver serves as the inviolable correctness oracle for all GPU development in Stage 9 and beyond.
3. **Backward Compatibility:** All existing signatures (`full_recompute`, `incremental_update_certified`, `incremental_update_exact`) maintain full backward compatibility with frozen results.
