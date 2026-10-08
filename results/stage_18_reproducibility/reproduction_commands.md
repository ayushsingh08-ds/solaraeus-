# Reproduction Commands Guide

This document records the exact command sequences and environment variables used to reproduce all Stage 1–16 outputs in an isolated, clean environment.

## 1. Environment Configuration
```bash
set PYTHONHASHSEED=42
set CUPY_SEED=42
```

## 2. Execution Sequences
```bash
# 1. Validate Core Pytest Suite
python -m pytest -o pythonpath=src

# 2. Reproduce Static Baseline & Shade Panel Solves
python scripts/execute_stage_05_shade_panel_full.py
python scripts/execute_stage_06_shade_panel_incremental.py

# 3. Reproduce GPU Validations
python scripts/execute_stage_10_gpu_full_vs_cpu.py
python scripts/execute_stage_11_gpu_incremental.py
python scripts/execute_stage_12_gpu_profiling.py

# 4. Reproduce Feasibility & Optimization
python scripts/execute_stage_13_geographic_feasibility.py
python scripts/execute_stage_14_constrained_optimizer.py
python scripts/execute_stage_15_final_validation.py

# 5. Reproduce Cross-Area Package
python scripts/execute_stage_16_additional_areas_and_publication.py
```
