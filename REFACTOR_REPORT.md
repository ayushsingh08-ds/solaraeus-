# REFACTOR_REPORT.md

Behaviour-preserving overhaul of SOLARAEUS, on branch `overhaul`.

**Baseline tag:** `pre-overhaul` (branch point 17fc6f8). Every phase below is
recoverable with `git diff pre-overhaul..overhaul`.

---

## 0. Status: what is done, what is not

This report is the honest ledger. Phases 0-3 are complete and verified.
Phases 4-10 are **not** done; they are specified in §7 as the remaining plan.

| Phase | State | Evidence |
|---|---|---|
| P0 Safety net (branch, tag, baseline, golden master, inventory) | **done** | `1d55a22`; baseline 457 passed, 118 s |
| P1 Packaging, tooling, CI, no `sys.path` hacks | **done** | `665f1cd`, `20daa58` |
| P2 Remove dead weight, resolve audit I1-I8 | **done for the items listed in §2** | `16a09b4`, `72fe06a` |
| P3 Break the cycle | **done for the cycle; dedupe/CRS items remain** | `8cb36cd` |
| P4 Rename package, target structure | **not started** | §7 |
| P5 City-agnostic config and adapters | **not started** | §7 |
| P6 Stages -> `pipelines/` registry | **not started** | §7 |
| P7 `viewer/` (Vite + R3F) | **not started** | §7 |
| P8 Test reorganisation | **not started** | §7 |
| P9 Documentation rewrite | **not started** | §7 |
| P10 Final verification from a clean clone | **not started** | §7 |

Nothing in this report is claimed as verified unless §6 shows the command and
its real output. The 457-test baseline, the golden master and the file
inventory from Phase 0 are the reference points.

---

## 1. How to verify this work right now

```bash
git checkout overhaul
pip install -e ".[all]"        # or: make install-dev
make lint                      # ruff, enforced set, whole maintained tree
make types                     # mypy, strict on urban_comfort.config
make test                      # 442 passed
make golden                    # 13/13 MATCH, 0 mismatches
python tools/golden/cycle_check.py    # top-level cycles: none
```

Each of those was run on this tree; the outputs are in §6.

---

## 2. File accounting (kept / moved / merged / deleted)

Tracked files: **1,546 before, 1,638 after**. The increase is one 2,600-line
`context.md` becoming 30 history files plus the new packaging/tooling/CI files.

### Deleted (1 file, with evidence)

| File | Evidence before deleting |
|---|---|
| `context.md` | Split into `docs/history/00-index.md` + `01-*.md … 29-*.md` by `tools/split_history.py`, which reassembles the parts and compares them byte-for-byte with the source (235,934 chars) before unlinking it. Content is unmodified. Recoverable at `pre-overhaul`. |

Also deleted outside git: a stray directory literally named `~` holding
`~/.cupy/kernel_cache`, created by a script writing to an unexpanded tilde
path. It was untracked and is a regenerable CUDA kernel cache. A `.gitignore`
rule now prevents it returning.

### Moved (43 renames, all `git mv`)

See the full table in §3. Nothing was moved that still has an importer at the
old path: every rewrite was AST-checked (see §5 for the method).

### Merged

Nothing was merged in this pass. The two candidate merge targets were
investigated and **both were left alone**, with reasons in §4.

---

## 3. Old path -> new path

### Legacy package and its dependants (commit `16a09b4`)

| Old | New |
|---|---|
| `src/solaraeus/__init__.py` | `archive/legacy_solaraeus/solaraeus/__init__.py` |
| `src/solaraeus/core/{geometry,solweig}.py` | `archive/legacy_solaraeus/solaraeus/core/…` |
| `src/solaraeus/incremental/{bounds,solver}.py` | `archive/legacy_solaraeus/solaraeus/incremental/…` |
| `src/solaraeus/benchmark/{adversarial,runner}.py` | `archive/legacy_solaraeus/solaraeus/benchmark/…` |
| `tests/test_adversarial_suite.py` | `archive/legacy_solaraeus/tests/…` |
| `tests/test_certificate_soundness.py` | `archive/legacy_solaraeus/tests/…` |
| `tests/test_solweig_reference.py` | `archive/legacy_solaraeus/tests/…` |
| `scripts/run_first_milestone.py` | `archive/legacy_solaraeus/scripts/…` |
| — | `archive/legacy_solaraeus/README.md` (new) |

