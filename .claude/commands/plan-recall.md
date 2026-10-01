---
description: Recall the state of the planning tournament — which round it reached, what each planner proposed, who was eliminated and why, and what the surviving plan says.
argument-hint: [planner name, round number, or a keyword — leave blank for the whole trail]
allowed-tools: Read, Grep, Glob
---

Recall the planning tournament's record for `$ARGUMENTS`.

1. Read `plans/INDEX.md`. If `$ARGUMENTS` is empty, list every round: the planners that competed, each one's strategy family and one-line thesis, and who was eliminated.
2. If `$ARGUMENTS` names a planner, read that planner's files across every round and report how its plan changed — what it absorbed, what it added, and which round it left in.
3. If it names a round number, read that round's plans and its `plans/SCORES.md` section, and report the scores with their evidence lines and the elimination justification.
4. Otherwise match it against strategy families and theses, and read the plans that match. If several match, say which is which.
5. If nothing matches, say so plainly, then read `plans/BRIEF.md` and report what the tournament is currently planning toward.

If `plans/PLAN.md` exists, report the winning strategy, its gates, and any risk the arbiter recorded as unresolved — and note that the tournament is finished rather than still running.

Report briefly: round, competitors, families, scores, eliminations with their axis, and what remains unresolved. Do not re-score anything, do not write any file, and do not resurrect an eliminated plan by discussing it as if it were still live.
