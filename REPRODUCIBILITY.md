# Solaraeus — Complete Project Reproducibility Guide

This document provides complete, reproducible instructions and code to regenerate the entire **Solaraeus 3D Urban Microclimate Digital Twin** from scratch.

---

## 1. System Requirements & Prerequisites

| Component | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11, macOS 12+, Linux (Ubuntu 20.04+) | 64-bit OS | Tested on Windows 11 & Linux x86_64 |
| **Python** | 3.10 | 3.11 | Required for scientific packages and PyTorch |
| **Node.js** | 18.0.0+ | 20.x+ | Required for React 19 + Three.js client |
| **npm** | 9.0+ | 10.x+ | Packaged with Node.js |
| **RAM** | 8 GB | 16 GB | Needed for 1m raster grids & 3D ray-casting |

---

## 2. Quickstart: One-Click Automated Reproduction

To reproduce all simulation outputs, 3D meshes, NetCDF datasets, validation reports, and the frontend web application in a single command:

### Windows (PowerShell or Command Prompt)
```powershell
# From the repository root:
python scripts/reproduce_all.py
```
*(Alternatively, double-click `scripts\reproduce.bat`)*

### Linux / macOS (Bash)
```bash
# From the repository root:
chmod +x scripts/reproduce.sh
./scripts/reproduce.sh
```

---

## 3. Step-by-Step Manual Reproduction Guide

If you prefer to execute each stage of the pipeline independently, follow these steps:

### Step 3.1: Python Environment Setup

#### Option A: Using Conda (Recommended)
```bash
# 1. Create conda environment from environment.yml
conda env create -f environment.yml

# 2. Activate environment
conda activate solaraeus
```

#### Option B: Using standard Python venv and pip
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3.2: Run Stage 1 Backend Simulation Pipeline

The master backend pipeline executes data ingestion, geometric harmonization, Steyn (1980) SVF ray-casting, diurnal shadow casting, $T_\text{mrt}$ radiative flux balancing, UTCI thermal stress modeling, watertight 3D building mesh extrusion, scientific NetCDF export, and cartographic publication maps.

```bash
python scripts/run_stage1.py
```

**What this script performs:**
1. **Data Acquisition**: Loads Washington Square Park elevation data (1m LiDAR DEM) and Overture Maps 3D building footprints.
2. **Harmonization & DSM**: Harmonizes coordinate reference systems (EPSG:32618 UTM 18N) and builds the 1m Digital Surface Model (DSM).
3. **Ray-traced Sky View Factor (SVF)**: Computes 36-direction horizon elevation angles via the Steyn (1980) formulation.
4. **Diurnal Solar Shadows**: Calculates astronomical sun positions across daytime hours and ray-traces directional building shadows.
5. **Mean Radiant Temperature ($T_\text{mrt}$)**: Solves Stefan-Boltzmann radiative exchange balances for both sunlit and shaded pedestrian points.
6. **Universal Thermal Climate Index (UTCI)**: Evaluates thermal comfort and heat stress classifications.
7. **3D Watertight Mesh**: Extrudes footprints to true LiDAR roof heights and exports `outputs/meshes/buildings.obj`.
8. **Scientific NetCDF & Validation Report**: Exports multi-dimensional grid `outputs/netcdf/stage1_microclimate.nc` and writes `outputs/reports/stage1_validation.md`.

---

### Step 3.3: Export React & Three.js Frontend Data Contracts

Converts the raw simulation grids into typed JSON data contracts optimized for the real-time 3D web viewport:

```bash
python scripts/export_frontend_data.py
```

**Output Contracts Created:**
- `outputs/data/simulation_config.json`: Spatial bounds, grid resolution (1m), study area metadata.
- `outputs/data/available_times.json`: Diurnal timestamps (06:00–19:00 EDT) with solar azimuth and altitude.
- `outputs/data/walkable_grid.json`: Binary obstacle map for pedestrian avatar collision detection.
- `outputs/meshes/buildings_mesh.json`: Indexed vertex/face buffers for fast Three.js loading.
- `outputs/json/{dsm,svf,shadows_*,tmrt_*,utci_*}.json`: Gridded metrics with bounding box and values.

---

### Step 3.4: Run Scientific Physics & Unit Tests

Verify all mathematical calculations, geometry transforms, and radiative physics:

```bash
pytest tests/ -v
```

