---
planner: planner-a
round: 1
strategy_family: differentiable-gpu-core
thesis: Make the whole radiative solve differentiable on the GPU, so designing cool cities becomes gradient-based optimisation instead of trial and error, and attribution falls out of the same graph.
date: 2026-09-30
status: eliminated
sources_verified: 3
sources_unverified: 2
---

# planner-a — round 1

## Strategy

Family: **differentiable-gpu-core**. Every other plan treats the simulator as a forward function you call many times. This one treats it as a differentiable function you call *once* and then optimise: the tree placement problem is an inverse problem, and inverse problems are what autodiff is for. The bet is that "where should the next 100 trees go" is the question a practitioner actually has, and that nobody in this space answers it with gradients today. I accept the largest schedule risk in the field in exchange for the largest novelty.

## Architecture

PyTorch as the stack, because autograd is the product, not an optimisation. Ray batches are tensors; shadow and sky-view terms are implemented with custom `autograd.Function` nodes whose backward pass is validated against finite differences. Acceleration: a 2D height-field ray-march is enough for occlusion — no BVH needed — but the ray-march must be vectorised over rays and steps and staged in shared-memory-sized tiles. Two modes on one code path: a warm forward mode for the interface, and a differentiable mode for optimisation. **CPU parity is the oracle**: the existing numpy SVF, shadow and radiation modules stay untouched, and a parity test asserts GPU agreement within a stated tolerance per component. CI runs the CPU path only; the GPU test is marked and run locally, exactly as the brief requires.

## Attribution

Attribution is not a separate pass: each component is a distinct term in the same graph — direct beam, diffuse sky, ground-reflected, building longwave, sky longwave, canopy transmission factor — so the components are readable *and* differentiable. The sum-to-total test is a graph-level assertion: recompute the total from the components and compare against the direct solve.

## Interface

The interface exposes both modes: drag a tree and the warm forward mode re-renders in under a second; press **suggest** and the differentiable mode returns a ranked placement of the next N interventions with the marginal cooling per intervention and its cost. It does not model wind, CFD, building energy or anthropogenic heat.

## Schedule

P1 parity-gated GPU forward core (CPU oracle first, then kernels); P2 attribution terms in the graph with sum-to-total; P3 the differentiable placement mode with finite-difference gradient checks; P4 Delhi data lock with the height audit; P5 paper. Gates: if gradient checks fail or the backward pass costs more than ~5× forward, the differentiable mode is cut and the plan falls back to the warm forward mode — the interface still ships, and the paper reports the forward-mode attribution and a measured negative result about autodiff cost.

## Cost claims

Measured on one machine, always against a named baseline: (a) GPU forward vs the repo's own numpy CPU path, same raster, same machine, reporting rays/second and scenario seconds; (b) GPU forward vs `solweig` on identical inputs, reporting wall clock, because a peer-reviewed Rust/WebGPU implementation exists and claiming speed without confronting it is indefensible; (c) the interface's loop latency, reported as p50/p95 over 50 edits. No number is published from an estimate.

## Paper plan

Contribution: **gradient-based intervention design for urban heat, with an attributed radiative solve and a data-scarce case study**. Venue class: urban climate or urban simulation. Evidence table: parity per component; attribution sum-to-total; measured speedup vs our own CPU baseline and vs `solweig`; the marginal cooling curve from the optimiser; the Delhi height-audit error budget. The paper's claim is *not* "faster than ENVI-met" — it is "the design question is an optimisation problem, and here is a differentiable model that answers it".

## Cut list

Building energy, anthropogenic heat, CFD wind, field measurements, browser-side compute, and multi-city generalisation are all out. Autodiff is the whole bet; anything that dilutes it is cut. If the bet fails at P3, the fallback is stated above rather than discovered late.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| A peer-reviewed SOLWEIG re-implementation exists on PyPI (Rust + PyO3) with optional WebGPU acceleration for shadow casting and anisotropic sky, automatic tiling for GPU memory, and parity tests against the reference Python implementation. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| WebGPU compute in three.js is written in TSL with storage buffers and `instanceIndex`, and browser support is broad enough in 2026 (Chrome, Edge, Firefox desktop; Safari 26 on macOS) to be a realistic deployment target. | https://threejsroadmap.com/blog/introduction-to-webgpu-compute-shaders | 2026-09-30 |
| Building heights for South Asia are available as a 4 m effective-resolution annual raster (2016-2023) with presence, fractional counts and height. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| Mean radiant temperature validation studies commonly report RMSE around 5 K for modelled Tmrt against measurement. | unverified | - |
| GPU-accelerated high-resolution solar potential estimation is established prior art, so "GPU urban radiation" is not itself novel. | unverified | - |
