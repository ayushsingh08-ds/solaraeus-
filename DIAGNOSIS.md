# DIAGNOSIS.md — per-file verdicts (STEP 1, read-only)

**Governing KEEP TEST:** a file stays only if (a) a CLI/example/test imports it, or (b) it reproduces a paper number. Everything else is ARCHIVED on a git tag with evidence. **Nothing has been moved, edited, or deleted — this is a plan.**

**Verdict tokens:** `KEEP` (survives as-is, possibly relocated) · `RENAME` (survives, name/body changes) · `MERGE` (fold into another survivor) · `ARCHIVE` (git-tag + remove; reachable but out of scope per target) · `DELETE` (unreachable scratch) · `FIX` (keep but a defect must be corrected during STEP 3) · `NHD` ("Needs human decision").

**Target layout** (new `src/solaraeus/`): `core · physics · reference · incremental · backends · sites · extensions · placement · validation · pipelines` + `cli.py`.

Import facts are from the AST graph (`_impmap.json`, scratch, to be DELETED before STEP 1 concludes). LOC from the same.

## Headline structural findings
1. **No dead modules.** All 16 graph "orphans" are package `__init__.py` shims (reachability artifact). Every functional module is import-reachable from a script/test/example.
2. **Two parallel packages.** `src/urban_comfort/` (≈95 modules) is the live engine. `src/solaraeus/` (7 modules) is the LEGACY SOLWEIG reference — `urban_comfort` never imports it; it is reached only by `run_first_milestone` + 3 tests. Target makes `urban_comfort` → the new `src/solaraeus/`, so the legacy pkg is archived FIRST (name collision).
3. **Legacy is an independent oracle.** `test_solweig_reference`, `test_certificate_soundness`, `test_adversarial_suite` validate the engine against the legacy pkg. Archiving it drops that cross-check → **NHD: migrate the oracle onto `urban_comfort` or archive the tests with it.**
4. **Three Tmrt implementations** (`radiation/tmrt.py`, `integration/tmrt_3d.py` with a *divergent* `/(a_l·σ)` inversion, legacy `core/solweig.py`) + **fabricated literals** in `integration/time_shadowing.py` & `tmrt_3d.py` and in report/figure generators — see §Cross-cutting.

## A. LEGACY `src/solaraeus/` (7 modules) → ARCHIVE (tag `pre-cleanup/legacy-solaraeus`)

| Module | loc | Purpose | Verdict | Evidence | Risk |
|---|---|---|---|---|---|
| solaraeus/__init__ | 6 | pkg shim | ARCHIVE | orphan | none |
| core/geometry | 229 | legacy scene/AABB | ARCHIVE | run_first_milestone; tests ×3 | name collides w/ new pkg |
| core/solweig | 355 | legacy SOLWEIG Tmrt (own SIGMA, `(s/σ)^¼`) | ARCHIVE/NHD | oracle for test_solweig_reference | losing independent oracle |
| incremental/bounds | 205 | duplicate concave-interval certificate | ARCHIVE | solver, tests | 2nd copy of certificate math |
| incremental/solver | 100 | legacy incremental loop | ARCHIVE | runner, test_certificate_soundness | — |
| benchmark/adversarial | 122 | legacy adversarial scenes | ARCHIVE | runner, tests ×2 | — |
| benchmark/runner | 153 | legacy harness | ARCHIVE | run_first_milestone, tests ×2 | — |
## B. `src/urban_comfort/` — core + physics (all KEEP; relocate)

