---
id: "002"
slug: free-package-funnel
idea: Publish Solaraeus as a free, pip-installable, canopy-aware package and use it as a credibility and lead funnel for consulting work instead of a paid product.
date: 2026-09-30
verdict: FIX FIRST
biggest_risk: A free package does not generate consulting leads by itself, so the plan's only revenue step rests on hope instead of a mechanism.
open_questions: 3
---

# 002 — Solaraeus as a free package and consulting funnel

The proposal is to stop selling software and instead publish the pipeline as a free, pip-installable, canopy-aware package, treating adoption as the credibility that eventually produces consulting work. Ruling 001 put the product framing on trial and returned FIX FIRST; this ruling covers the adjacent distribution strategy, and carries 001's open questions forward rather than restating them as settled.

## Believer

**WHO desperately needs this.** Two populations, and only one of them has money. The first is researchers and graduate students who need pedestrian-level Tmrt and UTCI on a specific site and cannot afford an ENVI-met seat or a week of setup — today they either re-implement sky view factor badly, give up, and use 30m satellite land-surface temperature that cannot tell a shaded bench from a sunlit one. The second is the small landscape or urban-design practice that needs one defensible shade analysis a year: today it either subcontracts a specialist or ships the project with no heat analysis at all.

**WHY now.** Everything that made this hard is free: 1m LiDAR, Overture footprints, ERA5 over the CDS API, and a browser that renders a 400,000-cell grid without a plugin. What is rare is not the physics but the packaging — this repo already regenerates every figure from one documented command, which is precisely the part most academic microclimate code never fixes. The marginal cost of turning that into a published package is a README and a wheel.

**The best version.** `pip install solaraeus`, point it at a bounding box, get 1m SVF, shadows, Tmrt, and UTCI plus a shareable interactive view, canopy included. It gets cited in papers and used in studio projects, and the people who use it are the same people who, when a client deadline and a budget appear, hire the person who wrote it.

**The unfair advantage.** Reproducibility plus the interactive view. The alternative free tools hand you rasters inside QGIS or Grasshopper; a one-command chain that also produces something a non-specialist can open in a browser is genuinely uncommon, and it is the difference between a tool academics cite and a tool practitioners use.

**The one bet the whole idea rests on:** that the population that adopts a free tool is the same population that later pays a human who knows that tool — that adoption converts into leads at all.

## Skeptic

**WHO will not pay.** Nobody, by construction: the artifact is free, and "consulting referrals" is not a revenue model, it is a hope that a revenue model appears later. The free-tool-to-consulting economy does exist — but the reference cases took a decade of peer-reviewed publication and institutional affiliation before anyone got hired off the back of their software. Attribution of a single author's repo is invisible next to that.

**The competitor or free workaround already solves this.** SOLWEIG inside UMEP is free, canopy-aware, validated against field measurements, and taught in the courses where these buyers learn their craft; vegetation is handled there by rasterizing trees into the surface model. Ladybug Tools is free and lives inside Grasshopper, where designers already work. A new free package enters a market whose incumbents are both better validated and better known, which means distribution — not physics — decides whether anyone ever sees it.

**The blind spot.** The builder has quietly equated "useful" with "used". Publishing costs a week; the obligations never end. Every rasterio or CRS break on a stranger's Windows machine, every "your Tmrt disagrees with my SOLWEIG run", every corrupted input file becomes unpaid work for an audience small enough that it does not reliably reach the people with budgets. Meanwhile the actual differentiator — canopy — is still missing from `src/`, so the package would launch claiming a capability it does not have.

**The single fastest way this dies.** Nobody notices. Three stars, no issues, six quiet months. The referrals never arrive, because they come from people with money already knowing your name, and an unpublicised package does not cause that.

**The fatal flaw:** if the objective is revenue, the plan contains no mechanism connecting the free artifact to a paying client, and no measurement that would reveal the funnel is empty — so do not build it as a business. Publish it as a portfolio piece at zero ongoing cost, or pick a channel with an observable lead, like direct outreach.

## Investor

**Is there proof people will PAY? No — and this plan does not test it.** Nothing has changed since 001: no buyer has been asked for anything. The honest thing to note is that the risk profile did change: this idea's downside is roughly a week of work against near-zero cash, which is a far cheaper way to be wrong than building a product.

**How soon the first real dollar arrives.** There is no direct path at all. Indirect revenue — "someone reads the repo, then hires me" — is unmeasurable in advance and realistically 6–18 months out, contingent on a reputation that may never compound. Compare the service path from 001: a named buyer, $500–1,500, first dollar in 2–4 weeks. This idea is strictly slower on money and strictly cheaper on cost.

**The single cheapest test that proves demand this week.** The same ten-email test 001 prescribed, run **before** publishing anything: ten named people who ran or commissioned a microclimate study in the last year, one line offering a fixed-price one-week study. It gates both paths, and it is still unrun. If one or more ask for a quote, publishing the package is a credibility asset for those buyers; if none of the ten reply, the free-package audience — the same population — is not there either, and the answer is a portfolio piece rather than a business.

**Would I put my own money in? No.** The one number that changes my mind: **100+ distinct installations or 5 unsolicited "can you help with my site?" emails within 90 days of publishing.** That would be a funnel that exists. Or, more simply, one paid pilot, which makes the entire question moot.

## Judge

**VERDICT:** FIX FIRST

**Biggest risk:** A free package does not generate consulting leads by itself, so the plan's only revenue step rests on hope instead of a mechanism.

**10-minute test:** Send the five emails 001 prescribed — *"fixed-price one-week pedestrian heat study of your site, $750, interactive view included"* — and count the quote requests before writing a single packaging script. Zero replies kills the business framing of this idea and of 001 together; one reply means the package is worth publishing as credibility collateral for that buyer.

**Flips to BUILD if:** a recipient asks for a quote **and** the published package ships a working `pip install` with canopy implemented and one validation plot against a measured reference — an observable lead plus an artifact that can survive an accuracy question. Publishing before both hold converts unpaid maintenance into a hobby with extra steps.

**Do this, not that:** the free package is a marketing budget, not a product. It is worth doing at near-zero marginal cost *in parallel* with the paid-service pitch, because it is the cheapest possible answer to "who is this person" — but it cannot be the plan's revenue mechanism, and it must not delay the ten-email test by a single day. Both paths are gated by the same experiment, and that experiment costs one afternoon.

**Open questions carried forward:**

- **[002]** Does publishing an unknown single-author package produce any observable lead within 90 days, or is it invisible without a distribution channel?
- **[001]** Will anyone pay for the interactive view when the raster output is free? Still completely untested, and it remains the load-bearing bet of both rulings — the five-email test answers it.
- **[001]** Is there a published or measured Tmrt or air-temperature series for Washington Square Park to validate against? Until there is, no canopy-aware claim can be defended in front of a paying client.
