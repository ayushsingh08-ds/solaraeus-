# SOLARAEUS Project Final Results Summary

**Document ID**: `SOLARAEUS-FINAL-RESULTS`  
**Execution Timestamp**: 2026-10-08  

---

## 1. Validated Computational Capabilities
1. **Flat-Ground CPU Reference Solver**: Bit-exact baseline verified across hundreds of unit and adversarial tests.
2. **GPU Full and Incremental Solvers**: Verified $100\%$ direct-shadow bit equivalence and $< 10^{-4}\text{ K}$ thermal convergence against CPU.
3. **Synthetic Terrain Physics**: Exact flat-ground bypass parity ($0.000000\text{ K}$ error), slope ray adjustment, and stepped-terrace clearance verification.
4. **Provisional Tree Geometry Engine**: Deterministic cylinder-ellipsoid ray intersection in CPU C++ and CUDA.
5. **Incremental Recomputation Mechanics**: $50\% - 85\%$ computational reuse with strict conservative shadow cone bounds.
6. **Constrained Intervention Optimization**: Verified multi-panel genetic, surrogate, and baseline searches under urban constraints.

---

## 2. Key Microclimate Metrics Summary
- **Baseline Pedestrian Thermal Stress (Church Street No-Intervention)**: Mean $T_{mrt} = 48.72^\circ\text{C}$, Mean $\text{UTCI} = 37.15^\circ\text{C}$ (Very Strong Heat Stress).
- **Stage 14 Optimized Shade Panel (`CAND_0028_EVOL`)**: Direct localized cooling $\Delta T_{mrt} = 12.60\text{ K}$.
- **Core Provisional Trees (T08–T13 Nominal)**: Canopy shade cooling $\Delta T_{mrt} = 2.45\text{ K}$ domain-averaged.
- **Combined Panels + Nominal Trees**: Total cooling $\Delta T_{mrt} = 3.65\text{ K}$ domain-averaged.
