---
planner: planner-d
round: 1
strategy_family: data-scarcity-first
thesis: Make the transferable method the contribution — reconstructing heights and canopy for a data-poor city with a published error budget, then show that the reconstructed precinct still yields decision-grade comfort answers.
date: 2026-09-30
status: competing
sources_verified: 2
sources_unverified: 3
---

# planner-d — round 1

## Strategy

Family: **data-scarcity-first**. The other plans treat Delhi as a case study to run their tool on. This plan treats the *data gap* as the scientific problem: free footprint data for Indian cities has no reliable heights, canopy is coarse, and every published microclimate study quietly runs where the data is good. The bet is that "how wrong can a comfort map be when the heights are reconstructed rather than surveyed, and how do you bound that error" is a genuinely publishable question — and that the answer is what makes this tool usable in the cities that need it most.

## Architecture

Our own GPU ray tracer (CuPy first; WebGPU later only if the browser path earns its place), because the error budget has to be propagated *through* our own solver to be meaningful — you cannot audit someone else's black box. The reference implementation (`solweig`) is used as the validation target, not as the engine, so the two implementations are genuinely independent. The repo's numpy physics remains the CPU oracle; parity tolerance per component is stated; CI stays GPU-free.

## Attribution

Components are produced by our solver (direct, diffuse sky, ground-reflected, building longwave, sky longwave, canopy transmission) and each is paired with the input uncertainty that feeds it — height error into building longwave and shadowing, canopy-density error into transmission — so the paper can report attribution *with* error bars instead of point estimates. Sum-to-total is tested, and the propagation is reported as a sensitivity band, not a confidence interval the model cannot justify.

## Interface

The tool reports uncertainty as part of the answer: comfort maps carry a band, and interventions are ranked by cooling per unit of input uncertainty. A practitioner sees not just "cooler here" but "cooler here, and this conclusion survives the height error". That framing is the interface's whole reason to exist. It does not model wind, building energy, or anthropogenic heat.

## Schedule

P1 build the height reconstruction: pull the 4 m building-height raster, disaggregate to footprints, and audit 20 buildings against Street View, reporting MAE/RMSE — this is the first deliverable, before any physics changes; P2 canopy source audit and the same treatment; P3 GPU core with CPU parity; P4 attribution under propagated uncertainty; P5 the loop and the Delhi experiment; P6 paper. Gates: if the height audit error exceeds a pre-registered threshold (say 3 m RMSE), the paper pivots to reporting the error and the method rather than claiming decision-grade maps, and says so.

## Cost claims

Two measured comparisons on one machine: our GPU core versus the repo's numpy CPU path (rays/second, scenario seconds), and our full-day precinct run versus a `solweig` reference run on identical reconstructed inputs (wall clock, and agreement). Runtime is reported alongside the accuracy band, because speed without validity is not a claim anyone should accept.

## Paper plan

Contribution: **a transferable method for reconstructing microclimate-grade geometry in data-scarce cities, with an error budget propagated into comfort and intervention answers, demonstrated in Delhi.** Evidence: height-audit error distribution; canopy-source audit; component parity and reference agreement; attribution with uncertainty; intervention ranking with per-tree cooling; runtime table. Venue class: urban climate. The novelty does not depend on beating anyone's kernel, which is precisely why it is robust to reviewers.

## Cut list

Browser-native compute, differentiable optimisation, field measurement campaigns, and multi-city generalisation are out. Ambition is spent on the error budget, because that is the claim the free alternatives do not make.

## Sourcing ledger

| Claim | Source | Accessed |
| :--- | :--- | :--- |
| Building presence, fractional counts and heights are available for South Asia as an annual 4 m effective-resolution raster covering 2016-2023. | https://sites.research.google/gr/open-buildings/temporal/ | 2026-09-30 |
| A parity-tested SOLWEIG implementation exists as a Python package with optional WebGPU acceleration, which makes it usable as an independent validation target. | https://github.com/UMEP-dev/solweig | 2026-09-30 |
| A global canopy-height product exists at 30 m and covers urban India, so canopy is a data task rather than an invention. | unverified | - |
| Published Tmrt validation error is commonly around 5 K RMSE, which sets the expected agreement envelope. | unverified | - |
| ENVI-met's documented scope is 1-10 m resolution over 24-48 hour periods, with runtimes reported in hours for large domains. | unverified | - |