| Module | Purpose | Verdict → target | Evidence (importers) | Risk / defect |
|---|---|---|---|---|
| config.py | SIGMA, materials, SVF/tol knobs, lat/lon | RENAME → core/config + split Table-I constants to cities/church_street/city.yaml | ~everything | default lat/lon=NYC; `sky_patch_configuration=32`, `max_svf_search_dist_m=60.0` (paper says 36/150 — see PAPER_TRACE) |
| geometry/primitives | AABB box primitives | KEEP → core/geometry | scene, visibility, tests | — |
| geometry/mesh | triangle mesh | KEEP → core/geometry | backends, visibility, optimizer | — |
| geometry/scene | scene container | KEEP → core/geometry | pervasive | — |
| grid/pedestrian_grid | z_ped=1.1 sample grid | KEEP → core | pervasive | — |
| solar/solar_position | NOAA sun angles | KEEP → physics | pervasive, test_solar_position | — |
| solar/sun_model | GLB mesh + sun (Bengaluru coords) | KEEP → sites/extensions | execute_final_3d, test_final_3d_sun_model | module-level `import trimesh`; site coords live here not config |
| solar/cloud_model | cloud/diffuse | KEEP → physics/extensions | time_shadowing, tmrt_3d, tests | — |
| radiation/tmrt | Stefan–Boltzmann inversion `(safe_s/σ)^¼` | KEEP → physics | update, full_recompute, backends | canonical Tmrt (cf. 2 rivals) |
| radiation/shortwave | 6-flux SW (F=0.06/0.06/0.22, a_k=0.70) | KEEP → physics | full_recompute, update, backends | — |
| radiation/longwave | 6-flux LW (a_l=0.97, Prata air emis) | KEEP → physics | full_recompute, certificate, update | — |
| comfort/utci | UTCI: pythermalcomfort else low-order fallback | FIX → physics | pervasive | no native 6th-order poly; fallback silently low-order (PAPER_TRACE CONDITIONAL) |
| visibility/ray_intersection | AABB ray test | KEEP → physics | shadow, test_ray_intersections | — |
| visibility/mesh_ray_intersection | Möller–Trumbore | KEEP → physics | mesh_shadow/visibility, tests | — |
| visibility/shadow | 1 ray/cell AABB shadow | KEEP → physics | full_recompute, update, tests | — |
| visibility/mesh_shadow | mesh shadow | KEEP → physics | test_mesh_shadows | — |
| visibility/directional_visibility | SVF horizon scan (num_azimuths=32, fn R=120) | KEEP → physics | full_recompute, update, tests | SVF discretization ≠ paper 36/150 |
| visibility/mesh_visibility | mesh SVF | KEEP → physics | directional_visibility, run scripts, tests | — |
| reference/full_recompute | baseline full solve (uses config 32/60) | KEEP → reference | pervasive (oracle) | drives golden master |
## C. `incremental/` (all KEEP → incremental/)

| Module | Purpose | Evidence | Risk / defect |
|---|---|---|---|
| incremental/certificate | concave-interval error certificate (ε_T=0.5) | update, harness, stage 06/07/08/11, tests | canonical cert (legacy bounds.py duplicates it) |
| incremental/update | certified/exact incremental solve | pervasive incremental+opt | imports gpu_incremental (CPU path pulls GPU module) |
| incremental/cache | result cache | harness, stage 06/08, tests | — |
| incremental/dependency_graph | dirty propagation | cache, harness, independent_audit, tests | — |
| incremental/affected_region | AABB-edit affected cells | certificate, independent_audit, tests | — |
| incremental/mesh_affected_region | mesh-edit affected cells | test_mesh_affected_region | — |
| incremental/mesh_update | mesh incremental | pervasive mesh/opt, tests | — |

## D. `backend/` (all KEEP → backends/)

| Module | Purpose | Evidence | Risk / defect |
|---|---|---|---|
| backend/base | backend interface | cpu/gpu backends | — |
| backend/cpu_backend | NumPy backend | gpu_backend, run_church_street_gpu, test | — |
| backend/gpu_backend | CuPy kernels (moller_trumbore_shadow, compute_svf_horizon, rasterize) | gpu_incremental, terrain/gpu, stages 08-12, tests | CONDITIONAL on CuPy; SVF kernel defaults 32/120 |
| backend/gpu_incremental | GPU incremental (`total_rays=cells*(1+azimuths)`) | update, optimizer×all, stages 11/12, tests | import-time pulled by CPU `update` |

## E. `optimization/` (19 modules → placement/; single + dual_panel families)

Target renames `two_panel_*` → `dual_panel_*` (NAMING_MAP). Single & dual share a parameters/feasibility/objective/ledger/surrogate/acquisition/optimizer/validation shape; consider a shared base during STEP 3 (NHD — behaviour-preserving?).

| Module | Purpose | Evidence | Risk / defect |
|---|---|---|---|
| parameters / two_panel_parameters | 7-/14-param encode + canonicalize | optimizer families, tests | dual canonicalize x-then-y |
| feasibility / two_panel_feasibility | geometric constraints | optimizer families, stage 13, tests | code setback 0.50 m / underside 2.5–5.5 m / area 10–60 m² ≠ paper 1.0 m / H≥3.5 / ≤30 m² (PAPER_TRACE) |
| objective / two_panel_objective | J(x) cooling objective | optimizer families | — |
| ledger / two_panel_ledger | evaluation ledger | surrogate, optimizer, tests | — |
| surrogate / two_panel_surrogate | RF/ExtraTrees (100/12) | acquisition, surrogate_optimizer | — |
| acquisition / two_panel_acquisition | LCB+EI (κ=2.0) / LCB (κ=1.5) | surrogate_optimizer, two_panel_opt, run scripts | **NHD** paper says UCB κ=1.96 → target name `ucb_acquisition` would misdescribe code; two_panel_acquisition:103-107 hardcodes a seed labelled `CAND_0063_SURR` with geometry ≠ reported winner |
| optimizer / two_panel_optimizer | classical search loop | stage 14/15/16, run scripts, tests | — |
| surrogate_optimizer | surrogate-driven search | run_church_street_surrogate_optimization | — |
| validation / two_panel_validation | candidate re-validation (certified) | optimizer, run scripts, test_intervention_optimization | — |
| robustness | seed/scenario sweep | run_church_street_two_panel_robustness | descriptor "1.5 m/s, 728.3 DNI" (PAPER_TRACE wind) |
| robustness_plots | plotting helper | robustness | pure matplotlib; → tools or placement |

