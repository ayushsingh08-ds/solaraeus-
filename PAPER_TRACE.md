# PAPER_TRACE.md — Paper (`research_paper_sol/solaraeus.tex`) ↔ Code ↔ Artifact

STEP-1 read-only trace. **Rule: report only; never change a paper number or code to make them agree.**
There is no PDF in the repo; `research_paper_sol/solaraeus.tex` (578 lines) is authoritative.

**Verdict legend**
- `MATCH` — paper value is reproduced by a code default and/or a recorded run artifact.
- `MISMATCH` — paper value contradicts the code/artifact (both shown; nothing changed).
- `HARDCODED` — the number is a baked-in literal in a figure/report generator, not computed at generation time (may still coincide with a measured artifact — noted).
- `CONDITIONAL` — holds only under a runtime condition (e.g. an optional dependency installed).
- `NEEDS-VERIFY` — traces partially; exact artifact/domain not yet pinned.

Code paths are repo-relative under `src/`. Artifact paths are under `results/`.

## 1. Site & inputs (Table I, .tex L124–156)

| Paper claim (.tex) | Code location | Artifact | Verdict |
|---|---|---|---|
| CRS UTM 43N EPSG:32643 | integration/coordinates.py (pyproj UTM43N) | preprocessing scene_summary.json | MATCH |
| Grid convergence γ=+0.5854° (L116,136) | coordinates.py:31 `grid_convergence_deg=0.585366` | — | MATCH |
| Origin X=782541.81 E, Y=1435736.11 N (L116) | coordinates.py:29-30 (782541.8055, 1435736.1103) | — | MATCH |
| Site 12.9749°N, 77.6054°E (L107) | solar/sun_model.py (Bengaluru 12.9749/77.6054) | — | MATCH — note config.py default is NYC 40.7128/-74.0060; site coords live in sun_model/adapter |
| Domain 380×296 m; grid 2.0 m; N_grid=28,120 (190×148, L112) | geometry/scene.py (res default 1.0; run uses 2.0) | scene_summary.json `total_cells=28120`; quality_checks.json 28120 | MATCH (28,120 confirmed) |
| 123 buildings = 37 core + 86 context (L119) | preprocessing/church_street_adapter.py (expected 37 core / 123) | scene_summary.json | MATCH (37 core + 123 total; context=86) — core/context split to reconfirm |
| 2,136 triangles | geometry/mesh.py + backend flatten | gpu_benchmark_trials.csv `triangles_tested=2148` | MISMATCH (2,136 vs 2,148) |
| α_s=57.9160°, φ_grid=267.5802° | solar/solar_position.py (runtime) | provenance.json | NEEDS-VERIFY (runtime solar; exact value to pin) |
| T_a=35.0°C, RH=19.73%, GHI 755.97 / DNI 728.31 / DHI 172.18 W/m² | config.Weather (run-supplied) | robustness.py:162 descriptor "728.3 W/m² DNI" | MATCH (DNI confirmed; others run-supplied) |
| v=1.1 m/s (L~119) | config.Weather | robustness.py:162 descriptor "1.5 m/s" | NEEDS-VERIFY (paper 1.1; robustness scenario 1.5) |
| α_bldg=0.20, α_gnd=0.15, ε_bldg=0.90 (L122) | config.py:89-103 WALL(0.20/0.90), GROUND(0.15/0.95) | — | MATCH (code ε_gnd=0.95) |
| 14 BBMP trees, Level-1 (L156) | tree_loader.py:104-171 / vegetation/tree.py:134-183 / tmrt_3d.py:115-122 = **6 trees T08–T13** | tree manifest `tree_count=6` | **MISMATCH (14 vs 6)** — docstring cites T01–T07,T14 but none are instantiated |
## 2. Physics (Eqs. 1–4, .tex L173–200)

| Paper claim | Code location | Verdict |
|---|---|---|
| Eq.1 SVF: N_φ=36 azimuths, Δφ=10° | directional_visibility.py:16 `num_azimuths=32`; config.py:67 `sky_patch_configuration=32` (`linspace(0,360,endpoint=False)` → Δφ=11.25°) | **MISMATCH (36 vs 32)** — no value 36 anywhere in src |
| Eq.1 SVF: R_max=150 m | config.py:68 `max_svf_search_dist_m=60.0` (used by reference/full_recompute.py:87); function default 120.0 (directional_visibility.py:17); scripts override 30/80/100 | **MISMATCH (150 vs 60/120)** — no 150 m radius anywhere |
| Eq.1 z_ped=1.1 m | config.py:63 `pedestrian_height=1.1` | MATCH |
| Eq.2 shadow Möller–Trumbore | visibility/mesh_ray_intersection.py (M–T, EPS_DET=1e-10); shadow.py = 1 ray/cell toward sun | MATCH (algorithm) |
| Eq.3 6-flux α_p=0.70, ε_p=0.97, F_up=F_down=0.06, F_sides=0.22 | shortwave.py / longwave.py (f_up/f_down=0.06, f_side=0.22); a_k=0.70, a_l=0.97 | MATCH (all four) |
| Eq.4 Tmrt σ=5.67037e-8 | config.py:10 `SIGMA=5.670374419e-8`; radiation/tmrt.py:39 `(safe_s/SIGMA)**0.25` | MATCH |
| UTCI 6th-order polynomial (pythermalcomfort) | comfort/utci.py:12-16 try-import pythermalcomfort → delegates (L37-40) ELSE low-order additive fallback `ta+(...)` (L50-55); no native 6th-order poly in repo | **CONDITIONAL** — holds only if pythermalcomfort installed; repo itself ships only a low-order fallback. independent_audit.py:229 mislabels the fallback as "multivariate polynomial" |
| "~33 rays/cell" (derived; artifacts) | `1 + sky_patch_configuration` = 1 shadow + 32 SVF = 33 (optimizer.py:205; gpu_incremental.py:375 `total_cells*(1+num_azimuths)`); 28,120×33=927,960 = recorded total_rays | MATCH-as-derived — ties to the 32-azimuth mismatch above (NOT 33 shadow rays) |