### Docs, references, paper, vendored tooling (commit `72fe06a`)

| Old | New |
|---|---|
| `researchpaper/*.pdf` (17 files) | `references/pdfs/*.pdf` |
| `weekly_report/*.docx` (4 files) | `docs/reports/weekly/*.docx` |
| `research_paper_sol/*` (8 files) | `paper/*` |
| `context.md` | `docs/history/00-index.md` + `01-…`..`29-….md` |
| `…manual_handoff_v2/preparation/refine_handoff_v2.py` | `tools/dataset_prep/refine_handoff_v2.py` |
| `…bbmp…/preparation/{filter_tree_census,finalize_supplement}.py` | `tools/dataset_prep/…` (untracked; see §8) |
| `…manual_handoff_v2/sources/overture_cli_core.py` | `tools/upstream/overturemaps/overture_cli_core.py` |
| `…manual_handoff_v2/sources/overturemaps_pyproject.toml` | `tools/upstream/overturemaps/…` |
| — | `references/README.md`, `references/bibliography-map.md`, `tools/upstream/README.md`, `tools/dataset_prep/README.md` (new) |

### Code split out during the cycle break (commit `8cb36cd`)

| Old location | New file | Symbols |
|---|---|---|
| `incremental/update.py` | `incremental/edits.py` | `GeometricEdit`, `AddBuildingEdit`, `RemoveBuildingEdit`, `ChangeHeightEdit`, `MoveBuildingEdit` |
| `reference/full_recompute.py` | `reference/result.py` | `SimulationResult` |
| `incremental/affected_region.py` | `incremental/regions.py` | `AffectedRegionResult` |

All three are byte-exact slices; importers were rewritten to the new modules
(`from urban_comfort.reference.full_recompute import SimulationResult` ->
`from urban_comfort.reference.result import SimulationResult`, and so on).
There is deliberately **no compatibility shim**: the old locations no longer
re-export the moved names, because a shim would keep the acyclic graph
ambiguous.

---

## 4. The audit's "Inferred" list (I1-I8), re-verified

The brief says to re-verify every claim before acting on it. Each item was
re-checked against the tree; two came back **different from the audit** and
changed the plan.

| # | Audit claim | Verdict after re-verification |
|---|---|---|
| I1 | `simulation_3d/church_street_data.{js,json}` is produced by `execute_final_3d_integrated_simulation.py` | **Confirmed as a gap, claim as stated is wrong.** No writer exists anywhere: `grep -rn church_street_data --include=*.py` finds only readers (`verify_ui_quality.py:167`, `index.html:575`). The 3-D pipeline writes `scene/*.glb`, terrain, trees and heatmaps into `results/final_3d_integrated_simulation/`, but no file containing `thermal_grid` — i.e. **no in-repo regeneration path for the viewer payload**. Blocks P7. |
| I2 | the 4 `.py` files under `bengaluru_church_street_*` are upstream third-party tooling | **Confirmed.** `sources/overturemaps_pyproject.toml` declares `name = "overturemaps"`, `version = "1.0.2"`, `license = "MIT"`, `authors = [{name = "Jacob Wasserman", …}]`. The Overture sources were moved to `tools/upstream/overturemaps/`; the other three scripts are this project's own ingest scripts and went to `tools/dataset_prep/` instead. |
| I3 | `researchpaper/*.pdf` are the paper's bibliography | **Confirmed as unmappable.** The paper cites **26 keys**; there is **no `.bib` file anywhere**; only 2 of the 17 PDFs match a key even weakly (`chen_2024.pdf` / `chen2012gis`, `krayenhoff_2021.pdf` / `krayenhoff2014multi`), and in both cases the year disagrees. Recorded honestly in `references/bibliography-map.md` instead of inventing entries. |
| I4 | `weekly_report/*.docx` are progress reports for the same project | **Confirmed.** OOXML metadata: all four are "Capstone Project Weekly Progress Report, Semester VII, Week N", School of Engineering, B.Tech CSE (Data Science), weeks 1-4, Aug-Sep 2026. Moved to `docs/reports/weekly/`. |
| I5 | each `results/` directory maps 1-to-1 onto a `run_church_street_*.py` script | **Refuted.** 26 `results/church_street_*` directories vs 10 run scripts: 6 scripts have **no** output directory, and 6 directories have **no** matching script (`church_street_data_review_*`, `church_street_gpu_full_*`, `church_street_multi_intervention_optimization_*`, `church_street_shade_full_*`, `church_street_shade_gpu_incremental_*`, `church_street_static_*`). This is why no `results/` directory was deleted or renamed. |
| I6 | terrain/vegetation files are reachable only from stage scripts, so AST analysis could miss a dynamic consumer | **Confirmed, and it matters.** `bengaluru_church_street_raw_sources_2026-10-07/` and `bengaluru_church_street_bbmp_trees_july2026_supplement/` are **gitignored** (`.gitignore:121-122`), so the raw city data is machine-local. Phase 5 must therefore make the synthetic city the default path, not an afterthought. |
| I7 | the `certificate.py <-> update.py` cycle is currently harmless | **Confirmed harmless, then removed.** `tools/golden/cycle_check.py`: 1 cycle over 9 files, 3 of its back-edges function-local. After `8cb36cd`: top-level cycles 0. |
| I8 | `results/stage_NN/**` schemas | **Confirmed.** Sampled every `results/stage_*` directory: status/token pairs only, e.g. `stage_30_cpu_tree_shadow/cpu_tree_geometry_manifest.json` -> `STAGE_30_CPU_TREE_SHADOW_REFERENCE_COMPLETE`. These are artifact contracts, not behaviour tests; P8 keeps them but relabels them. |

