# SOLARAEUS Data Manifest

Per **GLOBAL RULE 9**, this manifest records the URL, licence, access date, version, and checksum for every dataset utilized in the SOLARAEUS research protocol.

Per **GLOBAL RULE 1**, only **Berlin (primary)**, **Chicago (fallback + replication)**, and **London (reference + replication)** are admissible case study sites. All legacy data (Church Street / Bengaluru) is strictly excluded and cannot be used as evidence.

---

## 1. Primary Case Study: Berlin (Friedrichstraße / Gendarmenmarkt Corridor)

- **City**: Berlin, Germany
- **Corridor**: Friedrichstraße between Französische Str. and Mohrenstr. (Berlin-Mitte)
- **Coordinates**: 52.5145° N, 13.3888° E
- **CRS**: EPSG:25833 (ETRS89 / UTM Zone 33N), Vertical Datum DHHN2016
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings (LoD2 CityGML)**:
    - Source: Geoportal Berlin / Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen
    - URL: `https://daten.berlin.de/datensaetze/geoportal-berlin-3d-gebaeudedaten`
    - Licence: dl-de/by-2-0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
    - Access Date: 2026-10-13
    - Version: LoD2 2024 Release
    - Local Processed Array: `data/processed/berlin/baseline_svf.npy` (SHA256: `376609d3eaf6e1a73887856b312009514f4608b7700fe3224f261f977010103b`)
  - **Terrain (DGM1)**:
    - Source: Geoportal Berlin Digitales Geländemodell (DGM 1m)
    - URL: `https://daten.berlin.de/datensaetze/digitales-gelaendemodell-dgm-1-m`
    - Licence: dl-de/by-2-0
    - Access Date: 2026-10-13
    - Elevation: Flat Spree valley plain ($z = 34.2\,\mathrm{m}$ DHHN2016; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation (Baumkataster)**:
    - Source: Geoportal Berlin Baumbestand Berlin – Straßenbäume
    - URL: `https://daten.berlin.de/datensaetze/baumbestand-berlin-strassenbaeume`
    - Licence: dl-de/by-2-0
    - Access Date: 2026-10-13
    - Inventory: 16 roadside *Tilia cordata* (Littleleaf linden) trees ($h=9.5\,\mathrm{m}, r=3.5\,\mathrm{m}, \tau=0.15$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: Deutscher Wetterdienst (DWD) Open Data via `wetterdienst` Python API
    - Station: Station 00433 (Berlin-Tempelhof, 52.4675° N, 13.4021° E, 5.2 km from site)
    - Date of Observation: 2023-07-09 (Clear-sky peak summer heatwave, peak $T_{\mathrm{air}} = 32.1^\circ\mathrm{C}$)
    - URL: `https://opendata.dwd.de/climate_environment/CDC/`
    - Licence: Open Data / DWD (§ 4–6 DWD-Gesetz)
    - Local File: `data/raw/berlin/weather_24h.csv`
    - SHA256 Checksum: `59b9b53ac8cfbe43700a086e366367c39d4b23ff63490686c78762082621ced2`
  - **Baseline Literature Reference**:
    - Citation: Eingrüber, Meier, & Scherer (2025) *Geosci. Model Dev.*, 18, 141–160; Meier et al. (2017) TU Berlin
    - Baseline Range: Solar noon sunlit $T_{\mathrm{mrt}} \approx 57.0\text{–}61.5^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 32.0\text{–}36.5^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 23.0\text{–}26.5\text{ K}$

---

## 2. Fallback & Replication Study: Chicago (S LaSalle Financial Canyon)

- **City**: Chicago, Illinois, USA
- **Corridor**: S LaSalle St between W Adams St and W Jackson Blvd (The Loop)
- **Coordinates**: 41.8795° N, -87.6324° W
- **CRS**: EPSG:32616 (WGS 84 / UTM Zone 16N), Vertical Datum NAVD88
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings**:
    - Source: City of Chicago Open Data Portal Building Footprints
    - URL: `https://data.cityofchicago.org/Buildings/Building-Footprints/`
    - Licence: Public Domain / City of Chicago Data Terms of Use
    - Access Date: 2026-10-13
    - Heights: 45.0 m to 110.0 m high-rise masonry and glass canyon
  - **Terrain**:
    - Source: USGS 3D Elevation Program (3DEP) 1m DEM
    - URL: `https://www.usgs.gov/3d-elevation-program`
    - Licence: Public Domain (US Federal Government)
    - Access Date: 2026-10-13
    - Elevation: Flat Lake Michigan terrace ($z = 181.5\,\mathrm{m}$ NAVD88; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation**:
    - Source: City of Chicago Urban Forest Tree Inventory
    - Justified Approximation: 8 *Gleditsia triacanthos* (honey locust) sidewalk tree planters ($h=5.0\,\mathrm{m}, r=2.0\,\mathrm{m}$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: NOAA Local Climatological Data (LCD) Station KORD / Chicago O'Hare
    - Date of Observation: 2024-07-15 (Peak summer heatwave, peak $T_{\mathrm{air}} = 33.8^\circ\mathrm{C}$)
    - URL: `https://www.ncei.noaa.gov/cdo-web/`
    - Licence: Open Access / US Federal Government
    - Local File: `data/raw/chicago/weather_24h.csv`
    - SHA256 Checksum: `dde39d7ba67e6a9ed5bd9864403b6d1db1cfdd50c158070e5cc1df5703015324`
  - **Baseline Literature Reference**:
    - Citation: Middel et al. (2021) *Environ. Res. Lett.*; Sailor et al. (2015)
    - Baseline Range: Sunlit $T_{\mathrm{mrt}} \approx 58.5\text{–}63.0^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 32.5\text{–}36.5^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 24.0\text{–}28.0\text{ K}$

---

## 3. Reference & Replication Study: London (Exhibition Road Boulevard)

- **City**: London, United Kingdom
- **Corridor**: Exhibition Road between Cromwell Rd and Prince Consort Rd (South Kensington)
- **Coordinates**: 51.4985° N, -0.1738° W
- **CRS**: EPSG:27700 (OSGB36 / British National Grid), Vertical Datum ODN
- **Domain**: 240 m × 200 m, 48,000 cells at 1.0 m resolution
- **Data Layers**:
  - **Buildings**:
    - Source: Ordnance Survey Open Map – Local / GLA 3D Building Heights
    - URL: `https://osdatahub.os.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Access Date: 2026-10-13
    - Heights: 22.0 m to 32.0 m institutional Victorian limestone buildings
  - **Terrain**:
    - Source: Environment Agency LiDAR Composite DTM (1m)
    - URL: `https://environment.data.gov.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Access Date: 2026-10-13
    - Elevation: South terrace ($z = 21.0\,\mathrm{m}$ ODN; local datum $z = 0.0\,\mathrm{m}$)
  - **Vegetation**:
    - Source: Royal Borough of Kensington & Chelsea Street Tree Dataset
    - Inventory: 14 *Platanus x hispanica* (London plane) boulevard trees ($h=11.0\,\mathrm{m}, r=4.0\,\mathrm{m}, \tau=0.18$)
  - **Weather Forcing (24-Hour Diurnal Summer Heatwave)**:
    - Source: Met Office MIDAS Open / London Heathrow (EGLL)
    - Date of Observation: 2024-07-19 (Peak clear heatwave, peak $T_{\mathrm{air}} = 32.2^\circ\mathrm{C}$)
    - URL: `https://catalogue.ceda.ac.uk/`
    - Licence: Open Government Licence (OGL v3.0)
    - Local File: `data/raw/london/weather_24h.csv`
    - SHA256 Checksum: `3a30a8a952abec1990dd1c7e531722796b4496a4322ea001e8c2238048085e44`
  - **Baseline Literature Reference**:
    - Citation: Lindberg et al. (2018) *Urban Climate*, 23, 1–19 (UMEP / SOLWEIG Central London)
    - Baseline Range: Sunlit $T_{\mathrm{mrt}} \approx 55.5\text{–}59.8^\circ\mathrm{C}$, shaded $T_{\mathrm{mrt}} \approx 31.5\text{–}35.0^\circ\mathrm{C}$, $\Delta T_{\mathrm{mrt}} \approx 22.0\text{–}25.5\text{ K}$

---

## 4. Processed Diurnal Simulation Artifacts (Stage 2)

- **Berlin Diurnal Metrics**: `data/processed/berlin/diurnal_metrics.json`
  - SHA256: `76be74a39fac77669fed1da985cd3582a9dd5f674fdcd8cf1d8e1d9997589f34`
- **Chicago Diurnal Metrics**: `data/processed/chicago/diurnal_metrics.json`
  - SHA256: `f1c2eb66aef6ed3899045d897491616b4880e1ba80c01a1767c49e0ceacdbbf2`
- **London Diurnal Metrics**: `data/processed/london/diurnal_metrics.json`
  - SHA256: `f577c8f1645ce785ddb0d8fd39d7213189088df423865fb14565e946ca3bcbfe`

---

## 5. Deprecated / Legacy Sites Archive
- **Site**: Church Street (Bengaluru)
- **Classification**: DEPRECATED & OUT OF SCOPE per Global Rule 1.
- **Protocol Notice**: No legacy Church Street datasets are used as scientific evidence in this protocol.
