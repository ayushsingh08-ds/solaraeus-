# ARCHIVE_LOG.md — Track-1 archival evidence

Behaviour-preserving cleanup. Nothing here is deleted irrecoverably: the
annotated tag **`pre-cleanup`** (b9d5937) captures the entire pre-cleanup tree.
Recover any archived path with:

```bash
git checkout pre-cleanup -- <path>      # or: git show pre-cleanup:<path>
```

KEEP TEST (why a file may be archived): *a file stays only if (a) a CLI command,
example, or test imports it, or (b) it is needed to reproduce a number in the
paper. Everything else is archived with evidence.* Golden-master
(`tools/golden_master/compare.py`) is re-run after each batch and must stay GREEN.

---

## Batch 1 — "blocked-gates" lineage (stages 27–38) · NHD #3

**Finding.** Two script lineages targeted stages 27–38. The committed, substantive,
test-guarded, paper-cited artifacts carry the `*_COMPLETE` / documented-limitation
status tokens and are produced by the individual `execute_stage_29..38_*.py` scripts
and the `available_terrain` stage-27/28 scripts — **these are the contract and are
kept**. A competing script, `execute_stages_27_to_38_blocked_gates.py`, wrote a
parallel `real_*` / `*_BLOCKED` narrative. For every file both lineages write, the
*committed* content is the COMPLETE version (the keeper test passes against it), so
the blocked-gates lineage did **not** produce the committed contract. Its only
committed footprint is wholly-BLOCKED dirs and a few empty stub files that contradict
their COMPLETE siblings and are referenced by nothing.

**Correction to prior plan.** `tests/test_stages_27_to_38_gates.py` is **kept**, not
archived: it asserts the COMPLETE/documented-limitation tokens of the *winning*
artifacts (`tree_geometry_scene_manifest.json`, `stage_NN_test_results.json`,
`calibration_status.json`, `FINAL_PROJECT_COMPLETION_STATUS.json`) and passes (6/6).

| archived path | what it was | status token | evidence it is safe to archive |
|---|---|---|---|
| `scripts/execute_stages_27_to_38_blocked_gates.py` | losing-lineage driver | emits `*_BLOCKED` | no importer / CI / test; only docs name it |
| `results/stage_27_real_terrain_cpu_validation/` (7 files) | BLOCKED variant of stage-27 | `STAGE_27_BLOCKED` | superseded by `stage_27_available_terrain_cpu_validation/` (`*_COMPLETE`, keeper-tested); not paper-cited |
| `results/stage_28_real_terrain_gpu_validation/` (10 files) | BLOCKED variant of stage-28 | `STAGE_28_BLOCKED` | superseded by `stage_28_available_terrain_gpu_validation/` (`*_COMPLETE`, keeper-tested); not paper-cited |
| `results/stage_29_level1_tree_geometry/approved_tree_geometry.json` | empty stub (`approved_trees: []`) | `STAGE_29_BLOCKED` | contradicts sibling `approved_provisional_tree_geometry.json` (COMPLETE); read by nothing |
| `results/stage_29_level1_tree_geometry/tree_geometry_visualizations/README.md` | "Visualizations Blocked" note | — | sits beside the real `core_trees_elevation_profile.svg`; read by nothing |
| `results/stage_30_cpu_tree_shadow/cpu_tree_terrain_regression.json` | empty stub | `STAGE_30_BLOCKED` | contradicts sibling `cpu_tree_available_terrain_regression.json` (COMPLETE); read by nothing |

Verified before archiving: no reference in `tests/` (besides the kept gates test, which
reads only the COMPLETE siblings), `src/`, `examples/`, kept `scripts/`, or
`research_paper_sol/`. Keeper test green; golden-master GREEN after this batch.

---

## Batch 2 — superseded stage 25/26 lineages · NHD #3 (Decisions 2 & 4)

Note on Decision 4 ("retarget the stage 25/26 tests before archiving"): both stage tests
are **artifact readers**, not script runners — neither imports a `scripts/` module (they
read committed `results/` dirs). So there is no script target to retarget; each test
already reads the *kept* lineage's artifacts. No retarget was required.

### Stage 26 — Decision 2 (user: "deferral script authoritative; archive the other with a note")

| archived path | what it was | evidence it is safe to archive |
|---|---|---|
| `scripts/execute_stage_26_field_tree_validation.py` | PENDING-track producer (`STAGE_26_FIELD_VALIDATION_PENDING`) | orphan (no importer); the committed `results/stage_26_field_tree_validation/` already carries the deferral record (`stage_26_deferred_status.json` = `STAGE_26_FIELD_VALIDATION_DEFERRED`); `tests/test_stage_26_field_tree_validation.py` is deferral-tolerant and passes |

**Note (reproducibility):** the committed stage-26 dir is **co-produced**. `field_observation_schema.json`,
`tree_existence_validation.json`, `field_photo_manifest.json` and the tree CSVs originate from the
now-archived PENDING script; `stage_26_deferred_status.json` (the authoritative DEFERRED record) and
`stage_26_test_results.json` come from the kept `execute_stage_26_field_validation_deferral.py`. All
committed files are **kept** as test-guarded evidence; only the PENDING *script* is retired. Regenerating
the schema/existence/photo-manifest files is retired with it (recover the script via `pre-cleanup`).

### Stage 25 — evidence-derived · **corrects the earlier plan line**