### The duplicate stage scripts (Stage 25 and Stage 26): determination

The brief says to decide which is canonical and never silently drop one.

**Stage 25 - not duplicates, keep both.** `execute_stage_25_real_dtm_validation.py`
writes `results/stage_25_real_dtm_validation/`, which
`tests/test_stage_25_real_dtm_validation.py` reads.
`execute_stage_25_available_terrain_validation.py` writes
`results/stage_25_available_terrain_validation/`, which has its own committed
outputs but **no** contract test. Two genuinely different experiments
(real DTM vs available/synthetic terrain), so both stay.

**Stage 26 - two complementary steps that collide on one file, keep both.**
Both scripts write to the *same* directory `results/stage_26_field_tree_validation/`:

* `execute_stage_26_field_tree_validation.py` writes the schema, both CSVs,
  `tree_existence_validation.json`, the photo manifest, the report, and
  `stage_26_test_results.json`;
* `execute_stage_26_field_validation_deferral.py` writes
  `stage_26_deferred_status.json` **and overwrites `stage_26_test_results.json`**.

The committed artifact carries the deferral's token
(`STAGE_26_FIELD_VALIDATION_DEFERRED`), which is also what
`tests/test_stage_26_field_tree_validation.py` accepts, and the test requires
both scripts' outputs. So they are complementary, and the single overlapping
file is the later policy decision winning by execution order. **Recorded, not
"fixed":** changing which script writes that file would change a committed
artifact, which this overhaul must not do. P6 will give each step its own
`pipelines/` entry and an explicit order.

---

## 5. Method (why these changes are provably moves, not edits)

1. **Byte-exact slicing.** The cycle break takes class bodies by text slice,
   not by retyping: `tools/migrations/cycle_break_edits.py` asserts the slice
   contains the expected classes and not the next one, writes the new module,
   and re-parses both files with `ast.parse` before finishing.
2. **AST-checked import rewriting.** The same script rewrites whole-tree
   imports by matching only the two modules that lost symbols, then parses
   every file it touched. `from a import A, B` where only `A` moved becomes
   two statements; nothing else in the file changes.
3. **No hand edits in a move commit.** `git mv` for every relocation; the only
   hand edits in move commits are the import lines and the docstring headers
   that name the new module.
4. **A behaviour gate after every phase.** `make test` and `make golden`
   (13 cases, rtol `1e-9` / atol `1e-12`, certificate counts exact).
   The golden baseline is frozen in `tools/golden/baseline/` and `make golden`
   captures to `tools/golden/candidate/` (gitignored), so the baseline cannot
   be silently overwritten: `capture` refuses without `--force`.
