# Solaraeus — Frontend Section (React + Vite + 3D Map UI)

Added as a **parallel subproject** alongside the Python backend. It does not modify the existing `src/`, `data/`, `physics/` structure. It consumes the outputs those modules produce.

---

## New Top-Level Directory Tree (frontend additions highlighted)

```
solaraeus/
├── data/                    # Python backend data (unchanged)
├── src/                     # Python backend code (unchanged)
├── outputs/                 # Python backend outputs (unchanged)
├── tests/                   # Python tests (unchanged)
├── notebooks/               # Python notebooks (unchanged)
├── scripts/                 # Python orchestrators (unchanged)
│
├── frontend/                # ═══════════════════════════════════════
│   ├── package.json         # Node dependencies (Vite, React, Three.js, MapLibre/Leaflet, etc.)
│   ├── vite.config.ts       # Vite build config, proxy to backend API
│   ├── tsconfig.json        # TypeScript config
│   ├── tsconfig.node.json   # Node/TS config for Vite
│   ├── index.html           # Entry HTML
│   ├── README.md            # Frontend-specific setup notes
│   │
│   ├── public/              # Static assets served as-is
│   │   ├── favicon.svg
│   │   └── globe.svg        # optional app icon
│   │
│   └── src/                 # ═══════════════════════════════════
│       ├── main.tsx         # React entry point
│       ├── App.tsx          # Root component, routing/layout
│       ├── index.css        # Global styles, CSS variables (dark theme, design tokens)
│       │
│       ├── api/             # Backend communication layer
│       │   ├── client.ts    # HTTP client (fetch/axios), base URL, error handling
│       │   ├── queries.ts   # Typed API query functions:
│       │   │                 #   fetchSimulationConfig()
│       │   │                 #   fetchDSM()
│       │   │                 #   fetchShadows(time)
│       │   │                 #   fetchSVF()
│       │   │                 #   fetchTmrt(time)
│       │   │                 #   fetchUTCI(time)
│       │   │                 #   fetch3DMesh()
│       │   │                 #   fetchPedestrianGrid()
│       │   │                 #   fetchAvailableTimes()
│       │   │                 #   fetchTimelineData()
│       │   └── types.ts     # Shared TypeScript interfaces for backend data:
│       │                     #   SimulationConfig, DSMData, ShadowData, SVFData,
│       │                     #   TmrtData, UTCIData, MetricData, GeoBounds, TimeStep
│       │
│       ├── components/      # ═══════════════════════════════════
│       │   ├── layout/      # App shell
│       │   │   ├── AppShell.tsx     # Main layout: sidebar + map + panels
│       │   │   ├── Sidebar.tsx      # Controls: time slider, layer toggles, avatar mode, settings
│       │   │   ├── TopBar.tsx       # Title, status, loading, export buttons
│       │   │   └── Colorbar.tsx     # Shared color scale legend component
│       │   │
│       │   ├── map/         # Map components
│       │   │   ├── MapViewport.tsx      # Main 2D/3D map container
│       │   │   ├── Map3D.tsx            # Three.js / React Three Fiber 3D scene
│       │   │   ├── Map2D.tsx            # Optional 2D fallback (MapLibre/Leaflet)
│       │   │   ├── MapControls.tsx      # Zoom, pan, tilt, rotate, reset view
│       │   │   ├── SunIndicator.tsx     # 3D sun position marker in the scene
│       │   │   └── LayerSwitcher.tsx    # Toggle DSM / shadows / SVF / Tmrt / UTCI layers
│       │   │
│       │   ├── avatar/      # 3D Pedestrian Avatar & Walk Mode (NEW)
│       │   │   ├── PedestrianAvatar.tsx  # 3D avatar character/mannequin on street level
│       │   │   ├── AvatarControls.tsx    # WASD/Arrow navigation + First/Third-person camera
│       │   │   ├── AvatarComfortHUD.tsx  # Floating badge & microclimate readouts (Tmrt, UTCI, shade)
│       │   │   └── AvatarAura.tsx        # Footprint comfort color ring (UTCI thermal stress tint)
│       │   │
│       │   ├── layers/      # Data visualization layers (each renders one metric)
│       │   │   ├── LayerBase.tsx        # Shared layer interface/props
│       │   │   ├── DsmLayer.tsx         # DSM elevation → 3D extruded buildings + ground
│       │   │   ├── ShadowLayer.tsx      # Shadow mask → shaded/sunlit regions
│       │   │   ├── SvfLAYER.tsx         # Sky View Factor → color map
│       │   │   ├── TmrtLayer.tsx        # Mean Radiant Temperature → heat map
│       │   │   ├── UtciLayer.tsx        # UTCI → heat map with stress category legends
│       │   │   └── HeatmapRenderer.tsx  # Shared heatmap rendering logic (color scale, interpolation)
│       │   │
│       │   ├── ui/          # Reusable UI components
│       │   │   ├── TimeSlider.tsx       # Diurnal time scrubber (06:00–20:00)
│       │   │   ├── StatCard.tsx         # Metric cards (mean, max, min, %sunlit, etc.)
│       │   │   ├── Legend.tsx           # Categorical legend (UTCI stress levels, SVF ranges)
│       │   │   ├── LoadingOverlay.tsx   # Full-screen loading state
│       │   │   ├── ErrorBanner.tsx      # Error state display
│       │   │   └── Tooltip.tsx          # Hover tooltip showing value at point
│       │   │
│       │   └── dialogs/     # Modal dialogs
│       │       ├── ExportDialog.tsx     # Export current view/data as PNG/CSV/GeoJSON
│       │       └── InfoPanel.tsx        # About, data sources, methodology notes
│       │
│       ├── hooks/           # React hooks encapsulating logic
│       │   ├── useSimulationData.ts    # Fetches & caches all current time step data
│       │   ├── useTimeline.ts          # Manages time slider state + timeline data
│       │   ├── useLayerVisibility.ts   # Which layers are on/off
│       │   ├── useColorScale.ts        # Current color scale config
│       │   ├── useMousePosition.ts     # Mouse over map → world coords → tooltip
│       │   ├── useAvatarMovement.ts    # WASD/Arrow key listener, velocity, terrain clamping (DSM Z)
│       │   └── useAvatarComfort.ts     # Real-time sampling of Tmrt/UTCI/shadows at avatar (x,y)
│       │
│       ├── utils/           # Frontend-only utilities
│       │   ├── colorScales.ts          # Colormaps (viridis, plasma, RdYlBu, custom):
│       │   │                             #   getColor(value, min, max, palette)
│       │   ├── geoTransform.ts         # UTM grid ↔ pixel ↔ world coordinate helpers
│       │   ├── formatters.ts           # Format °C, %, m, UTC→local time, etc.
│       │   └── math.ts                 # Clamp, lerp, degree↔radian, etc.
│       │
│       ├── stores/          # State management (Zustand or React Context — pick one)
│       │   └── appStore.ts             # Global app state:
│       │                                 #   current_time, layer_visibility, color_scale,
│       │                                 #   is_3d_mode, camera_state, loaded_data_cache,
│       │                                 #   avatar_mode, avatar_position, avatar_comfort
│       │
│       ├── three/           # Three.js / React Three Fiber specific code
│       │   ├── scene.ts                # Scene setup, lighting, sky, ground plane
│       │   ├── buildingMesh.ts        # Load + render 3D building meshes from backend
│       │   ├── groundMesh.ts          # Render DSM as 3D height field (plane geometry with displaced vertices)
│       │   ├── shadowRing.ts          # Optional: visualize shadow rays for debugging
│       │   ├── sunLight.ts            # Directional light representing sun position
│       │   └── avatarModel.ts         # Procedural or low-poly 3D mannequin model and comfort materials
│       │
│       └── types/           # (optional) — may merge into api/types.ts
│           └── index.ts
│
├── environment.yml          # (unchanged — Python env)
├── .gitignore               # (unchanged — add frontend/node_modules, frontend/dist)
└── README.md                # (will note both backend + frontend setup)
```

