# NAMING_MAP.md — old → new (STEP 1, read-only plan)

Behaviour-preserving renames only. **Nothing moved/edited yet.** Pairs the TARGET STRUCTURE (`src/solaraeus/{core,physics,reference,incremental,backends,sites,extensions,placement,validation,pipelines}` + `cli.py`) and NAMING scheme with the real repo inventory (verified via AST graph + globs/greps).

**Rules:** units suffix `_m _k _c _deg _s _ms _w_m2`; banned in *names* → stage numbers, dates, `final/new/old/v2/tmp/misc/utils/helpers`, `execute_`/`run_` on library code. **KEEP VERBATIM:** status tokens, committed-artifact JSON keys, IDs. Ambiguities → **NHD** (listed §5).

## 1. Package + banned-name policy
- `src/urban_comfort/` → **`src/solaraeus/`** (the live engine becomes the package).
- current `src/solaraeus/` (7-file legacy SOLWEIG) → **archived first** (name collision; tag `pre-cleanup/legacy-solaraeus`).
- Banned-name hits to resolve: `two_panel_*`→`dual_panel_*`; `execute_`/`run_`/`generate_` script prefixes → dropped (become `cli` subcommands); `final` (execute_final_3d, stage_16/36/38, final_validation) → dropped; dates in frozen `results/*_2026…` dirs and `..._handoff_v2` → **exempt** (committed artifacts/pinned inputs, KEEP VERBATIM).
- No `utils/helpers/misc` modules exist today (good) — none to rename.

## 2. Module move map (old `urban_comfort/…` → new `solaraeus/…`)

### core/
| old | new |
|---|---|
| config.py | core/config.py (+ Table-I consts → cities/church_street/city.yaml) |
| geometry/primitives.py | core/geometry/primitives.py |
| geometry/mesh.py | core/geometry/mesh.py |
| geometry/scene.py | core/geometry/scene.py |
| grid/pedestrian_grid.py | core/pedestrian_grid.py |

### physics/
| old | new |
|---|---|
| solar/solar_position.py | physics/solar_position.py |
| solar/cloud_model.py | physics/cloud_model.py |
| radiation/tmrt.py | physics/mean_radiant_temperature.py |
| radiation/shortwave.py | physics/shortwave.py |
| radiation/longwave.py | physics/longwave.py |
| comfort/utci.py | physics/utci.py |
| visibility/ray_intersection.py | physics/ray_intersection.py |
| visibility/mesh_ray_intersection.py | physics/mesh_ray_intersection.py |
| visibility/shadow.py | physics/shadow.py |
| visibility/mesh_shadow.py | physics/mesh_shadow.py |
| visibility/directional_visibility.py | physics/sky_view_factor.py |
| visibility/mesh_visibility.py | physics/mesh_sky_view_factor.py |
### reference/
| old | new |
|---|---|
| reference/full_recompute.py | reference/full_recompute.py |

### incremental/
| old | new |
|---|---|
| incremental/certificate.py | incremental/certificate.py (class → `ErrorCertificate`) |
| incremental/update.py | incremental/update.py (lazy-import gpu_incremental — §M6) |
| incremental/cache.py | incremental/cache.py |
| incremental/dependency_graph.py | incremental/dependency_graph.py |
| incremental/affected_region.py | incremental/affected_region.py |
| incremental/mesh_affected_region.py | incremental/mesh_affected_region.py |
| incremental/mesh_update.py | incremental/mesh_update.py |

### backends/
| old | new |
|---|---|
| backend/base.py | backends/base.py |
| backend/cpu_backend.py | backends/cpu.py |
| backend/gpu_backend.py | backends/gpu.py |
| backend/gpu_incremental.py | backends/gpu_incremental.py |

### sites/  (georef + scene build for Church Street)
| old | new |
|---|---|
| integration/coordinates.py | sites/church_street/coordinates.py |
| preprocessing/church_street_adapter.py | sites/church_street/scene_builder.py |
| (scattered site consts) | cities/church_street/city.yaml (lat/lon, CRS, origin, γ, weather, materials, SVF knobs) |

### extensions/  (provisional 2.1.0 terrain/tree + 3D viewer path — all behind validate-extensions)
| old | new |
|---|---|
| terrain/dtm.py · terrain_scene.py · terrain_solver.py · gpu_terrain.py | extensions/terrain/{dtm,scene,solver,gpu}.py |
| vegetation/tree.py · tree_scene.py · tree_solver.py · gpu_tree.py | extensions/vegetation/{tree,scene,solver,gpu}.py |
| integration/tmrt_3d.py | extensions/mean_radiant_temperature_3d.py (**FIX** divergent inversion → delegate to physics) |
| integration/utci_3d.py | extensions/utci_3d.py |
| integration/time_shadowing.py | extensions/time_shadowing.py (**FIX** fabricated parity_metric) |
| integration/terrain_loader.py | extensions/terrain/loader.py (**lazy factory**, reads city.yaml) |
| integration/tree_loader.py | extensions/vegetation/loader.py (**lazy factory**) |
| integration/tree_geometry_builder.py | extensions/vegetation/geometry_builder.py |
### placement/  (was optimization/; `two_panel`→`dual_panel`)
| old | new |
|---|---|
| optimization/parameters.py | placement/parameters.py |
| optimization/two_panel_parameters.py | placement/dual_panel_parameters.py |
| optimization/feasibility.py | placement/feasibility.py |
| optimization/two_panel_feasibility.py | placement/dual_panel_feasibility.py |
| optimization/objective.py | placement/objective.py |
| optimization/two_panel_objective.py | placement/dual_panel_objective.py |
| optimization/ledger.py | placement/evaluation_ledger.py |
| optimization/two_panel_ledger.py | placement/dual_panel_evaluation_ledger.py |
| optimization/surrogate.py | placement/surrogate_model.py |
| optimization/two_panel_surrogate.py | placement/dual_panel_surrogate_model.py |
| optimization/acquisition.py | placement/acquisition.py (**NHD** name — §5) |
| optimization/two_panel_acquisition.py | placement/dual_panel_acquisition.py (**NHD**; drop CAND_0063_SURR seed — §M10) |
| optimization/optimizer.py | placement/placement_solver.py |
| optimization/two_panel_optimizer.py | placement/dual_panel_placement_solver.py |
| optimization/surrogate_optimizer.py | placement/surrogate_placement_solver.py |
| optimization/validation.py | placement/candidate_validation.py |
| optimization/two_panel_validation.py | placement/dual_panel_candidate_validation.py |
| optimization/robustness.py | placement/robustness.py |
| optimization/robustness_plots.py | tools/robustness_plots.py |