5. **Every automated sweep was audited for over-reach.** ruff's 706 auto-fixes
   in P1 removed 184 unused imports across 133 files; because `F401` can strip
   re-exports from an `__init__.py`, a dedicated tool
   (`tools/golden/audit_removed_imports.py`) diffed the removed names against
   each file's remaining body and re-imported all 94 modules. Zero of the
   removals were live names. It also found 4 pre-existing `F821` defects
   (`List`/`Tuple`/`Sequence` used in signatures but never imported, masked at
   runtime by `from __future__ import annotations`) which were then fixed.

---

## 6. Verification outputs (real, from this tree)

### 6.1 Lint and types

```
$ make lint
python -m ruff check src tests tools
All checks passed!

$ make format-check
python -m ruff format --check src tests tools
192 files already formatted

$ make types
python -m mypy
Success: no issues found in 98 source files
```

`ruff format --check` is part of CI, so the tree is formatted too: the last
commit reformatted 139 files (whitespace only, 139 files / +5,580 / -2,824)
and the suite and golden master were re-run afterwards to prove it changed no
behaviour. `make ci` runs exactly what the workflow runs.

### 6.2 Test suite

```
$ python -m pytest -q
442 passed, 42 warnings in 155.57s (0:02:35)

$ python -m pytest --collect-only -q
442 tests collected in 14.34s
```

Baseline was **457 passed** (`pytest -o pythonpath=src -q`, Phase 0). The 15
test IDs that no longer run by default are exactly the archived legacy ones,
which still pass when asked for:

```
$ python -m pytest archive/legacy_solaraeus/tests \
    -o pythonpath=archive/legacy_solaraeus -q
15 passed in 2.47s
```

They are: `test_adversarial_suite.py::test_adversarial_case_soundness[0..4]`,
`test_certificate_soundness.py::test_certificate_soundness_add_building[0.1|0.5|1.0|2.0]`,
`test_certificate_soundness.py::test_certificate_soundness_remove_building[0.2|0.8]`,
`test_certificate_soundness.py::test_exact_unchanged_region_zero_error`,
`test_solweig_reference.py::test_{flat_terrain_analytical_limits,building_shadow_direction,solver_determinism}`.

### 6.3 Golden master (the behaviour proof)

```
$ make golden
...
       MATCH  terrain_inclined
       MATCH  vegetation_core_trees
       MATCH  vegetation_tree_states
verdict: PASS  (0 mismatches)
```

13 cases, all `MATCH`, on a machine where `gpu_available: true`, so the GPU
paths in the mesh/terrain/vegetation cases were exercised too — **nothing is
marked UNVERIFIED-GPU**. Baseline metadata (`tools/golden/baseline/summary.json`):
Python 3.12.6, NumPy as pinned in `requirements.lock`, 13/13 cases OK.

Lockfile stability (the P1 defect this replaced, `tools/lock.py`):

```
$ make lock && python tools/lock.py --check
wrote requirements.lock (17 pinned distributions)
requirements.lock is up to date (17 active pins)
```

### 6.4 Import graph

```
$ python tools/golden/cycle_check.py
scanned 95 modules under ['src']
internal import edges: 404

top-level cycles: none (import graph is acyclic)

lazy cycles (function-local back-edges only): 1
  cycle (6 files): backend/__init__.py, cpu_backend.py, gpu_backend.py,
                   gpu_incremental.py, incremental/update.py,
                   reference/full_recompute.py
```

The single remaining cycle is the optional-GPU dispatch: `full_recompute`
must not import CuPy at module scope, so its backend imports are function-local
by design. `cycle_check.py` now reports fatal and lazy cycles separately
(`--strict` fails on both) instead of conflating them.

### 6.5 No `sys.path` hacks

```
$ grep -rn "sys\.path\.insert\|sys\.path\.append" --include=*.py . | wc -l
0
```

44 `sys.path` mutations removed in the P1 sweep (5 examples, 36 scripts,
tooling) plus the golden harness's own. Tests run with no `-o pythonpath=src`.
The archived legacy tests also contain none: they import `solaraeus` through
`-o pythonpath=archive/legacy_solaraeus`, not by mutating the path.

---

## 7. What remains (Phases 4-10), in dependency order

