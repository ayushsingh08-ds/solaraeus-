# Archived legacy package: `solaraeus` (2.5D prototype)

This directory holds the **first-generation** implementation of the
thermal-comfort engine, preserved verbatim so the work is never lost, and
moved out of `src/` so the name `solaraeus` is free for the current package.

## What is in here

| Path | What it is |
|---|---|
| `solaraeus/` | The legacy 2.5D prototype: `core/solweig.py` (its own SOLWEIG re-implementation), `core/geometry.py` (`UrbanGrid`, `AddBuilding`, `RemoveBuilding`), `incremental/bounds.py` (its own `compute_svf_decay_bound`), `incremental/solver.py`, `benchmark/` |
| `tests/` | The 3 tests that exercised only the legacy package, moved here so the default `pytest` run (`testpaths = ["tests"]`) does not collect them |
| `scripts/run_first_milestone.py` | The Milestone-1 experiment runner, which imports the legacy package |

## Why it is archived rather than deleted

`PROJECT_STRUCTURE.md` §9.2 records it as a second, complete implementation of
the same idea (1,163 LOC). Deleting it would destroy an independent lineage of
the method. It is unreachable from the engine: verified with

```
grep -rn "^\s*\(import solaraeus\|from solaraeus\)" --include=*.py .
```

which finds importers in **only** `archive/legacy_solaraeus/tests/*` and
`archive/legacy_solaraeus/scripts/run_first_milestone.py` — nothing in
`src/`, `examples/` or the surviving test suite. `src/urban_comfort/cli.py`
mentions the string `solaraeus`, but only as the *distribution/console-script*
name, not as an import.

## How to run the archived tests

They are not part of the default run and are not covered by CI. To run them
anyway, put this directory on the import path:

```
python -m pytest archive/legacy_solaraeus/tests -o pythonpath=archive/legacy_solaraeus
```

## Provenance

Recoverable as committed under the `pre-overhaul` tag at
`src/solaraeus/`, `tests/test_adversarial_suite.py`,
`tests/test_certificate_soundness.py`, `tests/test_solweig_reference.py`
and `scripts/run_first_milestone.py`.
