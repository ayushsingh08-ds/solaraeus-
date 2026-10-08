# Research Methodology: High-Throughput Certified Microclimate Optimization

## 1. Research Question
How can high-resolution urban microclimate simulations (mean radiant temperature $T_{\text{mrt}}$ and Universal Thermal Climate Index $\text{UTCI}$) be accelerated by orders of magnitude while providing strict mathematical error bounds for AI-driven shade canopy intervention optimization?

## 2. Solver Architecture
SOLARAEUS implements a dual-architecture solver:
1. **Authoritative CPU Reference**: Fully vectorized NumPy implementation following the standard SOLWEIG microclimate radiative balance equations, operating as the ground-truth numerical authority.
2. **High-Throughput GPU Backend**: CuPy-based parallel ray-casting and view-factor kernels executing on NVIDIA RTX tensor/CUDA hardware, delivering bit-identical direct shadows and machine-precision radiant flux fields.

## 3. Certified Incremental Recomputation
Rather than executing full domain recomputations for localized urban modifications (such as overhead shade panels), SOLARAEUS computes a conservative **candidate affected region** $\mathcal{A}_{\text{cand}}$:
$$\mathcal{A}_{\text{cand}} = \Omega_{\text{shadow}}(\Delta \mathcal{M}) \cup \Omega_{\text{svf}}(\Delta \mathcal{M}, R_{\text{max}})$$
Reusing physical quantities outside $\mathcal{A}_{\text{cand}}$ introduces an error bound $B_T(x) \le 0.50\text{ K}$, mathematically certified before field updates.

## 4. Feasibility Screening & Constrained Optimization
Intervention proposals are screened against geographic polygons, building setbacks ($\ge 0.50\text{ m}$), pedestrian underside clearance ($\ge 2.50\text{ m}$), and structural aspect ratios prior to simulation. Optimization is performed using Latin-Hypercube Sampling and Differential Evolution.
