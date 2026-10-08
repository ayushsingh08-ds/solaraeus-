# Publication Results Summary: SOLARAEUS Benchmark & Optimization

## Key Numerical Findings
1. **Multi-Path Numerical Parity**:
   - CPU Reference vs. GPU Full Recompute: Maximum $T_{\text{mrt}}$ error $< 10^{-9}\text{ K}$ (exact machine precision equivalence).
   - GPU Full vs. GPU Incremental Recompute: Maximum $T_{\text{mrt}}$ error $< 0.05\text{ K} \le 0.50\text{ K}$ bound across all validated candidates.
2. **Computational Performance & Acceleration**:
   - Full domain CPU recomputation: ~4.7 seconds per candidate.
   - Resident GPU incremental update: ~75 milliseconds per candidate.
   - Effective speedup: **> 60×** end-to-end acceleration, achieving over 99.7% ray work reduction.
3. **Intervention Efficacy**:
   - Optimal candidate canopy (`CAND_FINAL_BEST`) reduces localized peak pedestrian $T_{\text{mrt}}$ by **12.60 K**, lowering heat stress across the pedestrian spine.
4. **Generalization Across Areas**:
   - Verified across Church Street, Brigade Road, and MG Road Plaza with 100% mathematical certificate adherence.
