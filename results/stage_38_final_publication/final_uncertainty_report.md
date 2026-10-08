# SOLARAEUS Comprehensive Uncertainty and Error Budget Report

---

## 1. Uncertainty Budget Summary
| Error Source | Category | Magnitude ($T_{mrt}$) | Governance Classification |
|---|---|---|---|
| Tree Geometry Bounds (Small/Large) | Geometric Uncertainty | $\pm 1.45\text{ K}$ | `PROVISIONAL_PHOTO_ESTIMATED` |
| Canopy Attenuation ($\tau \in [0.00, 0.50]$) | Optical Uncertainty | $\pm 0.95\text{ K}$ | `LITERATURE_ASSUMED` |
| Street Elevation Profile (Synthetic vs DTM) | Topographic Uncertainty | $\pm 0.38\text{ K}$ | `SYNTHETIC_TERRAIN_ONLY` |
| Meteorological Boundary (DNI $\pm 10\%$) | Boundary Condition | $\pm 0.85\text{ K}$ | `MEASURED_METAR` |
| Numerical Solver Discrepancy (CPU vs GPU) | Algorithmic Error | $< 10^{-4}\text{ K}$ | `CERTIFIED_NUMERICAL` |
| **Combined Standard Uncertainty ($u_c$)** | **Root-Sum-Square** | **$\pm 1.95\text{ K}$** | **`NON_AUTHORITATIVE_ENVELOPE`** |

## 2. Non-Definitive Ranking Principle
Because the performance margin between top candidate configurations ($0.65\text{ K}$) is smaller than the combined parameter uncertainty ($1.95\text{ K}$), the optimizer rankings cannot be declared definitive in the real physical world without empirical calibration.
