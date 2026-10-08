# Stage 12: Comprehensive GPU Runtime, Memory & Work Profiling Report

**Date:** October 7, 2026  
**Hardware Device:** NVIDIA GeForce RTX 4050 Laptop GPU (CUDA 8.9, 20 SMs, 6.00 GB VRAM)  
**Host Architecture:** Intel64 Family 6 Model 183 Stepping 1, GenuineIntel (Windows 11)  
**Evaluation Scope:** 5 recorded trials per pathway (1 unrecorded warm-up trial) on Church Street domain ($148 \times 190 = 28,120$ cells).  

---

## 1. Executive Performance Benchmark

| Pathway | Mean Runtime (s) | Min (s) | Max (s) | Std Dev (s) | Kernel (ms) | Peak GPU Mem (MB) | Effective Speedup | Work Reduction |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **CPU Full** | 9.252 | 8.551 | 10.051 | 0.5876 | N/A | 0.0 | **1.00×** (Baseline) | 0.0% |
| **CPU Incremental** | 1.699 | 1.454 | 1.838 | 0.1449 | N/A | 0.0 | **5.44×** | 99.74% |
| **GPU Full** | 0.134 | 0.120 | 0.149 | 0.0117 | 60.00 | 1066.5 | **69.11×** | 0.0% |
| **GPU Incremental** | **0.191** | **0.188** | **0.193** | **0.0017** | **11.39** | **1066.5** | **48.52×** | **99.74%** |

---

## 2. Kernel Latency & Memory Telemetry

- **GPU Incremental Kernel Time**: **11.39 ms** (ultra-low latency on selective 72 cells).
- **Host-to-Device (H2D) Transfer**: 26.31 ms (dirty mask, dynamic mesh vertices/triangles).
- **Device-to-Host (D2H) Transfer**: 0.86 ms.
- **Ray-Work Reduction**: **925,584 rays eliminated** out of 927,960 total rays (**99.74% avoided**).
- **Cell Reuse Fraction**: **28,048 / 28,120 cells reused (99.74%)**.
- **Memory Footprint**: Peak GPU memory usage remained tightly bounded at **1066.5 MB** (< 20% of 6.00 GB total VRAM).

---

## 3. Profiling Acceptance Decision

```text
========================================================================
STATUS: STAGE_12_GPU_RUNTIME_MEMORY_WORK_PROFILING_COMPLETE
MEASURED SPEEDUPS & REUSE VERIFIED ACROSS 5 RECORDED TRIALS
GPU INCREMENTAL REUSE FRACTION: 99.74%
GPU INCREMENTAL KERNEL TIME: < 15 MS
========================================================================
```
