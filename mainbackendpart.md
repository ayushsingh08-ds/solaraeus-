No code should be written , i want u to understand the top level structure of project and understand whats gonna happen and store this structure in your main memory 
read the file mainfrontend.md as well to understand the full pipeline.

# Solaraeus Stage 1 — Project Structure

A clean, modular structure that separates **data**, **physics**, **visualization**, and **orchestration** so each piece can be developed, tested, and replaced independently.

---

## Top-Level Directory Tree

```
solaraeus/
├── data/                    # Raw downloaded data (gitignored)
│   ├── raw/                 # Never-processed original downloads
│   │   ├── overture_wsp_buildings.geojson
│   │   ├── era5_wsp_20240715.nc
│   │   ├── dem_source.tif
│   │   └── canopy_source.tif          # optional
│   ├── processed/           # Cleaned, harmonized intermediate data
│   │   ├── gdf_buildings_utm.parquet
│   │   ├── dem_1m.tif
│   │   └── gdf_sidewalks_utm.parquet  # optional
│   └── cache/               # Precomputed expensive artifacts
│       ├── dsm_1m.npy
│       ├── building_mesh.pkl
│       └── pedestrian_grid.npz
│
├── src/                     # All production code (the `solaraeus` package)
│   ├── __init__.py
│   ├── config.py            # Central configuration — study area, paths, physics params
│   │
│   ├── data/                # Data acquisition & harmonization
│   │   ├── __init__.py
│   │   ├── overture_loader.py      # Download/query Overture buildings
│   │   ├── era5_loader.py          # Download/extract ERA5 meteorology
│   │   ├── dem_loader.py           # Download/reproject DEM
│   │   ├── harmonize.py            # Unify everything to UTM 1m grid
│   │   └── utils.py                # Shared data helpers (CRS, sampling, raster ops)
│   │
│   ├── geometry/            # Geometry construction
│   │   ├── __init__.py
│   │   ├── dsm.py                  # Build 2.5D Digital Surface Model from buildings+ground
│   │   ├── meshes.py               # Extrude building polygons → 3D watertight meshes
│   │   └── pedestrian_grid.py      # Create pedestrian-height query point grid
│   │
│   ├── physics/             # The radiative engine (the core science)
│   │   ├── __init__.py
│   │   ├── solar.py                # Solar position (altitude, azimuth)
│   │   ├── svf.py                  # Sky View Factor via horizon ray-marching
│   │   ├── shadows.py              # 2.5D shadow casting (raster projection)
│   │   ├── radiation.py            # Direct/diffuse solar, longwave fluxes
│   │   ├── tmrt.py                 # 6-directional flux summation → Mean Radiant Temperature
│   │   └── utci.py                 # UTCI from Tmrt + meteorology (pythermalcomfort wrapper)
│   │
│   ├── visualization/       # Output rendering
│   │   ├── __init__.py
│   │   ├── maps.py                 # Static matplotlib visualizations (DSM, shadows, Tmrt, UTCI)
│   │   └── dashboard.py            # Optional Streamlit/Deck.gl interactive viewer
│
├── outputs/                 # Final results (gitignored)
│   ├── figures/             # Publication-ready plots
│   │   ├── dsm_wsp.png
│   │   ├── shadow_mask_wsp.png
│   │   ├── svf_wsp.png
│   │   ├── tmrt_wsp.png
│   │   └── utci_wsp.png
│   ├── netcdf/              # Gridded outputs (for reuse downstream)
│   │   ├── tmrt_20240715_1400.nc
│   │   └── utci_20240715_1400.nc
│   └── reports/             # Validation & sanity check logs
│       └── stage1_validation.md
│
├── tests/                   # Unit & integration tests
│   ├── __init__.py
│   ├── test_solar.py
│   ├── test_svf.py
│   ├── test_shadows.py
│   ├── test_radiation.py
│   └── test_utci.py
│
├── notebooks/              # Exploratory & development notebooks (optional)
│   ├── 01_data_exploration.ipynb
│   ├── 02_dsm_build.ipynb
│   └── 03_physics_validation.ipynb
│
├── scripts/                # Standalone runner scripts (glue, not library code)
│   ├── run_stage1.py       # Main orchestrator: download → process → physics → visualize
│   └── download_all.sh    # Optional: batch download script for all data sources
│
├── environment.yml         # conda environment (or requirements.txt / pyproject.toml)
├── .gitignore
└── README.md               # Project overview, how to run, data sources, limitations
```

