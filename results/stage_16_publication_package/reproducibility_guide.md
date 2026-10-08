# Reproducibility Guide

## Software and Hardware Requirements
- **OS**: Windows 11 / Linux x86_64
- **Python**: 3.12+
- **CUDA**: 12.8 / Driver 572+
- **GPU**: NVIDIA RTX (Compute Capability >= 8.6, >= 4 GB VRAM)
- **Key Libraries**: CuPy 14.2.0, NumPy, Shapely, PyProj, Matplotlib, Pytest

## Reproduction Steps
```bash
# 1. Run Complete Test Suite
python -m pytest -o pythonpath=src

# 2. Execute Stage 10 GPU Validation
python scripts/execute_stage_10_gpu_full_vs_cpu.py

# 3. Execute Stage 14 AI Optimizer
python scripts/execute_stage_14_constrained_optimizer.py

# 4. Execute Stage 15 Multi-Path Candidate Validation
python scripts/execute_stage_15_final_validation.py
```
All random seeds are strictly locked to `42`.
