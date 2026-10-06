# A6 — data-quality review: Church Street, Bengaluru

Status: REVIEW DRAFT — automated checks performed; researcher manual sign-off and independent georegistration remain pending. No simulation coding has started.

## Checks completed from the downloaded data

- Core: 37 records intersect the boundary; 28 have centroids inside. Full buildings are retained, not clipped.
- Additional 75 m context: 123 buildings including the core. Raw download: 227.
- Reported metre heights: 0/37 (100% missing). Source floor counts: 17/37. Floors are not heights or measurements.
- Invalid polygons: 0. Duplicate IDs: 0. Exact normalized footprint duplicates: 0.
- Small footprints under 20 m2: 1; large footprints over 5,000 m2: 0. Thresholds are reviewer flags, not deletion rules.
- Footprint pairs overlapping by more than 1 m2: 0; inspect details in `processed/quality_metrics.json` before extrusion.
- All selected T, Td, wind speed and direction carry NOAA QC code 1, meaning passed all ISD quality checks. Selected-day observations are every 3 hours, not hourly.
- Selected NASA radiation parameters are present; they are regional satellite/model estimates, not local measurements. Original units Wh/m2 over one hour are retained; hourly mean W/m2 uses division by 1 hour.
- Terrain: 3601 x 3601 tile, 1.000 arcsecond source sample spacing, 32 site samples, 0 missing. Core sample range: 916–934 m EGM96; this is DEM variation, not verified terrain relief or building height.
- GeoJSON uses WGS84 longitude/latitude. Metric calculations use UTM 43N EPSG:32643 with `always_xy=True`; maximum transform round-trip error: 3.55e-15 degrees. Local scene x/y are metric grid east/north relative to the recorded origin. Solar azimuth needs true/grid-north conversion.
- One 6 x 3 m canopy footprint is inside the boundary and has zero collisions with source building footprints. Position and physical feasibility are not surveyed.

## Unfinished manual inspection — required before coding

1. Open `site_inspection_map.png` and the GeoJSON in QGIS against independent, date-documented imagery. Check footprint shifts, duplicates/nesting, missing structures, courtyard/roof outlines and orientation. A plot of the same data does not validate geographic alignment.
2. Fill `processed/building_height_review.csv` and `processed/context_height_review.csv` with verified height evidence. Proposed floor-based values use ASSUMED 3.2 m per floor and are not promoted into model heights. Unknown floors remain missing; no blanket height is invented.
3. Resolve overlap flags and inspect very small buildings manually. Do not automatically delete them.
4. Check the true sidewalk edge, present access restrictions and canopy placement. The 12 m receptor envelope is assumed, not a surveyed pedestrian area. Church Street must not be assumed permanently vehicle-free.
5. Inspect existing trees, awnings and canopies. No vegetation intervention is defined, but leaving existing vegetation unmapped is a baseline simplification requiring explicit acceptance.
6. Verify the solar provider hourly label convention before assigning an interval or pairing its mean radiation with an instantaneous sun angle. Station wind instrument height is not documented in the downloaded file.
7. Check terrain alignment and flat-ground suitability. The DEM is not a local bare-earth survey, LiDAR, roof elevation layer or a height source.
8. With heights known, check that 75 m context covers potential shadow reach, H/tan(solar altitude), and perform a boundary-sensitivity check. Expand geometry if required.
9. Accept material/temperature assumptions and sign `manual_completion_checklist.md`. Then update package status. Until then the package is not simulation-coding-ready.

## Scientific limitations

Building release: September 2026; forcing: April 2024; terrain tile snapshot last modified 2016. This is a controlled scenario setup, not a validated 2024 historical reconstruction. Off-site weather and estimated solar forcing do not validate pedestrian temperature, wind, mean radiant temperature or comfort. No site visit or field measurements were performed.

Detailed machine-readable audit: `processed/quality_metrics.json`. Raw files were not repaired, deduplicated or geometrically simplified.


## A3/A6 additional height source acquired — estimated, not measured

Google Open Buildings 2.5D Temporal Dataset v1 (2023) provides presence-masked footprint-level height estimates for **33/37 core buildings** and **110/123 context buildings**. The original native-grid raster window, full source manifest, source asset URL and acquisition metadata are preserved. Core review rows with high priority: **9**.

Files: `data/raw/buildings/google_open_buildings_temporal_2023_context_window.tif`, `data/processed/estimated_building_heights.csv`, and `data/processed/estimated_heights_metadata.json`. Both height-review CSVs also contain these estimates.

These are **satellite/ML predictions**, not surveyed heights. Median and P10/P90 values summarize predicted pixels inside each footprint with a declared building-presence threshold of 0.5; they are not uncertainty bounds or verified top-of-roof heights. The source has about 4 m effective resolution despite 0.5 m stored pixels, is older than the Overture footprints, and needs extra care for tall buildings and the Global South. The provider's reported MAE is not a Bengaluru-specific accuracy guarantee.[^9](https://sites.research.google/gr/open-buildings/temporal) Dual CC-BY-4.0/ODbL licensing and Google Research attribution are documented.

No model height was promoted: `model_height_m` remains null. Check estimates against floor tags, imagery and manual/field evidence before accepting them. Original Overture metre heights remain 100% missing, which is distinct from the availability of separate unapproved height estimates.


## Handoff v2 clarification and approval status

- Main boundary geometry unchanged; the 75 m context is the outward UTM edge buffer with squared/miter corners, not a 75 m radius. Only main-boundary pedestrian receptors contribute reported results.
- 37 complete height-review rows keep source, floor-derived, Google/ML and observed evidence separate. All 37 source metre heights are missing; 17 floor counts and 33 ML candidates exist, with zero measured or approved model heights. Four absent ML candidates do not necessarily mean four totally evidence-free buildings: B19/B36 have floor tags.
- A generated Google ML CSV or floor-count CSV under `raw/` is a handoff table, not a vendor-original download. Original GeoParquet/GeoJSON, raster window and acquisition records are retained.
- The requested terrain TIFF is a lossless conversion of preserved native HGT, not an original provider TIFF. Point-sample centres, pixel transform, EGM96 datum, metres, NoData and composite-DEM status are explicit. Use it for validation/metadata only.
- Weather is Bengaluru City station observations applied as spatially uniform forcing, with derived RH and separate regional solar estimates. UTC source timestamps and IST conversion are explicit; solar interval alignment remains open.
- The panel is precisely specified but proposed, opaque and without posts; coordinates and true/grid bearings are distinct. Location, permissions and measured material properties are not established.
- Automated checks and this file do not constitute field inspection, researcher acceptance, local thermal validation or a simulator result. All approval gates remain open.