---

## What Goes Where — Design Rationale

### `data/` — Raw and Processed Data (Gitignored)

**Rule:** Never commit raw data or large processed rasters. The repository should contain only code. Data is downloaded by scripts at runtime (or manually placed there with a documented procedure).

| Subdirectory | Purpose | Examples |
|--------------|---------|-----------|
| `raw/` | Original downloads, untouched | `overture_wsp_buildings.geojson`, `era5_wsp_20240715.nc`, raw DEM GeoTIFF |
| `processed/` | Cleaned, reprojected, cropped intermediates | `gdf_buildings_utm.parquet`, `dem_1m.tif` |
| `cache/` | Expensive-to-compute artifacts worth reusing | `dsm_1m.npy`, `building_mesh.pkl` (3D mesh takes time to build; cache it) |

**Why separate raw/processed/cache?**
- If a download changes (new Overture release), you only re-download raw — processed and cache are invalidated by the pipeline, not manually
- If harmonization logic changes, you re-run from raw → processed, keeping cache for the final expensive artifacts
- Clean separation makes it obvious what is source data vs. derived data vs. cached computation

---

### `src/solaraeus/` — The Package

This is the actual library. Everything importable lives here. The structure mirrors the **data flow**:

```
raw data → harmonize → geometry → physics → visualization
```

Each subdirectory is a subpackage with its own `__init__.py`. This gives you:

```python
from solaraeus.data import overture_loader, era5_loader, harmonize
from solaraeus.geometry import dsm, meshes, pedestrian_grid
from solaraeus.physics import solar, svf, shadows, radiation, tmrt, utci
from solaraeus.visualization import maps
```

**Why modular by concern, not by file type?** Because the project's complexity lives in the physics and data steps. Keeping `svf.py`, `shadows.py`, `tmrt.py` separate means each can be unit-tested in isolation, each has a single responsibility, and each can be improved without touching the others.

---

### Module-by-Module Breakdown

#### `src/solaraeus/config.py` — Single Source of Truth

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class StudyArea:
    name: str = "washington_square_park"
    lat_center: float = 40.7308
    lon_center: float = -73.9975
    bbox_latlon: tuple = (40.7280, -73.9990, 40.7340, -73.9920)  # (S, W, N, E)
    utm_zone: int = 32618
    # UTM bounds — computed from bbox, but stored for convenience
    utm_bounds: tuple = (583540.0, 4508900.0, 583740.0, 4509100.0)  # (xmin, ymin, xmax, ymax)
    resolution_m: float = 1.0

@dataclass(frozen=True)
class SimulationConfig:
    study_area: StudyArea = StudyArea()
    date: str = "2024-07-15"
    day_of_year: int = 196
    utc_hour: int = 18  # 14:00 EDT = 18:00 UTC
    pedestrian_height_m: float = 1.1
    # Physics parameters
    n_svf_directions: int = 360
    svf_max_radius_m: int = 200
    atmospheric_transmission: float = 0.75  # clear-sky beam transmission
    sky_emissivity: float = 0.85
    ground_emissivity: float = 0.95
    cloud_fraction: float = 0.1  # from ERA5 SSRD/SSRD_clear ratio

@dataclass(frozen=True)
class DataConfig:
    data_dir: Path = Path("data")
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    cache_dir: Path = Path("data/cache")
    output_dir: Path = Path("outputs")
    figure_dir: Path = Path("outputs/figures")

@dataclass(frozen=True)
class ProjectConfig:
    study_area: StudyArea = StudyArea()
    simulation: SimulationConfig = SimulationConfig()
    data: DataConfig = DataConfig()
