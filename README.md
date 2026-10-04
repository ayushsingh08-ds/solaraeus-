# Solaraeus — 3D Urban Microclimate Digital Twin

Solaraeus simulates pedestrian-level urban heat at 1 m resolution and serves the result to an interactive 3D viewer. The default study area is **Washington Square Park, New York City** (a Lower Manhattan / Financial District area is also configured). The pipeline combines open building footprints, terrain and weather data into one unified surface model, then computes sky view factor, directional shadows, mean radiant temperature (Tmrt) and the Universal Thermal Climate Index (UTCI) for every pedestrian-accessible grid cell.

Everything is orchestrated by `scripts/run_stage1.py`; results land in `outputs/` as publication figures, a multi-dimensional NetCDF dataset, a watertight 3D building mesh, a validation report, and typed JSON data contracts that the React 19 + Three.js viewer in `frontend/` consumes.

## Quickstart

```bash
# 1. Environment — conda (recommended) or plain venv
conda env create -f environment.yml && conda activate solaraeus
#    or: python -m venv .venv && pip install -r requirements.txt

# 2. Run the full Stage 1 pipeline (data → geometry → physics → figures/NetCDF)
python scripts/run_stage1.py

# 3. Export the JSON contracts for the 3D viewer
python scripts/export_frontend_data.py

# 4. Verify the physics
pytest tests/ -v

# 5. Launch the viewer
cd frontend && npm install && npm run dev   # http://localhost:5173/
```

`python scripts/reproduce_all.py` runs all of the above in one command (Windows/macOS/Linux wrappers: `scripts/reproduce.bat`, `scripts/reproduce.sh`). Full environment notes, network requirements and troubleshooting live in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Repository layout

```
solaraeus/
├── src/                     # The Python library (data → geometry → physics → visualization)
│   ├── config.py            # Single source of truth: study areas, paths, physics parameters
│   ├── data/                # Acquisition and harmonization to a unified UTM 1 m grid
│   ├── geometry/            # 2.5D DSM, pedestrian grid, 3D building meshes
│   ├── physics/             # Solar position, SVF, shadows, radiation, Tmrt, UTCI
│   └── visualization/       # Static cartographic figures
├── scripts/                 # Orchestrators (not library code)
│   ├── run_stage1.py        # Main pipeline: download → process → physics → figures/report
│   ├── export_frontend_data.py  # Simulation grids → JSON contracts for the viewer
│   └── reproduce_all.py     # End-to-end reproduction + frontend build
├── tests/                   # Physics, geometry and visualization unit tests
├── data/                    # Raw / processed / cached datasets (gitignored contents)
├── outputs/                 # Figures, NetCDF, meshes, JSON contracts, validation report
├── notebooks/               # Exploratory notebooks (optional)
├── frontend/                # React 19 + Vite + Three.js viewer (see frontend/README.md)
├── environment.yml          # Conda environment
├── requirements.txt         # pip dependencies
└── REPRODUCIBILITY.md       # Full run instructions
```

## Pipeline architecture

The pipeline is a one-way flow — each stage consumes only the previous stage's output, which keeps data bugs from looking like physics bugs:

```
raw data → harmonize → geometry → physics → visualization / exports
```

### 1. Data acquisition and harmonization — `src/data/`

| Module | Job |
| :--- | :--- |
| `overture_loader.py` | Downloads (or loads cached) Overture Maps building footprints, keeps the height and floor fields, caches to `data/raw/`. |
| `era5_loader.py` | Fetches ERA5 single-level meteorology via the CDS API, converts accumulations to W/m², derives relative humidity, extrapolates wind to pedestrian height; falls back to the Open-Meteo archive/forecast API when ERA5 is unavailable. |
| `dem_loader.py` | Downloads the NASA SRTM 30 m HGT tile (AWS Skadi mirror), reprojects to the study-area UTM zone, and resamples to the 1 m simulation grid. |
| `harmonize.py` | The integration step: reprojects buildings/DEM onto one UTM grid, rasterizes building heights, crops to the study-area bounds, and returns the unified DSM, buildings table, pedestrian grid, meteorology and metadata. |
| `utils.py` | Shared CRS, raster-sampling, bounding-box and file-I/O helpers. |