---

## How Frontend Connects to Backend — Integration Without Breaking Structure

The frontend does **not** import Python code. It communicates with the backend through a clean interface. Two approaches, pick one:

### Approach A — File-Based (Simplest, No Server Needed for Stage 1)

The Python backend writes NetCDF/JSON/OBJ files to `outputs/`. The frontend reads them directly via HTTP (served as static files) or via a small file watcher.

```
Python backend (run_stage1.py)
  └──▶ writes outputs/netcdf/tmrt_20240715_1400.nc
  └──▶ writes outputs/figures/*.png
  └──▶ writes outputs/meshes/buildings_3d.obj  (from meshes.py)
  └──▶ writes outputs/data/simulation_config.json  (metadata: bounds, resolution, time, params)

Frontend (Vite dev server or static build)
  └──▶ fetch('/outputs/data/simulation_config.json')     → config
  └──▶ fetch('/outputs/netcdf/tmrt_20240715_1400.nc')  → Tmrt data (parse NetCDF in browser via jeode/mowel or pre-convert to JSON/GeoTIFF)
  └──▶ fetch('/outputs/meshes/buildings_3d.obj')        → 3D building mesh
  └──▶ fetch('/outputs/figures/tmrt_wsp.png')           → optional pre-rendered fallback image
```

**For the frontend to read NetCDF in the browser**, you have two options:
1. **Pre-convert in Python**: `outputs/netcdf/tmrt_20240715_1400.nc` → `outputs/json/tmrt_20240715_1400.json` (2D array + coordinates + metadata). The frontend reads JSON. Simple, reliable, works everywhere.
2. **Parse NetCDF in browser**: Use a library like `netcdfjs` or `rxswift-netcdf` (less mature). More complex, not recommended for Stage 1.

**Recommendation for Stage 1:** Add a `outputs/json/` directory. Python backend writes both NetCDF (for archival/reuse) and JSON (for the frontend). The JSON contains:
```json
{
  "metric": "tmrt",
  "date": "2024-07-15",
  "time_utc": "2024-07-15T18:00:00",
  "bounds": {"xmin": 583540, "ymin": 4508900, "xmax": 583740, "ymax": 4509100},
  "resolution_m": 1.0,
  "shape": [200, 200],
  "values": [[...2D array as nested arrays...]],
  "description": "Mean Radiant Temperature (°C) at pedestrian height 1.1m"
}
```

The frontend fetches these JSON files. Clean, zero-server, works with `vite preview` or any static host.

### Approach B — REST API (For Interactive/Real-Time Use)

The Python backend runs a lightweight server (FastAPI, Flask, or Streamlit) that serves API endpoints. The frontend fetches from these endpoints.

```
Python backend (FastAPI server on localhost:8000)
  └──▶ GET /api/config                    → SimulationConfig
  └──▶ GET /api/times                     → available time steps
  └──▶ GET /api/dsm                       → DSM as 2D array + metadata
  └──▶ GET /api/shadows?time=18:00       → shadow mask for given time
  └──▶ GET /api/svf                       → SVF map
  └──▶ GET /api/tmrt?time=18:00          → Tmrt map for given time
  └──▶ GET /api/utci?time=18:00          → UTCI map for given time
  └──▶ GET /api/mesh                     → 3D building mesh (OBJ/GLTF/JSON)
  └──▶ GET /api/pedestrian-grid          → pedestrian point grid

Frontend (Vite dev server, proxy to localhost:8000)
  └──▶ React Query / SWR / plain fetch → API calls → state → render
```

