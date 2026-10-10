## 20. Multi-Intervention Surrogate-Assisted Optimization (Stage 3)

### 20.1 Architectural Design & Mathematical Formulation
Stage 3 extends the single-panel optimization framework to simultaneous multi-intervention optimization of **exactly two overhead shade panels** ($2 \times 7 = 14$ parameters) under combined spatial, structural, and pedestrian constraints.

```
Two-Panel Parameter Vector (14D)
  -> Canonical Permutation-Invariance Sorting (x1 <= x2)
  -> Watertight 3D Mesh Generation (2 x 8 vertices, 2 x 12 triangles)
  -> Pairwise & Urban Geographic Feasibility Filter
  -> Combined Scene Edit (AddMultiMeshEdit)
  -> Exact Shadow Footprint Union & Overlap Calculation
  -> Certified GPU Incremental Multi-Mesh Simulation
  -> Error Certificate Verification (B_T(x) <= epsilon_T)
  -> Multi-Objective Comfort, Spatial Area & Construction Cost Evaluation
  -> Immutable Candidate Ledger Persistence (JSON & CSV)
  -> Periodic Tabular Surrogate Retraining (Ensemble Trees)
  -> Uncertainty-Aware Acquisition (Predicted-Best, LCB, High-Uncertainty, Boundary, Pareto)
```

**14-Parameter Parameterization**:
- Panel 1: $(x_1, y_1, L_1, W_1, h_1, \theta_1, \alpha_1)$
- Panel 2: $(x_2, y_2, L_2, W_2, h_2, \theta_2, \alpha_2)$

**Geographic, Pairwise & Construction Constraints**:
1. **Pedestrian Corridor Containment**: Each panel must remain strictly within the allowable Church Street pedestrian boundary polygon.
2. **Building Setbacks**: Minimum distance to all building walls $d_{\text{bldg}} \ge 0.50\,\text{m}$.
3. **Pedestrian Underside Clearance**: $2.50\,\text{m} \le h \le 5.50\,\text{m}$.
4. **Collision Avoidance**: $\text{Poly}_1 \cap \text{Poly}_2 = \emptyset$ (no overlapping or intersecting panels).
5. **Minimum Panel Separation**: Minimum mutual Euclidean distance $d(P_1, P_2) \ge 2.00\,\text{m}$.
6. **Total & Individual Canopy Area**: $A_1 \le 40\,\text{m}^2$, $A_2 \le 40\,\text{m}^2$, $10\,\text{m}^2 \le A_{\text{total}} \le 60\,\text{m}^2$.
7. **Aspect Ratio**: $1.0 \le \max(L, W)/\min(L, W) \le 5.0$.
8. **Machine-Readable Rejection Categories**: `VALID`, `INVALID_COORDINATES`, `OUT_OF_BOUNDS`, `BUILDING_COLLISION`, `INSUFFICIENT_CLEARANCE`, `EXCEEDS_MAX_DIMENSIONS`, `BELOW_MIN_DIMENSIONS`, `PANEL_COLLISION`, `INSUFFICIENT_PANEL_SEPARATION`, `EXCEEDS_TOTAL_AREA`, `BELOW_MIN_TOTAL_AREA`.

**Composite Scalar Objective**:
$$\min f(\mathbf{x}) = \text{mean\_UTCI} + 0.5 \cdot \text{P90\_UTCI} + \text{area\_penalty} + \text{construction\_cost\_penalty} + \text{obstruction\_penalty}$$
where:
- $\text{area\_penalty} = 0.005 \cdot (A_1 + A_2)$
- $\text{construction\_cost} = 2 \cdot \$5000 + (A_1 + A_2) \cdot \$250/\text{m}^2$
- $\text{cost\_penalty} = 0.0001 \cdot \text{construction\_cost}$

### 20.2 Key Modules Implemented in `src/urban_comfort/`
1. [`incremental/mesh_update.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/mesh_update.py):
   - Added `AddMultiMeshEdit(GeometricEdit)` applying multiple meshes simultaneously and returning exact combined 3D bounds.
2. [`incremental/affected_region.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/incremental/affected_region.py):
   - Added exact boolean union calculation $\text{mask}_{\text{union}} = \text{mask}_1 \cup \text{mask}_2$ for multiple dynamic meshes without duplicate cell evaluation.
3. [`optimization/two_panel_parameters.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_parameters.py):
   - `TwoPanelParams`, `TwoPanelBounds`, canonical permutation sorting ($x_1 \le x_2$), vector conversions, LHS and uniform sampling.
4. [`optimization/two_panel_feasibility.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_feasibility.py):
   - `TwoPanelConstraints`, `check_two_panel_feasibility`, comprehensive geometric & setback validation.
5. [`optimization/two_panel_objective.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_objective.py):
   - Multi-objective scoring, construction cost model, non-dominated Pareto front extraction.
6. [`optimization/two_panel_ledger.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_ledger.py):
   - `TwoPanelCandidateRecord`, `TwoPanelCandidateLedger` (JSON/CSV serialization, union and overlap spatial metrics).
7. [`optimization/two_panel_surrogate.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_surrogate.py):
   - 20-dimensional tabular Random Forest ensemble regression and feasibility classification with uncertainty estimation.
8. [`optimization/two_panel_acquisition.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_acquisition.py):
   - Seed generation (duplicated Stage 2 best, Stage 1/2 pairs, LHS pairs) + uncertainty-aware portfolio acquisition.
