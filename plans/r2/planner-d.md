---
planner: planner-d
round: 2
strategy_family: data-scarcity-first
thesis: Make the transferable method the contribution — reconstruct heights and canopy for a data-poor city with a published error budget, then show the reconstructed precinct still yields decision-grade answers, including where to intervene.
date: 2026-09-30
status: competing
sources_verified: 2
sources_unverified: 3
---

# planner-d — round 2

## Strategy

Round 1 scored 33/42. **Absorbed from the eliminated `differentiable-gpu-core` plan:** the inverse-problem framing, downgraded honestly to a bounded search — enumerate candidate planting configurations, evaluate them with the same solver, and report the marginal cooling curve rather than claiming a global optimum; and the two-mode split (fast forward mode for the loop, search mode for planning), which fits our own engine. **New research this round:** the practical disaggregation route from a 4 m height raster onto footprint polygons, and the audit protocol that turns reconstructed heights into a reported error distribution. **Axes this revision moves:** scientific defensibility 2→3, because the novelty claim no longer depends on beating anyone's kernel — it is the error budget, which the free alternatives do not publish. Engineering risk 2→3, because the riskiest input now has a pre-registered pivot.

## Architecture

Our own CuPy ray tracer for the forward path, with `solweig` as the independent validation target rather than the engine — the error budget has to be propagated through a solver we control to mean anything. The repo's numpy physics is the CPU oracle; parity tolerance is stated per component; CI stays GPU-free. The search mode wraps the forward solver in a candidate loop. If CuPy porting stalls, the numpy forward path still runs the whole study at reduced resolution and the paper says so.

## Attribution

Components come from our solver, each paired with the input uncertainty feeding it: height error into shadowing and building longwave, canopy-density error into transmission, meteorology error into the longwave terms. The paper reports attribution with bands, not point estimates, and the sum-to-total test runs before any band is published.

## Interface

Comfort maps carry an uncertainty band, and interventions are ranked by cooling per unit of input uncertainty, so a practitioner reads "cooler here, and this conclusion survives the height error". That is the interface's reason to exist and the clearest way to make the error budget visible rather than buried in a methods section. It does not model wind, building energy or anthropogenic heat.

## Schedule

P1 height reconstruction and the 20-building audit with MAE/RMSE reported before any physics changes; P2 canopy source audit and the same treatment; P3 GPU core with CPU parity; P4 attribution under propagated uncertainty; P5 the loop, the bounded placement search and the Delhi experiment; P6 paper. Pre-registered pivot: if the audit exceeds 3 m RMSE, the paper reports the reconstruction error and the method as the contribution and stops claiming decision-grade maps.

## Cost claims

Two same-machine measurements: our GPU core versus the repo's numpy CPU path (rays/second, scenario seconds), and our full-day precinct run versus a `solweig` reference run on identical reconstructed inputs (wall clock alongside agreement). Runtime is published only next to the accuracy band, because speed without validity is not a claim worth making.

## Paper plan

Contribution: a transferable reconstruction method for microclimate-grade geometry in data-scarce cities, with an error budget propagated into comfort and intervention answers, demonstrated in Delhi. Evidence: height-audit error distribution, canopy audit, component parity and reference agreement, attribution with bands, the marginal cooling curve from the bounded search, and the runtime table. Venue class: urban climate, where an error-budget contribution is native.

## Cut list

Browser compute, autograd, field campaigns and multi-city generalisation are out. The remaining stretch is the placement search, and it is explicitly optional in the schedule — the error budget is not.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| Building heights for South Asia are available at 4 m effective resolution annually from 2016-2023, which is the input the reconstruction starts from. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| A parity-tested SOLWEIG implementation exists as a Python package, making an independent validation target feasible without QGIS. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| A published workflow exists for disaggregating the 2.5D height raster onto building footprints. | unverified | - |
| A global canopy-height product at 30 m covers urban India, so canopy is a data task rather than an invention. | unverified | - |
| ENVI-met's documented scope is 1-10 m resolution over 24-48 hour periods, with large-domain runtimes reported in hours. | unverified | - |
