The Big Picture: How Data Flows Through the Project
Think of it as a factory assembly line:

Download raw data → Clean it up and put it in one coordinate system → Build geometry objects → Run physics calculations → Make pictures and save results
Each step hands its output to the next step. No step reaches backwards to grab data from a previous step. This clean one-way flow is the single most important thing for avoiding bugs.

Directory-by-Directory, Module-by-Module
1. data/ — Where Raw Data Lives (and Where It Gets Cleaned)
This directory has three sub-folders, and understanding the difference between them is critical.

data/raw/ — The "Do Not Touch" Zone
This is where downloaded files go, exactly as they came from the internet. Nothing in here is modified.

Overture building footprints — a GeoJSON file with hundreds of building polygons, each with a height number if available.
ERA5 weather data — a NetCDF file with temperature, humidity, wind, and solar radiation for every hour of the day.
DEM (terrain elevation) — a GeoTIFF raster showing ground elevation.
Canopy height (optional) — a raster showing tree heights.
Why keep raw data separate? If the Overture data changes (new release), you re-download and replace the raw file. You don't have to figure out which processed files need rebuilding — you just re-run the pipeline from raw forward.

data/processed/ — The "Cleaned Up" Zone
Files here have been reprojected, resampled, cropped, and otherwise prepared. They're derived from raw but are in a form the rest of the project can actually use.

Buildings in UTM coordinates (not lat/lon anymore)
DEM resampled to 1-meter grid
Sidewalk polygons (if you have them)
Key point: If your harmonization logic changes (e.g., you fix a coordinate transform bug), you delete the processed files and re-create them from raw. The raw files are still there.

data/cache/ — The "Expensive to Recreate" Zone
Some things take a long time to compute. The 3D building mesh, for example — extruding hundreds of polygons into watertight 3D meshes takes time. If the DSM hasn't changed, there's no reason to rebuild the mesh every time you run the pipeline. So you save it here and reload it.

Rule: Only cache things that are stable. If the DSM changes, the cached mesh is stale and must be rebuilt. The pipeline should know this — cache files should have version markers or timestamps so the code can tell if they're still valid.

2. src/solaraeus/config.py — The Settings File
This is a single file that holds every adjustable parameter for the entire project.

What it contains:

Where we're looking: latitude, longitude, bounding box, UTM zone, grid resolution (1 meter).
When we're simulating: the date (July 15, 2024), the time of day (14:00 local), day of year.
Who's experiencing the weather: pedestrian height above ground (1.1 meters — standard for thermal comfort calculations).
How the physics works: number of directions to check for sky view (360), how far to look for shadows (200 meters), atmospheric clarity, sky emissivity, ground emissivity, cloud cover.
Where files go: paths to raw/, processed/, cache/, outputs/.
Why this matters: If you want to simulate a different city, a different hour, or a different grid resolution, you change it here — not by hunting through six different files for magic numbers. Every module reads from this config. This is the single most important file for reproducibility and for avoiding "why did I get this result?" confusion two weeks later.