The earlier plan named `stage_25_real_dtm_validation` as the one to archive. That is **reversed**:
`stage_25_real_dtm_validation/` is the **contract** — `tests/test_stage_25_real_dtm_validation.py`
asserts its `STAGE_25_SYNTHETIC_TERRAIN_ONLY` / `REGIONAL_REFERENCE_ONLY` tokens, and the paper's
limitations declaration (`research_paper_sol/solaraeus.tex:484`, `FABDEM_REGIONAL_REFERENCE_ONLY`) rests
on it. It is **kept**. The unreferenced duplicate is archived instead:

| archived path | what it was | evidence it is safe to archive |
|---|---|---|
| `scripts/execute_stage_25_available_terrain_validation.py` | duplicate producer | orphan (no importer) |
| `results/stage_25_available_terrain_validation/` | duplicate run (`APPROVED_AS_REGIONAL_REFERENCE_ONLY`) | same 8-file set as the kept `stage_25_real_dtm_validation/`, whose richer artifact subsumes both facets (regional-reference-only **and** not-street-scale); referenced by no test, paper, src, or kept script |

Both stage tests green after this batch; golden-master GREEN.

---

## Batch 3 — legacy SOLWEIG oracle relocated · Decision 1

**Move (not a deletion; tracked as git renames, fully reversible).** The 7-file legacy
SOLWEIG reference engine `src/solaraeus/` was a name-collision blocker: it occupied the
`solaraeus` package name the live engine (`urban_comfort`) must take. It is a
deterministic reference oracle used only by tests, so it becomes a test-only fixture:

| from | to |
|---|---|
| `src/solaraeus/{__init__,core/geometry,core/solweig,incremental/bounds,incremental/solver,benchmark/adversarial,benchmark/runner}.py` | `tests/oracle/legacy_solweig/…` (same tree) |

- Internal absolute imports rewritten `solaraeus.*` → `legacy_solweig.*` (5 modules).
- Oracle tests retargeted `from solaraeus.*` → `from legacy_solweig.*`:
  `tests/test_solweig_reference.py`, `tests/test_certificate_soundness.py`,
  `tests/test_adversarial_suite.py` (the independent cross-check — kept).
- New `tests/conftest.py` puts `tests/oracle/` on `sys.path` so `import legacy_solweig`
  resolves without shipping it. The `solaraeus` name is now free in `src/`.
- Not touched: `tests/test_final_3d_scene_geometry.py` names the committed artifact
  `solaraeus_integrated_scene.glb` (KEEP VERBATIM — an artifact filename, not an import).

**Archived (git-rm, recover via `pre-cleanup`).**

| archived path | what it was | evidence it is safe to archive |
|---|---|---|
| `scripts/run_first_milestone.py` | `run_`-prefixed Milestone-1 demo driving the legacy oracle | orphan — imported by nothing; named only in docs (DIAGNOSIS / PROJECT_STRUCTURE / context); not a test/example/CLI target and reproduces no paper number (paper numbers come from the `urban_comfort` stages, not this legacy demo) |

Verified: 15 oracle tests pass (unchanged from baseline); full suite still collects
(457 tests, no import errors); golden-master GREEN (4/4, max|diff|=0.0).

---

## Batch 4 — root-folder clutter · user-directed hard delete

**Scope.** User instruction: "clear the root folder to have final clean repo" → chosen
policy "hard delete clutter." Three top-level entries fail the KEEP TEST on **both**
limbs — no import/read from `src/ tests/ examples/ tools/` (verified by grep: zero
hits), and they reproduce no paper number. Recovery anchor for this batch is the
annotated tag **`snapshot-pre-root-clear`** (9a7cd36), capturing the entire tree
immediately before this deletion:

```bash
git show snapshot-pre-root-clear:<path>        # recover a file
git checkout snapshot-pre-root-clear -- <path> # restore into the tree
```

| archived path | what it was | size | evidence it is safe to archive |
|---|---|---|---|
| `researchpaper/` (17 files) | external cited-literature PDF library | 147 MB | distinct from `research_paper_sol/` (the paper); `solaraeus.tex` cites via `\usepackage{cite}` keys that do not match these filenames and has no `\bibliography` path to them; zero refs in src/tests/examples/tools; reproduces no number |
| `weekly_report/` (4 files) | weekly progress `.docx` reports | 296 KB | zero refs anywhere in code; no paper linkage |
| `context.md` (1 file) | conversation / working-context dump | 236 KB | zero refs anywhere in code; no paper linkage |

**Kept despite looking like clutter (push-back on over-deletion).** `scripts/`,
`research_paper_sol/`, `PAPER_TRACE.md` kept under rule (b): `scripts/` is the
generation pipeline that reproduces every `results/` artifact and the paper figures;
`PAPER_TRACE.md` is the reproduction map the KEEP TEST names. `results/`, `data/`,
`configs/`, `bengaluru_church_street_manual_handoff_v2/` kept under rule (a) (read by
src loaders + tests + examples + tools; the handoff dir is scene_builder's default
`handoff_dir`). `README.md` kept as the project entry doc. `DIAGNOSIS.md`,
`NAMING_MAP.md`, `PROJECT_STRUCTURE.md`, `simulation_3d/` retained pending the final
STEP-4 sweep (active cleanup working-docs / paper §VI viewer component); recoverable
via the tag if dropped later.

Verified: grep of `src tests examples tools` for the three names = 0 hits;
golden-master GREEN (4/4, max|diff|=0.0) after this batch.
