# Bengaluru Church Street — revised manual data handoff v2

Status: **REVIEW DRAFT — NOT READY FOR SIMULATION CODING**. Prepared 2026-10-07T01:42:00.174501+05:30 (IST). The original v1 package is preserved; this folder is a separate revision. No simulator was coded, inspected or run, and no physical intervention or external write occurred.

## 1. Main boundary versus shadow context

Main analysis boundary: **77.6044–77.6064 E, 12.9743–12.9755 N** (approximately 217 × 133 m; 37 intersecting whole footprints).

Shadow context: transform that polygon to **EPSG:32643 UTM 43N**, expand every edge outward by **75.0 m**, with squared/miter corners, then return it to longitude/latitude. This is not a circle or a 75 m radius from the centre. Diagonal squared corners can be more than 75 m from an original corner.

The existing context geometry matches this construction to less than 1 mm. Its approximate bounding box is **77.603709131–77.607090869 E, 12.973622460–12.976177532 N**, approximately 367 × 283 m (10.38 ha). It contains 123 intersecting whole footprints including the 37 main footprints; 86 are context-only. The GeoJSON polygon, not rounded bounding-box text, is authoritative.

Use expanded-context buildings for shadow casting; **reported pedestrian results remain inside the unchanged main boundary**, intersected with the proposed pedestrian-analysis envelope. Preserve complete caster polygons; do not clip roofs/walls to either boundary. Buffer sufficiency is not yet proven. See `data/processed/analysis_domains.json`.

## 2. Height review — 37 complete records, no fabricated approvals

`data/processed/building_height_review.csv` has one row per B01–B37 and separate fields for source metre height, floor count, floor-derived proposal, Google/ML estimate, observed/manual/verified/model height, source labels, Google use, priority and reviewer evidence.

| Evidence | Available | Classification/status |
|---|---:|---|
| Overture source metre height | 0/37 | missing; source provenance is not proof of measurement |
| Source floor count | 17/37 | sourced tags, unverified |
| Floor-count-derived proposal | 17/37 | floors × assumed 3.2 m; inferred, unapproved |
| Google 2023 ML candidate | 33/37 | estimated, not measured, unapproved |
| On-site observed / approved model height | 0/37 | missing; model heights stay null |

Google estimates are used **for review only**, never as an approved model height. No ML candidate: **B19, B23, B32, B36**. B19/B36 have two-floor tags; B23/B32 have no floor tags. Nine automatic priority flags: **B02, B03, B17, B19, B23, B31, B32, B36, B37**. Also inspect tall B10 and small B27. Source-presence coverage is not calibrated confidence; P10/P90 are not confidence intervals. `context_height_review.csv` covers all 123 casters. Blank CSV values mean missing, not zero.

## 3. Terrain metadata and use

Dataset: Mapzen/Tilezen Skadi tile N12E077. Horizontal CRS **EPSG:4326**; vertical datum **EGM96 orthometric**; units **metres**; NoData **−32768**; native sampling **1 arcsecond**, roughly 30 m. Composite elevation DEM, **not certified bare-earth DTM**, surveyed roof elevations or building heights. Exact contributing source images have not been independently traced.

The actual original download is `N12E077.hgt.gz` and is preserved. `elevation_original.tif` is explicitly a **lossless format conversion**, not a provider-original TIFF. All 3601 × 3601 samples and native point centres are preserved, with no resampling or vertical transformation. See `data/raw/terrain/elevation_metadata.json`.

Initial engine requirement: use the DEM for extent/elevation validation and metadata only. Do not modify a flat mesh. Proposed ground remains **model-relative z=0**, subject to researcher acceptance. No existing engine was inspected.

## 4. Weather status and timestamps

“**Bengaluru City station observations applied as spatially uniform forcing at the Church Street site.**”

| Variable | Value | Classification |
|---|---:|---|
| Air temperature | 35.0°C | Observed off-site |
| Dew point | 8.5°C | Observed off-site |
| Relative humidity | 19.73% | Derived from observations (Magnus equation) |
| Wind speed | 1.5 m/s | Observed off-site |
| Wind direction | 90°, from east | Observed off-site; direction from true north |
| Solar radiation | See separately preserved GHI/DNI/DHI estimates | Regional satellite/model estimate |

Station **43295099999 / WMO 43295**, Bengaluru City (not HAL Airport), at **12.9666666 N, 77.5833333 E**. Geodesic station-to-centre distance **2.561595 km**. The original timestamp `2024-04-15T09:00:00` is **UTC**, not IST; local time is **2024-04-15 14:30:00 IST**, UTC+05:30 with no daylight saving. Selected temperature/dewpoint/wind fields have QC code 1. Wind measurement height is unknown.

This is a one-instant forcing row, not an hourly transient series. Station reports on this date are three-hourly. Solar source label **2024041509 UTC** contains GHI **755.97**, DNI **728.31**, DHI **172.18 Wh/m²** over one hour; dividing by one hour gives the same numeric hourly-mean W/m² values. These are not instantaneous or site-measured radiation. Provider hourly start/end alignment remains unverified and both endpoints remain null. DNI is direct normal, not horizontal.

