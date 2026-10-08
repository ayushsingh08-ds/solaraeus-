# SOLARAEUS CPU Reference API Specification (v2.0.0-cpu-ref)

## 1. Architectural Scope
The SOLARAEUS CPU reference solver provides the authoritative, mathematically audited baseline for urban microclimatic modeling (solar direct beam occlusion, sky-view factor horizon scanning, directional radiative flux integration, Mean Radiant Temperature, and UTCI comfort indexing).

## 2. Core Functions
### `full_recompute(scene, weather, config, backend='cpu') -> SimulationResult`
Performs a pure full evaluation from scratch across all grid cells.
- **`scene` (`Scene`)**: Watertight triangular meshes and pedestrian grid specification.
- **`weather` (`Weather`)**: Boundary forcing ($T_{air}$ in K, RH in %, wind speed in m/s, DNI/DHI in W/m²).
- **`config` (`SimulationConfig`)**: Spatial and temporal controls (geographic coordinates, date, local time, resolution, search radius).
- **Returns**: `SimulationResult` containing 2D spatial numpy arrays (`shadow_mask`, `direct_irradiance`, `svf`, `shortwave_flux`, `longwave_flux`, `tmrt`, `utci`).

### `incremental_update_certified(previous_scene, updated_scene, previous_result, edit, weather, config) -> Tuple[IncrementalUpdateResult, ErrorCertificate]`
Executes certified incremental update reusing unaffected static fields and recomputing only cells where predicted error exceeds `config.tmrt_tolerance`.
- Guarantees: $|T_{mrt}^{inc} - T_{mrt}^{full}| \le B_T(x) \le 	ext{tolerance}$ on all reused cells.
