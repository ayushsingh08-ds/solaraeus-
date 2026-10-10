## 27. Interactive 3D WebGL Digital Twin & Cinematic Frontend

### 27.1 Architecture & Implementation (`simulation_3d/`)
- **WebGL Runtime**: Three.js r128 client-side rendering with orbit controls, custom glsl heatmap shader (`heatmapShader.js`), and turbo/thermal scientific colormaps (`dataColormaps.js`).
- **Design System (`index.css`)**: Glassmorphism UI, WCAG AA compliance (contrast ratios > 7.0:1), Outfit typography with local font assets, responsive HUD overlays, and interactive inspection drawers.
- **Data Payload (`church_street_data.js` & `church_street_data.json`)**: Contains 123 LOD-1 building meshes, 14 surveyed trees (core corridor + context), terrain elevation geometry, hourly solar trajectory angles, and precomputed $T_{\mathrm{mrt}}$ / UTCI microclimate raster grids.
- **Verification Suite**: Executed `scripts/verify_ui_quality.py` with 100% audit pass:
  - Physics Baseline Hashes: PASS
  - Typography & Fonts Audit: PASS
  - WCAG AA Contrast Audit: PASS
  - Vegetation Completeness Audit (14/14): PASS
  - Clutter Budget Audit: PASS
  - Backend 20 Sampled Cells Audit: PASS
  - GPU Shader & Scientific Colormap Audit: PASS

---

