---
planner: planner-a
round: 1
strategy_family: kebab-case-family-name
thesis: One line stating what this combination of approaches bets on. No pipe characters.
date: YYYY-MM-DD
status: competing
sources_verified: 0
sources_unverified: 0
---

# <Planner> — round <N>

## Strategy

The family, the thesis, and why this combination rather than another. Name the one thing this plan believes that the others may not. If you are revising, state what you took from the eliminated plan, what new research you added, and which rubric axes this revision moves.

## Architecture

The GPU ray-tracing core: kernels, acceleration structure, resolution targets, memory budget, how the CPU path stays the correctness oracle and the CI path stays GPU-free. Name the exact stack (PyTorch, CuPy, raw CUDA, WebGPU, or a stated combination) and the reason.

## Attribution

How the hourly, per-cell decomposition is computed: the components, how they are instrumented out of the same solve rather than a second model, and how the components are proven to sum back to the total.

## Interface

The 3D design tool: what a practitioner loads, what they can change, what they see, the interaction latency target, and what the interface explicitly does not model.

## Schedule

Phases with gates and pre-committed fallbacks. Every phase ends with something checkable. State what happens when the phase overruns.

## Cost claims

Every performance claim, each with the baseline it will be measured against, on the same machine, and how the number will be reported. No estimates presented as results.

## Paper plan

The contribution, the venue class, the evidence table that makes the claims defensible, and what the draft must contain. This must be a deliverable, not an afterthought.

## Cut list

What you deliberately left out, and why it is safe to leave out. A plan with no cut list has not made any decisions.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| Every external claim, one row each. | https://example.com/primary-source | YYYY-MM-DD |
| Anything you could not open and verify. | unverified | - |
