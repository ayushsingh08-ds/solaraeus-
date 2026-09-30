---
id: "001"
slug: solaraeus
idea: Solaraeus — a 3D urban microclimate digital twin that computes 1m sky view factor, shadows, mean radiant temperature and UTCI over Washington Square Park and serves them to an interactive browser viewer.
date: 2026-09-30
verdict: FIX FIRST
biggest_risk: The physics is already free (UMEP/SOLWEIG, Ladybug; ENVI-met at the paid tier) and the flagship site's dominant comfort driver — tree canopy — is not modelled at all, so no buyer has a reason to pay for this specific thing.
open_questions: 4
---

# 001 — Solaraeus

A Stage 1 microclimate pipeline for Washington Square Park, NYC: Overture building footprints plus a 1m LiDAR DEM harmonized to EPSG:32618, a 36-radial Steyn (1980) sky view factor, diurnal shadow casting, Stefan-Boltzmann mean radiant temperature, UTCI, a watertight 3D mesh, NetCDF export, and a React + Three.js viewer. The claim under judgement is not whether it computes physics correctly — the test suite suggests it does — but whether anyone pays for it.

## Believer

**WHO desperately needs this.** The person who has to *convince someone else* that a plaza re-paving, a bus shelter, or a row of street trees will cut pedestrian heat stress — an urban designer, a landscape architect, or a parks planner standing in a public meeting. What they do today is show an ENVI-met render that costs a licence and a week of specialist setup, or hand over a static raster nobody in the room can read, or wave their hands. Nobody in that position currently has a link they can open in a browser, move the sun, walk the block, and hand to a sceptical committee member.

**WHY now.** The inputs that used to be the moat are free and public: 1m LiDAR and Overture footprints, ERA5 meteorology over the CDS API, and a browser that renders a 400,000-cell grid without a plugin. Five years ago this was a GIS analyst, a licensed desktop tool, and a week. The repo already demonstrates the whole chain runs end to end from one command, which is exactly the part most academic microclimate tools never fix.

**The best version.** Not a map viewer — a design instrument. A planner drags a canopy row across a corner of the park and watches pedestrian heat stress recompute before the meeting ends, then exports the before/after for the people who sign off on the budget. That artefact is the difference between "interesting model" and "thing that changed a decision".

**The unfair advantage.** The 3D web twin itself. SOLWEIG and UMEP are more mature science, but they hand you rasters in QGIS; the interactive, walkable, stakeholder-facing view is a real gap in the free tier, and this repo is already 80% of the way there. The reproducibility discipline (a single documented command regenerating every figure and dataset) is a second, quieter advantage: it is what makes a result defensible when someone disputes it.

**The one bet the whole idea rests on:** that a stakeholder who must persuade *other people* about heat pays for the interactive view, even when the underlying physics is free.

## Skeptic

**WHO will not pay.** The people who care most about pedestrian thermal comfort — researchers, students, the open-source QGIS crowd — pay exactly nothing, and their free tool is better than this one. The people who *could* pay, microclimate consultants at engineering and landscape firms, already own the paid incumbents, already have staff trained on them, and already sell the study. A Stage 1 model with no canopy, no wind field, and no validation against measurement does not replace what they bill with.

**The free workaround already exists, three times over.** UMEP's SOLWEIG implementation in QGIS computes SVF, shadows, mean radiant temperature, and UTCI from a DEM and building footprints — free, peer-reviewed, and validated in field studies. Ladybug Tools does the same inside the Rhino/Grasshopper workflow designers already use, also free. And ENVI-met owns the paid tier with a decade of validation literature behind it. Sparing a licence fee is not a buying motive; being the *fourth* option, with the least validation, is not a market position.

**The blind spot.** The flagship case study is a tree-heavy park, and trees are not in the model: `canopy` appears exactly once in this repo, as an `# optional` line in a planning document, and nowhere in `src/`. So at the one site the project tells its story about, the model omits the largest single determinant of pedestrian shade and will overstate heat stress in the places people actually sit. That is not a missing feature; it is a wrong answer at the loudest point of the demo. Compounding it, nothing in `outputs/` is checked against a measured Tmrt or air-temperature series — the figures are internally consistent, which is not the same as true.