Third Tmrt path: integration/tmrt_3d.py:197 uses `(max(10,s_str)/(a_l·SIGMA))**0.25` (divides by a_l·σ, l_up=0.95, walls=0.90) — a DIFFERENT inversion than core tmrt.py; see DIAGNOSIS.
## 3. Certificate (Theorem, .tex L220–234; Eq.8)

| Paper claim | Code location | Verdict |
|---|---|---|
| B_T(x)=ΔΦ_max/(4σT_min³) ≤ ε_T=0.50 K | certificate.py:198-203 concave-interval SB: `s_cached=σ(T+273.15)⁴`, `t_lower=(s_lower/σ)^¼`, `thermal_error_bound_k=t_cached−t_lower`; tol `tmrt_tolerance_k=0.5` (config.py:65) | MATCH |
| T_min ≥ 273.15 K floor | certificate.py:199 `s_lower=max(1.0, s_cached−Δs)` + `+273.15` throughout | MATCH (SB floor) |
| Eq.8 SVF solid-angle decay bound | certificate.py:63 `compute_svf_decay_bound` | MATCH |
| Dirty/clean masks | certificate.py:206 `dirty_mask=thermal_error_bound_k>tol`; verify_certificate:252 `reused=predicted_bound<=tol` | MATCH |
| (duplicate) legacy certificate | src/solaraeus/incremental/bounds.py:186-192 re-implements the same concave-interval SB | duplicate stack (ARCHIVE; see DIAGNOSIS) |

## 4. GPU performance (Table V, .tex L409–427)

| Paper claim | Code / artifact | Verdict |
|---|---|---|
| Kernels moller_trumbore_shadow_kernel, compute_svf_horizon_kernel | gpu_backend.py:32-385 (exact names) | MATCH |
| CPU full 5.71 s; CPU incr 0.42 s; 13.6× | stages_10_to_16 cpu_full 5.71 / cpu_inc 0.42 (5.71/0.42=13.6) | MATCH |
| GPU full 0.133 s; kernel 54.43 ms | gpu_runtime_summary.json mean 0.13387; kernel median 54.43109 | MATCH — but ALSO HARDCODED "133 ms" in generate_ieee_figures.py:281 |
| GPU incr 0.0114 s; kernel 11.40 ms | stages_10_to_16 gpu_inc 0.0114; kernel 11.40 | MATCH |
| GPU incr 500.87× (vs CPU full); 36.84× (vs CPU incr) | 5.71/0.0114=500.9; 0.42/0.0114=36.8 | MATCH |
| 1089.45 MB VRAM | stage_12 peak_gpu_vram_mb 1089.45 | MATCH |
| **GPU full 69.1× vs CPU** | gpu_runtime_summary.json effective_speedup "GPU Full"=69.1068 — but vs a ~9.25 s CPU basis; the SAME table's CPU-full is 5.71 s → 5.71/0.133=**42.9×** | **MISMATCH (internal)** — 69.1× uses a different CPU reference than the table's own 5.71 s; also HARDCODED in generate_ieee_figures.py:281; roll-up stages_10_to_16 carries a stale `gpu_full_mean_sec=0.4827` contradicting the 0.133 detail |
## 5. Results (Tables II / IV / VI + text, .tex L327–402)

