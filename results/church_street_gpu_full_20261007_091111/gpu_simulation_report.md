# Church Street GPU Simulation Backend: Full Execution & CPU Parity Report

## Executive Summary
This report documents the validation and performance audit of the GPU simulation backend implemented for the Church Street microclimate pipeline.
The GPU backend utilizes custom CUDA C++ Möller-Trumbore ray-triangle intersection and multi-azimuth horizon elevation scan kernels compiled via CuPy.
All evaluated physical fields were compared directly against the frozen CPU full recomputation reference (`results/church_street_shade_full_20261007_001600/`).

- **Numerical Parity Status**: **ALL CHECKS PASSED**
- **Discrepancy Count**: **0 across all 28,120 grid cells**
- **Direct Shadow Mask Parity**: **Bit-for-bit exact (0.000000 error)**
- **Sky View Factor (SVF) Parity**: **Max error 1.05e-14 (machine precision)**
- **Mean Radiant Temperature (Tmrt) Parity**: **Max error 1.14e-13 K (tolerance 0.05 K)**
- **UTCI Thermal Comfort Parity**: **Bit-for-bit exact (0.000000 error)**
- **Ray-Level Step Speedup**: **57.79×**
- **End-to-End Pipeline Speedup**: **5.52×**

## Hardware & Environment
- **GPU Device**: NVIDIA GeForce RTX 4050 Laptop GPU (6.14 GB VRAM)
- **Compute Architecture**: Ada Lovelace (SM 8.9)
- **CUDA Runtime**: CUDA 12.9 Toolkit Wheels / CuPy 14.2.0
- **Precision Policy**: IEEE-754 64-bit Floating Point (FP64) in CUDA kernels for absolute numerical fidelity.

## Profiling & Performance Breakdown
| Metric | Value |
| :--- | :--- |
| Direct Shadow Rays | 28,120 rays |
| SVF Directional Rays | 899,840 rays |
| Total Evaluated Rays | 927,960 rays |
| Scene Triangles | 2,148 triangles |
| Scene Upload Time | 0.599 ms |
| GPU Kernel Runtime | 59.371 ms |
| Host Transfer Time | 0.253 ms |
| Total GPU Ray-Work Time | 60.222 ms |
| CPU Reference Ray-Work Time | 3,480 ms |
| Peak GPU Memory Allocation | 1064.5 MB |
| Ray-Work Speedup | 57.79× |
| End-to-End Speedup | 5.52× |

## Numerical Tolerance Policy & Parity Table
| Physical Field | Documented Tolerance | Observed Max Absolute Error | Observed RMS Error | Discrepancies | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Direct Shadow Mask | 0.0 (exact bit match) | 0.000000e+00 | 0.000000e+00 | 0 | PASS |
| Sky View Factor (SVF) | 1.00e-04 | 1.054712e-14 | 3.929418e-16 | 0 | PASS |
| Direct Shortwave Irradiance | 1.00e-04 W/m² | 0.000000e+00 | 0.000000e+00 | 0 | PASS |
| Total Shortwave Flux | 1.00e-02 W/m² | 3.410605e-13 | 1.418430e-14 | 0 | PASS |
| Total Longwave Flux | 1.00e-02 W/m² | 3.410605e-13 | 2.443000e-14 | 0 | PASS |
| Mean Radiant Temp (Tmrt) | 0.050 K | 1.136868e-13 K | 8.205808e-15 K | 0 | PASS |
| UTCI Comfort Index | 0.050 °C | 0.000000e+00 °C | 0.000000e+00 °C | 0 | PASS |

## Ready for GPU Incremental Recomputation
All physical fields and boundary condition transformations have been verified with complete fidelity against the frozen reference. The GPU simulation backend is fully operational and certified.
