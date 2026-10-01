# Solaraeus — 3D Digital Twin Viewer

The interactive client of the Solaraeus urban-microclimate digital twin. It renders the Stage 1 simulation over Washington Square Park — DSM, sky view factor, hourly shadows, mean radiant temperature (Tmrt) and UTCI — on extruded 3D buildings, with a first-person pedestrian avatar that samples pedestrian-level comfort.

Built with Vite, React 19, TypeScript, Three.js via `@react-three/fiber` / `@react-three/drei`, and Zustand.

## Prerequisites

- Node.js 18+ (20+ recommended) and npm 9+

## Running

```bash
npm install       # install dependencies
npm run dev       # dev server at http://localhost:5173/
npm run build     # type-check and build the production bundle into dist/
npm run preview   # serve the production build locally
npm run lint      # oxlint
```

## Simulation data

The viewer reads JSON contracts produced by the Python pipeline. The dev server serves them from the repository's `outputs/` directory through the `/outputs/*` middleware in `vite.config.ts` — nothing is copied into `frontend/`:

- `outputs/data/*.json` — simulation config, available times, walkable grid
- `outputs/json/*.json` — gridded DSM / SVF / shadows / Tmrt / UTCI
- `outputs/meshes/buildings_3d.json` — indexed building mesh buffers

Regenerate them from the repository root:

```bash
python scripts/run_stage1.py            # simulation, figures, NetCDF
python scripts/export_frontend_data.py  # frontend JSON contracts
```

See the root [REPRODUCIBILITY.md](../REPRODUCIBILITY.md) for environment setup and the full pipeline.

## Source layout

- `src/components/map/` — the 3D scene: ground heatmaps, building mesh, atmosphere, sun indicator
- `src/components/layers/` — one component per simulation metric
- `src/components/avatar/` — pedestrian avatar, movement controls, comfort HUD
- `src/components/layout/` — app shell, floating panels, colorbars
- `src/api/` — typed clients and interfaces for the JSON contracts
- `src/stores/` — Zustand application state (active layer, time index, avatar mode)