```

**Why a config class?**
- Every module reads parameters from here — no scattered magic numbers
- Changing the study area means changing one line in `config.py`
- Reproducibility: the config captures exactly what was simulated
- Testing: swap in a different config for unit tests (e.g., a toy 50×50m grid)

---

#### `src/solaraeus/data/` — Acquisition & Harmonization

| File | Responsibility |
|------|----------------|
| `overture_loader.py` | Download Overture buildings via `overturemaps` CLI or Python API; load into GeoDataFrame; basic QC (count, height coverage) |
| `era5_loader.py` | Download ERA5 via CDS API (or load cached NetCDF); extract variables at target time; convert units (K→°C, J→W); compute RH, wind at pedestrian height |
| `dem_loader.py` | Download SRTM/Copernicus DEM; reproject to UTM; resample to 1m; compute relative elevation |
| `harmonize.py` | The **critical integration step**: take all sources and produce the unified 1m DSM raster + building annotation table + pedestrian grid. This is where coordinate mismatches are resolved. |
| `utils.py` | Small helpers: CRS transform utilities, raster sampling, bounding box utilities, file I/O patterns |

**Data flow within this subpackage:**

```
overture_loader.load()  →  GeoDataFrame (EPSG:4326)
era5_loader.load()      →  dict of scalar meteorological values
dem_loader.load()       →  rasterio DatasetReader or numpy array (various CRS)

harmonize.build_unified_grid(
    buildings_gdf,
    dem_array,
    met_data,
    config
)
→ returns: DSM (numpy), buildings_table (pandas), pedestrian_grid (numpy), metadata (dict)
```

---

#### `src/solaraeus/geometry/` — From Unified Grid to Physics Inputs

| File | Responsibility |
|------|----------------|
| `dsm.py` | Rasterize building footprints with heights onto the ground DEM → produce the final 2.5D DSM. Handles edge cases (MultiPolygons, height missing → estimate, overlapping buildings). |
| `meshes.py` | Extrude building polygons to 3D watertight `trimesh.Trimesh` objects. Merge into single mesh. Export to OBJ/PLY. This is for the Stage 2 reference ray tracer. |
| `pedestrian_grid.py` | Create the regular (N, 3) pedestrian point grid at 1.1m height. Optionally mask by sidewalk/road polygons. Feeds physics calculation and exports walkable navigation mask for the frontend 3D avatar controller. |

**Outputs of this subpackage:**
- `dsm: np.ndarray` — (H, W) float32, the primary physics input
- `building_mesh: trimesh.Trimesh` — 3D reference (optional for Stage 1, required for Stage 2)
- `pedestrian_points: np.ndarray` — (N, 3) float32, where physics is evaluated
- `pedestrian_mask: np.ndarray` — (N,) bool, which points are on walkable surfaces (exported to `outputs/data/walkable_grid.json` for frontend 3D avatar navigation)

---

#### `src/solaraeus/physics/` — The Radiative Engine

This is the **core scientific code**. Each module does one thing and does it well.

| File | Responsibility | Key Function Signature |
|------|----------------|----------------------|
| `solar.py` | Solar position: altitude, azimuth from lat/lon/time/day-of-year | `compute_solar_position(lat, utc_hour, day_of_year, lon=0.0) → (alt_rad, az_rad)` |
| `svf.py` | Sky View Factor via horizon ray-marching on the DSM raster | `compute_svf(dsm, transform, points_3d, n_dir=360, max_radius=200) → svf_values (N,)` |
| `shadows.py` | 2.5D shadow casting: which pedestrian points are in direct sun | `cast_shadows(dsm, transform, alt_rad, az_rad, max_distance=200) → sunlit_mask (H, W) or (N,)` |
| `radiation.py` | Compute direct, diffuse, and longwave fluxes at each pedestrian point | `compute_radiation(sunlit_mask, svf, SSRD, STRD, Ta, Tdew, cloud_fraction, ...) → fluxes dict` |
| `tmrt.py` | 6-directional flux summation → Mean Radiant Temperature | `compute_tmrt(fluxes, weights=(0.06, 0.06, 0.22×4)) → tmrt_values (N,)` in °C |
| `utci.py` | UTCI from Tmrt + meteorology | `compute_utci(Ta, tmrt_values, v_ped, RH) → utci_values (N,)` in °C |

**Physics data flow (the core pipeline):**

```
DSM (H, W) + pedestrian_points (N, 3) + transform
  │
  ├──▶ solar.compute_solar_position() → (alt_rad, az_rad)
  │
  ├──▶ svf.compute_svf(dsm, points_3d, alt_rad, az_rad) → svf (N,)
  │       horizon march in N_dir azimuth directions on DSM
  │
  ├──▶ shadows.cast_shadows(dsm, alt_rad, az_rad) → sunlit_mask (N,)
  │       2.5D projection: is point above the "shadow line" from nearest tall object?
  │
  ├──▶ radiation.compute_radiation(sunlit_mask, svf, SSRD, STRD, Ta, Tdew, ...)
  │       ├── K_direct = SSRD × cos(alt) × transmission × (1 if sunlit else 0)
  │       ├── K_diffuse = STRD_diffuse × svf
  │       ├── L_down = ε_sky × σ × T_sky⁴
  │       ├── L_up = ε_ground × σ × T_surface⁴
  │       └── return dict of directional fluxes (N, 6) or aggregated
  │
  ├──▶ tmrt.compute_tmrt(fluxes, cylinder_weights) → tmrt (N,) in °C
  │       S_str = Σ W_i × (K_i + L_i)
  │       Tmrt = (S_str / (ε_p × σ))^(1/4) - 273.15
  │
  └──▶ utci.compute_utci(Ta, tmrt, v_ped, RH) → utci (N,) in °C
          via pythermalcomfort.utci()
