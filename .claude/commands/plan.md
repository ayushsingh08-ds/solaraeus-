---
description: Run the planning tournament — competing planners each produce a researched plan for the whole project, one is eliminated per round, and the survivor becomes plans/PLAN.md.
argument-hint: [the brief, or a path to a file containing it — leave blank for plans/BRIEF.md]
allowed-tools: Read, Grep, Glob, Write, Edit, Agent, Task, Bash, WebSearch, WebFetch
---

Run the planning tournament on the brief in `$ARGUMENTS`.

Four planners — `planner-a` through `planner-d` — share one remit and compete on the strategy combination each invents. Every round eliminates exactly one. The last plan standing becomes `plans/PLAN.md`.

## Step 1 — Resolve the brief

- If `$ARGUMENTS` is non-empty, that is the brief. If it names a file path, read the file and use its contents.
- If it is empty, read `plans/BRIEF.md`. HTML comments and italic guidance text are not briefs.
- If there is no brief anywhere, ask me for one in a single question and stop. Never invent a project to plan.

## Step 2 — Determine the round

Read `plans/INDEX.md` and `plans/SCORES.md`. Round 1 has four planners; every later round has exactly one fewer, and the planner eliminated in the previous round does not compete again. If the tournament has already finished (`plans/PLAN.md` exists), say so and ask whether to start a fresh tournament in a new round folder rather than silently overwriting a finished one.

## Step 3 — Run the round

Delegate to the planners that are still competing — in round 1 that is all four: `planner-a`, `planner-b`, `planner-c`, `planner-d`; in every later round it is the survivors only — one at a time, and give each one:

- the brief,
- the round number and the path it must write to (`plans/r<N>/<planner>.md`),
- the strategy families already claimed this round, so it can pick a different one,
- and, for rounds after the first, the path to its own previous plan plus the eliminated plan it must absorb.

Each planner must read `plans/TEMPLATE.md` and produce a plan that satisfies it, with a sourcing ledger where every claim has a URL and an access date or is tagged `unverified`.

## Step 4 — Review and eliminate

Hand the round to `planner-arbiter`. It anonymizes the plans, enforces strategy diversity, scores every plan on the rubric with an evidence line per score, writes the round into `plans/SCORES.md` with a written justification for the elimination, and marks the eliminated plan's own frontmatter `eliminated`.

## Step 5 — Finalize when one remains

When a single planner survives, have the arbiter compose `plans/PLAN.md` from the surviving plan — including the rejected alternatives and the red-team notes from the three eliminated planners.

## Step 6 — Close the loop

Run `python scripts/plan_index.py --check`. If it reports drift, fix it the reliable way: `python scripts/plan_index.py` regenerates `plans/INDEX.md` from the round folders, and any remaining complaint is a real structural problem in the record, not a formatting one.

Then report in at most six lines: the round, who was eliminated and on which axis, who is left, the current leader's strategy family, and the path to the plan the winner would produce.
