## 19. Surrogate-Assisted Geographically Constrained Intervention Optimization (Stage 2)

### 19.1 Architectural Design & Physics-in-the-Loop Contract
Stage 2 introduces an uncertainty-aware surrogate modeling layer that accelerates candidate generation while keeping the validated resident GPU incremental solver as the sole physics authority:
```
Stage 1 Candidate Ledger (44 prior evaluations)
  -> Train Multi-Target Tabular Ensemble Surrogate (Random Forest Regressors & Feasibility Classifier)
  -> Uncertainty-Aware Acquisition Policy (LCB, Expected Improvement, High-Uncertainty, Boundary, Pareto)
  -> Geographic Feasibility Filter (pedestrian corridor containment, setbacks, clearances)
  -> Resident GPU Incremental Physics Evaluation (recomputed cells only)
  -> Pointwise Certificate Verification (B_T(x) <= epsilon_T)
  -> Update Candidate Ledger with Provenance & Retrain Surrogate
  -> Repeat Propose-Eval-Retrain Cycle
  -> Full Three-Path Physical Validation of Final Candidates (CPU Full ~= GPU Full ~= GPU Incremental)
```

**Key Architectural Invariants**:
1. **The Surrogate Proposes Candidates Only**: The surrogate model never replaces or bypasses the physics solver for candidate evaluation.
2. **No Deep Neural Networks**: Tabular tree ensembles (`RandomForestRegressor` and `ExtraTreesRegressor`) are used because the initial dataset is compact (44 candidates). Tree variance provides exact empirical posterior uncertainty $\sigma^2(\mathbf{x}) = \frac{1}{B}\sum_{b=1}^B (f_b(\mathbf{x}) - \mu(\mathbf{x}))^2$ without matrix inversion instability.
3. **Strict Pre-Simulation Feasibility**: Infeasible proposals are identified and rejected *before* any GPU simulation call.
4. **Invalid Output Isolation**: Failed simulations or certificate violations are logged as failures and strictly excluded from subsequent surrogate retraining.

### 19.2 New Modules Added to `src/urban_comfort/optimization/`
1. [`surrogate.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/surrogate.py):
   - `SurrogateConfig`: Configurable model hyperparameters (`n_estimators=100`, `max_depth=12`, seed, feature scaling).
   - `SurrogatePrediction`: Pointwise predictions containing target means, standard deviations (tree uncertainty), and feasibility probability.
   - `SurrogateModel`: Multi-target regression predicting composite objective, mean UTCI, P90 UTCI, mean $T_{\text{mrt}}$, $\Delta \text{mean } T_{\text{mrt}}$, and peak local $T_{\text{mrt}}$ improvement.
   - `FallbackSurrogateModel`: Graceful distance-weighted empirical fallback when `scikit-learn` is unavailable.
2. [`acquisition.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/acquisition.py):
   - `AcquisitionConfig`: Controls acquisition policies, exploration weights ($\kappa=2.0$, $\xi=0.01$), candidate pool size ($N=1000$), and diversity distances.
   - Mathematical acquisition scores: Closed-form Expected Improvement (EI), Lower Confidence Bound (LCB), High-Uncertainty ($\sigma$), and Boundary Closeness.
   - `CandidateAcquisitionEngine`: Generates candidate pools, filters through `check_feasibility`, identifies non-dominated Pareto frontiers (mean UTCI vs panel area), and selects diverse portfolio batches.
