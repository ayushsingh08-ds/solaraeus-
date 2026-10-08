# SOLARAEUS Stage 25: Available-Data Terrain Validation Report

**Stage**: Stage 25 — Available-Data Terrain Validation  
**Timestamp**: 2026-10-08T09:18:45.303455+00:00  
**Classification**: `SYNTHETIC_TERRAIN_ONLY`  
**Acceptance Token**: `STAGE_25_SYNTHETIC_TERRAIN_ONLY`  

---

## 1. Topographic Datasets Audited
1. **FABDEM v1.2**:
   - Native cell resolution: $30.87\text{ m}$.
   - Vertical error: $\pm 1.82\text{ m}$ RMSE.
   - Classification: `REGIONAL_REFERENCE_ONLY`. Retained as a regional elevation benchmark, barred from microscale street simulation.
2. **Synthetic Terrain Profiles**:
   - Resolution: $0.50\text{ m}$.
   - Profiles: Flat ($0\text{ m}$), Incline ($2.5\%$ slope), Stepped Curb ($0.15\text{ m}$ step), Swale (drainage depression).
   - Validated for numerical ray-tracing, receptor elevation calculations, and incremental caching.
3. **Measured Street-Scale DTM**:
   - Status: `MISSING`.

---

## 2. Gate Decision
Pursuant to researcher policy, synthetic terrain is approved for solver mechanics and sensitivity testing. Real-world street-scale claims remain blocked.