Data is split by lifecycle: `data/raw/` is untouched downloads, `data/processed/` holds cleaned/reprojected intermediates, and `data/cache/` holds expensive artifacts (DSM, SVF, pedestrian grid, building mesh) that are safe to reuse when their inputs have not changed.

### 2. Geometry — `src/geometry/`

| Module | Job |
| :--- | :--- |
| `dsm.py` | Builds the final 2.5D Digital Surface Model: ground elevation plus rasterized building heights. |
| `pedestrian_grid.py` | Creates the pedestrian query grid at 1.1 m above ground and masks building-footprint cells that a person could not occupy. |
| `meshes.py` | Extrudes building footprints to true roof heights into a watertight 3D mesh and exports OBJ plus an indexed web mesh. |

### 3. Physics — `src/physics/`

| Module | Job |
| :--- | :--- |
| `solar.py` | Solar position (altitude, azimuth) from latitude/longitude, UTC hour and day of year, using the Cooper (1969) declination model. Azimuth defaults to the project's meridian convention that yields ~135°–145° for the July afternoon south-west sun; pass `use_standard_compass=True` for clockwise-from-north (0°=N, 90°=E, 180°=S, 270°=W). |
| `svf.py` | Sky View Factor by horizon ray-marching: the maximum building elevation angle along each azimuth radial (Steyn 1980). |
| `shadows.py` | Direct-sun mask by 2.5D projection along the anti-solar direction; a cell is shaded when any obstacle rises above the solar ray. |
| `radiation.py` | Direct beam, diffuse sky, downward and upward longwave fluxes from the shadow mask, SVF and meteorology. |
| `tmrt.py` | Sums the directional fluxes through the standing-cylinder view factors and converts to Tmrt with the Stefan–Boltzmann law. |
| `utci.py` | UTCI via `pythermalcomfort` from air temperature, Tmrt, pedestrian wind and relative humidity, plus thermal-stress classification. |

### 4. Visualization and orchestration — `src/visualization/`, `scripts/`

`src/visualization/maps.py` renders the cartographic figures (DSM, shadow mask, SVF, Tmrt, UTCI) with colorbars, statistics and north arrows. `scripts/run_stage1.py` wires the whole pipeline together, runs sanity checks, writes figures, the NetCDF dataset and the validation report. `scripts/export_frontend_data.py` converts the simulation grids into the viewer's JSON contracts.

## Physics formulation

- **Sky View Factor (Steyn 1980)** — `SVF = 1 − (1/N) Σ cos²(β_i)`, where `β_i` is the maximum horizon elevation angle across `N` azimuth radials (default 360) searched out to 200 m.
- **Shadow casting** — the solar ray `z(s) = z₀ + s·tan(θ_alt)` along the anti-solar azimuth; a cell is shaded if any obstacle along the ray satisfies `DSM(x_s, y_s) > z_ray(s)`.
- **Mean radiant temperature** — `Tmrt = (S_str / (ε_p · σ))^(1/4) − 273.15`, with `σ = 5.67e−8 W/m²/K⁴` and `S_str` the absorbed flux summed over the cylinder view factors (0.06 top, 0.06 bottom, 0.22 per side).
- **UTCI** — the Fiala multi-node thermoregulation approximation, evaluated by `pythermalcomfort` from `(Ta, RH, v_ped, Tmrt)`.

## Validation criteria

These are the sanity bounds the test suite and the pipeline's validation report check against:

| Check | Expected |
| :--- | :--- |
| Solar position, NYC 2024-07-15 14:00 local | Altitude ~60–65°, azimuth ~135–145° (south-south-west) |
| SVF, flat open ground / 15 m × 15 m canyon | ≈ 1.0 / ≈ 0.3–0.4 |
| Shadow length, building height H at sun altitude θ | `H / tan(θ)` (20 m at 60° ≈ 11.5 m), opposite the sun |
| Direct solar flux | ≈ `SSRD · cos(θ_alt) · 0.75`, zero for shaded cells |
| Tmrt | Sunlit > 50 °C (typically 50–70 °C); shaded 30–45 °C; ΔTmrt > 10 °C |
| UTCI | Sunlit markedly higher than shaded (≈10 °C typical); heat-stress classes via pythermalcomfort |

