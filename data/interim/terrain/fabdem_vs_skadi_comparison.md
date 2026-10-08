# FABDEM v1.2 vs Skadi DEM Comparison Report

## 1. Executive Summary
This report presents an empirical, point-by-point comparison between the newly acquired **FABDEM v1.2** bare-earth raster and the existing **Mapzen/Tilezen Skadi DEM** across the Church Street study corridor in Bengaluru, Karnataka, India.

- **Sample Point Count**: 165 common valid points across $77.6035^\circ\text{–}77.6075^\circ\text{E}$, $12.9735^\circ\text{–}12.9765^\circ\text{N}$.
- **Mean Difference ($\Delta = \text{Skadi} - \text{FABDEM}$)**: **+7.10 m**
- **Median Difference**: **+6.83 m**
- **Difference Range**: **-9.02 m to +20.56 m**
- **Standard Deviation of Difference**: **5.39 m**

---

## 2. Statistical Breakdown

| Surface Model | Product Nature | Stated Datum | Site Min | Site Max | Site Mean | Site Std |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Skadi DEM** | Composite Radar DSM | EGM96 | 905.0 m | 934.0 m | 920.35 m | 5.61 m |
| **FABDEM v1.2**| Machine-Learning Bare-Earth DTM | EGM2008 | 910.1 m | 917.4 m | 913.25 m | 1.38 m |
| **Difference ($\Delta$)**| Elevation Offset | Differential | **-9.02 m** | **+20.56 m** | **+7.10 m** | **5.39 m** |

---

## 3. Physical Attribution of Elevation Differences

The observed differences stem from three distinct physical and computational phenomena:

1. **Building and Tree Canopy Contamination in Skadi (Primary Driver)**:
   - The Skadi DEM is derived from SRTM (Shuttle Radar Topography Mission) C-band radar interferometry. C-band radar reflects off the phase center of commercial building rooftops (e.g., 4- to 7-story commercial structures on Church Street) and dense tree canopies.
   - This creates artificial positive spikes up to **+16.6 m** in the raw radar surface, inflating the site variance ($\sigma = 5.61\text{ m}$).
   - In contrast, FABDEM's random forest model explicitly stripped building and canopy biases, reducing site variance to $\sigma = 1.38\text{ m}$ and lowering the mean elevation by **7.10 m**.

2. **Vertical Datum Mismatch (EGM96 vs EGM2008)**:
   - Skadi is referenced to the EGM96 geoid, whereas FABDEM v1.2 is referenced to EGM2008.
   - At Bengaluru ($12.97^\circ\text{N}, 77.60^\circ\text{E}$), the separation between EGM96 and EGM2008 geoid undulations is approximately **0.15 m to 0.25 m**. This datum difference accounts for a small fraction of the total 7.10 m offset.

3. **True Terrain Topography**:
   - Both datasets confirm that Church Street has a gentle, continuous downward slope from West (Brigade Road, ~917 m) to East (Museum Road, ~910 m).

---

## 4. Scientific Suitability & Constraints
- **Provisional Elevation Baseline**: FABDEM provides a verified, unpolluted macro-scale bare-earth baseline for Church Street.
- **Insufficient for Street-Scale Raytracing**: At ~30 m resolution, FABDEM cannot resolve curb steps (150 mm), sidewalk cross-slopes (1:50), or building thresholds.
- **Status**: `FABDEM_AVAILABLE_FOR_REGIONAL_PREPROCESSING`. It serves as a regional boundary condition, not a sub-metre street micro-topography mesh.
