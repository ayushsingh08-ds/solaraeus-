# PLAN — Solaraeus as a data-scarce-city microclimate instrument

**Surviving strategy family:** `data-scarcity-first` (planner-d, round 3, 40/42).
**Composed from:** the round-three plans of planner-d and planner-b, with the absorbed ideas recorded below and the rejected alternatives stated in full.
**Status:** survived three tournament rounds; pending the roast council's attack before build.

## Strategy

The claim this project makes is not that it out-computes anyone. It is that **microclimate-grade geometry can be reconstructed for a city where the data does not exist, with an error budget published alongside the answer, and that the resulting comfort map is still good enough to decide where to plant trees.** The physics is deliberately not the novelty: a parity-tested SOLWEIG implementation already exists as a Python package, so claiming novelty in radiative modelling would be indefensible and would invite exactly the comparison the roast council already made ("the physics is already free").

The delivery mechanism is our own GPU ray tracer plus a design loop, because a transferable method that ships as a notebook convinces nobody, and because the project's identity is a ray-traced instrument rather than a raster script.

What the plan bets on: that reviewers reward a published error budget more than a faster kernel, and that practitioners need the band as much as the number.

## Architecture

Three layers, each with a stated authority and a stated failure mode:

1. **Engine — our CuPy ray tracer.** Shadows, sky view factor, canopy transmission and the component solve, on a single consumer GPU, at 1 m over the Delhi precinct (roughly 600 × 600 m, ~360,000 cells, 36 radials, a full hourly day). It is ours because the error budget must be propagated *through* the solver to mean anything. **Resolution honesty is part of this layer:** 1 m is the simulation grid, while the reconstructed inputs behind it are coarser, and every cost and accuracy claim states the input resolution rather than inheriting the grid's. The repository's current New York terrain is a 30 m SRTM tile bilinearly resampled onto a 1 m grid while the documentation calls it LiDAR; that defect is corrected before any paper claim depends on it, and it is the reason the Delhi inputs are audited rather than trusted.
2. **Oracle — the repo's numpy physics.** Unchanged, and the correctness authority. GPU parity is asserted per component, not only on the final index. CI runs the CPU path only; the GPU suite is marked and run locally, so the repository never requires a GPU to be green.
3. **Reference — `solweig`, pinned.** Run on identical reconstructed inputs as an independent validation target. Its own documented parity tests against the reference Python model are the reason it is credible; its documented status as a compatibility re-implementation is the reason it must not be our engine.

Geospatial inputs are reconstructed, not assumed: building footprints from open data, heights from the 4 m annual height raster, canopy from a canopy-height product, meteorology from reanalysis anchored to station records for a documented heatwave day.

## Attribution

Six components, instrumented out of the same solve rather than computed by a second model: direct beam, diffuse sky, ground-reflected shortwave, building longwave, sky longwave and canopy transmission. Each is paired with the input uncertainty that feeds it — height error into shadowing and building longwave, canopy-density error into transmission, meteorology into the longwave terms.

Two rules make this a claim rather than a diagram: the components must sum back to the recomputed total **under test**, and the paper reports attribution **with bands**, never as point estimates.

## Interface

A practitioner loads the reconstructed precinct, paints canopy, repaints surface albedo, places shade structures, and reads three linked answers: a comfort map that carries its uncertainty band, a stacked attribution panel showing what is causing the heat, and a ranked list of the next planting sites by cooling per unit of input uncertainty.

Latency is a measured distribution — p50/p95 over fifty edits — not a single number. Every scenario can be promoted to a full reference run. The interface does not model wind fields, building energy, anthropogenic heat or thermal inertia across the day, and its README says so before the user discovers it.

## Schedule

| Phase | Deliverable | Gate |
| :-- | :-- | :-- |
| P1 | Building heights reconstructed from the 4 m raster onto footprints, plus a 20-building audit against street-level imagery, reported as MAE/RMSE | **Gate A** — physical work starts only if the audit clears the pre-registered 3 m RMSE bar |
| P2 | Canopy source audited and integrated; the same error treatment | Gate B — canopy coverage sanity-checked against imagery |
| P3 | GPU engine with per-component CPU parity | Gate C — stated tolerance per component, or the CPU path carries the study at reduced resolution |
| P4 | Attribution with propagated uncertainty and the sum-to-total test | Gate D — bands published only after the sum test passes |
| P5 | Reference comparison on identical inputs | **Gate E** — pre-registered: if comparison fails, it is published as the finding and the design claim is withdrawn |
| P6 | Interface, bounded placement search, latency measurement | Gate F — latency distribution measured, not asserted |
| P7 | Paper draft, artifact release, cold run | — |

**Pre-registered pivots, written before the work:** height audit above 3 m RMSE → the paper reports the reconstruction method and its error as the contribution and drops all decision-grade language. Reference comparison failure → the comparison becomes the paper's result. GPU port stall → the numpy path runs the study at reduced resolution, stated as such.

## Cost claims

Three measured numbers, each with a named baseline, all on one machine:

