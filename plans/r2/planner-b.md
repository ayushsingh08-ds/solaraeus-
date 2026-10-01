---
planner: planner-b
round: 2
strategy_family: reference-first-science
thesis: Do not compete with the validated reference implementation — wrap it, and make the project's contribution the attribution decomposition and the design loop, with an explicitly gradient-optional optimisation mode.
date: 2026-09-30
status: competing
sources_verified: 3
sources_unverified: 2
---

# planner-b — round 2

## Strategy

Round 1 scored 35/42 and survived on feasibility. **Absorbed from the eliminated `differentiable-gpu-core` plan:** the design question is an inverse problem, so the loop gains an optional optimisation mode — implemented as finite-difference probing over a small candidate set rather than autograd, which captures the value without a differentiable graph. **New research this round:** the reference package's own parity-testing approach, which I adopt as the template for our Tier 2 harness, and the TSL compute model, which makes a future browser path a port rather than a rewrite. **Axes this revision moves:** scientific defensibility 2→3, because the positioning now answers the first question every reviewer will ask — *why not just use the reference implementation?* — in one sentence: because it is a model, and this is an instrument. Interface 2→3, because "suggest the next interventions" is now a concrete action with a ranking, not a promise.

## Architecture

Two tiers, unchanged in shape and now explicit about their contract. **Tier 1:** `solweig` for reference runs and validation, pinned, with its parity provenance recorded as the reference's own guarantee. **Tier 2:** our CuPy intervention solver (shadows, sky view factor, canopy transmission) validated against Tier 1 at the scenario level, inheriting credibility it did not earn itself — which is the point, and which the paper states plainly. The repo's numpy physics stays the CPU oracle; CI stays GPU-free. Optimisation mode: candidate-set probing with finite differences, bounded so it cannot become a research project.

## Attribution

Components are defined to match Tier 1's component structure, so agreement is checkable component by component rather than only on the final index. Sum-to-total runs on both tiers. The paper reports per-component agreement, because a model that agrees on Tmrt while disagreeing on its components agrees by cancellation.

## Interface

The loop edits canopy, albedo and shade, reports ΔTmrt, ΔUTCI and the area above the strong-heat-stress threshold, and now ranks the next N interventions by marginal cooling. Every scenario can be promoted to a Tier 1 confirmation run with one click. It does not model wind, building energy or anthropogenic heat.

## Schedule

P1 reference reproduction on the New York control site; P2 Tier 2 component parity with the harness adopted this round; P3 the loop, the ranking action and measured latency; P4 Delhi heights, canopy, audit and a Tier 1 reference run; P5 inter-model comparison and the paper. Gate: if Tier 2 cannot reach a stated tolerance against Tier 1, the loop ships with a wider published band, never a hidden one.

## Cost claims

Same-machine measurements: Tier 2 loop latency (p50/p95 over 50 edits), Tier 2 versus the repo's numpy CPU path, and Tier 2 versus a Tier 1 reference run — reported even where the reference wins. The comparison against a published implementation is the number reviewers will trust, and it stays on the cost axis unimproved this round because a cross-runtime comparison is not apples to apples and I will not dress it up as one.

## Paper plan

Contribution: a validated, attributed design instrument demonstrated on a data-scarce Indian city, with a bounded optimisation mode for intervention placement. Evidence: component-level agreement with the reference, attribution sum-to-total, intervention deltas with per-tree cooling, the ranked placement curve, the height-audit error budget, and the runtime table. Venue class: urban climate.

## Cut list

No new radiative engine, no autograd, no browser path, no field measurement. Each cut buys time for the reference comparison, which is the shelf the paper stands on.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| The SOLWEIG Python package ships parity tests against the reference implementation, which is the model our own parity harness now follows. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| WebGPU compute in three.js is written in TSL over storage buffers, so a future browser path is a port of our component passes rather than a rewrite. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| Building heights for South Asia exist as a 4 m effective-resolution annual raster with presence, counts and heights. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| Published Tmrt validation error is commonly around 5 K RMSE, which sets the agreement envelope we will be judged against. | unverified | - |
| ENVI-met's documented scope is 1-10 m resolution over 24-48 hour periods with reported runtimes of hours per large domain. | unverified | - |