**For Stage 1, file-based (Approach A) is simpler and sufficient.** The frontend reads pre-computed JSON outputs. When you're ready for interactive time scrubbing (recompute on the fly), add the REST API (Approach B) — the frontend's `api/` layer is already structured to switch between file-based and API-based data fetching without changing components.

---

## Frontend Module Responsibilities (Detailed)

### `frontend/src/api/` — The Data Layer

This is the **only** place the frontend knows about the backend. Every component imports from here, never directly from `outputs/`.

```typescript
// frontend/src/api/types.ts
export interface GeoBounds {
  xmin: number; ymin: number; xmax: number; ymax: number;
}

export interface MetricData {
  metric: 'dsm' | 'shadows' | 'svf' | 'tmrt' | 'utci';
  date: string;
  timeUtc: string;
  bounds: GeoBounds;
  resolutionM: number;
  shape: [number, number];  // [rows, cols]
  values: number[][];       // 2D array [row][col], row 0 = north
  description: string;
  units: string;
  vmin: number;             // color scale min
  vmax: number;             // color scale max
}

export interface SimulationConfig {
  studyArea: {
    name: string;
    latCenter: number;
    lonCenter: number;
    utmZone: number;
    bounds: GeoBounds;
  };
  simulation: {
    date: string;
    dayOfYear: number;
    pedestrianHeightM: number;
    nSvFDirections: number;
    svfMaxRadiusM: number;
  };
  dataSources: {
    overtureVersion: string;
    era5Date: string;
    demSource: string;
  };
}

export interface TimeStep {
  utc: string;          // "2024-07-15T18:00:00"
  local: string;        // "14:00"
  hourFloat: number;    // 14.0
}

export interface BuildingMesh {
  vertices: number[];   // flat array [x,y,z, x,y,z, ...]
  faces: number[];      // flat array [i,j,k, i,j,k, ...]
  bounds: GeoBounds;
}
```

```typescript
// frontend/src/api/client.ts
const API_BASE = '/outputs';  // file-based: relative to Vite dev server or static host
// For API mode: const API_BASE = 'http://localhost:8000/api';

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.json();
}

export async function fetchText(path: string): Promise<string> {
  const res = await fetch(`${API_BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return res.text();
}
```

```typescript
// frontend/src/api/queries.ts
import { fetchJson, fetchText } from './client';
import type { MetricData, SimulationConfig, TimeStep, BuildingMesh } from './types';

export async function fetchConfig(): Promise<SimulationConfig> {
  return fetchJson<SimulationConfig>('data/simulation_config.json');
}

export async function fetchAvailableTimes(): Promise<TimeStep[]> {
  return fetchJson<TimeStep[]>('data/available_times.json');
}

export async function fetchMetric(metric: MetricData['metric'], timeUtc: string): Promise<MetricData> {
  // File naming: outputs/json/{metric}_{YYYYMMDD}_{HHMM}.json
  const date = '20240715';  // from config in real use
  const timeTag = timeUtc.slice(5, 16).replace(':', '');  // "180000" → "1800"
  return fetchJson<MetricData>(`json/${metric}_${date}_${timeTag}.json`);
}

export async function fetchDsm(): Promise<MetricData> {
  return fetchMetric('dsm', '2024-07-15T00:00:00');  // DSM doesn't depend on time
}

export async function fetch3DMesh(): Promise<BuildingMesh> {
  // Option 1: parse JSON version of OBJ
  return fetchJson<BuildingMesh>('meshes/buildings_3d.json');
  // Option 2: fetch OBJ text and parse in browser (use three-obj-loader)
  // return fetchText('meshes/buildings_3d.obj');
}
```

**Why this structure?**
- Components never know if data comes from files or a server — only `api/queries.ts` changes
- Types are centralized — components import types from `api/types.ts`
- Adding a new metric = add one query function + one type field

---

### `frontend/src/components/` — The UI

#### Layout Components

```
AppShell
├── TopBar (title, status, export button, layer count)
├── MapViewport (the main map area — fills remaining space)
│   ├── AvatarComfortHUD (floating badge & real-time microclimate readout)
│   └── AvatarControlsOverlay (WASD helper & First/Third-Person toggle)
└── Sidebar (right or left panel)
    ├── TimeSliderSection
    │   └── TimeSlider (diurnal scrubber 06:00–20:00)
    ├── AvatarSection (NEW)
    │   ├── AvatarToggle (switch between Orbit Camera and Street Walk Mode)
    │   ├── CameraModeSelector (Third-Person Follow vs First-Person Eye-Level)
    │   └── WalkSpeedSlider (1.0 m/s – 4.0 m/s)
    ├── LayerSection
    │   ├── LayerSwitcher (checkboxes: DSM, Shadows, SVF, Tmrt, UTCI)
    │   └── OpacitySlider (for overlay layers)
    ├── StatsSection
    │   ├── StatCard: Mean Tmrt
    │   ├── StatCard: Max Tmrt
    │   ├── StatCard: % Sunlit
    │   └── StatCard: Mean UTCI
    └── InfoSection
        ├── DataSources (which datasets, versions)
        └── Methodology (brief notes)