| Paper claim | Code / artifact | Verdict |
|---|---|---|
| Baseline SVF 0.6569±0.1206; Tmrt 45.81±2.18°C; UTCI 36.49°C | church_street_shade_full_20261007_001600/shade_panel_full_recomputation_report.md | MATCH (values) |
| Baseline UTCI std ±0.44 | artifact std = 0.53 | MISMATCH (0.44 vs 0.53) |
| Baseline over corridor N=668 (L327) | report aggregates total_cells=28,120 (quality_checks.json) | NEEDS-VERIFY (values trace to grid-wide 28,120; corridor-668 domain label unconfirmed) |
| Parity Tmrt max err 0.028902 (tol 0.50) | stages_10_to_16 max_abs_error_tmrt_k 0.028902 | MATCH |
| Parity SVF 0.004195 / SW 0.128809 / LW 0.129326 / UTCI 0.100000 | stage parity artifacts | NEEDS-VERIFY (exact file to pin) |
| 72 cells (0.26%) recomputed / 28,048 reused (99.74%) / 925,584 rays avoided | reused_vs_recomputed (28120,72,28048,99.74); rays_avoided=925584 | MATCH |
| "scaling to 14.2× on 320 m grids" | closest = 14.54× (AddBuilding,320m) HARDCODED in benchmark/independent_audit.py:642-774 & examples/run_independent_audit.py:406; no artifact holds 14.2 | **HARDCODED / NEEDS-VERIFY** (14.2 vs 14.54; "14.2" elsewhere = CuPy 14.2.0) |
| (reconciliation) 23.14× ChangeHeight 320 m | HARDCODED (same files); timing_reconciliation.csv is populated FROM these literals | HARDCODED (not an independent measurement) |
| Single BLR_SHADE_001 6.0×3.0 m @3.5 m; avg −10.03 K; peak −12.62 K | optimization artifacts / REPORT.md | NEEDS-VERIFY (avg/peak to pin) |
| CAND_0063_SURR J=54.93; evaluated 120; prune 88.3% | REPORT.md J=54.9269; evaluated=120 is a runtime proposal count (code budget 20/75), not a constant | MATCH (J); 120 TRACEABLE-to-run |
| CAND_0063_SURR geometry L5.40/W1.90/H3.50/θ98.4° | code hardcodes a *warm-start seed* labelled CAND_0063_SURR as L3.48/W2.95/H2.99/θ95.80 (two_panel_acquisition.py:103-107) | MISMATCH (code-seed geometry ≠ reported winner; reported winner traces to the single-panel run artifact) |
| Dual CAND_4196_SURR: 4,401 explored / 4,176 pruned (94.9%); 91.8 s; total 22.87 m²; peak −12.68 K; J=56.57; |ΔTmrt|≤0.014 K | REPORT.md 4401/4176; validation_report.json CAND_4196_SURR; cert err 0.008147≤0.014 | MATCH |
| 18 certificates | optimization/validation artifacts | NEEDS-VERIFY |
## 6. Serialization & viewer claims (.tex L316–317, L481)

| Paper claim | Code reality | Verdict |
|---|---|---|
| "CF-compliant NetCDF rasters" | NO NetCDF writer in repo (no netCDF4 / xarray / `to_netcdf`); one GeoTIFF writer exists in handoff prep (refine_handoff_v2.py:210) | **MISMATCH (absent)** |
| "watertight OBJ meshes" | NO OBJ writer; mesh export is GLB via trimesh (solar/sun_model.py:209-211) | **MISMATCH (format: GLB, not OBJ)** |
| "Three.js r128 … GLSL thermal shaders" | simulation_3d/vendor three.min.js; simulation_3d heatmap/thermal shader present | MATCH (shaders present; exact Three.js version to confirm) |
| "solar timeline scrubbers" | viewer has overlay/opacity controls; explicit time scrubber not confirmed | NEEDS-VERIFY |
| "virtual avatar comfort HUD" | NO avatar / HUD in simulation_3d (orbit camera only) | **MISMATCH (absent)** |

## 7. Material findings, ranked (report-only; nothing changed)

1. **Hardcoded headline numbers.** 69.1× / 133 ms (generate_ieee_figures.py:281); the 14.54× / 23.14× scaling series (benchmark/independent_audit.py:642-774, examples/run_independent_audit.py:406) with timing_reconciliation.csv populated FROM those literals; 42.0× (run_church_street_two_panel_robustness.py:716); fabricated parity_metric 99.4%/0.6% (integration/time_shadowing.py:182-187); fabricated base_tmrt_mean=48.72 (integration/tmrt_3d.py:201). Genuine speedups ARE computed live in harness.py / runner.py — but the *published* figures use baked-in literals.
2. **SVF discretization.** Paper 36 azimuths / 150 m vs code 32 / 60–120 m (config.py:67-68). Propagates into SVF, Tmrt, and the "33 rays/cell" accounting.
3. **Trees 14 → 6.** Only T08–T13 exist (3 independent hardcoded defs with mutually inconsistent coordinates); the paper's 14 is unsupported.
4. **GPU 69.1× internally inconsistent** with the table's own 5.71 s / 0.133 s (→ 42.9×); different CPU reference basis.
5. **UTCI provenance.** 6th-order polynomial only via optional pythermalcomfort; silent low-order fallback otherwise.
6. **Serialization claims** (NetCDF, OBJ, avatar HUD) not implemented (GLB instead; no HUD).
7. **Minor numeric drifts:** triangles 2,136 vs 2,148; UTCI std 0.44 vs 0.53; wind 1.1 vs 1.5 m/s; CAND_0063_SURR code-seed geometry vs reported winner.
8. **Duplicate physics stacks:** legacy src/solaraeus/ and integration/*_3d.py re-implement core (tmrt_3d uses a divergent inversion) — correctness + maintenance risk; detailed in DIAGNOSIS.
