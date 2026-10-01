# Brief — the question every planner answers

**The goal.** A cheap-to-run, GPU-ray-traced simulator of a city that shows hourly building-resolved heat, attributes how much heat each factor generates, and gives the people who fix these problems a 3D tool where they place trees and other cooling measures and watch the city cool in simulation first — with a publishable paper as a deliverable, not an afterthought.

Every planner plans **all** of it: the GPU ray-tracing core, the attribution, the 3D interface, the case study, and the paper. The differences between plans must come from the strategy combinations the planners invent, not from a division of labour.

## Ground truth the plans must respect

- **There is no GPU code in this repository today.** The physics is numpy CPU ray-marching: Steyn radial horizon scans in `src/physics/svf.py`, raster-shift shadow casting in `src/physics/shadows.py`, a Stefan-Boltzmann radiative balance in `src/physics/radiation.py`, and UTCI via `pythermalcomfort`. The frontend is WebGL `three` r186 with react-three-fiber and a single ground-plane hover raycast. `requirements.txt` carries no GPU dependency.
- Therefore the GPU ray tracer is **a new build**, the existing CPU path is its **correctness oracle**, and the same machine measures GPU against CPU. The parity test is written before the first kernel.
- **CI has no GPU.** The CPU path must stay green in CI; the GPU path is tested locally and labelled as such. A plan whose test suite needs a GPU is not acceptable.
- The repository has a working New York study area (Washington Square Park) and a real test suite (`pytest tests/ -v`). Use it as a control, or argue why not. **Correct the record on resolution first:** `src/data/dem_loader.py` downloads a 30 m SRTM tile from the AWS Skadi repository and bilinearly resamples it onto a 1 m grid, while the documentation calls it a 1 m LiDAR DEM. The simulation grid is 1 m; the data behind it is not. No plan may call a resampled raster LiDAR, and the same distinction applies to every Delhi input.

## The claims a plan has to make defensible

1. **Cheap — but not zero silicon.** For the Delhi precinct on a 1 m simulation grid (roughly 600 × 600 m, about 360,000 cells, 36 radials, a full hourly day) — noting that 1 m is the grid, while the terrain and canopy products behind it are coarser and every cost and accuracy claim must state the input resolution rather than inherit the grid's, one scenario runs in seconds to a couple of minutes on a single mid-range consumer GPU, with no licence, no cluster and no preprocessing chain. Benchmarked three ways: GPU against this repo's own CPU path on the same machine, against published runtimes for comparable scenarios in established commercial tools (cited, never invented), and as the interactive loop's latency.
2. **Attributed.** Per hour and per cell, the radiant load decomposes into direct sun, diffuse sky, ground-reflected shortwave, building longwave, sky longwave and canopy attenuation — and the components must sum back to the total, enforced by a test.
3. **Actionable.** Interventions are scene edits — canopy objects, surface albedo, shade structures, removal — re-run inside the loop, reporting ΔTmrt, ΔUTCI and the change in the area above the strong-heat-stress threshold.

## The case study

**Delhi**, because the paper must show the method working where data is scarce rather than where it is convenient. One precinct with dense canopy beside bare hardscape (Lodhi Garden is the reference candidate), on a documented heatwave day, forced by ERA5 and anchored to station records. Building heights are the critical-path risk: free footprint data for Delhi largely omits them, and shading without heights is fiction. Every plan must state its fallback chain and how the height input is audited.

## The forks each planner must decide, and may decide differently

- **GPU stack:** differentiable PyTorch versus lean CuPy or raw kernels. Differentiability unlocks gradient-based intervention optimisation — the strongest novelty available and the largest schedule risk.
- **Where the rays run:** server-side Python GPU, browser-side WebGPU compute, or a hybrid.
- **Attribution scope:** radiative components only, or also a clearly-labelled anthropogenic estimate (AC waste heat, traffic) built from published coefficients.
- **One city or two:** Delhi alone, or Delhi plus the existing New York site as a data-rich control that isolates the effect of data scarcity.
- **Paper shape and venue:** an attribution-and-validation paper at an urban-climate venue, or a design-loop paper at a simulation-and-planning venue.

## The definition of done the plan has to reach

- A GPU ray-traced core with CPU parity tests, and a GPU-free CI path.
- Hourly attribution that sums within tolerance under test.
- A 3D interface where a practitioner loads a precinct, places or removes canopy and changes surface properties, and gets updated hourly Tmrt and UTCI at a measured latency — with the interface's README stating what it does not model.
- A paper where every number traces to a committed script and an output file, with artifact metadata (licence, citation, pinned environment) and a cold run done by someone other than the author.

## Rules

Follow `plans/README.md` for the rubric and the tournament, and `plans/TEMPLATE.md` for the shape of your plan file. Every external claim needs a URL and an access date, or the tag `unverified`. A fabricated source or invented benchmark disqualifies the plan — this repository's roast council already runs on that rule, and `tests/test_plan_log.py` enforces it here.