### validation/  (golden/parity — distinct from placement/candidate_validation)
| old | new |
|---|---|
| benchmark/{harness,scenes,independent_reference,independent_audit,tightness,repeated_edits,baseline_comparison}.py | validation/… (independent_audit **FIX** hardcoded scaling) |
| benchmark/{aabb_vs_mesh_benchmark,mesh_certificate_audit,mesh_scaling_benchmark}.py | validation/mesh/… |
| validation/comparisons.py | validation/comparisons.py |
| validation/metrics.py | validation/metrics.py |

### pipelines/ + cli.py  (38 stages + run_/generate_ → 9 commands)
`build_scene · simulate · evaluate_edit · benchmark · optimize · validate_extensions · export_viewer · paper_artifacts · gates` (+ `cli.py`). Full legacy_stage_id→token registry: `pipelines/_legacy_registry.yaml` (DIAGNOSIS §I.1/I.2). Gate stages (19/24/blocked_gates) → `gates.yaml` + one parametrized test.
## 3. Identifier / symbol renames (apply package-wide, behaviour-preserving)
| concept | old (seen in code) | new |
|---|---|---|
| sky view factor | `svf`, `directional_visibility`, `num_azimuths` | `sky_view_factor`, `azimuth_count` |
| mean radiant temp | `tmrt`, `compute_tmrt` | `mean_radiant_temperature` (public API); `tmrt` ok as local |
| Tmrt tolerance | `tmrt_tolerance` | `tmrt_tolerance_k` |
| certificate bound | `b_t`, `predicted_bound` | `thermal_error_bound_k` |
| masks | `dirty_mask` / `clean_mask` | `dirty_mask` / `clean_mask` (unchanged) |
| certificate type | (certificate.py class) | `ErrorCertificate` |
| shade panel | `panel`, `ShadePanel?` | `ShadePanel` |
| two-panel family | `two_panel_*` | `dual_panel_*` |
| placement loop | `optimizer`, `two_panel_optimizer` | `placement_solver` / `dual_panel_placement_solver` |
| surrogate | `surrogate`, RF/ExtraTrees wrapper | `surrogate_model` |
| ledger | `ledger` | `evaluation_ledger` |
| acquisition | `acquisition` (LCB+EI κ2.0 / LCB κ1.5) | **NHD** `ucb_acquisition` vs `lcb_ei_acquisition` (§5) |
| units | bare floats | suffix `_m _k _c _deg _s _ms _w_m2` on fields/args |

## 4. KEEP VERBATIM (never renamed)
- **Status tokens** — every `STAGE_n_*`, `READY_FOR_*`, `ACCEPTED_FOR_RESEARCH`, `*_COMPLETE`, `*_PENDING`, `*_BLOCKED`, `SYNTHETIC_TERRAIN_ONLY`, `SOLARAEUS_PROJECT_COMPLETE_WITH_DOCUMENTED_LIMITATIONS`, `PUBLICATION_READY` (DIAGNOSIS §I).
- **Committed-artifact JSON keys** — `total_cells`, `max_abs_error_tmrt_k`, `reused_vs_recomputed`, `peak_gpu_vram_mb`, `effective_speedup`, etc.
- **IDs** — `BLR_SHADE_001`, `CAND_4196_SURR`, `CAND_0063_SURR`, tree IDs `T08`–`T13`.
- **Frozen dirs / inputs** — `church_street_preprocessing_20261006_224238`, `church_street_static_20261006_232110`, `..._handoff_v2`, `bengaluru_church_street_raw_sources_2026-10-07.zip` (dates exempt from the ban).

## 5. NHD naming decisions (need the user before STEP 3)
1. **`ucb_acquisition`** — code is LCB+EI portfolio (κ=2.0/1.5), paper says UCB (κ=1.96). Target name asserts UCB. → rename to `lcb_ei_acquisition` (truthful to code) OR keep `ucb_acquisition` and reconcile code/paper separately. **Do not let the name claim a method the code lacks.**
2. **`validation/` collision** — three things called "validation": golden/parity `validation/`, placement `candidate_validation`, and `extensions` parity. Proposed split above; confirm.
3. **`mean_radiant_temperature` vs `tmrt`** — public module named long-form, but the paper/artifacts/JSON keys use `tmrt`; keep `tmrt` in all serialized keys (KEEP VERBATIM) and as the local alias.
4. **`dual_panel` vs multi-panel** — scripts also say "multi_intervention"/"multi_panel"; confirm `dual_panel` is the intended canonical (code is 14-param = 2 panels).
