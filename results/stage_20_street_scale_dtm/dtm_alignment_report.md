# Stage 20: Street-Scale DTM Alignment & Geometric Feasibility Report

**Date:** October 8, 2026  
**Status:** `SYNTHETIC_TERRAIN_ONLY_VALIDATED`  
**Classification:** `REGIONAL_REFERENCE_ONLY` for FABDEM | `SYNTHETIC_TERRAIN_ONLY` for Solver Tests  

---

## 1. Topographic Evaluation

### FABDEM v1.2 Limitations
While FABDEM removes canopy and structural bias from Copernicus DEM, its native 30-metre pixel resolution is completely inadequate for urban microclimate ray tracing on pedestrian corridors:
1. **Vertical Curb Steps:** Church Street features 150 mm curb heights along pedestrian footpaths. In a 30 m pixel, these micro-elevations are completely flattened.
2. **Cross-Fall Drainage:** Transverse slopes of 1:50 to 1:40 cannot be resolved.
3. **Building Plinths:** Footprints would artificially float or intersect terrain without high-resolution total station surveys.

### Conclusion & Safety Boundary
- FABDEM is strictly relegated to regional boundary reference.
- No measured engineering-grade DTM exists for Church Street in current project records.
- Consequently, **all terrain-aware solver extensions (Stages 22–23) are developed and verified using mathematical synthetic terrain profiles**.
- Real-world terrain claims remain strictly blocked.
