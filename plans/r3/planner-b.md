---
planner: planner-b
round: 3
strategy_family: reference-first-science
thesis: Be the instrument on top of the validated reference implementation, with the reference comparison as the paper's entire spine and everything else cut to protect it.
date: 2026-09-30
status: eliminated
sources_verified: 3
sources_unverified: 2
---

# planner-b — round 3

## Strategy

Round 2 scored 40/42. **Absorbed from the eliminated `browser-native-compute` plan:** per-device latency reporting (a distribution, not a single number) and its observation that a browser port is feasible because our component passes are separable — recorded as a post-paper port, deliberately not built now. **New research this round:** none material, and I am recording that honestly rather than padding the ledger: the sources that matter were already opened, and the reference implementation's own scope is the constraint I am planning around. **Axes this revision moves:** it does not move them, and I will say so plainly — this round I protected the reference comparison by dropping the optimisation mode, which narrows the contribution to "a validated instrument", a claim the reference comparison alone has to carry. I judged that a smaller claim I can fully evidence beats a larger one I cannot, and the arbiter can weigh whether that judgement cost more than it bought.

## Architecture

Unchanged: `solweig` for reference runs and validation, our CuPy solver for the interactive tier, the numpy physics as the CPU oracle, CI GPU-free. The optimisation mode is cut — it was the most speculative part of the schedule and the reference comparison is what the paper stands on. Cost of that cut: the interface loses its most distinctive action and becomes a fast, validated, editable comfort map.

## Attribution

Components mirror the reference's component structure, agreement is reported per component, and the sum-to-total test runs on both tiers. This is now the plan's principal scientific content, and it is thin — which is the honest summary of this revision.

## Interface

Edits canopy, albedo and shade; reports ΔTmrt, ΔUTCI, and area above threshold; everything promotable to a Tier 1 confirmation run; loops report latency as a distribution. No ranking, no optimisation, no browser path.

## Schedule

P1 reference reproduction on the New York control site; P2 Tier 2 component parity; P3 the loop with measured latency; P4 Delhi heights, canopy and reference run; P5 comparison table and paper. Single gate: at P2, if component agreement is poor, stop and report the comparison as the finding rather than proceeding to a design claim.

## Cost claims

Loop latency distribution; our tier versus the repo's numpy path; our tier versus a reference run, published even when the reference wins. Unchanged from round 2, and still the axis where this plan is weakest, because a cross-runtime comparison is not apples to apples.

## Paper plan

Contribution: a validated, attributed instrument for pedestrian heat on a data-scarce city, with the reference comparison as evidence. Evidence: per-component agreement, sum-to-total, intervention deltas, height audit, runtime table. Risk I am naming rather than hiding: a reviewer may reasonably ask why the instrument exists if the reference does the physics, and the answer — because the reference is a model and this is a design loop — is now doing all the work.

## Cut list

Optimisation mode, browser path, autograd, field measurement, wind, building energy, anthropogenic heat. The cut list grew this round, which is the trade I made.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| The SOLWEIG package is explicitly an experimental, compatibility-focused implementation with parity tests against the reference Python model — which is what makes it usable as our validation target and what bounds its authority. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| WebGPU compute in three.js works over storage buffers in TSL, so our separable component passes could be ported to the browser after the paper. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| Building heights for South Asia exist at 4 m effective resolution with annual coverage, which the Delhi case study depends on. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| Published Tmrt validation error is commonly around 5 K RMSE, setting the envelope for the comparison. | unverified | - |
| ENVI-met's documented scope is 1-10 m over 24-48 hours with large-domain runtimes in hours. | unverified | - |
