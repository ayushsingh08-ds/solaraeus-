# SOLARAEUS 3D Viewer: Detailed Architectural & Rendering Diagnosis

This diagnosis document examines the architectural, rendering, and UI flaws identified in the baseline viewer implementation, tracing each problem to its exact source file, line numbers, and programmatic cause based on code inspection and rendered baseline screenshots.

---

### Problem 1: Heatmaps are Blocky and Blurry Simultaneously
- **Primary Source File:** `simulation_3d/app.js` (lines 559–574, 614–670) and `simulation_3d/church_street_data.js`
- **Root Cause:**
  1. The thermal grid is discrete with resolution $65 \times 50$ cells (`nx = 65, ny = 50`).
  2. The texture is generated via an HTML5 2D canvas (`canvas.width = 65, canvas.height = 50`) and uploaded as a CPU-drawn canvas texture (`THREE.CanvasTexture`).
  3. When mapped across the $260\,\text{m} \times 200\,\text{m}$ corridor plane, Three.js applies `THREE.LinearFilter`. Because each pixel represents an entire $4\,\text{m} \times 4\,\text{m}$ receptor cell, bilinear filtering blurs adjacent cells into indistinct smears while failing to provide sub-cell gradient continuity, resulting in a display that is both blurry and pixel-blocky.
  4. There is no shader-based reconstruction, no analytical interpolation, and no shader color look-up table (LUT).

### Problem 2: Missing Legend, Scale, and Uniform Purple UTCI Display
- **Primary Source File:** `simulation_3d/app.js` (lines 595–606, 636–640) and `simulation_3d/index.html` (lines 121–132)
- **Root Cause:**
  1. In `index.html`, the legend `#thermal-legend` is buried inside an accordion in the left panel and set to `display: none` by default; there is no persistent floating viewport colorbar legend with numeric ticks, units, or min/max.
  2. In `app.js` line 605, the UTCI colormap assigns values where $t \ge 0.7$ to RGB `[168, 85, 247]` (purple).
  3. In `updateHeatmapTexture()`, line 636 hardcodes `minVal = 32.5; maxVal = 37.5;`.
  4. In `church_street_data.js`, all daytime baseline corridor UTCI values are in the range $36.8^\circ\text{C} - 37.4^\circ\text{C}$ (extreme heat stress). Because $(37.15 - 32.5) / (37.5 - 32.5) = 0.93 > 0.7$, every single unbuilt receptor cell evaluates to $> 0.7$, rendering the entire street corridor as a solid, flat purple block.
  5. Furthermore, purple is a scientifically non-standard hue for thermal comfort; standard UTCI thermal stress conventions prescribe blue (cold), green (no stress), yellow/amber (moderate), orange (strong), red (very strong), and deep crimson/burgundy (extreme).

### Problem 3: Near-Opaque Overlay Smothering the Scene & Building Bleed
- **Primary Source File:** `simulation_3d/app.js` (lines 17, 650–656) and `simulation_3d/index.css`
- **Root Cause:**
  1. Default overlay opacity was initialized to `0.85`, which obliterates the underlying 3D street textures, curbs, and shadows.
  2. While building cells are masked to zero alpha on the 2D canvas, bilinear texture filtering across the boundary between an active corridor cell ($\alpha = 210$) and an adjacent building cell ($\alpha = 0$) interpolates alpha across the building footprint perimeter, creating a colored fuzzy halo that intrudes onto building bases.
  3. When the heatmap is activated, building materials do not switch to an unlit neutral massing material, leaving the scene excessively dark and cluttered.

### Problem 4: Dark Void, Flat Gray Box Massing, and Abruptly Cropped Ground
- **Primary Source File:** `simulation_3d/app.js` (lines 81–84, 323–335, 363–376)
- **Root Cause:**
  1. The ground mesh is a simple `PlaneGeometry(380, 280)` abruptly cut off at its outer coordinates, surrounded by a dark void (`#070b14`).
  2. There is no horizon glow gradient, atmospheric depth fade, or ground boundary vignette falloff extending beyond the study centroid.
  3. Buildings are rendered with a flat single-tone PBR material (`#222b3d`) without ambient occlusion, edge beveling, or roof-to-facade tonal variation.

