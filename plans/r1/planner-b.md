---
planner: planner-b
round: 1
strategy_family: reference-first-science
thesis: Do not compete with the validated reference implementation — wrap it, and spend the project's GPU effort on the intervention layer and the attribution decomposition that reviewers will actually accept.
date: 2026-09-30
status: competing
sources_verified: 3
sources_unverified: 2
---

# planner-b — round 1

## Strategy

Family: **reference-first-science**. The fastest route to a defensible paper is to stand on the parity-tested SOLWEIG implementation that now exists as a Python package, use it as both the physics reference and the validation target, and make the project's own contribution the parts nobody else has: the hourly attribution decomposition, the intervention design loop, and the data-scarce city method. The bet is that reviewers care about validity and transferability far more than about who wrote the ray marcher — and that a wrapper which is honest about being a wrapper is more publishable than a from-scratch solver that is 5 K off with no reference.

## Architecture

Two tiers. **Tier 1 (batch truth):** `solweig` runs the precinct for the full hourly day — it is Rust with optional WebGPU acceleration and ships parity tests against the reference Python model, so using it is a strength, not a shortcut. **Tier 2 (our layer):** a GPU-accelerated (CuPy) intervention solver for the interactive path, kept deliberately simpler than SOLWEIG — shadows, sky view factor, canopy transmissivity — and *validated against Tier 1 at the scenario level*, so the loop inherits Tier 1's credibility. The repo's existing numpy physics stays as the CPU oracle for our own kernels, and CI remains GPU-free. Stack: CuPy for our solver, `solweig` as a pinned dependency for reference runs.

## Attribution

Tier 1 exposes radiation components and thresholds (the package returns per-timestep Tmrt, shadow, UTCI/PET and radiation components, plus a summary carrying UTCI threshold exceedance), so our decomposition is defined to be consistent with that component structure rather than invented alongside it. Our Tier 2 solver reproduces the same component set, and the sum-to-total test runs on both.

## Interface

The design loop edits canopy, surface albedo, shade structures, and reports ΔTmrt, ΔUTCI and the change in area above the strong-heat-stress threshold, with a scenario re-run in the Tier 2 solver and a one-click promotion to a Tier 1 confirmation run. It does not model wind fields, building energy, or anthropogenic heat.

## Schedule

P1 pin and reproduce a published-style reference run for the New York site; P2 our component set and sum-to-total; P3 the loop with measured latency; P4 Delhi: heights, canopy, audit, and a reference run; P5 inter-model comparison and the paper. Gates: if Tier 2 cannot be brought within a stated tolerance of Tier 1, the loop ships with a larger stated uncertainty band rather than a hidden one.

## Cost claims

Three measured comparisons, all on the same machine: Tier 2 loop latency (p50/p95 over 50 edits); Tier 2 versus the repo's numpy CPU path; and Tier 2 versus a Tier 1 reference run, reported honestly even where the reference wins — because a comparison against a published implementation is the number reviewers trust, and hiding it would be the first thing they check.

## Paper plan

Contribution: **a validated, attributed design instrument for pedestrian heat, demonstrated on a data-scarce Indian city.** Because the physics is not ours, the paper's claims are all comparisons and attributions: agreement with the reference implementation, the attribution decomposition, and the measured effect of interventions. Evidence table: component parity, reference agreement with numbers, attribution sum-to-total, intervention deltas with per-tree cooling, height-audit error budget, and the runtime table. Venue class: urban climate.

## Cut list

We do not write a new radiative engine, we do not claim novelty in the physics, and we do not chase real-time performance at the cost of agreement. Academic credibility is bought with the reference comparison; anything that does not serve it is out.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| A peer-reviewed SOLWEIG re-implementation exists on PyPI (Rust + PyO3), exposes radiation components, UTCI/PET and UTCI threshold exceedance, accepts a vegetation canopy-height raster, and ships parity tests against the reference Python implementation. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| WebGPU compute in three.js works through TSL with storage buffers and `instanceIndex`, with broad 2026 desktop browser support, so an in-browser path is a real option rather than a promise. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| Building heights for South Asia exist as a 4 m effective-resolution annual raster (2016-2023) with presence, fractional counts and heights. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| Published Tmrt validation error is commonly around 5 K RMSE, which sets the expected agreement envelope. | unverified | - |
| ENVI-met's documented scope is 1-10 m horizontal resolution over 24-48 hour periods, and its runtime for a large domain is measured in hours to days. | unverified | - |
