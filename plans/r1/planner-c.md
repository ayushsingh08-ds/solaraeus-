---
planner: planner-c
round: 1
strategy_family: browser-native-compute
thesis: Put the rays in the browser with WebGPU compute so the design loop is instant and zero-install, and make interaction latency the deliverable rather than batch throughput.
date: 2026-09-30
status: competing
sources_verified: 2
sources_unverified: 2
---

# planner-c — round 1

## Strategy

Family: **browser-native-compute**. Every other plan puts the GPU behind a Python process and ships pixels to a viewer. This one runs the radiative solve itself in the browser via WebGPU compute shaders written in TSL, so the practitioner drags a tree and the heat field updates in milliseconds with no server round trip, no install, and no data upload. The bet is that the people who fix city heat are designers, not HPC users, and that "instant and zero-install" beats "faster on paper, slower in the way you actually work".

## Architecture

The precinct is baked once by a Python preprocessor into GPU-friendly buffers: height field, canopy layer, surface classes, per-hour sun vectors. In the browser, three.js (r186, already in `frontend/` with react-three-fiber) runs TSL compute passes — a ray-march over the height field for shadows and horizon angles, a sky-view term, and the component solve — with storage buffers holding per-cell results. The existing WebGL renderer remains as a fallback path, which means the app degrades instead of breaking. The repo's numpy physics is the oracle, and CI stays GPU-free because the parity tests run the CPU path and the browser kernels are validated locally against it with exported fixtures.

## Attribution

Each component is a separate compute pass writing into its own storage buffer, so attribution is literally the set of buffers the interface visualises: direct beam, diffuse sky, ground-reflected, building longwave, sky longwave, canopy transmission. The sum-to-total test runs twice — in the browser's own test harness and against the Python oracle — because a decomposition that only sums in one implementation is a coincidence.

## Interface

Everything is a scene edit: paint canopy, change albedo by drawing on the ground, place shade sails, delete. Each edit re-dispatches the compute pass and updates a stacked-bar attribution panel plus a heat-stress map. Latency target: under 100 ms per edit at 2 m over the precinct, measured with the browser's own performance timers rather than estimated. It does not model wind, building energy, anthropogenic heat, or thermal inertia across the day.

## Schedule

P1 export the precinct to GPU buffers and port the parity fixtures; P2 shadow and SVF passes with CPU-oracle agreement; P3 component passes, the sum test and the interface wiring; P4 intervention tools and latency measurement; P5 Delhi data and the paper. Gate: if WebGPU device variance breaks the pass on a target machine, the fallback is the server-side path reusing the same component definitions — the paper then reports the browser result as a measured platform study instead.

## Cost claims

Reported as (a) per-edit latency measured in the browser at a stated device, (b) rays/second from the solve, and (c) a head-to-head wall-clock against the repo's numpy CPU path for one full hourly day, where the honest expectation is that a browser GPU loses to a desktop GPU and wins only for *interaction*. The point is measured latency, not a victory claim.

## Paper plan

Contribution: **an attributed, zero-install, in-browser design instrument for pedestrian heat, with latency as the reported result.** Evidence table: per-component agreement with the CPU oracle, sum-to-total, per-edit latency distribution by device, a worked intervention case with per-tree cooling, and the Delhi data method. Venue class: urban simulation and planning, where an interaction contribution is legible — an urban-climate venue would demand the field validation that a browser study cannot supply.

## Cut list

No batch high-resolution production runs in the browser, no differentiable optimisation (two implementations are already the risk), no field measurement, no wind. Ambition is deliberately spent on interaction quality rather than on physical scope.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| three.js WebGPU compute uses TSL with storage buffers addressed by `instanceIndex`, and 2026 desktop support is broad enough for a real deployment target. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| A peer-reviewed SOLWEIG implementation exists as a Python package with optional WebGPU acceleration, which is both a validation reference and proof that WebGPU is being used in this domain. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| GPU-accelerated solar potential estimation is established prior art at city scale. | unverified | - |
| three.js ships a WebGPU renderer with WebGL fallback from r0.158 onward, so a graceful degradation path exists. | unverified | - |