## F. `integration/` (3D viewer path → extensions/ + sites/) — FIX-heavy

| Module | Purpose | Evidence | Risk / defect |
|---|---|---|---|
| integration/coordinates | CRS/origin/γ (EPSG:32643) | execute_final_3d, test_final_3d_coordinate_alignment, tree_loader | KEEP → sites/ (georef constants = Table I) |
| integration/tmrt_3d | 3D Tmrt engine | execute_final_3d, test_final_3d_tmrt | **FIX**: divergent inversion `(max(10,s)/(a_l·σ))^¼`; **fabricated `base_tmrt_mean=48.72`**; singleton; dead `compute_tmrt` import |
| integration/utci_3d | thin UTCI wrapper (calls core) | execute_final_3d, test_final_3d_utci | KEEP → extensions/ |
| integration/time_shadowing | diurnal shadow track | execute_final_3d, test_final_3d_time_shadowing | **FIX: fabricated `parity_metric` 99.4%/0.6% hardcoded** |
| integration/terrain_loader | FABDEM loader (singleton) | execute_final_3d, tree_geometry_builder, test_final_3d_terrain_loading | **FIX**: import-time CWD-relative conditional raster read → lazy factory |
| integration/tree_loader | tree manifest loader (singleton, 6 trees) | execute_final_3d, tree_geometry_builder, test_final_3d_tree_map_placement | **FIX**: import-time conditional CSV read; paper 14 vs 6 (PAPER_TRACE) |
| integration/tree_geometry_builder | builds tree meshes | execute_final_3d, test_final_3d_tree_map_placement | — |
## G. `terrain/` + `vegetation/` + `preprocessing/` (the 2.1.0 extensions → extensions/ + sites/)

All KEEP — reached by CLI stage scripts (so they pass the KEEP TEST), but every one is self-labelled PROVISIONAL / SENSITIVITY_USE_ONLY / NON_AUTHORITATIVE → they belong behind the `validate-extensions` pipeline, never in the authoritative baseline. GPU modules are CONDITIONAL on CuPy.

| Module | Purpose | Verdict → target | Evidence (importers) | Risk / defect |
|---|---|---|---|---|
| terrain/dtm | TerrainGrid raster | KEEP → extensions/terrain | stages 27/28/30-36 | — |
| terrain/terrain_scene | terrain-aware scene (delegates to flat Scene when terrain None) | KEEP → extensions/terrain | stages 22/27/28/30-36 | — |
| terrain/terrain_solver | 2.1.0-cpu-terrain solver | KEEP → extensions/terrain | stages 22/27/30/34, vegetation | `min(60.0,…)` search dist (:117) — same 60 m, not paper 150 |
| terrain/gpu_terrain | 2.1.0-gpu-terrain backend | KEEP → extensions/terrain | stages 23/28/31/32/34-36, gpu_tree | CONDITIONAL (CuPy) |
| vegetation/tree | Tree + `get_core_trees` | KEEP → extensions/vegetation | stages 29-36 | **source of the 6 trees T08–T13** (paper 14; PAPER_TRACE) |
| vegetation/tree_scene | tree+terrain scene | KEEP → extensions/vegetation | stages 31-36 | — |
| vegetation/tree_solver | 2.1.0 CPU tree shadow | KEEP → extensions/vegetation | stages 30-36 | — |
| vegetation/gpu_tree | GPU tree shadow | KEEP → extensions/vegetation | stages 31/32/34-36 | CONDITIONAL (CuPy) |
| preprocessing/church_street_adapter | builds Church St scene from raw sources | KEEP → sites/church_street (build-scene) | execute_final_3d, run_church_street_preprocessing, test_church_street_preprocessing | `terrain_status="retained_for_metadata_only_flat_model_ground_in_solver"` (:491-493) — confirms baseline solver is FLAT ground |

## H. `benchmark/` (10) + `validation/` (2) → validation/ + pipelines/benchmark

