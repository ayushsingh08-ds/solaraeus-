# SOLARAEUS Final Researcher Sign-Off and Promotion Authorization Form

**Project**: SOLARAEUS: High-Performance GPU Ray-Traced Urban Microclimate Simulation  
**Study Corridor**: Church Street, Bengaluru, Karnataka, India  
**Stage**: Final Researcher Sign-Off and Promotion Readiness  
**Date**: October 7, 2026  
**Status**: PENDING HUMAN RESEARCHER AUTHORIZATION (All checkboxes deliberately unchecked)

---

### Mandatory Notice for Reviewing Researcher
This form is the governing barrier preventing unvalidated interim data from contaminating the validated GPU physics solver and optimization routines. No promotion to `data/processed/` and no integration into solver code may occur until this form is completed and signed by an authorized researcher.

---

### Part 1 — Dataset and Inventory Decisions

Please review and mark each decision box:

- [ ] **1. Tree locations accepted as census-derived**:
  - The 14 BBMP municipal census coordinates (6 core trees T08–T13 and 8 context trees T01–T07, T14) are verified in EPSG:32643 and Church Street local coordinates.

- [ ] **2. Reported species accepted**:
  - Reported botanical binomials from the BBMP census are accepted as provisional taxon priors.

- [ ] **3. Current tree existence uncertainty accepted**:
  - All 14 trees retain `CURRENT_EXISTENCE_UNCERTAIN` policy. Historical imagery (2018–2020) is recognized as non-authoritative for current 2026 ground truth.

---

### Part 2 — Geometric Uncertainty Bounds (Core Trees T08 to T13)

Please review each core tree bounding envelope:

- [ ] **4. T08 (*Ficus religiosa*) geometry bounds accepted**:
  - Height $[11.0, 13.5, 16.0]	ext{ m}$, Crown Diameter $[9.5, 12.0, 15.0]	ext{ m}$, Crown Base $[3.8, 4.2, 4.5]	ext{ m}$.

- [ ] **5. T09 (*Syzygium cumini*) geometry bounds accepted**:
  - Height $[9.0, 11.0, 13.0]	ext{ m}$, Crown Diameter $[7.0, 8.5, 10.5]	ext{ m}$, Crown Base $[3.2, 3.8, 4.2]	ext{ m}$.

- [ ] **6. T10 (*Syzygium cumini*) geometry bounds accepted**:
  - Height $[7.5, 9.5, 11.5]	ext{ m}$, Crown Diameter $[6.0, 7.5, 9.0]	ext{ m}$, Crown Base $[2.8, 3.2, 3.6]	ext{ m}$.

- [ ] **7. T11 (*Saraca asoca*) geometry bounds accepted**:
  - Height $[6.5, 8.0, 9.5]	ext{ m}$, Crown Diameter $[4.2, 5.5, 6.8]	ext{ m}$, Crown Base $[2.4, 2.8, 3.2]	ext{ m}$.

- [ ] **8. T12 (*Saraca asoca*) geometry bounds accepted**:
  - Height $[6.0, 7.5, 9.0]	ext{ m}$, Crown Diameter $[3.8, 5.0, 6.2]	ext{ m}$, Crown Base $[2.2, 2.6, 3.0]	ext{ m}$.

- [ ] **9. T13 (*Tecoma stans*) geometry bounds accepted**:
  - Height $[3.8, 5.0, 6.5]	ext{ m}$, Crown Diameter $[2.6, 3.5, 4.5]	ext{ m}$, Crown Base $[1.4, 1.8, 2.2]	ext{ m}$.

- [ ] **10. Nominal geometry approved for Level 1 sensitivity testing**:
  - Nominal photo-estimates approved strictly for provisional Level 1 sensitivity bounding studies (not authoritative simulation certification).

- [ ] **11. Geometry approved for authoritative simulation**:
  - *(Leave unchecked if awaiting laser survey / TLS field ground truth)*.

---

### Part 3 — Context Trees & Terrain Governance

- [ ] **12. Context-tree inclusion accepted**:
  - Inclusion of western entrance conifers T06 and T07 as optional context geometry; exclusion of distant tree T14.

- [ ] **13. FABDEM restricted to regional reference use**:
  - FABDEM v1.2 restricted to regional macro-topography. Direct ingestion as microscale curb/sidewalk DTM is strictly forbidden.

- [ ] **14. Street-scale DTM requirement acknowledged**:
  - Acknowledges that sub-metre curb ($150	ext{ mm}$), gutter, and sidewalk cross-fall ($1:50$) data remains missing.

---

### Part 4 — Canopy Physics & Promotion Authorization

- [ ] **15. Canopy parameters remain literature assumptions**:
  - Shortwave transmissivity $\tau$, leaf albedo, and emissivity remain literature assumptions and must not be hardcoded as empirical truth.

- [ ] **16. LAI/LAD remain unvalidated**:
  - Leaf Area Index and Leaf Area Density profiles remain unvalidated pending radiometric / optical canopy audit.

- [ ] **17. Field validation requirement acknowledged**:
  - Acknowledges that on-site 2026 pedestrian validation and optical survey are required to close scientific gaps.

- [ ] **18. Promotion to processed data approved**:
  - Authorizes promotion of candidate files specified in `final_promotion_manifest.json` from `data/interim/` to `data/processed/`.

- [ ] **19. Simulation integration approved**:
  - Authorizes GPU/CPU solver code modification to ingest approved geometry. *(Leave unchecked until all prerequisites are fulfilled)*.

---

### Researcher Authorization & Sign-Off Record

**Researcher Name**: __________________________________________________  

**Institution**: ________________________________________________________  

**Date**: ______________________________________________________________  

**Approval Identifier**: ________________________________________________  

**Comments & Restrictions**:  
```text
[Enter directives, scope limitations, or field survey requirements here]
```

**Signature**: _________________________________________________________  

---
*Status: PENDING HUMAN RESEARCHER SIGNATURE. Solvers and processed directory remain locked.*
