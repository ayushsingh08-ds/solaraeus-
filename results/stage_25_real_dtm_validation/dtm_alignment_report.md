# SOLARAEUS Stage 25: Street-Scale DTM Alignment & Engineering Validation Report

**Stage**: Stage 25 — Real Street-Scale DTM Acquisition and Validation  
**Timestamp**: 2026-10-08T08:55:45.134778+00:00  
**Classification**: `SYNTHETIC_TERRAIN_ONLY`  
**Governing Rule**: Global Safety Rule 6 (Do Not Classify FABDEM as a Street-Scale DTM) & Rule 13 (Do Not Integrate Real-World DTM Before Stage 25 Passes)  

---

## 1. Topographic Data Evaluation
1. **FABDEM v1.2 Evaluation**:
   - Native cell size is $30.87\text{ m}$.
   - Vertical error is $\pm 1.82\text{ m}$, an order of magnitude larger than actual sidewalk curbs ($150\text{ mm}$).
   - Attempting to bilinear-resample FABDEM to $0.5\text{ m}$ creates false gradients across street pavements, tilting building foundations into the earth.
   - **Formal Finding**: FABDEM remains classified as `REGIONAL_REFERENCE_ONLY`.

2. **Measured Municipal DTM Status**:
   - No engineering total-station curb and gutter survey is present in the workspace.
   - Measured street DTM status is officially classified as `UNAVAILABLE`.

3. **Synthetic Terrain Profiles**:
   - 4 synthetic test geometries were designed and audited for software engine validation:
     - Profile 1: Flat grade ($z = 0.0\text{ m}$)
     - Profile 2: Uniform slope ($2.5\%$ longitudinal grade)
     - Profile 3: Stepped curb terrace ($0.15\text{ m}$ curb step)
     - Profile 4: Swale/depression with NoData boundary handling

---

## 2. Gate Determination
Because measured engineering survey data is unavailable, this stage cannot emit `MEASURED_STREET_SCALE_DTM_VALIDATED`.
Pursuant to post-roadmap specifications, the stage completes as:
```text
STAGE_25_SYNTHETIC_TERRAIN_ONLY
```
**Impact**: Real-world terrain claims and real-world terrain simulation remain **STRICTLY BLOCKED**.
