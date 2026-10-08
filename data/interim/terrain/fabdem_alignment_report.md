# FABDEM v1.2 Terrain Audit & Alignment Report

## Executive Summary
This report documents the formal technical audit of the **FABDEM v1.2** bare-earth elevation raster (`N12E077_FABDEM_V1-2.tif`) for the Church Street microclimate study area in Bengaluru, Karnataka, India.

- **Product Classification**: `FABDEM_AVAILABLE_FOR_REGIONAL_PREPROCESSING`
- **Product Heritage**: Machine-learning bare-earth Digital Terrain Model (DTM) produced by University of Bristol / Fathom (Hawker et al., 2022) under **CC BY-NC-SA 4.0**.
- **Underlying DSM**: Copernicus GLO-30 DSM (2021_1 release) with forest canopy and building height biases removed via random forest regression trained on GEDI spaceborne LiDAR and GHSL.

---

## Technical Specifications
- **Raster Dimensions**: 3600 columns $\times$ 3600 rows (1 band, `float32`)
- **Native CRS**: `EPSG:4326` (WGS84 2D Geographic Latitude/Longitude)
- **Native Cell Resolution**: $0.00027778^\circ \approx 30.14\text{ m}$ (East-West) $\times 30.73\text{ m}$ (North-South)
- **Horizontal Coverage**: Full $1^\circ \times 1^\circ$ tile ($77.0^\circ\text{E to } 78.0^\circ\text{E}$, $12.0^\circ\text{N to } 13.0^\circ\text{N}$)
- **Vertical Reference & Datum**: EGM2008 orthometric height in metres
- **NoData Value**: `-9999.0`
- **Tile Elevation Range**: Min 235.50 m, Max 1505.74 m, Mean 721.21 m, Std 158.03 m

---

## Church Street Site Topography
Across the Church Street study corridor window ($77.6035^\circ\text{–}77.6075^\circ\text{E}$, $12.9735^\circ\text{–}12.9765^\circ\text{N}$):
- **Minimum Elevation**: **910.12 m**
- **Maximum Elevation**: **917.40 m**
- **Mean Elevation**: **913.25 m**
- **Median Elevation**: **913.54 m**
- **Standard Deviation**: **1.38 m**

### Critical Physical Insights:
1. **Absence of Building Rooftop Spikes**: Unlike the uncorrected Skadi SRTM composite (which peaked at 934 m due to commercial high-rise radar reflections), FABDEM has a maximum elevation of 917.40 m, confirming successful stripping of building structures.
2. **True Regional Grade**: Church Street exhibits a gentle West-to-East slope, descending from ~917 m at the Brigade Road junction to ~910 m toward Museum Road over a 200 m distance.
3. **Street-Scale Limitation**: At ~30 m resolution, a single FABDEM cell spans the entire 12 m–15 m width of Church Street. Therefore, FABDEM cannot resolve:
   - 150 mm curb steps.
   - 1:50 (2%) cross-fall transverse drainage slopes.
   - Pavement vs sidewalk elevation steps.

---

## Conclusion & Governance
FABDEM is classified as **provisional regional terrain reference only**. It must not be resampled or used directly as sub-metre simulation-ready ground geometry.