```

**Why separate into 6 modules?** Each represents a distinct physical computation with its own validation:
- `solar.py` can be tested against NOAA solar calculator
- `svf.py` can be tested against analytical values for simple geometries (isolated cube, infinite canyon)
- `shadows.py` can be tested against 3D ray-cast shadows (Stage 2)
- `radiation.py` can be checked for energy balance consistency
- `tmrt.py` can be tested against hand calculations for simple cases
- `utci.py` can be validated against pythermalcomfort's own test suite

This modularity also means you can **skip or simplify** any step for debugging. If Tmrt looks wrong, you check SVF and shadows independently rather than debugging the entire pipeline at once.

---

#### `src/solaraeus/visualization/` — Output Rendering

| File | Responsibility |
|------|----------------|
| `maps.py` | Static matplotlib figures: DSM elevation, shadow mask overlay, SVF heat map, Tmrt heat map, UTCI heat map. Side-by-side comparisons. Colorbars, titles, annotations. |
| `dashboard.py` | (Optional, Stage 1+) Streamlit app with pydeck/WebGL for interactive 3D exploration. Sun slider, layer toggles, discrepancy views. |

**Stage 1 visualization outputs (required):**
1. `dsm_wsp.png` — DSM elevation map with colorbar
2. `shadow_mask_wsp.png` — DSM + shadow overlay (gray=shaded, white=sunlit) + sun direction marker
3. `svf_wsp.png` — SVF heat map (color = sky visibility, 0–1)
4. `tmrt_wsp.png` — Tmrt heat map (°C), with histogram
5. `utci_wsp.png` — UTCI heat map (°C), with stress category legend

**Each figure should include:**
- Title with date, time, location
- Colorbar with units
- Scale bar (10m, 50m)
- North arrow
- Stats text box (min, max, mean, StdDev)

---

#### `scripts/run_stage1.py` — The Orchestrator

This is the main entry point. It wires everything together into a single runnable pipeline.

```python
#!/usr/bin/env python3
"""
Stage 1: Build and validate the GPU-accelerated 2.5D raster engine.
Single time step (14:00 local, July 15, 2024) for Washington Square Park, NYC.
"""

import logging
from pathlib import Path

