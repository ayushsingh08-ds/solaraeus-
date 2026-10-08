# SOLARAEUS: Stages 17 Through 23 Final Engineering & Scientific Report

**Execution Date:** October 08, 2026  
**Solver Engine Versions:** `2.0.0-cpu-ref` (Frozen Flat Reference) | `2.1.0-cpu-terrain` / `2.1.0-gpu-terrain` (Terrain Extension)  
**Hardware Platform:** NVIDIA GeForce RTX 4050 Laptop GPU (6.00 GB VRAM, CC 8.9), Intel Core i7  

---

## 1. Executive Summary & Required Final Report Sections

### 1.1 Publication Review Status (`Stage 17`)
- **Status:** `AUDIT_PASSED`
- All empirical claims (speedup, error bounds, cooling magnitude, ranking uncertainty) match documented numerical results.
- Zero private paths or developer directories remain in publication documents.
- Third-party licenses (ODbL, CC-BY-SA, MIT, BSD) are fully documented.

### 1.2 Archival Manifest Status (`Stage 17`)
- **Release Candidate:** `solaraeus-v2.0.0-cpu-ref-rc1` (57 release files indexed with SHA-256 hashes).
- **Auto-Publish:** `False` (no automatic upload or remote distribution).

### 1.3 Clean-Environment Reproducibility Status (`Stage 18`)
- **Status:** `REPRODUCIBILITY_CONFIRMED`
- Replicated 9 key project systems from clean entry points with locked random seed `42`.
- Checksums and scalar fields match reference files with 0 tolerance breaches and 0 failures.

### 1.4 Researcher Approval Status (`Stage 19`)
- **Status:** `STAGE_19_HUMAN_APPROVAL_PENDING`
- In accordance with non-fabrication rules, all 19 approval decisions default to `PENDING`.
- No data has been promoted to `data/processed/` and real-world tree/terrain simulation remains blocked.

### 1.5 DTM Source and Quality Status (`Stage 20`)
- **Status:** `STAGE_20_SYNTHETIC_TERRAIN_ONLY`
- FABDEM v1.2 (30m) is officially classified as `REGIONAL_REFERENCE_ONLY` due to inability to resolve 150 mm curbs.
- Synthetic mathematical terrain profiles were constructed and validated for software engine testing. Real-world terrain claims remain strictly blocked.

### 1.6 Field Tree-Validation Status (`Stage 21`)
- **Status:** `STAGE_21_FIELD_VALIDATION_PENDING`
- Core trees T08–T13 and context trees retain `PHOTO_ESTIMATED_ONLY` and `UNCERTAIN_HISTORICAL_PHOTO_ONLY` classifications.
- On-site 2026 field survey is required before claiming calibrated tree geometry.

### 1.7 Terrain-Aware CPU API Status (`Stage 22`)
- **Status:** `STAGE_22_COMPLETE` (`STAGE_22_TERRAIN_AWARE_CPU_REFERENCE_COMPLETE`)
- API Version `2.1.0-cpu-terrain` implemented in `urban_comfort.terrain`.
- Supports regular raster `TerrainGrid` and `TerrainAwareScene`.
- Tested on synthetic incline, stepped curb, and NoData hole scenarios.

### 1.8 Terrain-Aware GPU Full Status (`Stage 23`)
- **Status:** `STAGE_23_COMPLETE` (`STAGE_23_TERRAIN_AWARE_GPU_AND_INCREMENTAL_COMPLETE`)
- API Version `2.1.0-gpu-terrain` implemented with CUDA C++ `terrain_shadow_kernel`.
- Achieves exact bit-match shadow parity with CPU terrain solver.

### 1.9 Terrain-Aware GPU Incremental Status (`Stage 23`)
- **Status:** `VALIDATED`
- Reuses resident GPU arrays for cells outside dirty mask, achieving 93.8% cell reuse with zero numerical deviation from full solve.

### 1.10 CPU/GPU Parity Results
- Flat-ground CPU vs GPU: Exact bit match for shadow (0.000000 error); $T_{mrt}$ error $5.68 \times 10^{-14}\,\text{K}$.
- Synthetic Incline CPU vs GPU: Exact bit match for shadow (0.000000 error); $T_{mrt}$ error $0.000000\,\text{K}$.

### 1.11 Flat-Ground Backward Compatibility
- When terrain is disabled (`terrain=None`), `2.1.0-cpu-terrain` and `2.1.0-gpu-terrain` execute an exact bypass delegating to `2.0.0-cpu-ref`, preserving **100% exact bit-level backward compatibility**.

### 1.12 Mathematical Certificates
- 9 CPU Terrain Certificates audited and passed (`CERT_01` through `CERT_09`).
- 5 GPU Terrain Certificates audited and passed (`CERT_GPU_01` through `CERT_GPU_05`).

### 1.13 Runtime and Memory Profiling
- CPU Terrain Solve: $\approx 0.08\,\text{s}$ (single-box) / $\approx 5.8\,\text{s}$ (Church Street scale).
- GPU Terrain Kernel: $\approx 0.015\,\text{s}$ (full solve) / $\approx 0.003\,\text{s}$ (incremental).
- GPU Memory Footprint: Peak VRAM $\le 128.0\,\text{MB}$ for synthetic scenes.

### 1.14 Protected-File Audit
- 14 historical benchmark files verified via SHA-256 in `results/stages_17_to_23_protection_audit.json`: **100% INTACT AND UNMODIFIED**.

### 1.15 Human Decisions Still Required
- Formal execution of `results/stage_19_researcher_approval/researcher_approval_form.md` by an authorized researcher.

### 1.16 Explicit Limitations
- Real Church Street simulations currently assume flat grade.
- Complex terrain and vegetation canopy physics are not yet certified for real-world municipal planning claims.

### 1.17 Whether Real-World Terrain Claims Are Allowed
- **NO.** Real-world terrain claims are strictly **BLOCKED** pending acquisition of an engineering-grade street DTM.

### 1.18 Whether Tree-Aware Integration Remains Blocked
- **YES.** Tree-aware solver integration remains strictly **BLOCKED** pending human researcher authorization and on-site field survey ground truth.

---

## 2. Status Tokens

```text
STAGE_17_COMPLETE
STAGE_17_PUBLICATION_REVIEW_AND_ARCHIVAL_RELEASE_COMPLETE

STAGE_18_COMPLETE
STAGE_18_CLEAN_ENVIRONMENT_REPRODUCIBILITY_COMPLETE

STAGE_19_HUMAN_APPROVAL_PENDING

STAGE_20_SYNTHETIC_TERRAIN_ONLY

STAGE_21_FIELD_VALIDATION_PENDING

STAGE_22_COMPLETE
STAGE_22_TERRAIN_AWARE_CPU_REFERENCE_COMPLETE

STAGE_23_COMPLETE
STAGE_23_TERRAIN_AWARE_GPU_AND_INCREMENTAL_COMPLETE
```

---

## 3. Final Stop Condition

As mandated by project instructions:
**After Stage 23, execution is stopped.** No tree/canopy integration, Level 1 tree geometry, canopy radiative parameters, or terrain/tree reoptimization has been initiated.
