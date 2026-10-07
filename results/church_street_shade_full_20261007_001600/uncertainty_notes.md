# Uncertainty Notes: Church Street Shade-Panel Intervention Simulation

**Execution Timestamp (UTC):** 20261007_001600  
**Scientific Framing:**
> “The shade-panel result is an exploratory full-recomputation comparison using real-world building geometry, partly uncertain building-height estimates, off-site weather forcing, estimated solar radiation, and assumed material properties.”

This sensitivity analysis isolates the modeled microclimatic impact of introducing a single 6.0 m × 3.0 m × 0.10 m overhead shade panel (`CANOPY_001`) into the Church Street canyon. All observed differences must be interpreted subject to the following key uncertainties:

## 1. Building Height Uncertainties
- **40 High/Extreme Uncertainty Buildings:** 40 of the 123 context buildings (including 7 within the core block) carry elevated height uncertainty flags due to lack of ground truth LiDAR, uncorroborated floor counts, or sparse ML coverage.
- **Impact on Canyon Shading:** Building height errors perturb the baseline shadow envelope along Church Street. For the 14:30 IST sun position (altitude = 57.9160°), shadows cast from surrounding buildings govern whether pedestrians in the corridor are sunlit or already shaded.

## 2. Off-Site Meteorological Forcing
- **Station Distance:** Observations were acquired from NOAA ISD Station 43295099999 (12.966667° N, 77.583333° E), located **2.56 km geodesic distance** southwest of the site.
- **Microclimate Divergence:** Bengaluru City station observations are applied as spatially uniform forcing. Canyon wind channeling, building thermal mass, anthropogenic vehicle heat, and local humidity gradients are not captured.

## 3. Solar Radiation Assumptions
- **Satellite Model Estimates:** NASA POWER hourly interval radiation (755.97 W/m² GHI, 728.31 W/m² DNI, 172.18 W/m² DHI) represents an hour-averaged modeled value for 09:00–10:00 UTC paired with the instantaneous 09:00:00 UTC sun position.

## 4. Fixed Material & Temperature Approximations
- **Assumed Optical Properties:** Building walls (α = 0.30, ε = 0.90), roofs (α = 0.20, ε = 0.90), pavement (α = 0.30, ε = 0.95), and the shade panel (α = 0.60, ε = 0.90) are assigned uniform literature values without spectral or angular dependence.
- **Isothermal Surface Assumption:** All surfaces (including the panel underside) are assumed isothermal at 35.0°C (308.15 K), neglecting radiative equilibrium warming under intense solar irradiance.

## 5. Geometric Simplifications
- **Omission of Vegetation:** Street trees along Church Street provide natural canopies that interact with both solar rays and the panel's microclimate.
- **Omission of Support Posts:** The geometric model assumes an unsupported canopy suspended at z = 3.5 m above flat ground (z = 0.0 m).
- **Flat Ground Approximation:** Natural street slope (approx 2.5 m block descent) is neglected in the solver.
