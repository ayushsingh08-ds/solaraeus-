---
planner: planner-d
round: 3
strategy_family: data-scarcity-first
thesis: The contribution is the transferable reconstruction method with a published error budget — and the tool that carries it keeps our own GPU engine, validated against the reference implementation component by component, with uncertainty visible in every answer a practitioner sees.
date: 2026-09-30
status: surviving
sources_verified: 3
sources_unverified: 2
---

# planner-d — round 3

## Strategy

Round 2 scored 38/42 and survived. **Absorbed from the eliminated `reference-first-science` plan:** its validation discipline — component-level parity rather than agreement on the final index, the reference comparison reported as numbers even where the reference wins, and the pre-registered stop rule ("if the comparison fails, publish the comparison as the finding"). I take the discipline and reject the family: wrapping the reference as the engine would leave this project with no engine of its own, which contradicts the GPU ray-traced core the whole project is built around. **Also absorbed:** the browser plan's per-device latency honesty, and the differentiable plan's inverse-problem framing, kept as a bounded candidate search. **New research this round:** re-read the reference implementation's stated scope to confirm it is a compatibility re-implementation with parity tests — which is exactly what makes it a valid independent target and exactly why it must not be our engine. **Axes this revision moves:** interface 2→3, because every answer now carries its uncertainty band and the placement search reports a marginal cooling curve with a measured latency budget rather than an interaction promise.

## Architecture

Three layers, each with a stated authority. **Engine:** our CuPy ray tracer — shadows, sky view factor, canopy transmission, component solve — because the error budget must be propagated through a solver we control. **Oracle:** the repo's numpy physics, unchanged, with GPU parity asserted per component; CI stays GPU-free. **Reference:** `solweig`, pinned, run on identical reconstructed inputs as an independent validation target, its own parity tests noted as the reason it is credible. The bounded placement search wraps the forward solver; it reports a curve, never an optimum.

## Attribution

Six components from our solve — direct beam, diffuse sky, ground-reflected, building longwave, sky longwave, canopy transmission — each paired with the input uncertainty that feeds it: height error into shadowing and building longwave, canopy-density error into transmission, meteorology into the longwave terms. Sum-to-total is tested before any band is published, and the paper reports attribution with bands rather than point estimates.

## Interface

A practitioner loads the reconstructed precinct, paints canopy, repaints surface albedo, places shade, and reads a comfort map that carries an uncertainty band, a stacked attribution panel, and a ranked list of the next planting sites by cooling per unit of input uncertainty. Latency is reported as a p50/p95 distribution over 50 edits, not a single number. The interface does not model wind, building energy, anthropogenic heat, or thermal inertia across the day — and it says so in its README.

## Schedule

P1 height reconstruction from the 4 m raster onto footprints, plus a 20-building audit against street-level imagery, reporting MAE/RMSE **before** any physics work begins. P2 canopy source audit, same treatment. P3 GPU engine with per-component CPU parity. P4 attribution with propagated uncertainty and the sum test. P5 reference comparison on identical inputs with the pre-registered stop rule. P6 interface, bounded placement search, latency measurement. P7 paper and artifact release. **The pre-registered pivot stands:** if the height audit exceeds 3 m RMSE, the paper reports the reconstruction error and the method as its contribution and stops claiming decision-grade maps. If the reference comparison fails, the comparison becomes the finding and the design claim is withdrawn.

## Cost claims

Same-machine, three numbers, each with its baseline: our GPU engine versus the repo's numpy CPU path (rays/second and scenario seconds); the full-day precinct run versus a `solweig` reference run on identical inputs (wall clock **and** agreement, published together); and the interface's per-edit latency distribution. Runtime never appears in the paper without the accuracy band beside it.

## Paper plan

Contribution: a transferable method for reconstructing microclimate-grade geometry in data-scarce cities, with an error budget propagated into comfort and intervention answers, demonstrated on a Delhi precinct, with a validated GPU design instrument as the delivery mechanism. Evidence table: height-audit error distribution; canopy-source audit; per-component parity against the CPU oracle; reference agreement on identical inputs; attribution with bands; the marginal cooling curve; the runtime table. Venue class: urban climate, where an error-budget contribution is native — and the design instrument is the demonstration, not the claim.

## Cut list

Autograd, browser-side compute, field measurement, CFD wind, building energy and anthropogenic heat. The browser path is recorded as a post-paper port, justified by the reference's own WebGPU precedent, and is not built now.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| The SOLWEIG Python package is a compatibility-focused re-implementation with parity tests against the reference Python model, optional WebGPU acceleration, and a vegetation canopy-height input — credible as an independent target, and explicitly not the reference. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| Building presence, counts and heights for South Asia exist as an annual 4 m effective-resolution raster (2016-2023), which is the reconstruction's starting point. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| WebGPU compute in three.js runs on TSL over storage buffers, making a post-paper browser port a port rather than a rewrite. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| A global canopy-height product at 30 m covers urban India, so canopy is a data task rather than an invention. | unverified | - |
| Published Tmrt validation error is commonly around 5 K RMSE, which sets the agreement envelope the reference comparison will be judged against. | unverified | - |