**Test Suite Coverage:**
- `test_solar.py`: Astronomical solar position and zenith angles.
- `test_shadows.py`: Directional shadow casting and sunlit/shaded boundary checks.
- `test_svf.py`: Steyn (1980) sky view factor mathematical bounds ($0.0 \le \text{SVF} \le 1.0$).
- `test_radiation.py`: Shortwave and longwave radiative flux balance calculations.
- `test_tmrt.py`: Mean radiant temperature convergence and shade cooling deltas ($\Delta T_\text{mrt} > 10^\circ\text{C}$).
- `test_utci.py`: 6th-order polynomial UTCI evaluation and heat stress categorization.
- `test_maps.py`: Cartographic publication plot generation.

---

### Step 3.5: Build and Run the 3D Digital Twin Frontend

The frontend is a Vite + React 19 + TypeScript + Three.js application featuring an Architectural Clay aesthetic and a floating spatial BIM/CAD dashboard.

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Build production bundle (verifies TypeScript types & builds dist/)
npm run build

# 4. Start local development server
npm run dev
```

Open your browser and navigate to:
**`http://localhost:5173/`**

---

## 4. Summary of Output Artifacts

| Category | File / Path | Description |
| :--- | :--- | :--- |
| **Scientific Data** | `outputs/netcdf/microclimate_*.nc` | CF-compliant NetCDF4 multi-dimensional climate dataset |
| **Validation Report** | `outputs/reports/stage1_validation.md` | Full physics verification report and statistical summary |
| **3D Geometry** | `outputs/meshes/buildings_3d.obj` | Watertight 3D extruded building mesh |
| **3D Geometry** | `outputs/meshes/buildings_3d.json` | Web-optimized indexed vertex and face buffer |
| **Data Contracts** | `outputs/data/simulation_config.json` | Study area configuration and geographic bounds |
| **Data Contracts** | `outputs/data/available_times.json` | Diurnal time steps and celestial sun coordinates |
| **Data Contracts** | `outputs/data/walkable_grid.json` | 1m pedestrian collision grid for avatar locomotion |
| **Cartographic Figures**| `outputs/figures/*.png` | Scientific publication plots for DSM, SVF, Shadows, $T_\text{mrt}$, and UTCI |
| **Production Web** | `frontend/dist/` | Standalone compiled client bundle (HTML/CSS/JS) |

---

## 5. Microclimate Physics Formulation

### 1. Sky View Factor (Steyn 1980)
$$\text{SVF} = 1 - \frac{1}{2\pi} \int_0^{2\pi} \cos^2(\beta(\phi)) \, d\phi \approx 1 - \frac{1}{N} \sum_{i=1}^N \cos^2(\beta_i)$$
Where $\beta_i$ is the maximum building horizon elevation angle in azimuthal direction $\phi_i$ across $N=36$ search radials.

### 2. Directional Shadow Casting
For sun altitude $\theta_\text{alt}$ and azimuth $\phi_\text{az}$:
$$z_\text{ray}(s) = z_0 + s \cdot \tan(\theta_\text{alt})$$
A surface cell is shaded if any terrain or building obstacle along the inverted solar ray satisfies $\text{DSM}(x_s, y_s) > z_\text{ray}(s)$.

### 3. Mean Radiant Temperature ($T_\text{mrt}$)
$$T_\text{mrt} = \left[ \frac{S_\text{str}}{\sigma} \right]^{0.25} - 273.15$$
Where $\sigma = 5.67 \times 10^{-8} \, \text{W}/(\text{m}^2\text{K}^4)$ is the Stefan-Boltzmann constant, and $S_\text{str}$ is the mean radiant flux absorbed by a human body from direct shortwave, diffuse sky, ground-reflected, and atmospheric longwave radiation.

### 4. Universal Thermal Climate Index (UTCI)
Evaluated using the Fiala multi-node human thermoregulation model approximated by a 6th-order polynomial function of air temperature ($T_a$), relative humidity ($RH$), 10m wind velocity ($v_{10}$), and $T_\text{mrt}$:
$$\text{UTCI} = f(T_a, RH, v_{10}, T_\text{mrt})$$

---

## 6. Troubleshooting

- **Python package import errors**:
  Ensure your virtual environment is active (`.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on Linux/macOS) and run `pip install -r requirements.txt`.
- **Port 5173 already in use**:
  If Vite chooses port 5174 or another port, simply check the terminal output for the local URL.
- **Missing Cached Data**:
  If `export_frontend_data.py` warns about missing intermediate cache files, execute `python scripts/run_stage1.py` first to generate them.