from solaraeus.config import ProjectConfig
from solaraeus.data import overture_loader, era5_loader, dem_loader, harmonize
from solaraeus.geometry import dsm, meshes, pedestrian_grid
from solaraeus.physics import solar, svf, shadows, radiation, tmrt, utci
from solaraeus.visualization import maps

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    cfg = ProjectConfig()
    
    # ---- 1. DATA ACQUISITION ----
    logger.info("Step 1: Downloading data...")
    buildings_gdf = overture_loader.load(cfg)          # → GeoDataFrame
    met_data = era5_loader.load(cfg)                   # → dict of scalars
    dem_array = dem_loader.load(cfg)                   # → np.ndarray (relative elevation)
    
    # ---- 2. HARMONIZATION ----
    logger.info("Step 2: Harmonizing to unified UTM 1m grid...")
    unified = harmonize.build_unified_grid(buildings_gdf, dem_array, met_data, cfg)
    dsm_raw = unified['dsm']
    buildings_table = unified['buildings_table']
    
    # ---- 3. GEOMETRY ----
    logger.info("Step 3: Building geometry objects...")
    dsm_final = dsm.build_dsm(dsm_raw, buildings_table, cfg)  # final 2.5D DSM
    pedestrian_points, ped_mask = pedestrian_grid.create(cfg, dsm_final)
    
    # Optional: build 3D mesh (for Stage 2; can skip for Stage 1 if not needed)
    try:
        building_mesh = meshes.build_building_meshes(buildings_table, dem_array, cfg)
        logger.info(f"3D mesh: {len(building_mesh.vertices)} vertices, watertight={building_mesh.is_watertight}")
    except Exception as e:
        logger.warning(f"3D mesh skipped: {e}")
        building_mesh = None
    
    # ---- 4. PHYSICS ----
    logger.info("Step 4: Running physics engine...")
    alt_rad, az_rad = solar.compute_solar_position(
        cfg.study_area.lat_center, cfg.simulation.utc_hour,
        cfg.simulation.day_of_year, cfg.study_area.lon_center
    )
    logger.info(f"Sun: altitude={np.degrees(alt_rad):.1f}°, azimuth={np.degrees(az_rad):.1f}°")
    
    svf_values = svf.compute_svf(dsm_final, pedestrian_points, cfg)
    sunlit_mask = shadows.cast_shadows(dsm_final, pedestrian_points, alt_rad, az_rad, cfg)
    fluxes = radiation.compute_radiation(sunlit_mask, svf_values, met_data, cfg)
    tmrt_values = tmrt.compute_tmrt(fluxes, cfg)
    utci_values = utci.compute_utci(met_data['Ta'], tmrt_values, met_data['v_ped'], met_data['RH'])
    
    # ---- 5. VALIDATION ----
    logger.info("Step 5: Running validation sanity checks...")
    validate_outputs(svf_values, tmrt_values, utci_values, sunlit_mask, cfg)
    
    # ---- 6. VISUALIZATION ----
    logger.info("Step 6: Generating output figures...")
    maps.plot_dsm(dsm_final, cfg)
    maps.plot_shadows(dsm_final, sunlit_mask, alt_rad, az_rad, cfg)
    maps.plot_svf(svf_values, cfg, pedestrian_points)
    maps.plot_tmrt(tmrt_values, cfg, pedestrian_points)
    maps.plot_utci(utci_values, cfg, pedestrian_points)
    
    # ---- 7. SAVE OUTPUTS ----
    logger.info("Step 7: Saving netCDF outputs...")
    save_netcdf_outputs(dsm_final, svf_values, tmrt_values, utci_values, pedestrian_points, cfg)
    
    logger.info("Stage 1 complete.")

if __name__ == "__main__":
    main()