Bug minimization: Because the config is frozen (can't be changed after creation), you can't accidentally modify a parameter halfway through a run. And because every value is named and documented, you can't confuse "360 SVF directions" with "200 meter shadow radius."

3. src/solaraeus/data/ — Getting Data and Making It Consistent
This subpackage has five files, each with a narrow job.

overture_loader.py — Downloading Building Footprints
What it does:

Calls the Overture Maps API (or reads a cached file) to get building polygons for your bounding box.
Returns a GeoDataFrame — a table where each row is a building, with columns for id, geometry (the polygon shape), height, number of floors, and which data source contributed it.
What can go wrong:

The bounding box might be in the wrong order (latitude vs. longitude swapped).
The height field might be missing for many buildings (different data sources have different coverage).
The file might be in lat/lon (EPSG:4326) when everything else is in UTM.
How to catch these early:

Print the number of buildings returned. If you asked for a 200×200m area and got 3 buildings or 30,000, something is wrong with the bounding box.
Check what percentage of buildings have a height value. If it's below 80%, you need a fallback height estimate or a different data source.
Print the CRS (coordinate reference system) of the returned data. It should say EPSG:4326. If it says something else, your later reprojection will silently produce wrong results.
era5_loader.py — Downloading Weather Data
What it does:

Calls the ECMWF CDS API to download ERA5 reanalysis data for your date and area.
Extracts the specific variables you need: air temperature, dewpoint (for humidity), wind components, solar radiation.
Converts units: Kelvin to Celsius, Joules per square meter to Watts per square meter.
Computes relative humidity from temperature and dewpoint.
Computes wind speed at pedestrian height (1.1m) from the 10-meter wind using a logarithmic profile.
What can go wrong:

ERA5 times are in UTC. If you want 14:00 local time in New York (EDT = UTC−4), you need 18:00 UTC, not 14:00 UTC. This is the most common error.
The CDS API requires a registered account and a configuration file. If it's not set up, the download fails silently or with a confusing error.
Wind at pedestrian height involves a roughness length parameter (how rough the urban surface is). Picking the wrong value gives wrong wind speeds.
How to catch these early:

Print the extracted values: "Air temperature 33.2°C, wind 2.1 m/s at 10m, 1.3 m/s at 1.1m." If you see -273°C or 300 m/s wind, something went wrong with unit conversion.
Print the time string you're extracting: "2024-07-15T18:00:00" — verify this is the correct UTC time for your local time.
Print the roughness length you're using and the resulting pedestrian wind speed. Compare against typical values for urban areas (1-3 m/s at pedestrian height on a moderately windy day).
dem_loader.py — Downloading Terrain Elevation
What it does:

Downloads a digital elevation model (SRTM or Copernicus DEM).
Reprojects it from its native coordinate system to UTM.
Resamples it to 1-meter resolution.
Computes relative elevation (subtracts the minimum so the lowest point is 0).
What can go wrong:

The DEM might be in a different CRS than expected.
Resampling from 30m to 1m doesn't add real detail — it just interpolates. For flat terrain this is fine; for steep terrain it can create artifacts.
The DEM might include buildings (if it's a surface model, not a bare-earth model). You want bare earth, not buildings on top of earth.
How to catch these early:

Print the elevation range: "Elevation ranges from 20m to 25m." For Washington Square Park, this should be a small range (the area is fairly flat). A range of 200m would indicate you downloaded the wrong tile.
Visually inspect the DEM raster. It should look like smooth ground, not blocky buildings.
harmonize.py — The Critical Integration Step
What it does:

Takes the building GeoDataFrame (in lat/lon), the DEM (in whatever CRS it came in), and the ERA5 weather data.
Reprojects everything to UTM Zone 18N.
Resamples everything to a 1-meter grid.
Crops everything to the study area bounding box.
Returns a unified grid: a DSM raster, a buildings table, the pedestrian grid, and metadata.
This is where most coordinate bugs happen. If the buildings are reprojected incorrectly, or the DEM is offset by a few meters, or the grid resolution doesn't match, every downstream calculation will be wrong in ways that are hard to detect.

What can go wrong:

The buildings get reprojected to UTM but the DEM gets reprojected differently (different datum, different transform), causing a misalignment.
The 1-meter grid's origin (the coordinate of pixel [0,0]) doesn't match between the building rasterization and the DEM. Buildings end up shifted relative to the ground.
The bounding box in UTM is slightly wrong, cutting off buildings at the edge or including extra area.
How to catch these early:

After harmonization, visualize the DSM. Buildings should appear on top of the ground in the correct locations. If buildings are floating in the middle of the park or shifted 50 meters to the east, the harmonization is broken.
Check that the grid dimensions match what you expect: "200 rows × 200 columns for a 200×200m area at 1m resolution." If you get 199×199 or 201×201, your bounding box or resolution math is off by one pixel — this causes subtle edge effects.
Print the coordinate of the center pixel and verify it matches the expected UTM coordinate of Washington Square Park's center.
utils.py — Small Helpers
Generic utilities used by the other data modules: coordinate transformations, raster sampling (getting the elevation at a specific point), bounding box utilities, file I/O helpers.

Bug minimization: Keep these functions small and test each one independently. A function that converts lat/lon to UTM should be tested against known coordinate pairs. A function that samples a raster at a point should be tested against manually computed values.

4. src/solaraeus/geometry/ — Building the Objects the Physics Uses
Three files, each producing one geometric object.

dsm.py — Building the Digital Surface Model
What it does:

Takes the ground elevation raster and the building footprints with heights.
Rasterizes the buildings onto the grid: for each pixel that falls inside a building polygon, sets the elevation to ground + building height.
The result is a 2.5D raster where each pixel has the height of the highest surface at that location (ground, building roof, or tree canopy if present).
What can go wrong:

Buildings with missing heights get a default value (like 8 meters). If too many buildings use the default, the DSM is wrong.
MultiPolygons (buildings with holes or multiple parts) might not rasterize correctly.
"all_touched=False" in rasterization means only pixels whose center is inside the polygon count. For narrow buildings (less than 1 meter wide), the center might miss the polygon, and the building disappears from the DSM. This is a known rasterization artifact.
How to catch these early:

Print the number of buildings with missing heights and what default was used.
Visualize the DSM and compare against the building footprints: every building polygon should correspond to a raised area in the DSM.
Check the elevation range: "DSM ranges from 20m to 45m." Buildings should be the high points. If the DSM max is 20m (same as ground), no buildings were rasterized.
meshes.py — Building 3D Meshes (for Later Stages)
What it does:

Takes each building polygon and extrudes it into a 3D block: a watertight triangular mesh with bottom, sides, and top.
Merges all building meshes into one combined mesh.
Exports to OBJ or PLY format for use by the 3D ray tracer in Stage 2.
What can go wrong:

Non-watertight meshes: holes in the geometry cause ray tracing to leak. The mesh must be closed.
Self-intersecting polygons: if a building footprint has a self-intersection (rare but possible in real data), the extrusion produces a broken mesh.
Overlapping buildings: if two building polygons overlap, the combined mesh has internal geometry that shouldn't be there.
How to catch these early:

After building the mesh, check mesh.is_watertight. If it's False, print which buildings failed and why.
Print the total vertex and face count. For a few hundred buildings in a 200×200m area, expect tens of thousands of vertices and faces. A count of zero means no meshes were created; a count of millions means something went wrong (maybe the polygons were duplicated).
pedestrian_grid.py — Building the Pedestrian Points
What it does:

Creates a regular grid of points at 1.1 meters above ground (the standard height for thermal comfort assessment).
Each point is at the center of a 1m×1m pixel, at the pedestrian height.
Optionally masks out points that are inside buildings (you can't have a pedestrian standing inside a wall).
What can go wrong:

The grid points don't align with the DSM pixels. If the grid is offset by half a pixel, every physics calculation is sampling the wrong elevation.
The pedestrian mask might be wrong: points inside buildings might not be masked, giving you physics results for impossible locations.
How to catch these early:

Print the number of pedestrian points: "40,000 points for 200×200m at 1m resolution." If the number is off, the grid geometry is wrong.
Print the number of masked points: "5,000 points inside buildings, 35,000 pedestrian-accessible." Check that the masked points correspond to where buildings actually are.
Verify the Z coordinate of pedestrian points: "All points at Z = ground_elevation + 1.1m." If points have Z = 1.1 (absolute) rather than ground + 1.1, they're at the wrong height.
5. src/solaraeus/physics/ — The Core Calculations
This is the heart of the project. Six separate files, each doing one physical calculation. They run in sequence, each taking the output of the previous one.

solar.py — Where Is the Sun?
What it does:

Takes the latitude, longitude, date, and time.
Computes the sun's position in the sky: altitude (how high above the horizon) and azimuth (which direction, measured clockwise from north).
The physics: Uses standard solar geometry formulas (Cooper 1969 declination model, spherical trigonometry). Accurate to about 1 degree — good enough for urban shading calculations.

What can go wrong:

Time zone confusion: computing solar position for 14:00 UTC instead of 14:00 local time. The sun would be in the wrong place.
Azimuth convention: some formulas measure azimuth from south, some from north, some counterclockwise, some clockwise. If you mix conventions, shadows go in the wrong direction.
Declination formula: using the wrong day of year or the wrong formula gives the wrong sun angle.
How to catch these early:

Test against a known reference: for New York City (40.73°N) on July 15 at 14:00 local time, the sun should be at roughly 60-65° altitude and 135-145° azimuth (south-southwest). If you get 20° altitude (sun near horizon) or 300° azimuth (northwest), your time or convention is wrong.
Use an online solar calculator (NOAA, SunEarthTools) to verify your output for a few test cases.
Print both altitude and azimuth in degrees (not radians) for human-readable verification.
svf.py — Sky View Factor
What it does:

For each pedestrian point, looks in many directions (e.g., 360 azimuth directions) and finds the highest obstacle in each direction.
Computes what fraction of the sky is visible: if all directions see the full sky, SVF = 1.0. If the sky is completely blocked (deep canyon), SVF approaches 0.
Uses the Steyn (1980) formula: SVF = average of cos²(horizon_angle) over all directions.
The physics: The horizon is found by "ray marching" outward from each point on the DSM, checking the elevation angle to each pixel along the way. The maximum elevation angle in each direction is the horizon. The sky view factor tells you how much diffuse sky radiation reaches that point.

What can go wrong:

The ray march goes in the wrong direction (azimuth off by 90° or mirrored). The horizon angles are computed for the wrong directions.
The maximum search radius is too short for deep canyons. If a canyon wall is 250m away but you only search 200m, the wall isn't seen and SVF is overestimated.
The cos² formula is applied incorrectly. Some implementations use cos (not squared) or a different exponent.
The horizon angle isn't clipped to valid range. If a pixel is lower than the starting point, the horizon angle should be negative (depression), not zero.
How to catch these early:

For a flat, open area with no buildings: SVF should be 1.0 (or very close). If you get 0.7 for open ground, the calculation is wrong.
For a deep canyon (buildings on both sides, 15m tall, 15m wide): SVF should be roughly 0.3-0.4. If you get 0.8, the canyon walls aren't being seen.
Print SVF statistics: "Mean SVF = 0.55, min = 0.12 (deep canyon), max = 0.98 (open area)." If min is 0.5, you're not seeing the canyon walls. If max is 1.05 (greater than 1), there's a calculation error.
Test on a synthetic case first: a 200×200m flat grid with one isolated 20m building. Compute SVF at points around the building and verify it drops in the building's shadow.
shadows.py — Which Points Are in Direct Sun?
What it does:

For the given sun position (altitude and azimuth), determines which pedestrian points receive direct sunlight.
Uses 2.5D projection: for each point, looks in the direction opposite to the sun (the shadow direction) and checks if any taller object blocks the sun.
A point is sunlit if its elevation is above the "shadow line" from the nearest taller object in the sun direction.
The physics: This is a simplification of true 3D shadow casting. Instead of casting a 3D ray toward the sun, it projects the DSM along the sun azimuth and checks elevations. It's fast and works well for most urban situations, but it can miss shadows from overhangs or complex geometries (which is why you later compare against the 3D ray tracer).

What can go wrong:

Shadow direction is reversed: shadows appear on the wrong side of buildings. If the sun is in the south, shadows should point north. If they point south, the azimuth convention is wrong.
Shadow length is wrong: shadow length = building_height / tan(sun_altitude). For a 20m building at 60° sun altitude, the shadow should be about 11.5m long. If the shadow is 5m or 30m, the altitude or projection math is wrong.
Points at the edge of a shadow might be incorrectly classified due to pixel alignment issues.
How to catch these early:

Visualize the shadow mask on top of the DSM. Shadows should appear as dark regions on the side of buildings opposite the sun. If the sun is in the south (azimuth ~140°), shadows should be on the north side of buildings.
Test on a single isolated building: place a 20m building in an open area, sun at 60° altitude, compute the shadow, and verify the shadow extends the correct distance in the correct direction.
Check the shadow mask statistics: "60% of pedestrian points are sunlit, 40% are shaded." For midday in an urban area, this is reasonable. If 99% are shaded (everything is dark), the sun is being treated as below the horizon. If 99% are sunlit (nothing casts shadows), the shadow algorithm isn't working.
radiation.py — Computing Radiant Fluxes
What it does:

Takes the shadow mask (which points are sunlit), the SVF (how much sky is visible), and the weather data.
Computes four components of radiant energy at each pedestrian point:
Direct solar: Sunlight coming directly from the sun. Present only for sunlit points. Depends on solar radiation from ERA5, atmospheric transmission, and the cosine of the sun altitude.
Diffuse solar: Sunlight scattered by the atmosphere. Present everywhere, proportional to the SVF (more sky visible = more diffuse radiation).
Downward longwave: Thermal radiation from the sky. Depends on sky temperature (from cloud cover and humidity).
Upward longwave: Thermal radiation from the ground and surrounding surfaces. Depends on surface temperature and the view factor to the ground.
The physics: The total radiant energy absorbed by a pedestrian is the sum of these four components. Direct solar dominates during sunny daytime (hundreds of watts per square meter). Diffuse solar and longwave are smaller but still significant.

What can go wrong:

Direct solar is computed for shaded points (the shadow mask isn't being applied).
Diffuse solar doesn't use SVF (giving the same diffuse radiation to canyon floors as to open areas).
Longwave radiation uses wrong temperatures or emissivities.
Units are mixed: solar radiation in W/m², longwave computed with temperature in Celsius instead of Kelvin.
How to catch these early:

For a sunlit point in open area at noon on a clear summer day, total absorbed radiation should be on the order of 400-600 W/m² (direct solar ~500-700 W/m² minus some reflection and absorption factors). If you get 50 W/m² or 2000 W/m², something is wrong.
For a shaded point in a deep canyon, total radiation should be much lower (100-200 W/m²), mostly diffuse sky radiation and longwave exchange.
Print the four flux components for a few representative points (open sunlit, open shaded, canyon floor) and verify they're in the right ballpark.
tmrt.py — Mean Radiant Temperature
What it does:

Takes the radiant fluxes and converts them to a single temperature value: Mean Radiant Temperature (Tmrt).
Uses the Stefan-Boltzmann law: Tmrt = (total_absorbed_flux / (emissivity × Stefan_Boltzmann_constant))^(1/4) - 273.15 (to convert from Kelvin to Celsius).
The pedestrian is modeled as a cylinder with different view factors: top (0.06), bottom (0.06), and four sides (0.22 each).
The physics: Tmrt is the temperature of an imaginary black enclosure that would absorb the same amount of radiant energy as the pedestrian actually absorbs from the environment. It's the standard way to express radiant heat load in thermal comfort assessment. A sunlit area on a hot day might have Tmrt of 60-70°C; a shaded area might be 30-40°C.

What can go wrong:

The Stefan-Boltzmann calculation uses Celsius instead of Kelvin. This gives wildly wrong temperatures.
The view factor weights are wrong. The standard human cylinder model uses specific weights (0.06 top, 0.06 bottom, 0.22 per side × 4 sides). Using equal weights or wrong values changes the result.
The Stefan-Boltzmann constant is wrong (using 5.67×10⁻⁸ W/m²/K⁴ — make sure the exponent is correct).
The fourth root is computed incorrectly (using square root or cube root instead).
How to catch these early:

For a sunlit open area on a hot summer day with high solar radiation: Tmrt should be >50°C, possibly 60-70°C. If you get 25°C (same as air temperature), the radiation isn't being counted.
For a shaded area: Tmrt should be noticeably lower than the sunlit area, maybe 30-40°C. If shaded Tmrt equals sunlit Tmrt, the shadow mask isn't being used.
Compare against published values: in urban heat stress literature, Tmrt on hot sunny days is commonly reported as 50-70°C in sun, 30-45°C in shade. If your numbers are way outside this range, something is wrong.
utci.py — Universal Thermal Climate Index
What it does:

Takes air temperature, Tmrt, wind speed at pedestrian height, and relative humidity.
Computes the UTCI using the pythermalcomfort library (a validated implementation of the UTCI-Fiala human heat balance model).
UTCI is expressed in °C and represents the "apparent temperature" — how hot it feels to a human, considering all four environmental factors.
The physics: UTCI is computed by a complex human heat balance model that simulates core temperature, skin temperature, sweat rate, and other physiological responses. It's the international standard for outdoor thermal comfort assessment. UTCI of 32-38°C is "strong heat stress," 38-46°C is "very strong heat stress."

What can go wrong:

Passing Tmrt in the wrong units (Kelvin instead of Celsius, or vice versa).
Passing wind speed at the wrong height (10m instead of 1.1m).
Passing relative humidity as a fraction (0.5) instead of a percentage (50%).
Using a UTCI implementation that doesn't match the standard.
How to catch these early:

Use pythermalcomfort's built-in validation if available. Compare your results against known UTCI values for standard conditions.
For a hot sunny day (Ta=33°C, Tmrt=60°C, wind=1 m/s, RH=40%): UTCI should be around 45-55°C (very strong to extreme heat stress). If you get 33°C (same as air temperature), the Tmrt isn't being used.
For a shaded area (Ta=33°C, Tmrt=35°C, wind=1 m/s, RH=40%): UTCI should be around 35-40°C (moderate to strong heat stress, but much better than sun). If shaded UTCI equals sun UTCI, Tmrt isn't different between the two.
Print UTCI for sunlit and shaded areas side by side. The sunlit area should have substantially higher UTCI (10-15°C difference is typical).
6. src/solaraeus/visualization/ — Making Pictures
maps.py — Static Figures
What it does:

Takes the computed rasters (DSM, shadow mask, SVF, Tmrt, UTCI) and makes publication-quality PNG figures.
Each figure shows the study area with a color-coded map of the metric, a colorbar, a title, a scale bar, and a north arrow.
The shadow figure overlays the shadow mask on the DSM so you can see where shadows fall relative to buildings.
What to check:

The figures should be readable: colorbar labeled with units, title shows date/time/location, scale bar shows real distances.
The DSM figure should clearly show building footprints as elevated areas.
The shadow figure should show shadows in the correct direction relative to the sun.
The Tmrt and UTCI figures should show hot areas (sunlit) in warm colors and cool areas (shaded) in cool colors.
dashboard.py — Interactive Viewer (Optional, for Later)
A Streamlit or similar web app that lets you interactively explore the results: slide through time, toggle layers on and off, click to see values at specific points. This is for Stage 2+ and not needed for Stage 1.

7. scripts/run_stage1.py — The Conductor
What it does:

This is the main script you run. It doesn't contain any physics. It just calls the other modules in order:
Download data
Harmonize to unified grid
Build geometry (DSM, pedestrian grid, 3D mesh)
Run physics (solar → SVF → shadows → radiation → Tmrt → UTCI)
Validate outputs (check they're reasonable)
Make figures
Save results to NetCDF and reports
Why it's separate from the physics: So you can re-run just the physics with different parameters without re-downloading data. So you can test individual physics modules without running the whole pipeline. So the pipeline is transparent: you can read this script and understand exactly what happens in what order.

8. tests/ — Catching Bugs Before They Matter
Each physics module has its own test file. Tests use simple, artificial cases where the correct answer is known.

Examples of what each test checks:

Solar test: "For NYC at 14:00 on July 15, altitude should be ~62°, azimuth ~140°. For equator at noon on equinox, altitude should be 90° (sun directly overhead). For pole at winter solstice, sun should be below horizon all day."

SVF test: "Flat ground with no buildings → SVF = 1.0. Inside a 15m×15m canyon with 15m tall buildings → SVF ≈ 0.35. Next to a single 20m building at 50m distance → SVF slightly reduced but close to 1.0."

Shadow test: "A 20m building at 60° sun altitude casts a shadow 11.5m long in the direction opposite the sun. A point 15m behind the building (in the shadow direction) is shaded. A point 5m to the side of the building is sunlit."

Radiation test: "At noon on a clear day with SSRD = 800 W/m² and sun altitude 60°, direct solar at a sunlit point should be roughly 800 × cos(60°) × 0.75 (transmission) ≈ 300 W/m². A shaded point should get 0 direct solar."

Tmrt test: "Sunlit point with high radiation → Tmrt >50°C. Shaded point → Tmrt <40°C. Open area at night (no solar radiation) → Tmrt close to air temperature."

UTCI test: "Hot sunny conditions → UTCI >40°C (strong heat stress). Same conditions but shaded → UTCI 35-40°C. Cold conditions → UTCI <10°C (cold stress)."

Why tests matter: When you change something (e.g., you fix a bug in the SVF calculation), you run the tests. If the SVF test now fails, you know your fix broke something. If all tests pass, you know the change didn't introduce new bugs. This is your safety net.

9. notebooks/ — Scratchpad for Development
Jupyter notebooks where you experiment, debug, and explore. Not part of the formal pipeline, but invaluable during development.

Data exploration: Look at the downloaded buildings. Check which have heights. Visualize the DEM. Understand what you're working with before processing.
DSM building: Step through the DSM construction interactively. Visualize intermediate results. Figure out why buildings are missing or misaligned.
Physics validation: Test the physics modules on synthetic cases. Compare SVF against hand calculations. Compare shadows against intuition. Figure out what's working and what isn't.
10. outputs/ — Where Results Go
Three sub-folders:

figures/ — PNG Images
The five required figures: DSM, shadows, SVF, Tmrt, UTCI. Each is a publication-quality map with colorbar, title, scale bar, and statistics.

netcdf/ — Gridded Data Files
The computed rasters saved in NetCDF format (a standard scientific data format). These can be read by other programs, shared, or used in later stages. Each file includes the data array plus metadata (coordinates, date, time, units, description).

reports/ — Validation Documentation
A written report (stage1_validation.md) that documents:

What was simulated (date, time, location, parameters)
What the results were (SVF range, Tmrt range, UTCI range, % sunlit vs shaded)
What sanity checks passed (SVF=1 for open areas, shadows in correct direction, Tmrt reasonable, UTCI reasonable)
What limitations exist (uniform meteorology, 2.5D shadow approximation, no canopy in Stage 1, etc.)
How the Frontend Fits In (React + Vite + Three.js)
The frontend is a completely separate subproject in frontend/. It doesn't import any Python code. It reads data files that the Python backend produces.

What it does:

Shows a 3D map of the study area using Three.js (a 3D graphics library for the web).
Renders the DSM as a height field (ground + buildings as a continuous elevated surface).
Renders the 3D building meshes (from the OBJ/JSON file the Python backend saves).
Overlays color-coded layers: shadow mask (shaded vs. sunlit areas), SVF (how much sky is visible), Tmrt (radiant temperature), UTCI (thermal comfort).
Lets you slide through time (the time slider re-fetches data for different hours).
Lets you toggle layers on and off.
Shows statistics: mean Tmrt, max Tmrt, mean UTCI.
Shows a tooltip with the value at the point you're hovering over.
How it gets data:

The Python backend saves JSON files in outputs/json/ and outputs/data/.
The frontend fetches these JSON files via HTTP.
The JSON contains: the 2D array of values, the grid bounds, the resolution, the color scale parameters, and a description.
Key frontend modules (in plain English):

api/ — The data fetcher. This is the only part that knows about the backend. It has functions like "fetch the Tmrt data for 14:00" or "fetch the building 3D mesh." All other parts of the frontend use these functions, never directly accessing files.

components/ — The visual pieces. The 3D map, the sidebar with the time slider and layer toggles, the colorbar legend, the statistics cards, the tooltip. Each is a self-contained visual element.

hooks/ — The state managers. These are React functions that manage data: "fetch and cache all current data," "manage the time slider," "track which layers are visible," "track the mouse position for the tooltip."

stores/ — The global state. A single place that holds the current time, which layers are on, the color scale, the loaded data. Every component reads from here, so when the time changes, all components update together.

three/ — The 3D scene builders. Functions that create Three.js objects: the ground plane with DSM height, the building meshes, the shadow overlay, the heatmap overlay, the sun indicator, the sun light.

utils/ — Helpers. Colormaps (so Tmrt uses the same colors everywhere), coordinate transforms (so a pixel in the data corresponds to the right point in the 3D scene), formatters (so temperatures display as "48.3°C" not "48.29999").

Bug minimization for the frontend:

The API layer is the only part that changes if you switch from file-based to server-based data. Components don't need to change.
Types are centralized. If the backend changes a data format, you update the types in one place and the TypeScript compiler tells you everywhere else that needs updating.
State is centralized. No component has its own copy of the time or the data. When time changes, one state update propagates everywhere.
Colormaps are defined once. If you decide Tmrt should use a different color scale, you change it in one place and it updates in the 3D scene, the tooltip, and the colorbar legend.
General Bug-Minimization Principles for the Whole Project
1. Validate at Every Step, Not Just at the End
Don't run the whole pipeline and then wonder why UTCI is wrong. Check each step's output before moving on:

After downloading buildings: check count, height coverage, CRS.
After harmonization: visualize the DSM, verify buildings are where they should be.
After solar: verify altitude and azimuth against a known reference.
After SVF: check open areas give SVF≈1, canyons give SVF<0.5.
After shadows: visualize, verify shadows are on the correct side of buildings.
After radiation: check flux magnitudes are reasonable.
After Tmrt: check sun >50°C, shade <40°C.
After UTCI: check sun > shade by a large margin.
If any step produces wrong results, stop and fix it before moving on. A bug in SVF propagates to shadows, radiation, Tmrt, and UTCI — finding it early saves hours of debugging.

2. Test on Synthetic Data First
Before running on real Washington Square Park data, test each physics module on artificial cases where you know the answer:

A flat 200×200m grid with no buildings: SVF should be 1.0 everywhere.
A grid with one isolated 20m building: you can compute the shadow by hand (length = height / tan(altitude), direction = opposite sun azimuth).
A grid with two buildings forming a canyon: you can estimate SVF.
If the physics works on these simple cases, it's much more likely to work on the real complex case. If it fails on the simple case, the bug is in the physics module, not in the data.

3. Print Intermediate Values
When something looks wrong, print the actual numbers being computed. "Sun altitude = 0.52 radians (30°), azimuth = 2.5 radians (143°)." "SVF at point [100,100] = 0.35." "Direct solar flux at point [100,100] = 287 W/m²." "Tmrt at point [100,100] = 52.3°C."

Numbers make bugs visible. A shadow that "looks wrong" is hard to diagnose. A shadow where the azimuth is 30° off is immediately obvious from the numbers.

4. Visualize Early and Often
A DSM visualized as a color map reveals misalignment that numbers alone might miss. A shadow mask overlaid on the DSM reveals direction errors. A Tmrt heat map reveals whether hot areas are where you expect them (sunlit open areas) and cool areas are where you expect them (shaded canyons).

Make a visualization after every major step. It's the fastest way to catch spatial errors.

5. Keep Coordinate Systems Explicit and Documented
The #1 source of bugs in geospatial projects is coordinate confusion. Every function that takes coordinates should document which CRS they're in. Every function that returns coordinates should document which CRS it's returning.

When you write a function, add a comment: "Args: points (N, 3) in UTM Zone 18N meters, Z = ground elevation + 1.1m." When you call it, verify your data is in the right CRS first.

6. Use Frozen Config
The config dataclass is frozen (can't be modified after creation). This prevents the common bug where a parameter gets changed halfway through a run, producing inconsistent results that are hard to debug. If you need different parameters, create a new config.

7. Don't Mix Physics and Data Code
The physics modules (svf.py, shadows.py, tmrt.py) should never import the data modules (overture_loader.py, era5_loader.py). They take arrays and scalars as inputs and return arrays and scalars as outputs. This means:

You can test physics modules with synthetic data, not just real data.
You can swap data sources without changing physics code.
You can swap physics implementations without changing data code.
Bugs are isolated: a data bug doesn't look like a physics bug.
8. Write the Validation Report as You Go
Don't wait until the end to document what you did and what the results were. After each major step, write a few sentences in the validation report:

"Downloaded 347 buildings, 92% have height data, CRS EPSG:4326."
"DSM ranges from 18.3m to 42.7m, 200×200 pixels at 1m resolution."
"Solar position at 14:00 local: altitude 62.3°, azimuth 140.2° (verified against NOAA calculator)."
"SVF: mean 0.52, min 0.14 (deep canyon), max 0.98 (open park). Open area SVF=0.98 (expected ~1.0)."
"Shadows: 62% of pedestrian points sunlit, shadows on north side of buildings (correct for south-positioned sun)."
"Tmrt: sunlit areas 52-68°C, shaded areas 28-42°C. Open sunlit Tmrt=58.3°C (expected >50°C)."
"UTCI: sunlit mean 45.2°C (very strong heat stress), shaded mean 33.8°C (moderate heat stress). Difference 11.4°C (expected >10°C for strong sun vs shade)."
This becomes your record of what was done and what was verified. When you come back in two weeks, you know exactly what worked and what didn't.

Summary: The Flow in Plain English
Download: Get building footprints, weather data, and terrain elevation from the internet.
Clean: Put everything in the same coordinate system (UTM, meters) and the same grid (1m resolution).
Build geometry: Create the elevation map (DSM), the pedestrian points, and (optionally) the 3D building meshes.
Find the sun: Calculate where the sun is in the sky for the given time and place.
Calculate sky view: For each pedestrian point, figure out how much of the sky is blocked by buildings.
Calculate shadows: Figure out which points are in direct sun and which are shaded.
Calculate radiation: Compute how much radiant energy reaches each point (direct sun, diffuse sky, thermal from sky, thermal from ground).
Calculate Tmrt: Convert the radiant energy to a temperature equivalent.
Calculate UTCI: Combine Tmrt with air temperature, humidity, and wind to get the thermal comfort index.
Visualize: Make color-coded maps of each result.
Validate: Check that every step produced reasonable results. Document what passed and what didn't.
Each step depends on the previous step being correct. Each step can be tested independently. Each step has clear expected outcomes you can check against. This is what makes the project maintainable and the results defensible.