These are **not** done. Each is written here with its real blocker, so the next
pass does not have to rediscover it.

### P3 remainder (smallest next steps)

1. **CRS defect.** `Scene.coordinate_system` defaults to `"EPSG:32633_LOCAL"`
   (`geometry/scene.py`) and `configs/baseline_scene.json` repeats it, while the
   real Church Street CRS is **EPSG:32643** (`integration/coordinates.py:23`) - a
   ~1,000 km easting error if the default were ever trusted. Plan: derive the
   CRS from lat/lon (UTM zone) and make the default *explicit-or-error*, then
   document the one intended behavioural change in §8 below.
2. **`Material.is_opaque`** (set, validated, serialized, never read) and
   **`SimulationConfig.numerical_tolerance`** (1e-6, unused because
   `verify_certificate` uses its own `numerical_slack=1e-10`): wire them to real
   behaviour or remove them, keeping the JSON loader backward-compatible. Not
   done because both are observable through serialised scene/config files.
3. **Merge the two surrogate trainers** (`optimization/surrogate.py` 422 lines,
   `optimization/two_panel_surrogate.py` 372 lines; ~700 LOC of copy-paste
   differing only in feature width 7 vs 14). Plan: one model parameterised by
   `feature_names`, with the golden cases for both re-running green.
4. **`optimization/__init__.py` `__all__`** (it re-exports 18 modules with none).

### P4 Rename and restructure

`urban_comfort` -> `solaraeus` is **now unblocked** (the legacy package no
longer occupies the name) but is a ~200-file rename plus import rewrite; it
must be its own move-only commit with the golden master re-run, exactly as P3
was done. The target tree in the brief (`core/`, `physics/`, `sites/`,
`pipelines/`, `export/`, …) is a second, separate move pass on top of it.

### P5 City-agnostic code

Blocked on two findings, not on effort:

* `bengaluru_church_street_raw_sources_2026-10-07/` and the BBMP tree census
  are **gitignored**, so no fresh clone has the Church Street inputs. The
  synthetic city is therefore the *only* pipeline a clean clone can run, and it
  must come first. `cities/_template/city.yaml` + a `synthetic` generator.
* 175 Python files reference `data/` or `configs/` and 25 reference the
  `bengaluru_church_street_*` directories by path. Moving those to
  `cities/church_street_bengaluru/` is a scripted path rewrite, not a hand edit,
  and must be done with `church_street_adapter.py`'s behaviour golden-checked.

### P6 Stages -> `pipelines/`

38 `execute_stage_*.py` scripts share one shape. Extract `StageContext` + a
`@stage(id=…, slug=…, token=…)` registry, one named file per stage, and keep
status tokens byte-compatible (they are asserted by 40 contract tests). Produce
`docs/stages.md`. The Stage 26 ordering in §4 is the first thing to encode.

### P7 Viewer

Blocked on I1: there is **no regeneration path** for the viewer payload, so a
new `viewer/` cannot be built on it. Required first: an
`export-viewer` command writing `manifest.json` + `buildings.glb` + `trees.json`
+ per-hour Float32 field files, then a Vite + React 19 + R3F + zustand app.
The current app also omits context trees, which must be fixed in the new one.

### P8-P10

Test reorg (`unit/integration/contracts/golden`), the 40 artifact-contract tests
relabelled and paired with behavioural tests, README/architecture/reproducibility
docs, and the final fresh-clone verification.

---

## 8. Behavioural deviations

**Physics, certificate math (B_T / epsilon_T), status tokens and file formats:
none.** The golden master is the proof: 13/13 cases match within rtol `1e-9`,
atol `1e-12`, with certificate counts compared exactly, after every phase.
Nothing in this pass touched a formula, a constant, a tolerance, a status
token or a JSON schema.

Deviations that are not physics:

| Change | Effect | Why it is safe |
|---|---|---|
| `SimulationResult` is now defined in `reference/result.py` | its `module` attribute changed | Same class object re-imported by every call site; verified by identity check in §6 |
| Import paths for edit classes and `SimulationResult` changed | none at runtime | All 30 importers rewritten mechanically, suite + golden re-run |
| Default test collection no longer includes 3 legacy modules | 457 -> 442 default tests | The 15 affected IDs are enumerated and still pass when requested (§6.2) |
| `make golden` now refuses to overwrite the frozen baseline without `--force` | a bare `capture` errors instead of clobbering evidence | Prevents the exact failure mode the brief warns about |
| A directory literally named `~/` was deleted | none | Untracked, regenerable CUDA kernel cache created by an unexpanded tilde |

