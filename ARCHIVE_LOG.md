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