```

**The orchestrator does NOT contain physics logic.** It calls into the modules. This means:
- The physics modules can be tested independently with `pytest`
- The orchestrator can be re-run after any module changes
- A different orchestrator (e.g., for a Jupyter notebook or web API) can call the same modules
- The pipeline is transparent: you can see exactly what happens in what order

---

#### `tests/` — Unit & Integration Tests

Each physics module gets its own test file. Tests use small, analytically tractable cases.

| Test File | What It Tests |
|-----------|---------------|
| `test_solar.py` | Solar position against NOAA calculator for several lat/lon/times |
| `test_svf.py` | SVF for: (a) flat open ground → SVF=1.0, (b) isolated cube → known value, (c) infinite canyon (H/W=1) → ~0.3-0.4 |
| `test_shadows.py` | Shadow for: (a) isolated building → shadow length = height/tan(alt), (b) point behind building → shaded, (c) point to the side → sunlit |
| `test_radiation.py` | Fluxes for clear-sky noon: K_direct should be SSRD×cos(alt)×transmission; diffuse should be STRD×SVF |
| `test_tmrt.py` | Tmrt for sunlit open area on hot day → >50°C; Tmrt for shaded area → <40°C; energy balance check |
| `test_utci.py` | UTCI for known inputs → compare against pythermalcomfort reference values; UTCI(sun) > UTCI(shade) by large margin |

**Integration test** (`test_integration.py`): Run the full pipeline on a tiny synthetic domain (e.g., 50×50m with 3 buildings) and verify end-to-end that outputs are produced without errors.

---

#### `notebooks/` — Exploration & Development

Not required for production, but invaluable during development:

- `01_data_exploration.ipynb` — Inspect downloaded Overture buildings, ERA5 values, DEM. Check height coverage. Visualize raw data before processing.
- `02_dsm_build.ipynb` — Step through DSM construction interactively. Visualize intermediate rasters. Debug rasterization issues.
- `03_physics_validation.ipynb` — Run physics modules on synthetic cases. Compare SVF against analytical values. Compare shadows against 3D ray cast. Plot Tmrt/UTCI histograms.

---

#### `outputs/` — Final Results (Gitignored)

| Subdirectory | Contents |
|--------------|----------|
| `figures/` | PNG publication-ready plots from `visualization/maps.py` |
| `netcdf/` | Gridded outputs in NetCDF format (reusable by Stage 2+): `tmrt_20240715_1400.nc`, `utci_20240715_1400.nc` with coordinates, attributes |
| `reports/` | `stage1_validation.md` — written validation log with sanity check results, known limitations, numbers |

---

## Data Flow Diagram

```
┌──────────────────┐
│  DATA SOURCES    │
│  (internet/cds)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ overture_loader  │────▶│   harmonize.py   │────▶│    dsm.py        │
│ (buildings GDF)  │     │  (unify CRS,     │     │  (rasterize to   │
└──────────────────┘     │   resample,      │     │   1m DSM)        │
                         │   crop)          │     └────────┬─────────┘