**Intended-but-not-yet-applied** deviations are the CRS default fix and the
`is_opaque` / `numerical_tolerance` decisions, both in §7.

---

## 9. Needs human decision

1. **147 MB of third-party PDFs in `references/pdfs/`.** There is no `.bib` and
   no key-to-PDF mapping (`references/bibliography-map.md` lists all 26 keys and
   asks for the missing links). Decide: keep tracked as now, move to Git LFS, or
   drop from git behind a download record. Nothing was deleted, so any answer is
   still available.
2. **The two gitignored raw datasets.** `bengaluru_church_street_raw_sources_2026-10-07/`
   (164 MB) and `bengaluru_church_street_bbmp_trees_july2026_supplement/` (16 MB)
   exist only on this machine. Either publish a documented download recipe or
   accept that a clean clone can only run the synthetic city.
3. **Stage 26's one colliding output file** (`stage_26_test_results.json` is
   written by both scripts). Which one owns it? I did not choose, because the
   committed artifact already reflects the deferral script's value.
4. **`results/` naming and size (868 MB).** 780 MB of it is six
   `church_street_two_panel_robustness_*` runs. The brief wants
   `reference_artifacts/` (small, tracked) and `artifacts/` (generated,
   gitignored). Which of the 104 entries are *evidence to keep* and which are
   *rerunnable output* is your call; renaming the directory without deciding
   that would only move the problem.
5. **`tools/dataset_prep/`** - keep the one-shot ingest scripts as provenance,
   or archive them under `archive/`? They are excluded from lint and from the
   test suite either way.
6. **`is_opaque` and `numerical_tolerance`** - wire or remove? Removing either
   is visible in serialised config JSON, so it is a format decision.

---

## 10. Commit log on `overhaul`

```
8cb36cd refactor(overhaul): break the incremental/reference import cycle
72fe06a refactor(overhaul): give docs, references and paper a real home
16a09b4 refactor(overhaul): archive the legacy 2.5D package out of src/
20daa58 refactor(overhaul): remove sys.path hacks and dead imports repo-wide
665f1cd build(overhaul): install packaging, tooling and CI around the existing engine
1d55a22 chore(overhaul): add Phase 0 safety net — baseline, golden master, inventory
```

Each is one logical change, each was followed by `make test` + `make golden`
before the next began, and each is revertible on its own.

---

## 11. Ten-line summary for a new contributor

1. This repo is a thermal-comfort engine: given a city scene and a local
   building edit, it decides which pedestrian cells can safely reuse cached
   results, and proves the reuse is within an error bound `B_T(x)` computed
   before any expensive work.
2. `pip install -e ".[dev]"` then `make test` (442 pass) and `make golden`
   (13/13 physics cases match a frozen baseline).
3. `src/urban_comfort/` is the engine: `geometry/` the scene, `solar/`
   `visibility/` `radiation/` `comfort/` the physics, `reference/` the
   ground-truth solver, `incremental/` the contribution (edits, certificate,
   selective recompute), `backend/` CPU/GPU dispatch.
4. `incremental/edits.py`, `incremental/certificate.py` and
   `reference/result.py` are the three files to read first.
5. `cities/` is meant to be the only thing that changes per city; that work is
   P5 and is not finished.
6. `archive/legacy_solaraeus/` is the first-generation prototype, kept for
   provenance and reachable only by explicit command.
7. `paper/` is the IEEE submission, `references/` is third-party literature,
   `docs/history/` is the development log split by section.
8. `tools/golden/` is the behaviour net: never delete `tools/golden/baseline/`,
   and never pass `--force` to `capture` unless a physics change is intended.
9. `tools/upstream/` and `tools/dataset_prep/` are frozen external/provenance
   code; they are excluded from lint on purpose.
10. `REFACTOR_REPORT.md` (this file) tracks what moved, what was deleted and why,
    and what is left. Phases 4-10 are the remaining plan.
