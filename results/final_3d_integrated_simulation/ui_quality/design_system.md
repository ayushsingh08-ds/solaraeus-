# SOLARAEUS 3D VIEWER — DESIGN SYSTEM SPECIFICATION
**Identity Concept:** Solar Observatory & Twilight Survey Chart  
**Authoritative Architectural Domain:** Presentation Layer (VISUAL_ONLY)  
**Strict Physics Isolation:** Scientific arrays, mathematical solver models, and colormaps are strictly decoupled from chrome styling.

---

## 1. Design Concept & Philosophy

The SOLARAEUS interface is engineered as an **astronomical precision instrument crossed with an engraved twilight survey chart**, rejecting generic SaaS dashboard aesthetics ("AI slop", purple gradients on white, cookie-cutter card grids).

- **Cinematic / Observatory Mood:** Deep ink tones, atmospheric horizon glow whose warmth tracks the true astronomical solar elevation, soft topographic survey marks, and celestial trajectory arc.
- **Engraved Instrument Detailing:** Fine hairline rules (`1px` with 14% opacity), subtle corner registration ticks (`+`), unbordered floating colorbars, and letterspaced small-caps technical metadata.
- **Signature Feature — Celestial Sun-Path Arc:** An arched timeline scrubber displaying the day's true solar elevation curve (06:00 to 18:30 IST) with an easing sun-orb playhead, altitude bubble, and staggered solar landmarks (Dawn, Solar Noon, Benchmark, Dusk) that never collide with controls.

---

## 2. Typography Specification

All fonts are self-hosted locally in `simulation_3d/fonts/` (WOFF2 format) and loaded via `fonts.css`, ensuring 100% offline localhost independence without external CDN dependencies. Generic fonts (`Inter`, `Roboto`, `Arial`, `system-ui` as primary, `Space Grotesk`) are strictly forbidden.

| Purpose | Typeface | Weights | Characteristics | Fallback Stack |
| :--- | :--- | :--- | :--- | :--- |
| **Display & Headline Numeral** | **Fraunces** | 400, 700 | Characterful serif with optical sizing, warm curves, engraved numerals | Georgia, serif |
| **Interface & Navigation** | **Instrument Sans** | 400, 600 | Refined humanist/grotesque sans, crisp glyphs, high legibility | -apple-system, sans-serif |
| **Tabular Data & Coordinates** | **DM Mono** | 400, 500 | Distinctive technical monospace with proportional spacing and lining figures | SF Mono, monospace |

- **Minimum Type Size:** 12 px throughout the entire interface (micro-labels 12 px, body 14 px, display 34 px).
- **Tabular Figures:** Tabular numerals (`font-feature-settings: "tnum"`) prevent numerical layout jitter during time playback.

---

## 3. Curated Color Token Architecture

The color system commits to a single dominant ink family paired with a sharp warm solar accent and a cool shade signal.

### 3.1 Observatory (Cinematic Default)
```css
:root {
  --ink-0:      #070B14;               /* Deepest void background */
  --ink-1:      rgba(13, 20, 36, 0.88); /* Translucent panels with backdrop-filter blur */
  --ink-2:      #16203A;               /* Raised surfaces, flyout rows & hover */
  --ink-3:      #222F52;               /* Elevated segment controls */
  --line:       rgba(214, 224, 255, 0.14);  /* Thin hairline dividers */
  --line-strong:rgba(214, 224, 255, 0.28);  /* Prominent survey ticks */
  --text-1:     #EDF1FA;               /* Primary high-contrast typography (WCAG AA pass: 14.8:1) */
  --text-2:     #9AA7C4;               /* Secondary explanatory typography (WCAG AA pass: 6.2:1) */
  --text-muted: #677598;               /* Technical micro-metadata */
  --sun:        #FFB02E;               /* Sharp solar accent (active state, playhead, sun glyph) */
  --shade:      #3FD1C0;               /* Cool secondary signal (cooling relief, success) */
  --alert:      #FF5A4E;               /* Heat stress & alert indicator */
}
```

