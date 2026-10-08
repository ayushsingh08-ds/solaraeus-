# Final Candidate Validation and Physical Uncertainty Report (Stage 15)

## Executive Summary
This report documents the exhaustive four-path numerical validation and physical uncertainty analysis
conducted for the optimal shade panel interventions on Church Street, Bengaluru.

### Validated Candidate Set
- **Selected Optimal Candidate (`CAND_FINAL_BEST`)**: Local Cartesian center `(155.0, 55.0) m`, Length `4.41 m`, Width `3.08 m`, Underside Clearance `3.46 m`, Heading `103.28°`, Albedo `0.46`.
- **Canonical Benchmark Candidate (`CAND_CANONICAL`)**: Baseline Church Street shade canopy `BLR_SHADE_001` `(131.79, 64.01) m`, Dimensions `6.00 × 3.00 m`, Clearance `3.50 m`.
- **Top Alternative Candidate (`CAND_ALT_LHS`)**: LHS top-ranked proposal `(153.48, 57.46) m`, Dimensions `4.15 × 3.83 m`.

## Numerical Solver Parity (Exact 4-Path Comparison)
| Comparison Pair | Target Tolerance | Measured Maximum Error | Status |
| :--- | :--- | :--- | :--- |
| **CPU Full vs GPU Full** | Machine Precision ($10^{-9}$ K) | `1.14e-13 K` | **PASS (Exact Equivalence)** |
| **GPU Full vs GPU Incremental** | Certified Bound ($0.50$ K) | `0.0187 K` | **PASS (Within Bound)** |
| **CPU Full vs GPU Incremental** | Certified Bound ($0.50$ K) | `0.0187 K` | **PASS (Within Bound)** |

## Uncertainty & Ranking Stability Analysis
- **Monte Carlo Perturbations**: 20 randomized geometric, positional, and solar forcing perturbations.
- **95% Confidence Interval for Optimal Objective**: `[53.4955, 55.8792]`.
- **Empirical Ranking Stability**: `35.0%`.
- **Authoritative Presentation Status**: `NON_DEFINITIVE_OVERLAPPING_CI`.
- **Scientific Policy**: Because physical and atmospheric perturbations cause overlapping 95% confidence intervals between top designs, candidate ranking is explicitly **NOT presented as definitive**, but rather as an ensemble cluster of high-performing interventions.
