---
id: "003"
slug: engine-code
idea: Solaraeus simulation engine — a 2.5D raster radiative transfer and thermal comfort codebase in src/ combining Steyn SVF, shift-based shadow projection, Stefan-Boltzmann Tmrt, and pythermalcomfort UTCI.
date: 2026-09-30
verdict: FIX FIRST
biggest_risk: Scientific shortcuts and performance traps (30m SRTM upsampling, 21,000 array allocations, flipped azimuth hacks, missing canopy) render the engine legally indefensible for compliance and unscalable beyond a toy park tile.
open_questions: 4
---

# 003 — Solaraeus Simulation Engine

A code review and council trial of the Solaraeus physics, geometry, and data pipeline in `src/` (`src/physics/`, `src/geometry/`, `src/data/`, and `scripts/run_stage1.py`). The engine claims to execute a 1m diurnal microclimate simulation over Washington Square Park, computing astronomical solar angles, Steyn (1980) sky view factors, direct obstacle shadows, mean radiant temperature ($T_\text{mrt}$), and UTCI thermal stress.

## Believer

**WHO desperately needs this.** Applied microclimate modelers and computational designers who cannot wait 14 hours for an ENVI-met finite-volume CFD simulation to converge on a single block, and who find Ladybug Grasshopper scripts too fragile to deploy as automated backend web services. Today, their choice is either an overnight academic CFD package or no 3D spatial simulation at all. Solaraeus gives them an end-to-end Python pipeline that runs in under 3 minutes, takes open geospatial inputs, and exports standard NetCDF4 and typed Three.js JSON contracts in one pass.

**WHY now.** Vectorized raster array operations and the availability of global building footprints (Overture Maps) and free meteorological reanalysis (ERA5 / Open-Meteo) make it possible to replace supercomputer CFD with analytical radiative transfer models. For 90% of urban heat mitigation decisions (e.g. comparing shade canopies, ground pavement albedo, and building setback shadows), radiative equilibrium and sky view factor dominate convective turbulence. Packaging this as a self-contained, reproducible Python library (`src/physics/`) bridges the gap between academic climate scripts and production web backends.

**The best version.** A blazingly fast, pip-installable geospatial microclimate engine (`pip install solaraeus-engine`) that ingests any GeoTIFF DEM and GeoJSON building layer, evaluates diurnal radiative fluxes and UTCI heat stress at 1-meter resolution in 30 seconds via GPU or Numba acceleration, and outputs both scientific NetCDF datasets and 3D web meshes without requiring proprietary licenses or GIS desktop GUIs.

**The unfair advantage.** Architectural elegance and end-to-end reproducibility. Unlike clunky Fortran-based legacy models or GUI-bound GIS plugins, Solaraeus exposes clean, modular Python functions (`compute_svf`, `cast_shadows`, `compute_radiation`, `compute_tmrt`, `compute_utci`) with rigorous parameter type annotations, complete input validation, and an automated CLI orchestration script (`scripts/run_stage1.py`) that executes from zero to publication maps in a single call.

**The one bet the whole idea rests on:** that urban designers and municipal resilience planners care more about instant, reproducible radiative comfort indicators than full aerodynamic Navier-Stokes wind turbulence, making a 2.5D raster approximation commercially and practically valuable.

## Skeptic

**WHO will not pay.** Any licensed engineer, microclimate researcher, or environmental consultant doing real compliance work. If an engineering firm submits an environmental impact assessment (EIA) to a zoning board based on this engine, opposing counsel will shred it during technical cross-examination in ten minutes. The code claims "1m LiDAR DEM" in documentation, but `src/data/dem_loader.py` actually downloads coarse 30m NASA SRTM radar tiles from the year 2000 and resamples them via bilinear interpolation. That is resolution inflation, not true 1m LiDAR; it misses all real ground elevation variations, curbs, and terrain relief.

**The competitor or free workaround already exists, and their science is sound.** UMEP/SOLWEIG is open source, actively maintained by Göteborg and Reading universities, fully validated in dozens of peer-reviewed field campaigns, and properly handles both 3D building walls and tree canopy transmissivity. If someone wants free raster physics, SOLWEIG already exists; if they need certified compliance, they use ENVI-met or Ansys. Solaraeus has neither the academic validation of SOLWEIG nor the regulatory certification of ENVI-met.

**The blind spot.** The engine is riddled with algorithmic bottlenecks and dangerous coordinate hacks. In `src/physics/svf.py`, the Steyn algorithm runs a loop over 360 azimuth directions and up to 80 radial steps, calling `_shift_2d` on every step. That is over 21,000 full 2D array allocations and copies in pure Python numpy for a single simulation! On a 1km x 1km grid, that thrashes tens of gigabytes of RAM. Worse, in `src/physics/shadows.py` lines 84-88, there is a horrifying compass patch: `if 130.0 <= az_deg <= 155.0: compass_deg = 360.0 - az_deg`. This was hacked in because `src/physics/solar.py` defaults to a non-standard meridian azimuth convention; as a consequence, any legitimate morning sun in the southeast (~140°) gets mirrored to the southwest! Add in `meshes.py` extruding every building in the domain from the global minimum DEM elevation (leaving uphill building foundations hanging in mid-air), and `run_stage1.py` asserting hardcoded park-specific SVF thresholds (`svf_walk_max >= 0.80`, `svf_walk_min <= 0.50`) that crash on any non-park geography, and you have an engine that only works on one specific tile by coincidence.