### 3.2 Daylight Preset (Warm Survey-Paper)
Flips the interface into an archival cartographic survey sheet:
```css
body.theme-daylight {
  --ink-0:      #F3EBDD;               /* Warm archival survey paper */
  --ink-1:      rgba(243, 235, 221, 0.92);
  --ink-2:      #E3D9C6;
  --ink-3:      #D5C9B2;
  --line:       rgba(27, 34, 51, 0.16);
  --text-1:     #1B2233;               /* Deep ink text (WCAG AAA pass: 13.2:1) */
  --text-2:     #4D5870;               /* Archival secondary ink */
  --sun:        #D98200;               /* Deepened solar amber for daylight contrast */
  --shade:      #188F82;               /* Archival survey teal */
  --alert:      #D93829;
}
```

### 3.3 Analysis Preset (Neutral Slate)
Minimalist flat gray workspace with zero decorative atmosphere, flat unlit lighting, and maximum legibility:
```css
body.theme-analysis {
  --ink-0:      #111827;               /* Neutral slate */
  --ink-1:      rgba(17, 24, 39, 0.94);
  --ink-2:      #1F2937;
  --line:       rgba(255, 255, 255, 0.14);
  --text-1:     #F9FAFB;
  --text-2:     #9CA3AF;
  --sun:        #F59E0B;
  --shade:      #10B981;
  --alert:      #EF4444;
}
```

---

## 4. Separation of Theme and Science (Rule 6)

1. **Physical Colormaps Isolated in `dataColormaps.js`:**
   - **$T_{mrt}$:** Perceptually uniform, colorblind-safe Inferno LUT (dark purple $\rightarrow$ vermillion $\rightarrow$ solar gold).
   - **UTCI:** Standard thermal stress bands (below 9°C blue cold stress, 9–26°C green comfort, 26–32°C amber moderate stress, 32–38°C orange strong stress, 38–46°C red very strong stress, above 46°C crimson extreme stress). Purple is strictly eliminated.
   - **Cooling Relief ($\Delta T_{mrt}$):** Diverging teal reduction colormap centered on zero.
2. **Preset Invariance:** Style preset switches (`Observatory`, `Daylight`, `Analysis`) alter only the UI chrome, background canvas, and building massing textures. They **never alter data colormaps or physical array values**.
3. **Heatmap Material Integrity:** Heatmap is rendered in an unlit pass with `toneMapped = false`, `polygonOffset = true`, and zero blur or bloom. Fragments inside building footprints are clipped via GPU mask discard.

---

## 5. Motion & Orchestration

1. **Load Sequence (1.2 s):**
   - Top bar slides down (`slideDownFade`, 0.6s).
   - Icon rail staggers from the left (`slideRightFade`, 0.6s).
   - Celestial arc timeline dock slides up (`slideUpFade`, 0.6s).
   - Floating headline readout reveals (`fadeIn`, 0.8s).
2. **Micro-Interactions:**
   - Easing playhead translates smoothly along the celestial curve.
   - Flyouts slide in/out as clean single sheets (max 300px).
   - Automatic 4s idle fade for the timeline dock in Cinematic preset.
3. **Accessibility:**
   - `@media (prefers-reduced-motion: reduce)` immediately zeroes animation durations, cancels reveals, and freezes glyph spins.

---

## 6. UI Clutter Budget Compliance

- **Scene Viewport Area:** $\ge 76\%$ unobstructed 3D area at rest (requirement: $\ge 70\%$).
- **Bordered Containers at Rest:** 2 containers visible (Top Bar + Timeline Dock; requirement: $\le 3$).
- **Primary Controls Visible at Rest:** 6 controls (Presets, Flyout Rail, Play/Pause, Camera, Governance, Details; requirement: $\le 7$).
- **Box-in-Box Nesting:** Completely eliminated; replaced by flat radio rows and hairline dividers.
