# `tools/dataset_prep/` — project-authored dataset scripts

These scripts were used **once** to turn downloaded upstream datasets into the
review-ready handoff folders that now live under `cities/church_street_bengaluru/`.
They are kept as provenance: the brief for this overhaul forbids deleting
content, and these record exactly how the Church Street inputs were assembled.

They are **not** part of the engine, are not imported by `src/`, and are not
run by the test suite or CI. They expect the raw downloads to be present and
were written against absolute paths from the machine that produced the handoff,
so they are not expected to run unmodified elsewhere.

| Script | What it produced | Inputs it expected |
|---|---|---|
| `refine_handoff_v2.py` | the revised Church Street manual handoff (`building_height_review.csv`, `analysis_domains.json`, provenance records) | Overture/OSM/Google height pulls, FABDEM terrain |
| `filter_tree_census.py` | the BBMP 2026-07 tree census subset inside the study boundaries | BBMP OpenCity census download |
| `finalize_supplement.py` | the tree-supplement package (`SHA256SUMS.txt`, licensing notices, download record) | the filtered census |

## Status

These are **one-shot historical scripts**. If a city needs a repeatable ingest
path, that belongs in `src/solaraeus/sites/adapters/` (see
`docs/adding-a-city.md`), not here. Listed under "Needs human decision" in
`REFACTOR_REPORT.md`: keep as provenance, or move to the archive.