**The fastest way this dies.** Running the engine on any site other than Washington Square Park. The moment a user feeds it downtown Boston, midtown Manhattan, or a sunny university quad, the hardcoded validation assertions crash, the building foundations float, and the missing tree canopy model predicts lethal heat stress where people are actually walking under leafy oak trees.

**The fatal flaw:** The engine claims physical rigor, but trades scientific fidelity for demo aesthetics. A thermal comfort engine that models zero tree canopy, assumes constant wind speed across a skyscraper grid, assumes sunlit asphalt is only 4°C above air temperature, and defaults unmeasured NYC buildings to 8-meter two-story cottages is a visual rendering tool, not a physical simulation engine.

## Investor

**Proof of payment: zero.** Nobody has ever paid a single dollar for this code, and in its current state, nobody can. You cannot sell closed-source software whose algorithms are slower than open-source C/Fortran solvers, nor can you sell consulting reports whose numbers fail the most basic scientific due diligence.

**Value of the codebase as an asset.** As intellectual property, the engine has negative enterprise value today: an acquirer or enterprise customer would spend more money auditing, refactoring, and defending the code than it would cost to build a clean wrapper around UMEP/SOLWEIG or Ladybug. The 21,000-allocation `_shift_2d` bottleneck makes it unsuitable as a multi-tenant cloud SaaS backend, and the SRTM data deception creates legal liability.

**Time to first real dollar.** 
- If trying to sell this engine as an API or SaaS: **never**, until the architecture is rewritten in Numba/C++, true USGS 3DEP LiDAR is connected, and canopy physics is added.
- If treated as an internal engineering accelerator for custom consulting reports: **30 to 60 days**, but only if the founder immediately discards the hardcoded hacks and validates the output against a published meteorological station (like Central Park or a mesonet sensor).

**The cheapest test that proves demand this week.** Benchmark the engine against SOLWEIG on the exact same 500m x 500m tile in New York. Compare run-time, memory footprint, and $T_\text{mrt}$ outputs. Send the side-by-side technical comparison to 3 environmental engineers: *"We built a pure-Python microclimate engine with typed JSON web export. Would you use this over UMEP if it had Numba acceleration and canopy support?"* If all three tell you they cannot risk their license on unvalidated code, do not spend another month optimizing shaders.

**Would I put my own money in? No.** It is a classic engineering demo: impressive high-level architecture and visually pleasing outputs, built on top of brittle hacks and scientific shortcuts that collapse under scrutiny. **The one number that changes my mind:** 1 formal benchmark paper or technical whitepaper proving Solaraeus matches measured urban sensor data within $\pm 1.5^\circ\text{C}$ $T_\text{mrt}$ without manual parameter tuning.

## Judge

**VERDICT:** FIX FIRST

**Biggest risk:** Scientific shortcuts and performance traps (30m SRTM upsampling, 21,000 array allocations, flipped azimuth hacks, missing canopy) render the engine legally indefensible for compliance and unscalable beyond a toy park tile.

**10-minute test:** Run `scripts/run_stage1.py` with a bounding box for Times Square (or any non-park urban core) and watch it crash in `validate_outputs` due to hardcoded park assertions, or profile `compute_svf` with Python's `cProfile` to inspect the 21,000 array allocations in `_shift_2d`.

**Flips to BUILD if:** Three concrete technical fixes are completed: (1) Replace the Python `_shift_2d` array-allocation loop in `svf.py` and `shadows.py` with a compiled Numba or C ray-marcher; (2) Unify solar and shadow azimuth onto standard navigation coordinates (0°=North, clockwise) and delete the `if 130 <= az <= 155` azimuth mirroring hack; (3) Ingest real 1m USGS 3DEP LiDAR and add a basic crown transmissivity model for tree canopy so the flagship park simulation reflects reality.

**Open questions carried forward:**

- Can the 2.5D raster ray-marching algorithm achieve sub-second execution on a 1000x1000 grid using Numba/JIT or GPU compute, or is 2.5D raster shifting fundamentally the wrong architecture?
- How much does the lack of microscale wind turbulence (CFD) distort UTCI in street canyons compared to radiative variations?
- What is the true licensing and legal risk of calling a 30m SRTM resampled grid a "1m LiDAR DEM"?
- Will the author commit to building a proper tree canopy layer, or will the engine permanently ignore vegetation?
