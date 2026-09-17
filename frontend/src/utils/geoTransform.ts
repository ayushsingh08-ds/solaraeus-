import { clamp } from './math';

export interface GridDimensions {
  rows: number;
  cols: number;
  baseElevation?: number;
}

const DEFAULT_DIMS: GridDimensions = {
  rows: 673,
  cols: 599,
  baseElevation: 6.0,
};

/**
 * Converts a grid cell (row, col, elevationZ) to Three.js world coordinates [x, y, z].
 * Row 0 is North (-Z in Three.js), Col 0 is West (-X in Three.js).
 */
export function gridToWorld(
  row: number,
  col: number,
  elevationZ: number = 6.0,
  dims: GridDimensions = DEFAULT_DIMS
): [number, number, number] {
  const x = col - dims.cols / 2 + 0.5;
  const z = row - dims.rows / 2 + 0.5;
  const y = Math.max(0, elevationZ - (dims.baseElevation ?? 6.0));
  return [x, y, z];
}

/**
 * Converts Three.js world coordinates (x, z) to grid indices [row, col].
 */
export function worldToGrid(
  x: number,
  z: number,
  dims: GridDimensions = DEFAULT_DIMS
): [number, number] {
  const col = Math.round(x + dims.cols / 2 - 0.5);
  const row = Math.round(z + dims.rows / 2 - 0.5);
  return [
    clamp(row, 0, dims.rows - 1),
    clamp(col, 0, dims.cols - 1),
  ];
}

/**
 * Converts local building mesh vertex [x_local, y_local, z_local] from buildings_3d.json
 * into centered Three.js world coordinates [x, y, z].
 * x_local in [0, cols], y_local in [0, rows] (0=South, rows=North).
 */
export function buildingVertexToWorld(
  xLocal: number,
  yLocal: number,
  zLocal: number,
  dims: GridDimensions = DEFAULT_DIMS
): [number, number, number] {
  const x = xLocal - dims.cols / 2;
  const z = -(yLocal - dims.rows / 2); // Invert since yLocal 0 is South, Three.js North is -Z
  const y = Math.max(0, zLocal - (dims.baseElevation ?? 6.0));
  return [x, y, z];
}
