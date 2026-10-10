# `tools/upstream/` — vendored third-party tooling

Code here was written by **other projects**. It is kept only so the dataset
acquisition steps in this repository can be reproduced and audited; the engine
never imports it.

| Path | Origin | Licence |
|---|---|---|
| `overturemaps/overture_cli_core.py` | [Overture Maps](https://overturemaps.org) Python tooling (`overturemaps` distribution) | MIT |
| `overturemaps/overturemaps_pyproject.toml` | the upstream `pyproject.toml` this file was copied from — it is the licence/provenance record, because the upstream `LICENSE` file itself was not vendored | MIT |

## Attribution

`overturemaps_pyproject.toml` declares:

```
name = "overturemaps"
version = "1.0.2"
license = "MIT"
authors = [{name = "Jacob Wasserman", email = "jwasserman@meta.com"}]
```

That file is the licence record for `overture_cli_core.py`. If you re-vendor
or upgrade this file, copy the upstream `LICENSE` alongside it.

## Rules for this directory

1. Do not import anything here from `src/` — it is not a runtime dependency.
2. Do not modify vendored files; if a change is needed, record it in
   `overturemaps/CHANGES.md` instead.
3. Project-authored dataset scripts belong in [`../dataset_prep/`](../dataset_prep/),
   not here.
