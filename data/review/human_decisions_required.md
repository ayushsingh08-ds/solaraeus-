# SOLARAEUS Human Decisions Required Before Simulation Integration

**Date**: October 7, 2026  
**Audience**: Lead Scientific Researcher & Project Principal Investigators  
**Status**: Awaiting Human Decision Input

The automated data-preparation and uncertainty-bounding pipeline has concluded. Under project scientific integrity rules, the agent is strictly prohibited from making executive research assumptions or authorizing simulation promotion on behalf of human researchers.

Below are the **10 explicit scientific decisions** that require human determination:

---

### 1. Are the six core tree locations accepted?
- **Evidence**: Verified in BBMP municipal tree census (July 2026 dataset), georeferenced to EPSG:32643 and Church Street local coordinates. All cluster along the southern pedestrian sidewalk ($X \in [20.07, 97.09]\text{ m}$).
- **Human Decision**: Accept as authoritative 2D horizontal coordinates for Church Street pedestrian corridor modeling?

### 2. Are the reported species accepted?
- **Evidence**: Municipal botanical classification: *Ficus religiosa* (T08), *Syzygium cumini* (T09, T10), *Saraca asoca* (T11, T12), *Tecoma stans* (T13).
- **Human Decision**: Accept reported binomials as provisional priors, or require independent botanical herbarium voucher verification?

### 3. Are the historical image matches acceptable?
- **Evidence**: 29 KartaView sequential photos (June 2020) and 8 Wikimedia Commons photos (2018–2024). All six core trees matched with `MATCH_CONFIRMED`.
- **Human Decision**: Accept photographic cross-referencing as empirical basis for qualitative crown shape and relative proportion scaling?

### 4. Are the dimension uncertainty bounds acceptable?
- **Evidence**: Three bounded states formulated for each core tree: Conservative-Small (Min), Nominal (Central), and Conservative-Large (Max) based on perspective scaling against building floor plates and vehicular clearances.
- **Human Decision**: Accept bounding envelope as defensible representation of geometric uncertainty?

### 5. May nominal geometry be used for Level 1 sensitivity testing?
- **Evidence**: Nominal photo estimates provide realistic crown extents ($3.5\text{–}12.0\text{ m}$ diameter, $5.0\text{–}13.5\text{ m}$ height) for preliminary shading sensitivity.
- **Human Decision**: Authorize nominal geometry strictly for sensitivity exploration, with primary published certificate runs remaining blocked?

### 6. Are context trees required in the initial scene?
- **Evidence**: Conifers T06 and T07 (*Araucaria columnaris*) at western entrance ($X = -3.3\text{ m}, -9.3\text{ m}$) cast evening shadows into the western corridor entrance. Tree T14 is $>70\text{ m}$ north and casts no corridor shadows.
- **Human Decision**: Include T06 and T07 as optional context geometry, and formally exclude T14 from initial scene?

### 7. Is FABDEM acceptable only as a regional reference?
- **Evidence**: FABDEM v1.2 stripped $+16.6\text{ m}$ commercial building radar artifacts, establishing a clean bare-earth slope from West ($917.4\text{ m}$) to East ($910.1\text{ m}$). Native resolution ($\approx 30.87\text{ m}$) cannot resolve curbs or gutters.
- **Human Decision**: Restrict FABDEM to regional macro-topography boundary reference, and prohibit its ingestion as microscale street DTM?

### 8. Should simulation wait for a street-scale DTM?
- **Evidence**: Real Church Street contains $150\text{ mm}$ curb steps and $1:50$ transverse drainage cross-slopes that affect pedestrian surface geometry.
- **Human Decision**: Proceed with planar inclined corridor baseline based on FABDEM slope, or block 3D terrain simulation until an engineering curb survey is conducted?

### 9. Are literature canopy assumptions acceptable for a future sensitivity-only study?
- **Evidence**: Physical shortwave transmissivity ($\tau \in [0.05, 0.30]$), LAI, and LAD are literature assumptions from SOLWEIG / ENVI-met databases; no on-site pyranometer measurements exist.
- **Human Decision**: Authorize literature parameter ranges strictly for future sensitivity studies, while blocking Level 2 canopy certification?

### 10. Is any data approved for promotion?
- **Evidence**: Four candidates logged in `final_promotion_manifest.json` (2D tree locations, photo catalog, regional FABDEM raster, uncertainty bounds).
- **Human Decision**: Complete and sign `final_researcher_signoff_form.md` to authorize file promotion into `data/processed/`, or retain in `data/review/` pending field survey?

---
*End of Human Decisions Document.*