## 5. Precisely defined proposed shade panel

- Object CANOPY_001 / intervention BLR_SHADE_001; one `overhead_shade_panel`.
- UTM-defined length **6.0 m**, width **3.0 m**, area **18 m²**, underside **3.5 m**, thickness **0.10 m**, top **3.6 m** above proposed flat ground.
- Centre **77.60561994802289 E, 12.974866036977149 N**; all four exact corners and local-metre coordinates are in `intervention_definition.json`.
- Long-axis bearing **103.027908442° clockwise from true north**, corresponding to **102.442501929° clockwise from UTM grid north**. Do not confuse these references.
- **Opaque**, shortwave transmissivity 0; **no supporting posts** in this geometric pilot. This is not structural advice or a claim a real unsupported panel can stand.
- Generic panel material: assumed **albedo 0.60**, **emissivity 0.90**, initial surface temperature **35°C**. Not measured or equilibrated.
- Status **proposed**, researcher approval null. Source-footprint clearance approximately 1.751 m; no mapped-footprint collision, but actual sidewalk, trees/awnings, existing shade, traffic clearance and permissions remain unverified.

The intervention JSON exposes the requested top-level fields without placeholder values. The baseline has no proposed new panel; `original_geometry:null` is not evidence that no real canopy exists.

## 6. Provenance, licensing and honest raw-file roles

`data/processed/provenance.json` records every dataset's source URL, original download timestamps (UTC and IST), version/snapshot, license evidence, attribution, original filenames and hashes, plus per-file processing lineage. File inventory excludes the manifest itself to avoid a self-hash cycle; `SHA256SUMS.txt` also hashes the manifest.

Overture release **2026-09-23.1** is historical relative to this handoff's actual date **7 October 2026 IST**. The original downloads occurred **6 October UTC / 7 October IST**. Download dates are not observation, imagery, release or terrain-acquisition dates. Geometry 2026, height imagery 2023, forcing 2024 and older terrain are non-contemporaneous controlled-scenario inputs, not a verified historical reconstruction.

- Overture: **ODbL-1.0**, with underlying source attribution retained.
- Google temporal heights: **CC-BY-4.0 / ODbL-1.0** dual terms; Google Research attribution.
- Terrain: provider/source attribution and SRTM/GMTED public-domain source terms; exact source mix not independently traced. Do not assign a new blanket license.
- NASA POWER: **CC-BY-4.0 per the NASA-managed AWS registry listing**, with POWER service/version/access-date and CERES attribution. The original API file itself contains no SPDX label.
- NOAA international station records: publicly accessible archive; **no record-specific SPDX license identified**. NOAA's policy distinguishes Federal-produced from externally contributed data, so universal CC0 is not invented. Clarify station-specific terms before public redistribution.

Raw originals are preserved separately from requested aliases/exports. Existing GeoParquet metadata preserved; canonical filename is a byte-identical alias. `floor_counts.csv`, `google_ml_height_estimates.csv` and `solar_estimates.csv` are documented generated handoff tables, **not vendor-original CSV downloads**. The terrain TIFF is a format conversion.

## Folder to hand off

```text
data/
  raw/
    buildings/
      overture_buildings_2026-09-23.1.geoparquet
      overture_buildings_raw.geojson
      floor_counts.csv
      google_ml_height_estimates.csv
      [preserved original acquisition exports and native ML window]
    terrain/
      elevation_original.tif
      elevation_metadata.json
      N12E077.hgt.gz
    weather/
      bengaluru_station_observations.csv
      solar_estimates.csv
      [original station/solar/catalogue files]
  processed/
    site_selection.json
    site_boundary.geojson
    shadow_context_boundary.geojson
    analysis_domains.json
    building_height_review.csv
    building_height_review_schema.json
    context_height_review.csv
    weather_forcing.csv
    weather_forcing_metadata.json
    material_assumptions.json
    intervention_definition.json
    provenance.json
    package_status.json
    validation_report.json
    [preserved geometry and supporting data]
  data_quality_report.md
  manual_checklist.md
```

## Acceptance before coding

The records and formats are populated; **manual height verification is not complete**. Follow `data/manual_checklist.md`. Researcher must validate geometry/heights and panel placement, settle solar intervals, accept assumptions, check buffer adequacy and sign off. All CSVs are **static data outputs**, with raw sources and methods preserved. Automated checks are not human approval.

### Source references

- https://stac.overturemaps.org/2026-09-23.1/catalog.json
- https://sites.research.google/gr/open-buildings/temporal
- https://github.com/tilezen/joerd/blob/master/docs/formats.md
- https://github.com/tilezen/joerd/blob/master/docs/attribution.md
- https://www.ncei.noaa.gov/data/global-hourly/access/2024/43295099999.csv
- https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf
- https://power.larc.nasa.gov/docs/referencing/
- https://registry.opendata.aws/nasa-power/
- https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf
