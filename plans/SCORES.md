# Tournament Scores

Rubric: feasibility ×3, scientific defensibility ×3, sourcing integrity ×2, engineering risk ×2, interface and deliverable clarity ×2, measured cost claims ×2. Each axis 0–3, weighted total out of 42. Peer scores were collected on anonymized plans; the arbiter scored independently and reconciled. Plans are listed under their anonymized label with their real planner recorded, because the record must be auditable even though the round was blind.

## Round 1

| Plan | Feasibility | Defensibility | Sourcing | Risk | Interface | Cost | Weighted total | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A (planner-b) | 3 | 2 | 3 | 3 | 2 | 2 | 35 | survives |
| B (planner-d) | 3 | 2 | 3 | 2 | 2 | 2 | 33 | survives |
| C (planner-c) | 2 | 2 | 3 | 2 | 3 | 2 | 32 | survives |
| D (planner-a) | 2 | 3 | 3 | 1 | 2 | 2 | 31 | eliminated |

Evidence:

- **A (planner-b)** — feasibility 3: every phase ends in a checkable artefact and the reference dependency is pinned. Defensibility 2: the novelty claim is thin because the physics belongs to the reference implementation.
- **B (planner-d)** — defensibility 2: the error budget is a real contribution but the round-one plan does not yet pre-commit to a pivot if the audit fails. Risk 2: the height reconstruction is the critical path with no stated alternative.
- **C (planner-c)** — interface 3: interaction is the deliverable and latency is measurable. Feasibility 2: two implementations of the same physics is the largest hidden cost in the round.
- **D (planner-a)** — defensibility 3: the only genuinely novel framing in the round, and the attribution-as-graph design is elegant. Risk 1: autograd through a ray-march plus CPU parity is the heaviest critical path in the tournament, with no fallback that preserves the contribution.

**Eliminated:** planner-a — engineering risk ×2, with feasibility as the secondary cause: the plan bets the schedule on a differentiable graph whose backward pass, gradient checks and parity work are all unproven, and its cut-list fallback discards the very novelty the plan is built on. The survivors must absorb the inverse-problem framing at a cost they can afford.

## Round 2

| Plan | Feasibility | Defensibility | Sourcing | Risk | Interface | Cost | Weighted total | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A (planner-b) | 3 | 3 | 3 | 3 | 3 | 2 | 40 | survives |
| B (planner-d) | 3 | 3 | 3 | 3 | 2 | 2 | 38 | survives |
| C (planner-c) | 2 | 3 | 3 | 2 | 3 | 3 | 37 | eliminated |

Evidence:

- **A (planner-b)** — defensibility 2→3: the positioning now answers the reviewer's first question explicitly. Interface 2→3: the ranking action is concrete. Cost stays 2 and is named as the weak axis rather than inflated.
- **B (planner-d)** — defensibility 2→3 and risk 2→3: the pre-registered pivot converts the critical path from a hope into a decision rule. Interface stays 2: the uncertainty-banded map is a good idea that round two describes rather than specifies.
- **C (planner-c)** — defensibility 2→3: a platform study with per-device latency and a task-based evaluation is measurable. Cost 2→3: measured in the browser by its own timers. Feasibility stays 2 and is what ends it.

**Eliminated:** planner-c — feasibility ×3, with interface and cost strong: maintaining two implementations of the same physics, with parity fixtures exported between them and no reference-implementation agreement anywhere in the plan, is more work than the round allows and produces a paper whose central claim an urban-climate venue cannot grade. The survivors must absorb the per-device latency honesty.

## Round 3

| Plan | Feasibility | Defensibility | Sourcing | Risk | Interface | Cost | Weighted total | Decision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A (planner-d) | 3 | 3 | 3 | 3 | 3 | 2 | 40 | survives |
| B (planner-b) | 3 | 2 | 3 | 3 | 3 | 2 | 37 | eliminated |

Evidence:

- **A (planner-d)** — interface 2→3: every answer carries its band and the placement search reports a marginal cooling curve with a per-edit latency distribution. It keeps its own GPU engine, which is the project's stated identity, and adopts the validation discipline without adopting the wrapper.
- **B (planner-b)** — defensibility 3→2: this revision cut the optimisation mode and leaned further into being the instrument on top of the reference, so the plan's own contribution narrowed to "a validated instrument" at the exact moment a competitor plan showed the same validation discipline applied to a contribution that does not depend on the reference's goodwill.

**Eliminated:** planner-b — scientific defensibility ×3, triggered by the improvement gate: a revision that scores below its previous round, on the axis that carries the paper, is eligible for elimination even from the lead. The winner must absorb its discipline — component-level parity, the reference comparison published even where the reference wins, and the pre-registered stop rule — because those three things are the difference between a claim and a hope.