**The single fastest way this dies.** A demo of one park with no user. The repo has 35 committed result artefacts, a passing physics test suite, and no user, no licence file, no price, and no pilot. It dies of being admired and unused.

**The fatal flaw:** if the honest answer to "who signs the invoice" is nobody — because this is a portfolio piece, a thesis, or a research interest — then do not build it as a product. It is already finished as a portfolio piece, and everything past Stage 1 is unpaid work.

## Investor

**Proof people will pay for this: no.** There is no price, no user, no pilot, and no waitlist anywhere in the repo. At this stage the evidence of demand is zero — not weak, zero.

**Where the money already sits.** Firms do spend real money on pedestrian microclimate studies, which is the encouraging half: the budget line exists and someone is already capturing it. The discouraging half is that the incumbent captures it as *consulting* — an expert's hours plus a licence — not as software, and the deliverable they hand over is a report, not a web app.
**How soon the first real dollar arrives.** Two paths, and the gap between them is the whole decision:

- **Service path (sell the study, not the software):** pitch a fixed-price single-site pedestrian heat study at **$500–1,500**, deliverable a one-week report plus the interactive view. First dollar realistically in **2–4 weeks**.
- **Municipal software path:** sell to a parks or transportation agency. Procurement alone runs **6–18 months**, with pilot-then-purchase cycles on top. First dollar in **a year or more**, and the whole budget for a first pilot is likely under five figures.

**The cheapest test that proves demand this week.** One day of writing, zero build: email **10 named people** who commissioned or ran an urban heat or microclimate study in the last twelve months — engineering firms, landscape practices, city sustainability offices — with a one-line offer: *fixed-price one-week pedestrian heat study of your site, $750, interactive view included*. Ask for a quote request or a purchase order, never for an opinion. Success bar: **one person asks for a quote, or agrees to pay any amount ≥ $500.**

**Would I put my own money in? No — not yet.** The model works and the compute cost is trivial, but the market is unproven and the likely buyer count is small and slow. **The one number that changes my mind:** one paid pilot invoice at $500 or more from a buyer who is not a friend, or three of those ten recipients asking for a quote. Either one turns this from a portfolio piece into a business hypothesis worth funding.

## Judge

**VERDICT:** FIX FIRST

**Biggest risk:** Free tools already cover the physics, and the flagship study site's dominant comfort factor — tree canopy — is not modelled, so nobody currently has a reason to pay for this specific thing.

**10-minute test:** Write one paragraph and email it to 5 named people who ran a microclimate study in the last year: *"Fixed-price one-week pedestrian heat study of your site, $750, delivered as an interactive view you can show your client."* Count how many ask for a quote. Zero replies means no market and the next ruling is KILL; one quote request means BUILD a service around this pipeline before adding a single feature.

**Flips to BUILD if:** two things happen together — (1) one named buyer agrees in writing to pay $500 or more for a study on their site, and (2) canopy is added and the flagship result is validated against at least one measured temperature or Tmrt series, so the demo is not wrong where it is loudest. Do all of that *after* the test, not before: no buyer means the physics work is a hobby, and the current repo is already a good hobby.

**Why not KILL:** the pipeline genuinely runs end to end and reproducibly, which is more than most tools in this niche manage, and the interactive stakeholder view is a real gap in the free tier. The idea is not bad; it is aimed at the wrong buyer and missing the factor that matters at its own case study. Both are fixable in a week, cheaper than Stage 2.

**Open questions carried forward:**

- Will anyone pay for the interactive view when the raster output is free? Completely untested — and it is the load-bearing bet.
- Does adding canopy change the headline WSP numbers enough to invalidate the committed figures in `outputs/`?
- Is there a published or measured Tmrt / air-temperature series for Washington Square Park to validate against, or must validation wait for a field campaign?
- Is the intent to sell this at all, or is it a portfolio/thesis artefact? If the latter, stop after Stage 1 and keep it as research.