```

#### Map Components

```
MapViewport
├── Map3D (React Three Fiber canvas — primary)
│   ├── Scene setup (scene, camera, renderer, lights)
│   ├── GroundMesh (DSM as displaced plane geometry)
│   ├── BuildingMesh (3D extruded buildings from backend mesh)
│   ├── ShadowLayer (2D shadow mask projected onto ground plane as colored mesh or decal)
│   ├── HeatmapOverlay (Tmrt/UTCI/SVF as colored plane on top of ground)
│   ├── PedestrianAvatar (NEW: 3D character mesh at street level, WASD controlled)
│   │   ├── AvatarAura (dynamic color ring at feet reflecting local UTCI stress)
│   │   └── AvatarCameraRig (Third-person spring-arm or First-person eye-level)
│   ├── SunIndicator (small sphere/glow at sun direction, far away)
│   ├── GridHelper (UTM grid lines for reference)
│   ├── OrbitControls (active in Orbit view mode)
│   └── SunLight (directional light from sun position — actual lighting in 3D scene)
│
└── [Optional] Map2D (2D fallback — MapLibre GL or Leaflet)
    └── Renders same data as static raster layers on a 2D map
```

**3D scene design decisions:**

| Element | How |
|---------|-----|
| **DSM ground** | Plane geometry with vertex displacement: each vertex's Z = DSM value at that grid cell. Grid resolution matches DSM (1m). Shows terrain + buildings as a continuous height field. |
| **Buildings separately** | If backend provides `buildings_3d.obj` as separate meshes, render them as individual mesh objects on top of the ground. This gives clean building edges (the DSM height field can look rough at building edges due to rasterization). |
| **Shadow layer** | Two options: (a) a colored plane on top of the ground — sunlit pixels = bright, shaded = dark; (b) modulate the ground material's color/emissive based on shadow mask. Option (b) is more integrated; option (a) is simpler. |
| **Heatmap layers (SVF, Tmrt, UTCI)** | A colored plane at a slight offset above the ground (z = pedestrian_height + 0.05m), with vertex colors from the metric data. Use the same colormap for all metrics but different color scales (viridis for SVF, RdYlBu or custom for Tmrt/UTCI). |
| **3D Pedestrian Avatar (NEW)** | Low-poly 3D character or stylized mannequin walking on streets and sidewalks. Position $(x, y)$ responds to WASD / Arrow keys. Elevation $Z$ is clamped to the DSM ground elevation at that coordinate. Collision detection checks building footprints to prevent walking through walls. |
| **Avatar Camera Rig (NEW)** | Toggles between **Third-Person Follow** (smooth spring-arm camera trailing behind avatar) and **First-Person** (camera positioned at 1.6m pedestrian eye-level to view shaded canyons and sunlit avenues from street level). |
| **Live Thermal Comfort HUD (NEW)** | Sleek glassmorphic overlay tracking the avatar. Converts avatar $(x, y) \to [row, col]$ and samples real-time metrics: $T_\text{mrt}$ (°C), $UTCI$ (°C), Direct Sun vs Shaded status, and $SVF$. Shows immediate comfort category changes when walking into tree or building shade. |
| **Avatar Comfort Aura (NEW)** | Dynamic decal or ring under the avatar's feet tinted according to instantaneous UTCI thermal stress (e.g. green for thermal comfort, yellow/orange for moderate heat, crimson for extreme heat stress). |
| **Sun indicator** | A small emissive sphere or sprite at a distance in the sun direction. Updates as the time slider moves. |
| **Sun light** | A `DirectionalLight` in Three.js positioned at `camera_target + sun_direction * distance`. This makes the 3D scene lighting match the actual sun position — shadows in the 3D scene align with the shadow data layer. |

#### Layer Components

Each metric layer is a self-contained component that:
1. Receives the metric data (2D array + bounds + color scale params)
2. Renders itself as a Three.js mesh (plane with vertex colors or a texture)
3. Can be toggled on/off by `LayerSwitcher`
4. Has a consistent interface so layers are interchangeable

```typescript
// frontend/src/components/layers/LayerBase.tsx
interface LayerProps {
  data: MetricData;
  visible: boolean;
  opacity: number;
  colorScale: [string, string, string];  // (low, mid, high) color hex
  onHover?: (row: number, col: number, value: number) => void;
  onClick?: (row: number, col: number, value: number) => void;
}

