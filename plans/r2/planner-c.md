---
planner: planner-c
round: 2
strategy_family: browser-native-compute
thesis: Put the rays in the browser with WebGPU compute so the design loop is instant and zero-install, and rank interventions by measured effect rather than by gradients.
date: 2026-09-30
status: eliminated
sources_verified: 2
sources_unverified: 2
---

# planner-c — round 2

## Strategy

Round 1 scored 32/42; the weakest axis was defensibility, because "an interactive tool" is a claim an urban-climate venue finds hard to grade. **Absorbed from the eliminated `differentiable-gpu-core` plan:** intervention *ranking* — but implemented without gradients, by evaluating a bounded candidate set of planting sites in the browser and sorting by measured ΔTmrt per tree, which is honest about being a search rather than pretending to be an optimum. **New research this round:** how the reference package structures its components and thresholds, which I now mirror exactly so that agreement can be asserted per component rather than only on the final index. **Axes this revision moves:** defensibility 2→3, by reframing the claim as a measurable platform study — per-device latency distributions and a task-based evaluation of the interface rather than an assertion of usefulness. Cost 2→3, because per-device latency is measured in the browser with its own timers and reported as a distribution.

## Architecture

Unchanged and unchanged deliberately: the precinct is baked into GPU buffers by a Python preprocessor, and the browser runs TSL compute passes for shadows, horizon angles and the component solve, with the existing WebGL path as fallback. Two implementations remain the main risk, so the parity fixtures are exported from the CPU oracle and the sum-to-total test runs in the browser harness *and* against the oracle.

## Attribution

Separate storage buffers per component, visualised directly as the stacked attribution panel, with the component names and definitions taken from the reference implementation so that our numbers can be compared to its output without translation.

## Interface

Paint canopy, repaint albedo, place shade, delete — each edit re-dispatches the solve. Latency target under 100 ms per edit at 2 m, measured per device and reported as a distribution, plus a ranked list of the next N planting sites by measured cooling per tree. Task-based evaluation with a handful of practitioners replaces the vague usability claim. It does not model wind, building energy, anthropogenic heat or thermal inertia.

## Schedule

P1 export buffers and parity fixtures; P2 shadow and SVF passes agreeing with the oracle; P3 component passes, sum test and the panel; P4 intervention tools, ranking and latency measurement; P5 the practitioner evaluation and the paper. Gate: if WebGPU behaves badly on a target device, the server path reuses the same component definitions and the paper becomes a platform study — reported, not hidden.

## Cost claims

Per-edit latency in the browser at named devices, rays/second from the solve, and one full-day wall clock against the repo's numpy path. The honest expectation stands: a browser GPU loses to a desktop GPU on batch work and wins on interaction, so interaction is what gets claimed.

## Paper plan

Contribution: an attributed, zero-install, in-browser design instrument, evaluated as an interaction and reported as a per-device platform study, with the Delhi data method as the bridge to practice. Evidence: per-component agreement with the oracle, sum-to-total in both implementations, latency distributions, ranked placement lists, and a task-based evaluation. Venue class: urban simulation and planning, where an interaction contribution is legible.

## Cut list

No differentiable optimisation (I take the ranking without the gradient), no batch production runs in the browser, no field measurement, no wind. The ambition stays on interaction quality.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| three.js WebGPU compute runs on TSL with storage buffers addressed by `instanceIndex`, with broad 2026 desktop support, making an in-browser solve a deployment rather than a promise. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| The SOLWEIG Python package exposes radiation components and UTCI threshold exceedance, giving the component definitions our browser passes mirror. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| GPU-accelerated solar potential estimation at city scale is established prior art. | unverified | - |
| three.js ships a WebGPU renderer with a WebGL fallback from r0.158 onward, so graceful degradation is available. | unverified | - |
