# SOLARAEUS Final Reproducibility Guide

---

## 1. Software Environment
- Operating System: Windows 11 x64
- Python Version: 3.12.6
- Core Dependencies: NumPy 1.26+, SciPy 1.13+, CuPy 13.0+, Pytest 8.0+
- GPU Acceleration: NVIDIA CUDA 12.x compatible GPU

## 2. Deterministic Execution
All simulation and optimization runs utilize fixed deterministic random seeds:
- Optimization Seed: `42`
- Latin Hypercube Seed: `1234`
- Spatial sampling resolution: `1.0m` regular orthogonal grid

## 3. Test Suite Invocations
To verify the entire project test suite:
```bash
python -m pytest -o pythonpath=src
```