1. **Our GPU engine versus this repo's numpy CPU path** — rays/second and seconds per scenario, same raster.
2. **Our full-day precinct run versus a `solweig` reference run on identical inputs** — wall clock *and* agreement, published together, even where the reference wins.
3. **Interface per-edit latency** — p50/p95 over fifty edits, per device.

No number enters the paper from an estimate, and runtime never appears without the accuracy band beside it.

## Paper plan

**Contribution:** a transferable method for reconstructing microclimate-grade geometry in data-scarce cities, with an error budget propagated into pedestrian comfort and intervention decisions, demonstrated on a Delhi precinct, delivered through a validated GPU instrument.

**Evidence table:** height-audit error distribution; canopy source audit; per-component parity against the CPU oracle; component-level agreement with the reference implementation on identical inputs; attribution with bands; the marginal cooling curve from the bounded placement search; the runtime table.

**Venue class:** urban climate, where an error-budget contribution is native. The design instrument is the demonstration, not the claim — which is what keeps the paper defensible when a reviewer asks why the reference implementation is not simply used directly.

## Cut list

Autograd and differentiable optimisation (the inverse-problem framing survives as a bounded candidate search). Browser-side compute (recorded as a post-paper port, justified by the reference implementation's own WebGPU precedent). Field measurement campaigns, CFD wind, building energy modelling, anthropogenic heat, and multi-city generalisation. Each cut buys time for the error budget and the reference comparison, which are the two pillars the claim stands on.

## Rejected alternatives

- **`differentiable-gpu-core` (planner-a, eliminated round 1, 31/42).** Rejected on engineering risk: autograd through a ray-march, gradient checks and CPU parity together are the heaviest critical path available, and its own fallback discarded the novelty it was built on. **Absorbed:** the inverse-problem framing, downgraded honestly to a bounded candidate search that reports a marginal cooling curve instead of an optimum.
- **`browser-native-compute` (planner-c, eliminated round 2, 37/42).** Rejected on feasibility: two implementations of the same physics with parity fixtures between them, and no reference-implementation agreement anywhere in the plan, producing a claim an urban-climate venue cannot grade. **Absorbed:** per-device latency reported as a distribution rather than a single number, and the browser path as a documented post-paper port.
- **`reference-first-science` (planner-b, eliminated round 3, 37/42 after a 40/42 round two).** Rejected on scientific defensibility after the improvement gate triggered: the final revision cut its most distinctive feature and narrowed its contribution to being an instrument on top of someone else's engine, so the plan's value depended on the reference implementation's goodwill rather than on a method of its own. **Absorbed:** component-level parity rather than index-level agreement, the reference comparison published even where the reference wins, and the pre-registered stop rule that turns a possible failure into a reported result.

## Red team

The three eliminated planners reviewed this document before it was accepted. Their critiques are recorded unresolved where they remain unresolved.

- **planner-a (eliminated round 1):** the bounded placement search cannot claim optimality, and a marginal cooling curve presented without an explicit statement of its search space will be read as an optimum by exactly the audience this project wants to impress. *Response:* accepted; the interface and the paper will state the candidate set and that the curve is a lower bound, not an optimum.
- **planner-c (eliminated round 2):** the interface promises an interactive loop but names no per-edit latency budget for the *reconstruction* path, only for the solve — if the canopy repaint forces a re-derivation of the surface model, the loop stalls on the thing the user actually does most. *Unresolved risk, carried into P6 with a measurement requirement before any latency claim is published.*
- **planner-b (eliminated round 3):** validation rests on a single reference implementation, and a 20-building height audit cannot bound precinct-wide error; independent agreement — a second model or any published measurement — is absent from the plan. *Partially resolved:* the audit is a sample by design and its error distribution is published; the absence of a second independent check is named in the paper's limitations rather than papered over, and a second comparison is the first post-paper extension.
- **Arbiter's note on the record:** the surviving plan scores 40/42, and both missing points sit on **measured cost claims**, because the cross-runtime comparison against the reference implementation is not apples to apples and no plan in this tournament produced a same-machine baseline it fully controls. That axis is the plan's known weak point and should be the first thing reviewed when real numbers exist.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| The SOLWEIG Python package is a compatibility-focused re-implementation with parity tests against the reference Python model, optional WebGPU acceleration for shadow casting and anisotropic sky, tiling for GPU memory, and a vegetation canopy-height input — credible as an independent validation target, and explicitly not the reference implementation. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| Building presence, counts and heights for South Asia are available as an annual 4 m effective-resolution raster covering 2016-2023, which is the reconstruction's starting point. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| WebGPU compute in three.js runs on TSL over storage buffers with an `instanceIndex` execution model and broad 2026 desktop support, making a post-paper browser port a port rather than a rewrite. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| A global canopy-height product at 30 m covers urban India, so canopy is a data task rather than an invention — the exact product and licence are unconfirmed. | unverified | - |
| Published mean-radiant-temperature validation error is commonly around 5 K RMSE, which sets the agreement envelope the reference comparison will be judged against; the 403-blocked source must be replaced with an opened primary source before the paper cites any figure. | unverified | - |