## Frontend

The viewer in `frontend/` is a separate Vite + React 19 + TypeScript application using Three.js (`@react-three/fiber` / `drei`) and Zustand. It renders the extruded building mesh and the metric layers over the study area, with a diurnal time slider and a first-person pedestrian avatar that samples pedestrian-level comfort.

- `src/api/` — typed clients for the JSON contracts (`outputs/data/`, `outputs/json/`, `outputs/meshes/`).
- `src/components/map/` — 3D scene: ground heatmaps, building mesh, atmosphere, sun indicator.
- `src/components/layers/` — one component per metric (DSM, shadows, SVF, Tmrt, UTCI).
- `src/components/avatar/` — pedestrian avatar, movement controls, comfort HUD, comfort aura.
- `src/hooks/`, `src/stores/`, `src/utils/` — data loading, timeline/state, color scales and geo transforms.

The dev server serves the repository's `outputs/` directory directly through the `/outputs/*` middleware in `vite.config.ts`. See [frontend/README.md](frontend/README.md) for setup and the data contract paths.

## Study areas and data sources

Study areas are defined in `src/config.py`: **Washington Square Park** (default; 40.7308°N, −73.9975°W, EPSG:32618 UTM 18N) and **Lower Manhattan / Financial District**. Both simulate on a 1 m grid.

| Input | Source |
| :--- | :--- |
| Building footprints and heights | Overture Maps (`overturemaps` Python package), cached locally |
| Terrain elevation | NASA SRTM 30 m HGT tiles, AWS Skadi mirror |
| Meteorology | ERA5 single-level reanalysis (Copernicus CDS API), Open-Meteo fallback |

## Configuration

`src/config.py` holds every adjustable parameter in frozen dataclasses — no magic numbers are scattered through the modules. The default simulation is **2024-07-15, 18:00 UTC (14:00 EDT)**: pedestrian height 1.1 m, 360 SVF directions, 200 m shadow/SVF search radius, atmospheric transmission 0.75, sky emissivity 0.85, ground emissivity 0.95, cloud fraction 0.1. Switching study area, date or resolution is a config change, not a code change.

## Output artifacts

| Category | Path | Description |
| :--- | :--- | :--- |
| Figures | `outputs/figures/*.png` | DSM, shadow mask, SVF, Tmrt, UTCI and diagnostic plots |
| Gridded metrics | `outputs/json/*.json` | DSM/SVF/shadows/Tmrt/UTCI grids with bounds, for the viewer |
| Data contracts | `outputs/data/*.json` | Simulation config, available times, walkable collision grid |
| 3D geometry | `outputs/meshes/buildings_3d.obj` / `.json` | Watertight extruded buildings, OBJ and indexed web mesh |
| Scientific dataset | `outputs/netcdf/*.nc` | Multi-dimensional microclimate dataset |
| Validation report | `outputs/reports/stage1_validation.md` | What was simulated, what passed, what is limited |

## Known limitations

- **1 m is the simulation grid, not the data resolution.** Terrain comes from 30 m SRTM and is bilinearly resampled onto the 1 m grid; it is not LiDAR, and no sub-30 m detail exists in the elevation input.
- **Tree canopy is not modelled in Stage 1.** Vegetation is absent from the DSM, so shaded park comfort under trees is not represented.
- **Shadow casting is a 2.5D raster projection.** Overhangs, arcades and complex facades are approximated.
- **Meteorology is uniform over the domain** — no CFD wind field, no building energy model, no thermal inertia across the day.
- **One instant per physics run.** The viewer steps through the hourly JSON grids exported alongside the default run; the pipeline does not perform a full time-series simulation on its own.
