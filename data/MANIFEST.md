# SOLARAEUS Data Manifest

Per **GLOBAL RULE 9**, this manifest records the URL, licence, access date, version, and checksum for every dataset utilized in the SOLARAEUS research protocol.

Per **GLOBAL RULE 1**, only **Berlin (primary)**, **Chicago (fallback + replication)**, and **London (reference + replication)** are admissible case study sites. All legacy data (Church Street / Bengaluru) is strictly excluded and cannot be used as evidence.

---

## 1. Case Study Sites (Protocol Scope)

### 1.1 Berlin (Primary Case Study)
- **City**: Berlin, Germany
- **Coordinates**: 52.5200° N, 13.4050° E (UTM 33N / EPSG:25833)
- **Status**: Target site (Ingestion pending Stage 2)
- **Data Layers**:
  - **Buildings**: OpenStreetMap / Berlin 3D City Model (LoD2 / ALKIS)
    - Source URL: `https://daten.berlin.de/datensaetze/geoportal-berlin-3d-gebaeudedaten`
    - Licence: dl-de/by-2-0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
    - Access Date: Scheduled
    - Version: 2024
    - SHA256 Checksum: TBD upon ingestion
  - **Terrain (DTM)**: DGM1 (Digitales Geländemodell 1m)
    - Source URL: `https://daten.berlin.de/datensaetze/digitales-gelaendemodell-dgm-1-m`
    - Licence: dl-de/by-2-0
    - Access Date: Scheduled
    - Version: 2024
    - SHA256 Checksum: TBD upon ingestion
  - **Vegetation / Trees**: Berlin Baumkataster (Street Trees)
    - Source URL: `https://daten.berlin.de/datensaetze/baumbestand-berlin-strassenbaeume`
    - Licence: dl-de/by-2-0
    - Access Date: Scheduled
    - Version: 2024
    - SHA256 Checksum: TBD upon ingestion
  - **Weather Forcing**: DWD (Deutscher Wetterdienst) Open Data Station 00433 (Berlin-Tempelhof)
    - Source URL: `https://opendata.dwd.de/climate_environment/CDC/`
    - Licence: Open Data / DWD
    - Access Date: Scheduled
    - Version: Historical Summer 2024
    - SHA256 Checksum: TBD upon ingestion

---

### 1.2 Chicago (Fallback + Replication)
- **City**: Chicago, Illinois, USA
- **Coordinates**: 41.8781° N, -87.6298° W (UTM 16N / EPSG:32616)
- **Status**: Fallback replication site
- **Data Layers**:
  - **Buildings**: City of Chicago Open Data Portal Building Footprints
    - Source URL: `https://data.cityofchicago.org/Buildings/Building-Footprints/`
    - Licence: Public Domain / City of Chicago Terms
    - Access Date: Scheduled
    - Version: 2024
    - SHA256 Checksum: TBD upon ingestion
  - **Weather Forcing**: NOAA Local Climatological Data (KORD / Chicago O'Hare)
    - Source URL: `https://www.ncei.noaa.gov/cdo-web/`
    - Licence: Open Access / US Federal Government
    - Access Date: Scheduled
    - Version: Summer 2024
    - SHA256 Checksum: TBD upon ingestion

---

### 1.3 London (Reference + Replication)
- **City**: London, United Kingdom
- **Coordinates**: 51.5074° N, -0.1278° W (British National Grid / EPSG:27700)
- **Status**: Reference replication site
- **Data Layers**:
  - **Buildings**: Ordnance Survey Open Map - Local / GLA 3D Building Stock
    - Source URL: `https://osdatahub.os.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Access Date: Scheduled
    - Version: 2024
    - SHA256 Checksum: TBD upon ingestion
  - **Weather Forcing**: Met Office MIDAS Open / London Heathrow
    - Source URL: `https://catalogue.ceda.ac.uk/`
    - Licence: OGL v3.0
    - Access Date: Scheduled
    - Version: Summer 2024
    - SHA256 Checksum: TBD upon ingestion

---

## 2. Minimal Synthetic Benchmark Baseline (Stage 1)
- **Dataset**: `results/raw/stage_1/baseline_synthetic/`
- **Description**: Single 10m x 10m x 10m watertight cube on flat ground ($50\text{ m} \times 50\text{ m}$ domain, $10{,}000$ cells, $dx = 0.5\text{ m}$, fixed sun altitude 45°, azimuth 180°).
- **Generator**: `benchmarks/run_synthetic_baseline.py`
- **Access / Run Date**: 2026-10-13T07:48:40Z
- **Licence**: MIT (Internal synthetic code generator)
- **Version**: Stage-1 Git Commit `12dc47941b9e81cc0a2cd3f4828d444fea0e9de4`
- **Output Artifacts**:
  - `baseline_metrics.json`
  - `cpu_shadow.npy`
  - `gpu_shadow.npy`
  - `cpu_svf.npy`
  - `gpu_svf.npy`
  - `cpu_tmrt.npy`
  - `gpu_tmrt.npy`
  - `cpu_utci.npy`
  - `gpu_utci.npy`
  - `synthetic_cube_baseline_comparison.png`

---

## 3. Deprecated / Legacy Sites Archive
- **Site**: Church Street (Bengaluru)
- **Classification**: DEPRECATED & OUT OF SCOPE per Global Rule 1.
- **Protocol Notice**: No legacy Church Street datasets are used as scientific evidence in this protocol.
