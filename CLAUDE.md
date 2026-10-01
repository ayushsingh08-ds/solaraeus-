# Solaraeus

A 3D urban microclimate digital twin: a Python 3.11 science pipeline (`src/data` → `src/geometry` → `src/physics` → `src/visualization`, orchestrated by `scripts/`) plus a React 19 + Three.js viewer in `frontend/`. `REPRODUCIBILITY.md` has the full run instructions; `pytest tests/ -v` is the check.

## The Idea Roast Council

Four subagents in `.claude/agents/` — believer, skeptic, investor, judge — roast an idea and persist the ruling in `roasts/`. Run `/roast <idea>`; resume an old decision with `/roast-recall`. `roasts/` is the council's only memory.

Rulings are never edited after the fact: a changed mind is a new, higher-numbered ruling that supersedes the old one. Keep `roasts/INDEX.md` in sync with `python scripts/roast_index.py`, and note that `tests/test_roast_log.py` fails on a malformed ruling or a stale index.

## The Planning Tournament

Four planners in `.claude/agents/` — planner-a through planner-d — each research the whole project from a different strategy family, and `planner-arbiter` scores every round, eliminates exactly one plan per round, and finalizes the survivor as `plans/PLAN.md`. Run `/plan`; recall the trail with `/plan-recall`.

Plans are never deleted or rewritten: a changed mind is a new round, not an edit. Keep `plans/INDEX.md` in sync with `python scripts/plan_index.py`, and note that `tests/test_plan_log.py` fails on a malformed plan, a stale index, or a broken trail. The tournament is finished — `plans/PLAN.md` (strategy family `data-scarcity-first`) is the spec for the next build phase.