// Each concrete layer implements this interface
```

### `frontend/src/hooks/` — State & Logic

| Hook | Purpose |
|------|---------|
| `useSimulationData` | Top-level hook: fetches config + current metric data + 3D mesh. Exposes `data`, `loading`, `error`, `refresh()`. All other hooks/components consume this. |
| `useTimeline` | Manages the time slider. Fetches available times. On time change, triggers re-fetch of time-dependent metrics (shadows, Tmrt, UTCI). |
| `useLayerVisibility` | `{ dsm: bool, shadows: bool, svf: bool, tmrt: bool, utci: bool }` with setters. Consumed by `LayerSwitcher` and `MapViewport`. |
| `useColorScale` | Current palette + min/max for the active metric. Provides `getColor(value)` function. |
| `useMousePosition` | Raycasts from mouse into the 3D scene. Returns world coordinates + which grid cell the mouse is over + the value at that cell. Drives the tooltip. |
| `useAvatarMovement` (NEW) | Handles WASD / Arrow keyboard inputs, walking velocity, yaw heading, collision avoidance against building footprints, and terrain height clamping ($Z = \text{DSM}[x, y]$). |
| `useAvatarComfort` (NEW) | Converts avatar world coordinates $(x, y) \to [row, col]$ and samples current $T_\text{mrt}$, $UTCI$, shade mask, and $SVF$. Computes UTCI thermal stress category for the live HUD badge and footprint aura. |

---

### `frontend/src/utils/` — Helpers

| File | Contents |
|------|----------|
| `colorScales.ts` | Colormap definitions as arrays of [position, rgb] or hex-stops. Functions: `interpolateColor(colorA, colorB, t)`, `getColor(value, min, max, stops)`. Includes: viridis, plasma, inferno, RdYlBu, coolwarm, and a custom "thermal" palette for UTCI (blue→green→yellow→red→dark red). |
| `geoTransform.ts` | UTM grid ↔ Three.js world coordinates. `gridToWorld(row, col, bounds, resolution) → [x, y, z]`. `worldToGrid(x, y) → [row, col]`. Used by all layers to position their geometry. |
| `formatters.ts` | `formatTemperature(celsius)`, `formatPercent(ratio)`, `formatLength(meters)`, `formatTime(utcString)`, `formatAzimuth(degrees)`. |
| `math.ts` | `clamp(val, min, max)`, `lerp(a, b, t)`, `degToRad(deg)`, `radToDeg(rad)`, `sunPositionToDir(alt, az)` (returns normalized [x,y,z] direction vector). |

---

### `frontend/src/stores/` — Global State

Using Zustand (lightweight, no boilerplate) as an example:

```typescript
// frontend/src/stores/appStore.ts
import { create } from 'zustand';

interface AppState {
  // Data
  config: SimulationConfig | null;
  currentMetrics: {
    dsm: MetricData | null;
    shadows: MetricData | null;
    svf: MetricData | null;
    tmrt: MetricData | null;
    utci: MetricData | null;
  };
  buildingMesh: BuildingMesh | null;
  availableTimes: TimeStep[];
  currentUtcTime: string;

  // UI state
  is3DMode: boolean;
  layerVisibility: {
    dsm: boolean; shadows: boolean; svf: boolean; tmrt: boolean; utci: boolean;
  };
  activeLayer: 'dsm' | 'shadows' | 'svf' | 'tmrt' | 'utci';
  colorScale: { palette: string[]; min: number; max: number; };

  // Avatar & Street Walk Mode (NEW)
  avatar: {
    enabled: boolean;
    cameraMode: 'orbit' | 'third-person' | 'first-person';
    position: [number, number, number];  // [x, y, z] in Three.js world coordinates
    heading: number;                     // Yaw rotation angle in radians
    walkSpeed: number;                   // Walking speed in m/s (default: 1.4 m/s)
    comfort: {
      isSunlit: boolean;
      tmrt: number;                      // °C
      utci: number;                      // °C
      svf: number;                       // 0.0 - 1.0
      stressCategory: string;            // "No thermal stress", "Moderate heat stress", etc.
    } | null;
  };

  // Actions
  setCurrentTime: (utc: string) => void;
  toggleLayer: (layer: keyof AppState['layerVisibility']) => void;
  setActiveLayer: (layer: AppState['activeLayer']) => void;
  setColorScale: (palette: string[], min: number, max: number) => void;
  set3DMode: (enabled: boolean) => void;

  // Avatar Actions (NEW)
  toggleAvatarMode: (enabled?: boolean) => void;
  setAvatarCameraMode: (mode: 'orbit' | 'third-person' | 'first-person') => void;
  updateAvatarPosition: (pos: [number, number, number], heading: number) => void;
  updateAvatarComfort: (comfort: AppState['avatar']['comfort']) => void;
  setWalkSpeed: (speed: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // initial state
  config: null,
  currentMetrics: { dsm: null, shadows: null, svf: null, tmrt: null, utci: null },
  buildingMesh: null,
  availableTimes: [],
  currentUtcTime: '2024-07-15T18:00:00',
  is3DMode: true,
  layerVisibility: { dsm: true, shadows: true, svf: false, tmrt: true, utci: false },
  activeLayer: 'tmrt',
  colorScale: { palette: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'], min: 0, max: 1 },

  // avatar initial state
  avatar: {
    enabled: false,
    cameraMode: 'orbit',
    position: [0, 0, 1.1],
    heading: 0,
    walkSpeed: 1.4,
    comfort: null,
  },

  // actions
  setCurrentTime: (utc) => set({ currentUtcTime: utc }),
  toggleLayer: (layer) => set((s) => ({ layerVisibility: { ...s.layerVisibility, [layer]: !s.layerVisibility[layer] } })),
  setActiveLayer: (layer) => set({ activeLayer: layer }),
  setColorScale: (palette, min, max) => set({ colorScale: { palette, min, max } }),
  set3DMode: (enabled) => set({ is3DMode: enabled }),

  // avatar actions
  toggleAvatarMode: (enabled) => set((s) => ({
    avatar: {
      ...s.avatar,
      enabled: enabled !== undefined ? enabled : !s.avatar.enabled,
      cameraMode: (enabled !== undefined ? enabled : !s.avatar.enabled) ? 'third-person' : 'orbit',
    },
  })),
  setAvatarCameraMode: (mode) => set((s) => ({ avatar: { ...s.avatar, cameraMode: mode } })),
  updateAvatarPosition: (pos, heading) => set((s) => ({ avatar: { ...s.avatar, position: pos, heading } })),
  updateAvatarComfort: (comfort) => set((s) => ({ avatar: { ...s.avatar, comfort } })),
  setWalkSpeed: (walkSpeed) => set((s) => ({ avatar: { ...s.avatar, walkSpeed } })),
}));
```

**Why Zustand over React Context?** Less boilerplate, no providers needed, selectors avoid re-renders. For a project of this size, it's the pragmatic choice. If the user prefers, React Context + `useReducer` works too — the structure is the same, only the plumbing differs.

---

### `frontend/src/three/` — Three.js Specific Code

Kept separate from components so the 3D scene logic is testable and reusable.

```
three/
├── scene.ts          # createScene(): Scene, Camera, Renderer, lights, sky
├── buildingMesh.ts   # createBuildingMesh(vertices, faces): Mesh — rendered from backend OBJ/JSON
├── groundMesh.ts     # createGroundMesh(dsmData, bounds, resolution): Mesh — DSM as displaced plane
├── shadowPlane.ts    # createShadowPlane(shadowData): Mesh — colored plane from shadow mask
├── heatmapPlane.ts   # createHeatmapPlane(metricData, palette, min, max): Mesh — colored plane for SVF/Tmrt/UTCI
├── sunLight.ts       # updateSunLight(sunDirection): DirectionalLight position + target
├── sunIndicator.ts   # createSunIndicator(): Mesh — sun marker in the sky
└── utils.ts          # geometry helpers: plane with displaced vertices, vertex colors, etc.
```

---

## Data Format Contract (Backend → Frontend)

This is the **interface** between the two subprojects. The Python backend produces these files; the frontend consumes them. Neither side cares how the other works internally.

```
outputs/
├── data/
│   ├── simulation_config.json     # Read once on app load
│   └── available_times.json       # Read once; list of time steps for the slider
│
├── json/                          # 2D metric grids as JSON (frontend-readable)
│   ├── dsm_20240715_0000.json     # DSM (static, one file)
│   ├── shadows_20240715_1800.json # Shadow mask at 18:00 UTC
│   ├── svf_20240715_0000.json     # SVF (static, one file)
│   ├── tmrt_20240715_1800.json    # Tmrt at 18:00 UTC
│   └── utci_20240715_1800.json    # UTCI at 18:00 UTC
│
└── meshes/
    └── buildings_3d.json           # 3D building vertices + faces (from meshes.py)
    # or buildings_3d.obj           # if using OBJ loader in browser
