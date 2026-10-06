# Manual review checklist — Bengaluru Church Street handoff v2

Prepared 2026-10-07T01:42:00.174501+05:30. Data preparation is not manual sign-off.

- [ ] Confirm the unchanged main reporting boundary and 75 m squared-corner UTM shadow-context boundary. Keep all reported pedestrian receptors inside the main boundary.
- [ ] Review all 37 rows in `processed/building_height_review.csv`; keep observed, source-provided, floor-derived, ML and manual-estimate evidence separate. Record accepted height, source category, evidence, reviewer and date.
- [ ] Resolve absent ML estimates for B19, B23, B32 and B36; B19/B36 have unverified two-floor tags, B23/B32 have no floor count. No default height is assigned.
- [ ] Prioritise B02, B03, B17, B19, B23, B31, B32, B36 and B37; review tall Barton Centre B10 and small-footprint B27 as well. Automated priority is not calibrated confidence.
- [ ] Review all 123 context-caster records, including 86 outside the main selection. Unknown context heights may affect main-boundary shadows.
- [ ] Check footprint alignment/completeness against independent imagery or field evidence. Inspect edge-crossing geometry, trees, awnings and existing canopy shadows.
- [ ] Accept elevation only as coarse DEM metadata/validation; it is not certified bare earth, roof data or local surveyed terrain. Flat model-relative z=0 remains an assumption.
- [ ] Confirm off-site station forcing, 09:00 UTC = 14:30 IST, derived RH and unknown wind-instrument height. Do not call it on-site weather.
- [ ] Resolve the solar provider hourly start/end convention and averaging before aligning solar fluxes to the station instant.
- [ ] Accept/correct the exact panel coordinates, true/grid orientation, 0.10 m thickness, opaque material, assumed albedo/emissivity/initial temperature and omitted posts.
- [ ] Check actual walkway and clearances. This panel is a hypothetical simulation object, not an approved physical installation.
- [ ] Accept or replace each material and initial-temperature assumption; determine a defensible baseline vegetation policy.
- [ ] Verify 75 m shadow-context adequacy using shadow reach and expanded-buffer sensitivity after heights are known.
- [ ] Confirm record-specific NOAA station redistribution terms before public redistribution; retain all dataset attributions.
- [ ] Sign below only when the manual package is genuinely accepted.

Researcher: __________________
Reviewed date/time and timezone: __________________
Evidence/changes: __________________
Ready for simulation coding: YES / NO (currently NO)