| Module | Purpose | Evidence | Risk / defect |
|---|---|---|---|
| benchmark/harness | live full-vs-incremental timing | run_all_evaluations, run_publication_validation | genuine live speedups computed here (cf. hardcoded figures) |
| benchmark/scenes | scaling-scene factory | run_all/independent_audit/publication, test_mutation_audits | — |
| benchmark/independent_reference | external SOLWEIG cross-check | run_all_evaluations, run_publication_validation | independent oracle (cf. §A legacy) |
| benchmark/independent_audit | mutation + certificate audit | run_independent_audit, tests ×3 | **HARDCODED scaling 14.54×/23.14× literals (:642-774)**; `audit_certificate_independently`, `run_mutation_tests` |
| benchmark/tightness | bound-tightness report | run_publication_validation | — |
| benchmark/repeated_edits | repeated-edit sequence | run_publication_validation, run_independent_audit | — |
| benchmark/baseline_comparison | baseline deltas | run_publication_validation | — |
| benchmark/aabb_vs_mesh_benchmark | AABB vs mesh timing | test_aabb_vs_mesh_benchmarks | — |
| benchmark/mesh_certificate_audit | mesh cert audit | test_mesh_certificate_audits | — |
| benchmark/mesh_scaling_benchmark | mesh scaling timing | test_mesh_scaling_benchmarks | — |
| validation/comparisons | `compare_results` field deltas | test_incremental_updates, test_validation_comparisons | name collides w/ target `validation/` pkg + optimization `validation` — NAMING_MAP must disambiguate |
| validation/metrics | error metrics | test_validation_comparisons | — |
## I. `scripts/` (59 files → 9 pipelines + cli.py) — registry + structural findings

59 scripts: 38 `execute_stage_*` + `execute_final_3d_integrated_simulation` + `execute_stages_27_to_38_blocked_gates` + 9 `run_church_street_*` + `run_first_milestone` + `resolve_researcher_signoff` + `verify_ui_quality` + 7 `generate_*`. **No stage script is a library import target** (empty import edges as *importers* only — they are entry points). Target: their orchestration MERGEs into `pipelines/{build_scene,simulate,evaluate_edit,benchmark,optimize,validate_extensions,export_viewer,paper_artifacts,gates}.py` + `cli.py`; file-check gates (19/24 + blocked_gates) collapse to one `gates.yaml` + one test. **Status tokens KEEP VERBATIM** → emit `pipelines/_legacy_registry.yaml` (legacy_stage_id → pipeline + token) in STEP 3; the authoritative source is the scripts-agent handback in this transcript.

Pipeline distribution (59): build-scene 3 · simulate 5 · evaluate-edit 8 · benchmark 5 · optimize 7 · validate-extensions 14 · export-viewer 1 · paper-artifacts 10 · gates 6.

### I.1 — `execute_stage_*` registry (token verbatim; `STAGE_n_` prefix elided where obvious)