┌──────────────────┐     └────────┬─────────┘              │
│  era5_loader     │───▶ dict of  │                          │
│  (met scalars)   │     met values                      │
└──────────────────┘                                    │
┌──────────────────┐                                    │
│  dem_loader      │───▶ dem_array                       │
│  (ground elev)   │     (1m, relative)                 │
└──────────────────┘                                    │
                         │                              │
                         ▼                              ▼
                  ┌─────────────────────────────────────────────┐
                  │           harmonize.build_unified_grid()     │
                  │  Returns: dsm_raw, buildings_table,          │
                  │            met_data, grid_metadata           │
                  └─────────────────────────────────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────────────┐
                  │              GEOMETRY SUBPACKAGE              │
                  │  dsm.build_dsm()        → dsm_final (H,W)    │
                  │  pedestrian_grid.create() → points (N,3)    │
                  │  meshes.build_meshes()  → building_mesh      │
                  └─────────────────────────────────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────────────┐
                  │              PHYSICS SUBPACKAGE               │
                  │                                              │
                  │  solar → (alt, az)                           │
                  │    │                                         │
                  │    ├──▶ svf.compute_svf()    → svf (N,)     │
                  │    ├──▶ shadows.cast()       → mask (N,)    │
                  │    ├──▶ radiation.compute()  → fluxes (N,)  │
                  │    ├──▶ tmrt.compute()       → tmrt (N,)    │
                  │    └──▶ utci.compute()       → utci (N,)    │
                  │                                              │
                  └─────────────────────────────────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────────────┐
                  │           VISUALIZATION + OUTPUTS             │
                  │  maps.plot_*()          → figures/*.png      │
                  │  save_netcdf()         → netcdf/*.nc        │
                  │  write_validation()    → reports/*.md       │
                  └─────────────────────────────────────────────┘
```

---

## Import Hierarchy — What Imports What

```
run_stage1.py (script)
  ├──▶ solaraeus.config (ProjectConfig)
  ├──▶ solaraeus.data.overture_loader
  ├──▶ solaraeus.data.era5_loader
  ├──▶ solaraeus.data.dem_loader
  ├──▶ solaraeus.data.harmonize
  ├──▶ solaraeus.geometry.dsm
  ├──▶ solaraeus.geometry.meshes
  ├──▶ solaraeus.geometry.pedestrian_grid
  ├──▶ solaraeus.physics.solar
  ├──▶ solaraeus.physics.svf
  ├──▶ solaraeus.physics.shadows
  ├──▶ solaraeus.physics.radiation
  ├──▶ solaraeus.physics.tmrt
  ├──▶ solaraeus.physics.utci
  └──▶ solaraeus.visualization.maps

solaraeus.data.harmonize
  ├──▶ solaraeus.data.utils
  ├──▶ geopandas, rasterio, numpy, pyproj

solaraeus.physics.*
  ├──▶ numpy, torch (for GPU), pythermalcomfort
  └──▶ solaraeus.config (for parameters like n_dir, max_radius, transmission)

solaraeus.visualization.maps
  ├──▶ matplotlib, numpy
  └──▶ solaraeus.config (for paths, metadata)
```

**Critical rule:** Physics modules should NOT import data modules, and data modules should NOT import physics modules. Data acquisition and harmonization are upstream. Physics consumes the harmonized outputs. Visualization consumes physics outputs. This clean separation prevents circular imports and makes each layer independently testable.

---

## Configuration Management — Best Practices

1. **Everything parameterized lives in `config.py`.** No magic numbers in physics modules. If you change the number of SVF directions from 360 to 720, you change it in `SimulationConfig`, not by editing `svf.py`.

2. **Config is frozen (dataclass with `frozen=True`).** Prevents accidental mutation during a run.

3. **Paths are `pathlib.Path`, relative to project root.** The project root is determined at runtime (e.g., `Path(__file__).parent.parent` from `run_stage1.py`, or an environment variable `SOLARAEUS_ROOT`). This makes the project relocatable.

4. **Data paths are configurable.** For development, you might use small sample data. For production, you use the full data. A `DataConfig` with overrideable paths supports this.

5. **Physical parameters are explicit.** Atmospheric transmission, sky emissivity, ground emissivity, roughness length — all in `SimulationConfig` with documented defaults. This makes assumptions visible and changeable.

---

## What "Professional" Means Here

| Aspect | Good | Bad |
|--------|------|-----|
| **Module boundaries** | Each file has one clear responsibility. SVF code is not mixed with shadow code is not mixed with UTCI code. | One 2000-line `physics.py` that does everything. |
| **Imports** | Clean hierarchy. Physics doesn't import data. Data doesn't import physics. | Circular imports. `svf.py` importing `overture_loader` to get buildings. |
| **Config** | Single `config.py` with dataclasses. All parameters visible and documented. | Magic numbers scattered across 6 files. |
| **Tests** | Each physics module has unit tests against analytical cases. Integration test for the full pipeline. | No tests, or one `test_all.py` that just runs the pipeline and hopes for the best. |
| **Data management** | `data/raw/`, `data/processed/`, `data/cache/` with clear purposes. Gitignored. | Raw data committed to git. Or everything in one `data/` folder with no structure. |
| **Outputs** | Figures, NetCDF, validation report — each in its own subdirectory. | Everything dumped into a single `output/` folder. |
| **Orchestrator** | `run_stage1.py` only wires modules together. No physics logic. | `run_stage1.py` is 500 lines of physics code mixed with I/O. |
| **Documentation** | Each module has a docstring explaining inputs, outputs, and physics. Config parameters are documented. | No docstrings. Reader has to read the code to understand what a function does. |

---