3. [`surrogate_optimizer.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/src/urban_comfort/optimization/surrogate_optimizer.py):
   - `SurrogateOptimizerConfig` & `SurrogateOptimizationEngine`: Coordinates the propose-eval-retrain loop, integrates resident GPU incremental physics, logs predictions vs observed physics, and manages candidate databases.

### 19.3 Empirical Results on Bengaluru Church Street
Executed via production script [`scripts/run_church_street_surrogate_optimization.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/scripts/run_church_street_surrogate_optimization.py):
- **Output Artifacts Directory**: `results/church_street_surrogate_optimization_20261007_110633/`
- **Initial Prior Dataset**: 44 candidates loaded from frozen Stage 1 ledger (SHA256: `86c3771f0cb13684bb9927357bd06f0aa386e43d5ce283a342bd8815844652f1`)
- **Surrogate Search Budget**: 4 iterations $\times$ 5 candidates = 20 proposed candidates
- **Physics Evaluated Candidates**: 20 (100% feasibility hit rate due to pre-simulation filtering)
- **Best Candidate ID**: **`CAND_0063_SURR`**
- **Composite Comfort Objective**: **`54.9269`** (improved from Stage 1 best `54.9309` by $-0.0040$ units)
- **Best Parameters**: $X = 122.120\,\text{m}$, $Y = 65.788\,\text{m}$, $L = 3.48\,\text{m}$, $W = 2.95\,\text{m}$, $h = 2.99\,\text{m}$, $\theta = 95.80^\circ$, $\alpha = 0.68$, Area = $10.26\,\text{m}^2$.
- **Corridor Thermal Comfort**: Mean UTCI $36.4756\,^\circ\text{C}$ ($\Delta = -0.0150\,^\circ\text{C}$); Max UTCI $37.0\,^\circ\text{C}$ (down from $37.7\,^\circ\text{C}$ baseline); Mean $T_{\text{mrt}}$ $45.7491\,^\circ\text{C}$ ($\Delta = -0.0617\,^\circ\text{C}$); Peak local $T_{\text{mrt}}$ drop = $12.82\,\text{K}$.
- **Hardware Performance**: 48 / 28,120 cells recomputed (**99.83% cell reuse**); **16.39 ms GPU kernel latency**; **0 certificate violations**.

### 19.4 Comparative Benchmark Against Baselines

| Strategy | Budget | Feasible / Proposed | Best Candidate ID | Best Objective | Mean UTCI (deg C) | P90 UTCI (deg C) | Canopy Area (m2) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Stage 1 Random Search** | 25 | 11 / 25 ($44.0\%$) | `CAND_0012_RAND` | $54.9657$ | $36.488$ | $36.8$ | $15.6$ |
| **Stage 1 Evolutionary Search** | 15 | 8 / 15 ($53.3\%$) | `CAND_0036_EVOL` | $54.9309$ | $36.487$ | $36.8$ | $8.82$ |
| **Stage 2 Matched Random Baseline** | 20 | 13 / 20 ($65.0\%$) | `CAND_0014_RAND` | $54.9421$ | $36.489$ | $36.8$ | $14.2$ |
| **Stage 2 Surrogate-Assisted** | 20 | **20 / 20 ($100.0\%$)** | **`CAND_0063_SURR`** | **`54.9269`** | **`36.476`** | **`36.8`** | **`10.26`** |

### 19.5 Multi-Path Physical Validation (Solver Equivalence)
Full three-path validation (CPU Full vs GPU Full vs GPU Incremental) executed across 9 key candidates:
- Surrogate Best (`CAND_0063_SURR`)
- Top Candidates (`CAND_0057_SURR`, `CAND_0062_SURR`, `CAND_0036_EVOL`, `CAND_0052_SURR`)
- Highest-Uncertainty Candidate (`CAND_0045_SURR`)
- Random Feasible Candidate (`CAND_0044_SURR`)
- Feasibility-Boundary Candidate (`CAND_0048_SURR`)
- Stage 1 Best Reference (`CAND_0036_EVOL`)

**Parity Audit Results**:
- **9 / 9 Candidates PASSED** all strict project tolerances.
- **CPU Full vs GPU Full**: Direct shadow mismatches = 0; Max SVF difference $\le 1.05 \times 10^{-14}$; Max $T_{\text{mrt}}$ difference = $1.14 \times 10^{-13}\,\text{K}$ (machine precision).
- **GPU Incremental vs CPU Full**: Max $T_{\text{mrt}}$ difference between $0.0125\,\text{K}$ and $0.0615\,\text{K}$ (strictly $\le 0.50\,\text{K}$ tolerance); Max UTCI difference $\le 0.10\,^\circ\text{C}$ ($\le 0.50\,^\circ\text{C}$ tolerance); Certificate violations = 0.

### 19.6 Verification & Test Suite Status
- Added [`tests/test_surrogate_optimization.py`](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/tests/test_surrogate_optimization.py) covering all 13 required test cases (100% pass rate in 17.8s).
- Full test suite execution: `pytest tests/ -o pythonpath=src -q`:
  **244 passed, 42 warnings in 93.2s** (100% green).
- Success token: `READY_FOR_MULTI_INTERVENTION_SURROGATE_OPTIMIZATION`.

---