9. [`optimization/two_panel_optimizer.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_optimizer.py):
   - Propose-eval-retrain loop with resident GPU incremental multi-mesh simulation.
10. [`optimization/two_panel_validation.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/two_panel_validation.py):
    - Multi-path parity audits (CPU Full vs GPU Full vs GPU Incremental) for dual-panel configurations.

### 20.3 Empirical Results on Bengaluru Church Street
Executed via production runner [`scripts/run_church_street_two_panel_optimization.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/run_church_street_two_panel_optimization.py):
- **Output Artifacts Directory**: `results/church_street_multi_intervention_optimization_20261007_114326/`
- **Total Proposals Screened/Logged**: 4,201
- **Geographically Feasible Candidates**: 25 (Seed portfolio: 10, Surrogate iterations: 3 × 5 = 15)
- **Best Two-Panel Candidate ID**: **`CAND_4196_SURR`**
- **Composite Comfort Objective**: **`56.5658`**
- **Panel 1 Parameters**: $X = 124.016\,\text{m}$, $Y = 59.628\,\text{m}$, $L = 6.76\,\text{m}$, $W = 2.07\,\text{m}$, $h = 3.79\,\text{m}$, $\theta = 113.83^\circ$, $\alpha = 0.56$, $A_1 = 14.01\,\text{m}^2$
- **Panel 2 Parameters**: $X = 151.939\,\text{m}$, $Y = 59.040\,\text{m}$, $L = 3.85\,\text{m}$, $W = 2.30\,\text{m}$, $h = 4.16\,\text{m}$, $\theta = 93.68^\circ$, $\alpha = 0.47$, $A_2 = 8.86\,\text{m}^2$
- **Total Combined Canopy Area**: **`22.87 m²`**
- **Mutual Panel Separation**: **`27.93 m`** (well above minimum 2.0 m limit)
- **Estimated Construction Cost**: **`$15,718.22`**
- **Corridor Thermal Comfort**:
  - Corridor Mean UTCI: **`36.48 °C`** ($\Delta = -0.011\,^\circ\text{C}$)
  - Corridor P90 UTCI: **`36.80 °C`**
  - Mean $T_{\text{mrt}}$: **`45.76 °C`** ($\Delta = -0.050\,^\circ\text{C}$)
  - Peak Local $T_{\text{mrt}}$ Drop: **`12.68 K`**
- **Hardware Telemetry**: Recomputed 438 / 28,120 cells (**>98.4% cell reuse**); **0 certificate violations**.

### 20.4 Comparison with Single-Panel and Random Baselines

| Strategy | Intervention Count | Total Area (m2) | Best Candidate ID | Best Objective | Peak Local ΔTmrt (K) | Cost ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 Single Evolutionary** | 1 | 8.82 | `CAND_0036_EVOL` | 54.9309 | 14.12 | $7,205 |
| **Stage 2 Single Surrogate** | 1 | 10.26 | `CAND_0063_SURR` | 54.9269 | 12.82 | $7,565 |
| **Stage 3 Two-Panel Random Search** | 2 | 26.54 | `CAND_0039_RAND` | 56.5757 | 10.95 | $16,635 |
| **Stage 3 Two-Panel Surrogate** | 2 | **22.87** | **`CAND_4196_SURR`** | **56.5658** | **12.68** | **$15,718** |

*Note: Two-panel objective includes $2 \times \$5,000$ base construction cost penalty and higher area penalty, reflecting true multi-structure capital budgeting.*

### 20.5 Multi-Path Physical Solver Parity Verification
All 10 audited candidates (top 5, best random, highest uncertainty, boundary candidates, and Stage 2 single-panel baseline) PASSED all strict tolerances:
- **CPU Full vs GPU Full**: Direct shadow mismatches = 0; Max SVF difference $\le 10^{-14}$; Max $T_{\text{mrt}}$ difference $\le 10^{-13}\,\text{K}$ (exact solver equivalence).
- **GPU Incremental vs GPU Full**:
  - `CAND_4196_SURR` (Best): $\max |\Delta T_{\text{mrt}}| = 0.008147\,\text{K} \le 0.50\,\text{K}$
  - `CAND_0039_RAND` (Top 2): $\max |\Delta T_{\text{mrt}}| = 0.014312\,\text{K} \le 0.50\,\text{K}$
  - `CAND_2826_SURR` (Top 3): $\max |\Delta T_{\text{mrt}}| = 0.014451\,\text{K} \le 0.50\,\text{K}$
  - `CAND_2825_SURR` (Highest Uncertainty): $\max |\Delta T_{\text{mrt}}| = 0.032306\,\text{K} \le 0.50\,\text{K}$
  - `CAND_4199_SURR` (Separation Boundary): $\max |\Delta T_{\text{mrt}}| = 0.014991\,\text{K} \le 0.50\,\text{K}$
  - `CAND_0063_SURR` (Stage 2 Single Baseline): $\max |\Delta T_{\text{mrt}}| = 0.012534\,\text{K} \le 0.50\,\text{K}$
- **Certificate Violations**: **0 across all 10 candidates**.

### 20.6 Verification & Test Suite Status
- Added [`tests/test_two_panel_optimization.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_two_panel_optimization.py) covering all 19 required test cases.
- Full regression suite execution: `pytest tests/ -o pythonpath=src -q`:
  **263 passed, 42 warnings in 103.2s** (100% green; 0 failures).
- Success token: `READY_FOR_MULTI_PANEL_INTERVENTION_TYPE_OPTIMIZATION`.

---

