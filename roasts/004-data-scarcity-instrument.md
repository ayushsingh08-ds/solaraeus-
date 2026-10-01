---
id: "004"
slug: data-scarcity-instrument
idea: The planning tournament's surviving plan — build Solaraeus as a data-scarce-city microclimate instrument: our own GPU ray tracer, building heights and canopy reconstructed with a published error budget, a design loop that shows uncertainty, validated component by component against the pip-installable SOLWEIG reference, with a Delhi case study and an urban-climate paper.
date: 2026-09-30
verdict: BUILD
biggest_risk: The propagated error band may be so wide that the intervention ranking is statistically indistinguishable from noise, which would leave the method publishable while the instrument's headline answer — where to plant — collapses.
open_questions: 3
---

# 003 — The surviving tournament plan as a data-scarce-city instrument

The tournament ran four generalist planners over three rounds, eliminating one per round, and the survivor is the `data-scarcity-first` family: reconstruct the geometry a city does not have, publish what the reconstruction costs you in accuracy, and prove the answer is still good enough to decide where to plant. This ruling is the council's attack on that plan before it is built.

## Believer

**WHO desperately needs this.** The people who must decide where shade goes in a city that has almost no survey data: municipal parks and climate-cell staff in an Indian megacity, and the small consultancies they hire. What they do today is either nothing, or a satellite land-surface-temperature map at 30 m that shows a hot neighbourhood and cannot say which side of which street to plant on.

**WHY now.** Three things landed at once: a paragraph of code installs the reference SOLWEIG implementation with a canopy input and optional GPU acceleration, a 4 m annual building-height raster now covers South Asia, and GPU ray tracing runs on a gaming laptop. The plan's first two phases cost a day, not a quarter — you can falsify the whole premise before writing a kernel.

**The best version.** The instrument answers the practitioner's actual question with its own uncertainty attached: *plant here, this much cooler, and this conclusion survives the height error*. No free tool says that last clause, and the intervening-weeks pay-off is a ranked list rather than a prettier map.

**The unfair advantage.** The plan owns its engine, so the error budget is propagated through a solver it controls — a wrapper cannot make that claim about someone else's black box, and a black box cannot redesign itself for a design loop.

**The one bet the whole idea rests on:** that a decision-maker values a bonded error bar more than a prettier map, and that the band stays narrow enough for the ranking to mean something.

## Skeptic

**WHO will not pay.** Nobody, again, and this plan does not change that. It is a research plan with an error budget, and an error budget is exactly what a procurement officer cannot put in a tender. The buyer problem from ruling 001 is untouched — this plan buys credibility, not customers, and the plan itself never claims otherwise.

**The free workaround, and it is unusually strong here.** The plan validates against `solweig`, which is pip-installable, canopy-aware, optionally GPU-accelerated and audited against the reference model. A reviewer will ask the obvious question the plan half-answers: if the reference is credible enough to validate against, why is the project maintaining its own engine at all? "Because the error budget must be propagated through a solver we control" is a real answer, but it is one sentence doing an enormous amount of work — and it is the sentence the paper's contribution will stand or fall on.

**The blind spot.** The plan's novelty is a published error budget for reconstructed geometry, which means the paper's headline is a number the plan has not measured yet, on data the plan has not downloaded. A 20-building audit is a *sample*; precinct-wide error is an extrapolation from it, and the plan says "distribution" where a reviewer will read "20 points, chosen by the author, compared against street-level imagery of unknown vintage". That is a legitimate method — it is also one referee report away from being called anecdotal, and the plan does not pre-commit to how the 20 are selected.

**The single fastest way this dies.** The height raster's vertical accuracy turns out to be worse than 3 m RMSE in dense Delhi. The pre-registered pivot then fires honestly and the paper becomes a reconstruction-error study: publishable, much weaker, and about a method others can replicate in an afternoon.

**The fatal flaw:** if the error band is wide enough to matter, the ranking that gives the instrument its reason to exist is noise; if the band is narrow, the contribution is small. The plan has not established that a middle ground exists — and until it does, it is selling an instrument before knowing whether its answer survives its own error bar.

## Investor

**Proof people will pay: still zero, and this plan is not trying.** It buys credibility, which ruling 002 identified as the collateral the consulting path needs. Judge it as an investment in evidence, not revenue.

**Time and cost to the first falsifiable answer: one day.** Download the height raster over the precinct, audit five buildings against imagery, run the reference implementation once on reconstructed inputs. That is the cheapest, most falsifiable first day any plan in this thread has offered, and it is the single strongest thing about it.

**The cheapest test that settles the central question this week.** Not the paper, not the kernel: take the reconstructed heights, put a defensible ± band on them, re-run the intervention ranking inside that band, and see whether the top five sites survive the perturbation. If the ordering scrambles, the instrument's headline output is noise and the plan's pre-registered pivot must fire *before* the GPU work, not after.

**Would I put my own money in? No — but I would fund the first day.** The one number that changes my mind: an intervention ranking whose *ordering* is stable under the propagated band, reported alongside the audit RMSE. Stability of the ranking, not narrowness of the band, is the number that decides whether this is an instrument or a poster.

## Judge

**VERDICT:** BUILD

**Biggest risk:** The propagated error band may be so wide that the intervention ranking is statistically indistinguishable from noise, which would leave the method publishable while the instrument's headline answer — where to plant — collapses.

**10-minute test:** Before writing a single kernel, download the 4 m height raster over the Lodhi Garden precinct and check five buildings against street-level imagery. If the spread is already ±3 m or worse on five buildings, the pre-registered pivot fires now: the paper becomes a reconstruction-error study and the design instrument is deferred, not built on hope.

**Flips to FIX FIRST if:** the five-building check blows the error bar, or the ranking-stability check comes back scrambled — in either case the fix is explicit: re-scope to the reconstruction method and drop every decision-grade claim from the interface and the abstract. It would flip to KILL only if both the audit and the reference comparison fail, which would mean neither the method nor the validation survives, and there is nothing left to publish.

**Why BUILD rather than FIX FIRST, given the roast's history.** Two previous rulings on this project returned FIX FIRST for the same reason both times: the work was aimed at an unproven buyer and unmeasured physics. This plan is different in the one way that matters to the council — its first two phases are cheap, falsifiable and *scheduled before any novel engineering*, and it has pre-committed to publishing the failure. A plan whose worst case is a shorter, honest paper is a plan worth building. The category error to avoid is treating BUILD as approval of the instrument: this ruling approves the audit and the comparison, nothing else.

**Open questions carried forward:**

- **[003]** Does the 4 m height raster clear the pre-registered 3 m RMSE bar in dense Delhi, or does the audit force the pivot to a reconstruction-error paper?
- **[003]** Is the intervention ranking stable once the uncertainty band is applied — or are the top sites statistically indistinguishable, which would make the instrument's headline answer noise?
- **[003]** Will component-level agreement with the reference implementation hold within the stated tolerance on reconstructed inputs, or does the comparison itself become the paper's finding?
