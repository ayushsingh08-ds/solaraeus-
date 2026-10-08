/**
 * SOLARAEUS 3D: Scientific Data Colormaps Module (dataColormaps.js)
 * 
 * Strict Separation of Theme and Science:
 * Colormaps, break values, and thermal comfort bands are physically authoritative
 * and are NEVER altered, recolored, or modified by interface style presets or themes.
 */

(function (window) {
  'use strict';

  // 1. Standard UTCI Thermal Stress Categories (Bröde et al., 2012 / Błażejczyk et al., 2013)
  // Below 9°C: Cold stress
  // 9°C to 26°C: No thermal stress (comfort)
  // 26°C to 32°C: Moderate heat stress
  // 32°C to 38°C: Strong heat stress
  // 38°C to 46°C: Very strong heat stress
  // Above 46°C: Extreme heat stress
  const UTCI_BANDS = [
    { max: 9.0, label: 'Cold Stress', color: [59, 130, 246] },         // Blue #3b82f6
    { max: 26.0, label: 'No Thermal Stress', color: [16, 185, 129] },   // Emerald #10b981
    { max: 32.0, label: 'Moderate Heat Stress', color: [234, 179, 8] }, // Amber/Yellow #eab308
    { max: 38.0, label: 'Strong Heat Stress', color: [249, 115, 22] },  // Orange #f97316
    { max: 46.0, label: 'Very Strong Heat Stress', color: [239, 68, 68] }, // Red #ef4444
    { max: 60.0, label: 'Extreme Heat Stress', color: [153, 27, 27] }   // Crimson #991b1b
  ];

  // Helper for linear interpolation
  function lerp(a, b, t) {
    return a + (b - a) * Math.max(0, Math.min(1, t));
  }

  // 2. Colormap Color Evaluators
  const colormaps = {
    // Inferno-class colormap for Mean Radiant Temperature (Tmrt)
    inferno: function (t) {
      t = Math.max(0, Math.min(1, t));
      // Keystops for Inferno: (0.0: deep dark purple, 0.3: magenta, 0.65: bright vermillion/orange, 1.0: pale solar gold)
      let r, g, b;
      if (t < 0.25) {
        const f = t / 0.25;
        r = lerp(10, 68, f);
        g = lerp(5, 15, f);
        b = lerp(35, 112, f);
      } else if (t < 0.55) {
        const f = (t - 0.25) / 0.3;
        r = lerp(68, 187, f);
        g = lerp(15, 55, f);
        b = lerp(112, 84, f);
      } else if (t < 0.82) {
        const f = (t - 0.55) / 0.27;
        r = lerp(187, 249, f);
        g = lerp(55, 142, f);
        b = lerp(84, 9, f);
      } else {
        const f = (t - 0.82) / 0.18;
        r = lerp(249, 252, f);
        g = lerp(142, 240, f);
        b = lerp(9, 160, f);
      }
      return [Math.round(r), Math.round(g), Math.round(b), 255];
    },

    // Standard Universal Thermal Climate Index (UTCI) colormap (Never uses purple)
    utci: function (val) {
      // Direct physical temperature mapping
      if (val < 9.0) {
        // Cold stress: soft cyan to blue
        const t = Math.max(0, (val - (-5.0)) / 14.0);
        return [Math.round(lerp(30, 59, t)), Math.round(lerp(64, 130, t)), Math.round(lerp(175, 246, t)), 255];
      } else if (val < 26.0) {
        // Comfort zone: lush green
        const t = (val - 9.0) / 17.0;
        return [Math.round(lerp(16, 52, t)), Math.round(lerp(185, 211, t)), Math.round(lerp(129, 153, t)), 255];
      } else if (val < 32.0) {
        // Moderate heat stress: green to gold
        const t = (val - 26.0) / 6.0;
        return [Math.round(lerp(52, 234, t)), Math.round(lerp(211, 179, t)), Math.round(lerp(153, 8, t)), 255];
      } else if (val < 38.0) {
        // Strong heat stress: gold to bright orange
        const t = (val - 32.0) / 6.0;
        return [Math.round(lerp(234, 249, t)), Math.round(lerp(179, 115, t)), Math.round(lerp(8, 22, t)), 255];
      } else if (val < 46.0) {
        // Very strong heat stress: orange to red
        const t = (val - 38.0) / 8.0;
        return [Math.round(lerp(249, 239, t)), Math.round(lerp(115, 68, t)), Math.round(lerp(22, 68, t)), 255];
      } else {
        // Extreme heat stress: dark crimson
        const t = Math.min(1, (val - 46.0) / 10.0);
        return [Math.round(lerp(239, 153, t)), Math.round(lerp(68, 27, t)), Math.round(lerp(68, 27, t)), 255];
      }
    },

    // Symmetric Diverging Colormap for Cooling Relief (ΔTmrt / ΔUTCI)
    // Cool cyan/teal for negative ΔT (cooling), transparent/gray at 0, warm amber/red for positive ΔT
    diverging: function (t) {
      t = Math.max(0, Math.min(1, t));
      let r, g, b, a;
      if (t < 0.5) {
        // Cooling: Cyan to Teal
        const f = (0.5 - t) / 0.5;
        r = Math.round(lerp(200, 6, f));
        g = Math.round(lerp(220, 182, f));
        b = Math.round(lerp(240, 212, f));
        a = Math.round(lerp(40, 235, f));
      } else {
        // Warming: Amber to Red
        const f = (t - 0.5) / 0.5;
        r = Math.round(lerp(200, 239, f));
        g = Math.round(lerp(220, 68, f));
        b = Math.round(lerp(240, 68, f));
        a = Math.round(lerp(40, 235, f));
      }
      return [r, g, b, a];
    },

    // Sequential Viridis-class colormap for Sky View Factor (SVF) & Durations
    sequential: function (t) {
      t = Math.max(0, Math.min(1, t));
      const r = Math.round(lerp(68, 253, t));
      const g = Math.round(lerp(1, 231, t));
      const b = Math.round(lerp(84, 37, t));
      return [r, g, b, 255];
    }
  };

  // 3. Generate 256x1 Three.js DataTexture LUT
  function createLutTexture(type, minVal, maxVal) {
    if (typeof THREE === 'undefined') return null;

    const size = 256;
    const data = new Uint8Array(size * 4);

    for (let i = 0; i < size; i++) {
      const t = i / (size - 1);
      let rgba;
      if (type === 'utci') {
        const mn = minVal !== undefined ? minVal : 30.0;
        const mx = maxVal !== undefined ? maxVal : 40.0;
        const val = mn + t * (mx - mn);
        rgba = colormaps.utci(val);
      } else if (type === 'tmrt' || type === 'inferno') {
        rgba = colormaps.inferno(t);
      } else if (type === 'cooling') {
        rgba = colormaps.diverging(t);
      } else {
        rgba = colormaps.sequential(t);
      }

      data[i * 4] = rgba[0];
      data[i * 4 + 1] = rgba[1];
      data[i * 4 + 2] = rgba[2];
      data[i * 4 + 3] = rgba[3];
    }

    const tex = new THREE.DataTexture(data, size, 1, THREE.RGBAFormat);
    tex.minFilter = THREE.LinearFilter;
    tex.magFilter = THREE.LinearFilter;
    tex.wrapS = THREE.ClampToEdgeWrapping;
    tex.wrapT = THREE.ClampToEdgeWrapping;
    tex.needsUpdate = true;
    return tex;
  }

  // 4. Calculate UTCI Thermal Stress Band details for a numeric value
  function getUtciBand(val) {
    for (let i = 0; i < UTCI_BANDS.length; i++) {
      if (val < UTCI_BANDS[i].max || i === UTCI_BANDS.length - 1) {
        return UTCI_BANDS[i];
      }
    }
    return UTCI_BANDS[UTCI_BANDS.length - 1];
  }

  // Export module
  window.SOLARAEUS_COLORMAPS = {
    colormaps,
    createLutTexture,
    createColormapTexture: createLutTexture,
    getUtciBand,
    UTCI_BANDS
  };

})(window);