```

Each JSON metric file:

```json
{
  "metric": "tmrt",
  "date": "2024-07-15",
  "timeUtc": "2024-07-15T18:00:00",
  "timeLocal": "14:00",
  "bounds": { "xmin": 583540.0, "ymin": 4508900.0, "xmax": 583740.0, "ymax": 4509100.0 },
  "resolutionM": 1.0,
  "shape": [200, 200],
  "values": [
    [45.2, 46.1, 47.3, ...],
    [44.8, 45.9, 48.2, ...],
    ...
  ],
  "units": "°C",
  "description": "Mean Radiant Temperature at 1.1m pedestrian height",
  "colorScale": {
    "min": 30,
    "max": 70,
    "palette": ["#313695", "#4575b4", "#74add1", "#abd9e9", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"]
  }
}
```

**For large grids (e.g., 1000×1000 = 1M values), JSON gets big (~8 MB per file).** In that case, either:
- Downsample for the frontend (serve a 200×200 version for display, keep full resolution for analysis)
- Use a binary format (GeoTIFF via georeferenced tile server, or Protocol Buffers)
- Serve via API with range requests / tiling

For Stage 1 with a 200×200m domain, JSON is fine.

---

## Frontend ↔ Backend Development Workflow

**During development:**

```
Terminal 1: Python backend
  cd solaraeus
  source .venv/bin/activate  (or .venv\Scripts\activate on Windows)
  python scripts/run_stage1.py
  # → produces outputs/json/*.json, outputs/data/*.json, outputs/meshes/*.json

Terminal 2: Frontend
  cd solaraeus/frontend
  npm install
  npm run dev
  # → Vite dev server at http://localhost:5173
  # → reads from outputs/ via fetch('/outputs/...')
```

**Vite proxy config (optional, if using API mode):**

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

With file-based mode, no proxy needed — Vite serves the `outputs/` folder as static files (configure `publicDir` or copy files into `frontend/static/` during build).

---

## Component Tree — Visual Layout

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  TopBar: [Solaraeus logo] [Washington Square Park] [✓ Loaded] [Export View]   │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                          │ │
│  │                    MapViewport (3D Three.js Scene)                       │ │
│  │                                                                      ┌───┤ │
│  │     [Ground plane with DSM height field]                           │ │   │ │
│  │     [3D Building meshes on top]                                   │ 🌞 │ │
│  │     [Colored heatmap overlay: Tmrt / UTCI / SVF]                 │ │   │ │
│  │     [Shadow mask overlay (sunlit / shaded)]                       │ │   │ │
│  │                                                                      │ │   │ │
│  │     🚶 [3D Pedestrian Avatar walking on street]                      │ │   │ │
│  │        ├── 🟢 [Dynamic Comfort Aura (UTCI stress ring at feet)]      └───┤ │
│  │        └── 🏷️  [Floating Live Comfort HUD:                           │ │
│  │                 Tmrt: 35.2°C · UTCI: 25.8°C (Comfort Zone) · Shaded]     │ │
│  │                                                                          │ │
│  │     [Controls: Orbit View | WASD Avatar Walk Mode | 1st/3rd Person]      │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
├────────────────────────────────────────────────────────────────────────────────┤
│  Sidebar (right panel)                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │  ⏱ Time: 14:00 local  [═══════════●════════════════] 18:00 UTC           │  │
│  │                                                                          │  │
│  │  🚶 Avatar Street Walk Mode: [ ☑ Enabled ]  View: [ 3rd-Person / 1st ]   │  │
│  │     Speed: [━━━━●━━━━━━] 1.4 m/s   (WASD to walk roads/sidewalks)        │  │
│  │                                                                          │  │
│  │  ☐ DSM (elevation)  ─── opacity [━━━━━━━━●━━━━━━] 1.0                   │  │
│  │  ☑ Shadows (sunlit/shaded) ─── opacity [━━━━●━━━━━━━━] 0.6              │  │
│  │  ☐ SVF (sky view factor) ─── opacity [━━━━━━━━●━━━━━━] 1.0              │  │
│  │  ☑ Tmrt (mean radiant temp) ─── opacity [━━━━●━━━━━━━] 0.8              │  │
│  │  ☐ UTCI (thermal comfort)  ─── opacity [━━━━━━━━●━━━━━━] 1.0              │  │
│  │                                                                          │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │ Mean Tmrt   │  │ Max Tmrt    │  │ Mean UTCI   │  │ Avatar Comfort   │  │  │
│  │  │   48.3 °C   │  │   62.1 °C   │  │   32.7 °C   │  │ 25.8°C (Comfort) │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └──────────────────┘  │  │
│  │                                                                          │  │
│  │  Data Sources: Overture 2026-07-22 · ERA5 · SRTM 30m                    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Color Scales (Design Tokens)

Use these consistently across the frontend — both in 3D and any 2D overlays:

| Metric | Palette | Range | Notes |
|--------|---------|-------|-------|
| **DSM (elevation)** | Terrain: greens→browns→whites | min–max elevation | `gist_earth` or custom green-brown-white gradient |
| **Shadows** | Binary: dark gray (shaded) → bright yellow/white (sunlit) | 0–1 | Simple 2-stop gradient. Sunlit = warm, shaded = cool gray. |
| **SVF** | Viridis (dark→light) | 0–1 | Low SVF = dark (canyon), high SVF = bright (open sky) |
| **Tmrt** | Red thermal: blue→green→yellow→red→dark red | ~25–70°C | Hot = red. Use `RdYlBu_r` reversed or custom thermal. |
| **UTCI** | Custom thermal stress: blue (cold) → green (comfort) → yellow → orange → red (extreme heat) | -20 to +55°C | Matches UTCI stress categories. Blue = no stress, red = extreme heat stress. |

These colormaps should be defined once in `utils/colorScales.ts` and used everywhere — in 3D vertex colors, in tooltips, in the colorbar legend, and in any 2D overlay.

---

## Shared Types — Import Pattern

```
frontend/src/
├── api/types.ts        ← ALL shared types live here
├── api/queries.ts      ← imports from types.ts
├── components/map/*.tsx  ← import types from '../../api/types'
├── components/ui/*.tsx  ← import types from '../../api/types'
├── hooks/*.ts           ← import types from '../../api/types'
├── stores/appStore.ts   ← import types from '../api/types'
└── utils/*.ts           ← rarely need types, but import from '../../api/types' if so
```

**Rule:** No component imports another component's internal types. All shared data structures go through `api/types.ts`. This keeps the type system consistent and avoids version skew between what the backend produces and what the frontend expects.

---

## Recommended Dependencies

```json
// frontend/package.json (key dependencies)
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.5.0",           // state management
    "@react-three/fiber": "^8.15.0", // React renderer for Three.js
    "@react-three/drei": "^9.99.0",  // Three.js helpers (OrbitControls, Environment, etc.)
    "three": "^0.160.0",             // 3D engine
    "three-obj-loader": "^0.1.4",   // optional: load OBJ files from backend
    "mapLibre-gl": "^4.0.0",         // optional: 2D map fallback
    "react-map-gl": "^7.1.0",        // React wrapper for MapLibre
    "recharts": "^2.10.0",           // optional: charts for stats panel
    "date-fns": "^3.0.0"             // time formatting
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/three": "^0.160.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

**Minimal for Stage 1:** React, Vite, TypeScript, Zustand, React Three Fiber + Drei, Three.js. Everything else can be added later. The 2D map fallback is optional for Stage 1 — the 3D scene is primary.

---

## File-Based Data Flow (Stage 1 Actual Sequence)

```
1. Python: run_stage1.py
   ├── Downloads data → data/raw/
   ├── Harmonizes → data/processed/
   ├── Computes physics → (in memory)
   ├── Saves DSM + metrics as JSON → outputs/json/
   ├── Saves config + times → outputs/data/
   ├── Saves 3D mesh → outputs/meshes/
   └── Saves figures → outputs/figures/

2. Frontend: npm run dev
   ├── App.tsx mounts
   ├── useSimulationData() hook fires:
   │   ├── fetchConfig() → outputs/data/simulation_config.json
   │   ├── fetchAvailableTimes() → outputs/data/available_times.json
   │   ├── fetchDsm() → outputs/json/dsm_20240715_0000.json
   │   ├── fetch3DMesh() → outputs/meshes/buildings_3d.json
   │   └── (initial time) fetchMetric('tmrt', '2024-07-15T18:00:00')
   │       → outputs/json/tmrt_20240715_1800.json
   ├── Data lands in Zustand store
   ├── MapViewport renders:
   │   ├── GroundMesh from DSM data
   │   ├── BuildingMesh from 3D mesh data
   │   ├── ShadowPlane from shadow data (if visible)
   │   └── HeatmapPlane from Tmrt data (if visible, active layer)
   └── Sidebar renders:
       ├── TimeSlider with available times
       ├── LayerSwitcher with visibility toggles
       └── StatCards from metric statistics

3. User drags time slider → useTimeline updates currentUtcTime → useSimulationData re-fetches shadows/tmrt/utci for new time → MapViewport updates planes → scene updates
```

---

## What the Frontend Does NOT Do

- Does not run physics — that's the Python backend's job
- Does not download raw data — that's the Python backend's job
- Does not write to `src/`, `data/`, `tests/`, `scripts/` — those stay Python
- Does not require a server for Stage 1 — file-based mode works without one
- Does not parse NetCDF in the browser (uses pre-converted JSON)

---

## What "Professional" Means for the Frontend

| Aspect | Good | Bad |
|--------|------|-----|
| **Type safety** | Full TypeScript. All backend data has typed interfaces. No `any`. | Components receiving untyped JSON and hoping for the best. |
| **Separation of concerns** | `api/` knows about backend. `components/` know about UI. `hooks/` know about state. `three/` knows about 3D. Nothing crosses layers improperly. | A map component that fetches its own data AND renders AND manages state. |
| **State management** | Centralized store (Zustand or Context). Single source of truth for time, layers, colors. | Ten different `useState` calls scattered across components, out of sync. |
| **Visual design** | Consistent color scales, typography, spacing, dark theme via CSS variables. Design tokens in `index.css`. | Inline styles everywhere, random color choices per component. |
| **Loading states** | Explicit loading, error, and empty states. `LoadingOverlay` while data fetches. `ErrorBanner` on failure. | Components rendering `null` or crashing when data isn't ready yet. |
| **Performance** | Data fetched once and cached in store. Layers memoized. Three.js scene updates only when data changes. | Refetching everything on every time slider tick. Re-rendering the whole scene for a color change. |
| **Responsive layout** | Map fills available space. Sidebar is fixed width. Layout adapts to window resize. | Fixed pixel sizes. UI breaks on smaller windows. |
| **Accessibility** | Keyboard-navigable controls. Colorblind-aware palettes (avoid red-green only). Tooltips on hover + focus. | Colors as the only way to convey information. No keyboard support. |

---

## Gitignore Additions

```
# Frontend
frontend/node_modules/
frontend/dist/
frontend/*.tsbuildinfo

# Frontend environment
frontend/.env
frontend/.env.local

# Frontend build artifacts (if any generated locally)
frontend/public/favicon.ico
```

Update root `.gitignore` to include these. The `frontend/` directory itself is committed (it's code). `frontend/node_modules/` and `frontend/dist/` are not.

---

## README Additions (Frontend Section)

Add to root `README.md`:

```markdown
## Frontend (React + Vite + Three.js)

The interactive map and 3D visualization UI lives in `frontend/`. It consumes data produced by the Python backend (`scripts/run_stage1.py`) via JSON files in `outputs/json/` and `outputs/data/`.

### Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The app reads pre-computed metric data from the `outputs/` directory served as static files by Vite.

### Backend Data Requirements

Before the frontend can display anything, run the Python backend to generate data:

```bash
cd ..
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python scripts/run_stage1.py
```

This produces:
- `outputs/data/simulation_config.json` — study area metadata, simulation parameters
- `outputs/data/available_times.json` — available time steps for the timeline slider
- `outputs/json/dsm_*.json` — Digital Surface Model (elevation)
- `outputs/json/svf_*.json` — Sky View Factor
- `outputs/json/shadows_*.json` — Shadow mask (one per time step)
- `outputs/json/tmrt_*.json` — Mean Radiant Temperature (one per time step)
- `outputs/json/utci_*.json` — UTCI (one per time step)
- `outputs/meshes/buildings_3d.json` — 3D building geometry for the 3D scene

### Connecting to a REST API (Future)

To switch from file-based to API-based data fetching, edit `frontend/src/api/client.ts` to point `API_BASE` at your backend server (e.g., `http://localhost:8000/api`), and implement the corresponding endpoints in the Python backend. The components and hooks do not need to change.

### Technology Stack

- React 18 + TypeScript + Vite
- Zustand (state management)
- React Three Fiber + Drei (3D scene via Three.js)
- Recharts (statistics charts, optional)
- MapLibre GL (2D map fallback, optional)
```

---

## Summary — What Was Added

| Added | Purpose |
|-------|---------|
| `frontend/` directory | New subproject, parallel to `src/` and `data/` |
| `frontend/package.json` + Vite + TypeScript config | React + Three.js development environment |
| `frontend/src/api/` | Backend communication layer: types, client, query functions |
| `frontend/src/components/` | Layout, map, layers, avatar (walk mode & comfort HUD), UI components, dialogs |
| `frontend/src/hooks/` | State logic: data fetching, timeline, layer visibility, mouse position, avatar movement & comfort sampling |
| `frontend/src/utils/` | Color scales, coordinate transforms, formatters |
| `frontend/src/stores/` | Global app state (Zustand) including active camera & avatar controller |
| `frontend/src/three/` | Three.js scene setup, building/ground/shadow/heatmap mesh builders, avatar models |
| `outputs/json/` convention | JSON metric files as the backend→frontend data contract |
| `outputs/data/simulation_config.json` | Single config file the frontend reads on load |
| Avatar Walk Mode & Comfort Inspector | 3D pedestrian avatar, WASD street movement, 1st/3rd person camera, dynamic comfort aura, live UTCI/Tmrt HUD |
| Updated `.gitignore` | Exclude frontend build artifacts |
| README section | How to run frontend + backend together, data contract, tech stack |

The original Python structure (`src/`, `data/`, `physics/`, `tests/`, `scripts/`, `outputs/`) is untouched. The frontend is a separate concern that consumes the outputs those modules produce. When you're ready for real-time or interactive computation, add a REST API to the Python backend — the frontend's `api/` layer is already structured to support that switch without changes to components or hooks.