| Stage | → pipeline | status token | verdict |
|---|---|---|---|
| 05 shade_panel_full | simulate | `…FULL_RECOMPUTATION_COMPLETE` | MERGE → pipelines/simulate |
| 06 shade_panel_incremental | evaluate-edit | `…INCREMENTAL_RECOMPUTATION_COMPLETE` | MERGE → evaluate_edit |
| 07 certificate_and_cpu_audit | benchmark | `…CERTIFICATE_AUDIT_AND_CPU_EFFICIENCY_COMPLETE` | MERGE → benchmark (reclassified from evaluate-edit) |
| 08 cpu_reference_freeze | gates | `…CPU_REFERENCE_API_FROZEN` | MERGE → gates (reclassified from simulate) |
| 09 gpu_direct_shadow_svf | benchmark | `…GPU_DIRECT_SHADOW_SVF_BACKEND_COMPLETE` | MERGE → benchmark (GPU-hard) |
| 10 gpu_full_vs_cpu | benchmark | `…GPU_FULL_VS_CPU_VALIDATION_COMPLETE` | MERGE → benchmark (GPU-hard) |
| 11 gpu_incremental | evaluate-edit | `…GPU_INCREMENTAL_RECOMPUTATION_COMPLETE` | MERGE → evaluate_edit (GPU-hard) |
| 12 gpu_profiling | benchmark | `…RUNTIME_MEMORY_WORK_PROFILING_COMPLETE` | MERGE → benchmark (GPU-hard) |
| 13 geographic_feasibility | optimize | `…GEOGRAPHIC_FEASIBILITY_AND_PARAMETERIZATION_COMPLETE` | MERGE → optimize |
| 14 constrained_optimizer | optimize | `…BASELINE_SEARCH_AND_CONSTRAINED_AI_OPTIMIZER_COMPLETE` | MERGE → optimize (GPU-hard) |
| 15 final_validation | evaluate-edit | `…FINAL_CANDIDATE_VALIDATION_AND_UNCERTAINTY_COMPLETE` | MERGE → evaluate_edit |
| 16 additional_areas_and_publication | paper-artifacts | `…ADDITIONAL_AREA_TESTING_AND_PUBLICATION_COMPLETE` | MERGE → paper_artifacts |
| 17 publication_review | paper-artifacts | `…PUBLICATION_REVIEW_AND_ARCHIVAL_RELEASE_COMPLETE` | **FIX** claim metrics are literals (max_abs_error_tmrt_k=1.1368e-13, 500.87×) |
| 18 clean_reproducibility | gates | `…CLEAN_ENVIRONMENT_REPRODUCIBILITY_COMPLETE` | **FIX** `matches_reference=True` hardcoded (no re-run) |
| 19 researcher_approval | gates | `STAGE_19_HUMAN_APPROVAL_PENDING` | MERGE → gates.yaml |
| 20 street_scale_dtm | validate-extensions | `STAGE_20_SYNTHETIC_TERRAIN_ONLY` | MERGE → validate_extensions |
| 21 field_tree_validation | validate-extensions | `STAGE_21_FIELD_VALIDATION_PENDING` | MERGE → validate_extensions |
| 22 cpu_terrain_extension | validate-extensions | `…TERRAIN_AWARE_CPU_REFERENCE_COMPLETE` | MERGE → validate_extensions |
| 23 gpu_terrain_extension | validate-extensions | `…TERRAIN_AWARE_GPU_AND_INCREMENTAL_COMPLETE` | MERGE (GPU-hard) |
| 24 researcher_approval | gates | `STAGE_24_APPROVED` | MERGE → gates.yaml |
| 25a available_terrain_validation | validate-extensions | `STAGE_25_SYNTHETIC_TERRAIN_ONLY` | **KEEP (current)** → validate_extensions |
| 25b real_dtm_validation | validate-extensions | `STAGE_25_SYNTHETIC_TERRAIN_ONLY` | **ARCHIVE (superseded dup — Res. A)** |
| 26a field_tree_validation | validate-extensions | `STAGE_26_FIELD_VALIDATION_PENDING` | **NHD (collides w/ 26b — Res. B)** |
| 26b field_validation_deferral | validate-extensions | `STAGE_26_FIELD_VALIDATION_DEFERRED` | **NHD (current intent; overwrites 26a's json)** |
| 27 available_terrain_cpu_validation | validate-extensions | `…AVAILABLE_TERRAIN_CPU_VALIDATION_COMPLETE` | MERGE (collides w/ blocked_gates — Res. C) |
| 28 available_terrain_gpu_validation | validate-extensions | `…AVAILABLE_TERRAIN_GPU_AND_INCREMENTAL_COMPLETE` | MERGE (GPU-hard; Res. C) |
| 29 provisional_level1_tree_geometry | build-scene | `…PROVISIONAL_LEVEL1_TREE_GEOMETRY_COMPLETE` | MERGE (Res. C collision) |
| 30 cpu_tree_shadow | simulate | `…CPU_TREE_SHADOW_REFERENCE_COMPLETE` | MERGE (Res. C) |
| 31 gpu_tree_shadow | simulate | `…GPU_TREE_SHADOW_COMPLETE` | MERGE (GPU-hard; Res. C) |
| 32 tree_incremental | evaluate-edit | `…TREE_AWARE_INCREMENTAL_COMPLETE` | MERGE (Res. C) |
| 33 canopy_sensitivity | validate-extensions | `…CANOPY_SENSITIVITY_COMPLETE` | MERGE (Res. C) |
| 34 terrain_tree_parity | validate-extensions | `…TERRAIN_TREE_PARITY_COMPLETE` | MERGE (file `_parity` writes dir `_validation`; Res. C) |
| 35 terrain_tree_optimization | optimize | `…PROVISIONAL_TERRAIN_TREE_OPTIMIZATION_COMPLETE` | MERGE (Res. C) |
| 36 final_terrain_tree_validation | validate-extensions | `…PROVISIONAL_TERRAIN_TREE_VALIDATION_COMPLETE` | MERGE (Res. C) |
| 37 field_comparison | validate-extensions | `STAGE_37_FIELD_DATA_UNAVAILABLE` | MERGE (Res. C) |
| 38 final_publication_and_closure | paper-artifacts | `…FINAL_PUBLICATION_…COMPLETE` + `SOLARAEUS_PROJECT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS` | MERGE → paper_artifacts (Res. C) |
| — final_3d_integrated_simulation | simulate (composite) | `SOLARAEUS_DATA_DRIVEN_3D_SIMULATION_COMPLETE_WITH_DOCUMENTED_LIMITATIONS` | **FIX-heavy** (§F) then MERGE → simulate/export_viewer |
| — stages_27_to_38_blocked_gates | gates | `STAGE_27_BLOCKED … STAGE_38_BLOCKED` | **ARCHIVE** (no runtime checks; `tests_passed=5` literal; collides 27-38 — Res. C) |
### I.2 — `run_*` / `generate_*` / governance registry

| Script | → pipeline | status token | verdict |
|---|---|---|---|
| run_church_street_preprocessing | build-scene | `READY_FOR_STATIC_FULL_SIMULATION` | MERGE → build_scene — **PRODUCER of frozen `prep/`** |
| run_church_street_static_simulation | simulate | `READY_FOR_SHADE_PANEL_FULL_RECOMPUTATION_AFTER_METADATA_RECONCILIATION` | MERGE → simulate — **PRODUCER of frozen `baseline/`** |
| run_church_street_gpu_simulation | benchmark | prints `SUCCESS (READY FOR GPU INCREMENTAL)` | MERGE (GPU-hard) |
| run_church_street_shade_panel_simulation | evaluate-edit | `READY_FOR_SHADE_PANEL_INCREMENTAL_COMPARISON` | MERGE → evaluate_edit |
| run_church_street_shade_panel_incremental | evaluate-edit | `ACCEPTED_FOR_RESEARCH` | MERGE → evaluate_edit |
| run_church_street_shade_panel_gpu_incremental | evaluate-edit | `ACCEPTED_FOR_RESEARCH` | MERGE (GPU-hard) |
| run_church_street_intervention_optimization | optimize | `READY_FOR_SURROGATE_ASSISTED_INTERVENTION_OPTIMIZATION` | MERGE → optimize (S1) |
| run_church_street_surrogate_optimization | optimize | `READY_FOR_MULTI_INTERVENTION_SURROGATE_OPTIMIZATION` | MERGE → optimize (S2) |
| run_church_street_two_panel_optimization | optimize | `READY_FOR_MULTI_PANEL_INTERVENTION_TYPE_OPTIMIZATION` | MERGE → optimize (S3; `dual_panel`) |
| run_church_street_two_panel_robustness | optimize | `ROBUST_TWO_PANEL_VALIDATION_COMPLETE` | MERGE → optimize; FIX hardcoded 42.0× (:716) |
| run_first_milestone | evaluate-edit | prints `MILESTONE 1` ("100% sound") | **ARCHIVE w/ legacy pkg** (imports `solaraeus/`; §A/NHD-oracle) |
| resolve_researcher_signoff | build-scene | writes `status:"approved"` | **FIX/NHD** — bakes 6 approval gates + 37-building CSV as literals |
| verify_ui_quality | gates | `ALL_REQUIREMENTS_PASSED` / `REQUIREMENTS_FAILED` | MERGE → gates |
| generate_church_street_review | paper-artifacts | `NOT_READY_FOR_SIMULATION` + `READY_FOR_PREPROCESSING_ONLY` | MERGE → paper_artifacts |
| generate_ieee_figures | paper-artifacts | (print only) | **FIX** hardcoded `CPU 5.71s/GPU 133ms/69.1×` (:281) |
| generate_architecture_diagram | paper-artifacts | (print only) | **FIX** embeds "Soundness 100%" literal |
| generate_stages_05_to_09_… | paper-artifacts | `STAGES_05_TO_09_EXECUTION_COMPLETE` | MERGE → paper_artifacts |
| generate_stages_10_to_16_… | paper-artifacts | `STAGES_10_TO_16_EXECUTION_COMPLETE` | MERGE → paper_artifacts |
| generate_stages_17_to_23_… | paper-artifacts | (aggregator) | MERGE → paper_artifacts |
| generate_stages_24_to_38_… | paper-artifacts | (aggregator; gate ledger) | MERGE → paper_artifacts |
| generate_viewer_screenshots_and_style_report | export-viewer | embeds `SOLARAEUS_DATA_DRIVEN_3D_…LIMITATIONS` | MERGE → export_viewer |

### I.3 — Structural resolutions (verified file:line)
- **Res. A (Stage 25 dup, no file collision):** `…available_terrain_validation` (CURRENT, "Final Post-Roadmap") vs `…real_dtm_validation` (SUPERSEDED, "Post-Stage-23"); different out-dirs, identical token. → keep available, ARCHIVE real_dtm.
- **Res. B (Stage 26 TRUE collision):** both write `results/stage_26_field_tree_validation/stage_26_test_results.json`; `…field_validation_deferral` (CURRENT, 59 loc) OVERWRITES `…field_tree_validation` (:50). Last-run-wins → DEFERRED. **NHD: which is authoritative-of-record.**
- **Res. C (NEW CRITICAL — stages 29-38 collision):** the 10 individual `execute_stage_29..38` scripts (emit `*_COMPLETE`) and `execute_stages_27_to_38_blocked_gates` (emits `*_BLOCKED`, no runtime checks, `prerequisite_met=False` literal) write to IDENTICAL result dirs → **contradictory last-run-wins verdicts**. Also stages 27/28: individual→`*_available_terrain_*`, monolith→`*_real_terrain_*` (naming split, no collision). **NHD: one lineage; ARCHIVE blocked_gates.**
- **Res. D (frozen-dir hardcoders):** `prep/`=church_street/preprocessing, `baseline/`=church_street/static_baseline hardcoded across stages 05/06/07/11/12/13/14/15/16/18 + SHA-256 contracts over `baseline/shadow_results.npz` (stage_14:92/711, 08, 15/16, generate_stages_*). **HARD RULE: never regenerate these two; pin via `reference_artifacts/inputs.lock`.**
## J. `tests/` (86 files → tests/{unit,contracts,golden}) — per tests-agent inventory

Split: **~42 UNIT** (physics/geometry/incremental/backend/optimization behavior) · **~43 CONTRACT** (status-token / file-existence assertions mirroring stages) · **0 GOLDEN** (nearest = `test_gpu_backend.py` frozen-reference subtest). STEP 2 populates `tests/golden/` from the golden-master baseline.

- **Contract collapse:** `test_stage_10..38` (29) + `test_stages_27_to_38_gates` + the stage-mirroring `test_final_3d_*` → ONE parametrized test driven by `tests/contracts.yaml` (one row per stage: pipeline, token, expected artifacts). **Schema must allow token-optional rows** — tests for stages 17/18/22/23 assert no `success_token` key.
- **Coverage gaps from Res. A/B:** tests exist only for the SUPERSEDED/collided variants — `test_stage_25_real_dtm_validation`, `test_stage_26_field_tree_validation` — the CURRENT scripts (25a available, 26b deferral) have NO test. **NHD:** retarget these tests onto the current scripts before archiving the old ones, or coverage drops silently.
- `test_stage_34_terrain_tree_validation` mirrors the OUTPUT-dir name, not the script stem `_parity` (confirms §I dir-name drift).
- `test_stages_27_to_38_gates` tests the blocked_gates monolith → ARCHIVE with it (Res. C) or retarget to `gates.yaml`.
- **Oracle tests (NHD, headline finding 3):** `test_solweig_reference`, `test_certificate_soundness`, `test_adversarial_suite` validate the engine against legacy `src/solaraeus/` → migrate the oracle onto the new pkg or archive these with the legacy pkg (§A).
- `test_final_3d_coordinate_alignment` is MIXED (unit georef math + contract artifact check) — split on move.
- Verdict: all KEEP (every test is its own importer, trivially passes KEEP TEST); dispositions are relocations + the one parametrized collapse, which is behaviour-preserving only if `contracts.yaml` reproduces each asserted token/artifact exactly.

## K. `examples/` (5 → 3) + `simulation_3d/` viewer → viewer/legacy/

| File | Verdict → target | Note |
|---|---|---|
| examples/single_building | KEEP → examples/ | minimal end-to-end demo |
| examples/compare_full_incremental | KEEP → examples/ | canonical incremental-vs-full demo |
| examples/run_all_evaluations | KEEP → examples/ | drives benchmark/ harness+scenes+independent_reference |
| examples/run_publication_validation | **MERGE → pipelines/benchmark** | overlaps benchmark pipeline (harness/tightness/repeated_edits/baseline_comparison) |
| examples/run_independent_audit | **FIX then MERGE → pipelines/benchmark** | consumes HARDCODED independent_audit scaling (:406); not an independent measurement |
| simulation_3d/{app,church_street_data,dataColormaps}.js | KEEP → viewer/legacy/ | `church_street_data.js` = generated data blob (regen by export-viewer) |
| simulation_3d/heatmapShader.js | KEEP → viewer/legacy/ | GLSL thermal shader (paper §6 MATCH) |
| simulation_3d/index.html | KEEP → viewer/legacy/ | **no avatar/HUD, no time-scrubber** (paper §6 MISMATCH) |
| simulation_3d/vendor/{three.min,OrbitControls}.js | KEEP → viewer/legacy/vendor/ | Three.js (r128 to confirm) |
## L. `results/` retention (HARD RULE: keep only pinned + paper-cited + golden)

**Never regenerate** the two frozen folders. Keep, ARCHIVE-on-tag everything else.

| Keep bucket | Paths (evidence) |
|---|---|
| Pinned baselines (frozen) | `church_street/preprocessing/`, `church_street/static_baseline/` — pin in `reference_artifacts/inputs.lock` (path+SHA-256) |
| Paper Table II (results) | `church_street/shade_full/shade_panel_full_recomputation_report.md` (0.6569 / 45.81 / 36.49) + `scene_summary.json`,`quality_checks.json` (28,120 cells; 123 bldg) |
| Paper Table V (GPU) | `gpu_runtime_summary.json`, `gpu_benchmark_trials.csv`, `stage_12_gpu_profiling/`, `stages_10_to_16` roll-up (5.71/0.42/0.133/0.0114; 500.87×/36.84×; 1089.45 MB; parity 0.028902; 72/28,048/925,584) |
| Paper Tables IV/VI (placement) | optimization `REPORT.md`, `validation_report.json` (CAND_0063_SURR J=54.93; CAND_4196_SURR J=56.57) |
| Provenance | `provenance.json` (solar α_s/φ_grid) |
| Stage manifests | one manifest JSON per retained stage dir (not the bulk arrays) |
| Golden subset | small CPU golden slice for STEP 2 compare (to be selected) |

Everything else under `results/` (intermediate npz, per-trial dumps, superseded stage dirs, the Res. C `*_real_terrain_*`/blocked stub dirs) → **ARCHIVE on `pre-cleanup/results-bulk`**. Do NOT delete; tag + remove.

## M. Cross-cutting defects (the STEP-3 FIX backlog; report-only now)

1. **Three Tmrt inversions.** canonical `radiation/tmrt.py:39` `(safe_s/σ)^¼` ✓ · `integration/tmrt_3d.py:197` `(max(10,s)/(a_l·σ))^¼` **divergent** (divides by a_l·σ) · legacy `solaraeus/core/solweig.py:290` `(s/σ)^¼`. **FIX:** tmrt_3d must delegate to core (or document why its inversion differs); legacy archived with §A.
2. **Fabricated literals** (not computed at generation): `base_tmrt_mean=48.72` (tmrt_3d.py:201); `parity_metric` 99.4%/0.6% (time_shadowing.py:182-187); IEEE `69.1×`/`133 ms` (generate_ieee_figures.py:281); scaling `14.54×`/`23.14×` (independent_audit.py:642-774, run_independent_audit.py:406, timing_reconciliation.csv populated FROM them); `42.0×` (two_panel_robustness.py:716); stage_17 claim metrics; stage_18 `matches_reference=True`; blocked_gates `tests_passed=5`. **FIX:** compute live or move to clearly-labelled fixtures. (Genuine live speedups DO exist in harness.py/runner.py.)
3. **Import-time CWD-relative I/O singletons:** `integration/terrain_loader.py:183` (`terrain_loader = TerrainLoader()` reads raster at import, path relative to CWD) and `integration/tree_loader.py` (CSV at import). **FIX → lazy factories** reading `cities/church_street/city.yaml`.
4. **SVF discretization** 32 azimuths / 60–120 m (config.py:67-68, directional_visibility.py:16-17) vs paper 36 / 150 m. **NHD — report-only; change neither paper nor code to force agreement** (PAPER_TRACE §2).
5. **UTCI provenance CONDITIONAL.** `comfort/utci.py` delegates to pythermalcomfort if installed, else a low-order additive fallback; no native 6th-order Bröde polynomial in-repo; `independent_audit.py:229` mislabels the fallback as "multivariate polynomial". **FIX:** ship a real 6th-order poly or gate the claim on the dependency.
6. **CPU path imports GPU module.** `incremental/update` pulls `gpu_incremental` at import → CPU-only runs import CuPy-adjacent code. **FIX:** lazy/guarded import.
7. **Duplicate certificate stack.** `incremental/certificate.py` (canonical) vs legacy `solaraeus/incremental/bounds.py:186-192` (same concave-interval SB). Resolved by archiving legacy (§A).
8. **Site constants scattered.** `config.py` default lat/lon = NYC 40.7128/-74.0060; real site (Bengaluru 12.9749/77.6054) lives in `solar/sun_model.py`; georef (EPSG:32643, origin, γ) in `integration/coordinates.py`. **FIX:** consolidate all Table-I constants into `cities/church_street/city.yaml`.
9. **Feasibility constants ≠ paper.** code setback 0.50 m / underside 2.5–5.5 m / area 10–60 m² vs paper 1.0 m / H≥3.5 m / ≤30 m². **NHD — report-only.**
10. **CAND_0063_SURR seed ≠ reported winner.** `two_panel_acquisition.py:103-107` hardcodes a warm-start seed labelled `CAND_0063_SURR` (L3.48/W2.95/H2.99/θ95.80) ≠ paper winner (L5.40/W1.90/H3.50/θ98.4). **FIX/NHD:** rename the seed (ID is reserved-verbatim) or source it from the artifact.
11. **`ucb_acquisition` naming conflict.** target name says UCB; code is LCB+EI portfolio (κ=2.0/1.5), paper says UCB κ=1.96. **NHD:** name after the code (`lcb_ei_acquisition`) or reconcile with paper — do not let the target name assert a method the code does not implement.

---

### STEP-1 exit checklist
- [x] `PAPER_TRACE.md` — complete (7 sections, all evidence-backed).
- [x] `DIAGNOSIS.md` — complete (§A–§M; every `src/` module, all 59 scripts, all 86 tests, examples, viewer, results).
- [ ] `NAMING_MAP.md` — old→new map (flag `two_panel`→`dual_panel`, `ucb_acquisition` NHD, `validation/` disambiguation).
- [ ] Delete scratch `_impmap.py` + `_impmap.json`.
- [ ] **STOP for the user's `approved`** — no branch/tag/baseline/move/edit until then.

**Open NHDs for the approval gate:** (1) legacy-oracle migrate-vs-archive-with-tests; (2) Stage 26 authoritative-of-record (pending/deferral); (3) Stage 29-38 lineage (individual vs blocked_gates); (4) retarget Stage 25/26 tests before archiving superseded variants; (5) SVF 36/150 vs 32/60-120 — paper or code; (6) `ucb_acquisition` naming; (7) which 3 examples survive.
