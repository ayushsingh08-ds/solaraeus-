import { clamp } from './math';

export type RGB = [number, number, number];

export interface ColorStop {
  pos: number; // 0.0 to 1.0
  color: RGB;
}

// Curated scientific colormaps matching Python backend
export const COLORMAPS: Record<string, ColorStop[]> = {
  // Magma (Tmrt radiant heat load)
  magma: [
    { pos: 0.0, color: [0, 0, 4] },
    { pos: 0.2, color: [40, 11, 84] },
    { pos: 0.4, color: [101, 21, 110] },
    { pos: 0.6, color: [182, 54, 121] },
    { pos: 0.8, color: [251, 136, 97] },
    { pos: 1.0, color: [252, 253, 191] },
  ],

  // Cividis (Sky View Factor 0 to 1)
  cividis: [
    { pos: 0.0, color: [0, 32, 77] },
    { pos: 0.25, color: [51, 68, 105] },
    { pos: 0.5, color: [124, 123, 120] },
    { pos: 0.75, color: [186, 178, 97] },
    { pos: 1.0, color: [255, 234, 70] },
  ],

  // Viridis (DSM Elevation)
  viridis: [
    { pos: 0.0, color: [68, 1, 84] },
    { pos: 0.25, color: [59, 82, 139] },
    { pos: 0.5, color: [33, 145, 140] },
    { pos: 0.75, color: [94, 201, 98] },
    { pos: 1.0, color: [253, 231, 37] },
  ],

  // Thermal / Spectral_r (UTCI Heat Stress)
  utci: [
    { pos: 0.0, color: [43, 131, 186] },   // Cool / Light blue
    { pos: 0.25, color: [171, 221, 164] }, // Neutral green
    { pos: 0.5, color: [255, 255, 191] },  // Moderate yellow
    { pos: 0.75, color: [253, 174, 97] },  // Strong orange
    { pos: 0.9, color: [215, 25, 28] },    // Very strong red
    { pos: 1.0, color: [128, 0, 38] },     // Extreme crimson
  ],

  // Shadows (Binary Shaded Slate / Sunlit Solar Orange - Reference 2 & 3)
  shadows: [
    { pos: 0.0, color: [51, 65, 85] },    // Shaded slate roadway corridor (#334155)
    { pos: 1.0, color: [255, 122, 0] },   // Sunlit radiant solar orange (#FF7A00)
  ],
};


export function interpolateRGB(c1: RGB, c2: RGB, t: number): RGB {
  return [
    Math.round(c1[0] + (c2[0] - c1[0]) * t),
    Math.round(c1[1] + (c2[1] - c1[1]) * t),
    Math.round(c1[2] + (c2[2] - c1[2]) * t),
  ];
}

export function getColorRGB(val: number, min: number, max: number, paletteName: string = 'magma'): RGB {
  const stops = COLORMAPS[paletteName] || COLORMAPS.magma;
  if (min >= max) return stops[0].color;

  const t = clamp((val - min) / (max - min), 0.0, 1.0);

  for (let i = 0; i < stops.length - 1; i++) {
    const s1 = stops[i];
    const s2 = stops[i + 1];
    if (t >= s1.pos && t <= s2.pos) {
      const localT = (t - s1.pos) / (s2.pos - s1.pos);
      return interpolateRGB(s1.color, s2.color, localT);
    }
  }

  return stops[stops.length - 1].color;
}

export function getColorHex(val: number, min: number, max: number, paletteName: string = 'magma'): string {
  const [r, g, b] = getColorRGB(val, min, max, paletteName);
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

export function getUtciStressInfo(utciVal: number): { label: string; color: string; level: number } {
  if (utciVal < 9.0) {
    return { label: 'Cold Stress', color: '#38bdf8', level: 0 };
  } else if (utciVal <= 26.0) {
    return { label: 'No Thermal Stress', color: '#4ade80', level: 1 };
  } else if (utciVal <= 32.0) {
    return { label: 'Moderate Heat Stress', color: '#facc15', level: 2 };
  } else if (utciVal <= 38.0) {
    return { label: 'Strong Heat Stress', color: '#fb923c', level: 3 };
  } else if (utciVal <= 46.0) {
    return { label: 'Very Strong Heat Stress', color: '#ef4444', level: 4 };
  } else {
    return { label: 'Extreme Heat Stress', color: '#991b1b', level: 5 };
  }
}
