## 1. Project Objective & Core Mathematical Guarantee

The primary mission of this project is to develop an experimental, CPU-based research prototype capable of **provably safe, error-bounded incremental updates** for urban thermal-comfort calculations under local 3D building edits (such as additions, removals, height adjustments, translations, and multi-building edits).

The engine derives, tests, and verifies the fundamental mathematical certificate guarantee:

$$|\widetilde{T}_{\mathrm{mrt}}(x) - T_{\mathrm{mrt}}^{\mathrm{full}}(x)| \leq B_T(x) \leq \varepsilon_T$$

where:
- $\widetilde{T}_{\mathrm{mrt}}(x)$: Mean Radiant Temperature computed via selective incremental reuse.
- $T_{\mathrm{mrt}}^{\mathrm{full}}(x)$: Mean Radiant Temperature from ground-truth full-domain recomputation.
- $B_T(x)$: A closed-form, computable upper bound evaluated in $O(1)$ operations per grid cell *prior* to recomputation.
- $\varepsilon_T$: The user-specified error tolerance (in Kelvin).

---

