# SOLARAEUS Tree-Geometry and Terrain Researcher Sign-Off Form

**Project**: SOLARAEUS: High-Performance GPU Ray-Traced Urban Microclimate Simulation  
**Study Site**: Bengaluru, Church Street Pedestrian Corridor  
**Stage**: Data-Review, Uncertainty-Bounding, and Sign-Off Preparation  
**Date**: October 7, 2026  
**Document Status**: PENDING RESEARCHER COMPLETION (Do NOT auto-fill checkboxes)

---

### Instructions for Lead Researcher
Review the accompanying [RESEARCHER_REVIEW_REPORT.md](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/RESEARCHER_REVIEW_REPORT.md), [tree_dimension_uncertainty_bounds.csv](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/tree_dimension_uncertainty_bounds.csv), and [terrain_review_decision.json](file:///c:/Users/AYUSH%20SINGH/Documents/GitHub/solaraeus/data/review/terrain_review_decision.json). Check the appropriate boxes below to authorize or restrict promotion into subsequent simulation workflows.

---

### Section 1 — Data Review and Acceptance Decisions

Please evaluate each item and mark the corresponding decision box:

- [ ] **1. Tree Locations Accepted**:
  - The 14 BBMP municipal census coordinates (6 core trees T08–T13 and 8 context trees T01–T07, T14) are verified in EPSG:32643 and Church Street local coordinates.

- [ ] **2. Species Labels Accepted**:
  - Reported botanical binomials from the BBMP census are accepted as provisional taxon priors.

- [ ] **3. Current-Existence Statuses Accepted**:
  - All 14 trees retain `CURRENT_EXISTENCE_UNCERTAIN` policy. Historical imagery (2018–2020) is recognized as non-authoritative for current 2026 ground truth.

- [ ] **4. Dimension Bounds Accepted**:
  - The conservative-small, nominal, and conservative-large geometric bounding envelope for the six core trees is accepted for sensitivity analysis.

- [ ] **5. Nominal Geometry Accepted for Level 1 Testing**:
  - The nominal photo-estimates are approved strictly for provisional Level 1 sensitivity testing (not authoritative simulation certification).

- [ ] **6. Context-Tree Inclusion Accepted**:
  - Optional inclusion of entrance conifers T06 and T07 approved; exclusion of distant context tree T14 approved.

- [ ] **7. FABDEM Use Restricted to Regional Reference**:
  - FABDEM v1.2 is restricted to regional macro-topography. Direct ingestion as microscale curb/sidewalk DTM is strictly forbidden.

- [ ] **8. Canopy Parameters Accepted as Assumptions Only**:
  - Radiative parameters (transmissivity $\tau$, LAI, LAD) remain classified as literature assumptions. Level 2 canopy parameter validation is pending.

- [ ] **9. Simulation Promotion Approved**:
  - Authorization to promote candidate files specified in `promotion_candidates.json` into `data/processed/`.

---

### Section 2 — Sign-Off Metadata and Approval Record

**Researcher Name**: __________________________________________________  

**Institutional / Project Affiliation**: ________________________________  

**Sign-Off Date**: ____________________________________________________  

**Approval Identifier / Token**: ______________________________________  

**Researcher Comments & Conditions**:  
```text
[Enter comments, scope limitations, or field survey directives here]
```

---
*Note: This sign-off form must remain unsigned and unchecked until explicit manual researcher review is executed. Physics solvers remain completely locked against unverified tree geometry.*
