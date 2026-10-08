# Data and Code Availability Statement

---

## 1. Source Code
The complete source code of SOLARAEUS is organized under `src/urban_comfort/`:
- `geometry/`: Primitives, building representations, and pedestrian grid abstractions.
- `solar/`: Deterministic astronomical solar position calculator.
- `visibility/`: Shadow masking and directional sky view factor ray tracers.
- `radiation/`: Shortwave, longwave, and mean radiant temperature calculators.
- `comfort/`: Universal Thermal Climate Index (UTCI) polynomial solver.
- `backend/`: NVIDIA GPU CUDA kernel backends.
- `incremental/`: Affected-region caching and resident incremental solvers.
- `terrain/`: Digital terrain model representations and spatial solvers.
- `vegetation/`: Level 1 analytical tree geometry and canopy sensitivity solvers.

## 2. Artifacts and Results
All generated simulation outputs, benchmarks, manifests, and certificates are versioned in `results/`.