### Problem 5: Colliding Pins and Persistent Callout Occlusion
- **Primary Source File:** `simulation_3d/app.js` (lines 208–224, 480–520, `setInitialCallout()`)
- **Root Cause:**
  1. `app.js` explicitly invokes `setInitialCallout()` on initialization, permanently rendering an unprompted large callout card right over the central avenue (`pos = (105, 5.5, -70)`).
  2. The callout obscures the tree cluster pin and the candidate panel pin.
  3. Pin projection in `updateScreenProjections()` renders all 5 landmark pins unconditionally without 2D screen-space collision detection, distance culling, or scenario-based visibility filtering.

### Problem 6: Missing Context Vegetation (Only T08–T13 Displayed)
- **Primary Source File:** `simulation_3d/church_street_data.js` (lines 12–45) and `src/urban_comfort/integration/tree_loader.py`
- **Root Cause:**
  1. `church_street_data.js` only serialized the 6 core trees (T08 to T13) from `data/review/core_tree_review.csv`.
  2. Municipal BBMP census context trees (T01–T07, T14) present in `data/review/context_tree_review.csv` and `bengaluru_church_street_bbmp_trees_july2026_supplement/` were omitted from the 3D data payload.
  3. Consequently, the avenue appears largely devoid of its actual tree canopy beyond the small cluster on the south walkway.

### Problem 7: Control Duplication, Tiny Typography, and Timeline Collisions
- **Primary Source File:** `simulation_3d/index.html` (lines 71–101, 277–306, 308–340) and `simulation_3d/index.css`
- **Root Cause:**
  1. The interface implements scenario selection and overlay mode selection in two separate places: in the left HUD sidebar AND in the bottom floating dock, cluttering screen space.
  2. Text sizes in secondary navigation elements and slider labels are set between $7.5\,\text{px}$ and $9.5\,\text{px}$, severely violating accessibility and readability standards (minimum $12\,\text{px}$).
  3. Fixed percentage positions on `.solar-arc-markers span` cause labels (e.g. `14:30 (Benchmark)`) to physically collide with the play/pause button and the digital clock readout at narrower viewport widths.

### Problem 8: Cluttered Box-in-Box Sidebar Hierarchies
- **Primary Source File:** `simulation_3d/index.html` (lines 62–274) and `simulation_3d/index.css`
- **Root Cause:**
  1. Both the left and right sidebars employ heavy nested containers (`.panel-section` $\rightarrow$ `.stats-grid` $\rightarrow$ `.stat-box` $\rightarrow$ `.diag-table` $\rightarrow$ `.disclaimer-card`), totaling more than 14 simultaneous bordered/opaque boxes visible at rest.
  2. The scene viewport ratio drops below $55\%$ on standard $1366 \times 768$ laptop screens, violating the clutter budget ($> 70\%$ clear scene area).

### Problem 9: Hardcoded Static Badges
- **Primary Source File:** `simulation_3d/index.html` (lines 65, 177, 261)
- **Root Cause:**
  1. Labels such as `<span class="live-tag">GPU CERTIFIED</span>`, `<span class="verified-tag">415/415 AUDITED</span>`, and `<strong class="text-emerald">&lt; 10⁻⁶ K (Exact 0.00 K)</strong>` are hardcoded static HTML strings.
  2. They are not dynamically linked to live simulation state, solver manifests, or certificate files, eroding scientific credibility.

### Problem 10: Ineffective Shadow Contrast in Realistic 3D Mode
- **Primary Source File:** `simulation_3d/app.js` (lines 160–185, 323–330)
- **Root Cause:**
  1. The street pavement material was styled as a very dark slate (`color: 0x141824`, roughness 0.88, metalness 0.08).
  2. Because the pavement color was nearly black, ray-traced shadows cast by buildings and trees had almost zero perceptual contrast against the unshaded ground, making shadows appear missing even when 57% of the corridor was shaded.
  3. `normalBias = 0.025` caused shadow acne filtering to over-erode shadow edges on low-angle surfaces.

---
**Status:** Diagnosis complete. All 10 root causes identified and documented. Proceeding to comprehensive redesign and implementation.
