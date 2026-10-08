# Cross-Area Generalization Boundaries and Physical Limitations

## 1. Domain Applicability Envelope
The SOLARAEUS solver and its certified GPU incremental backend have been validated across:
1. **Narrow pedestrian street canyons** (e.g. Bengaluru Church Street, H/W ~ 1.5 - 2.5).
2. **Commercial vehicular/pedestrian corridors** (e.g. Brigade Road, H/W ~ 1.0).
3. **Open civic and commercial plazas** (e.g. MG Road Metro Plaza, open sky view factor > 0.65).

## 2. Documented Unsupported Features & Exclusions
- **Steep Complex Terrain**: Models with terrain slopes exceeding 5.0% (such as `AREA_HILLSIDE_COMPLEX`) are strictly rejected.
- **Tree and Canopy Geometry**: Neither FABDEM terrain nor BBMP tree point geometries are integrated into the solver radiative transfer engine in Stages 10–16. All canopy and ground interactions are evaluated on approved flat-ground urban meshes.
- **Micro-Scale Turbulence & CFD**: The solver computes 3D radiative transfer (shortwave and longwave) and energy balance; local aerodynamic convective vortex shedding is parameterized via SOLWEIG empirical wind scaling.
