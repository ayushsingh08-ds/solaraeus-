export function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

export function radToDeg(rad: number): number {
  return (rad * 180) / Math.PI;
}

/**
 * Converts solar altitude and azimuth (in degrees) to a 3D unit direction vector [x, y, z].
 * In Three.js: X = East, Y = Up (Elevation), Z = South.
 * Solar Azimuth convention: 0° = North, 90° = East, 180° = South, 270° = West.
 */
export function sunPositionToVector(
  altDeg: number,
  azDeg: number,
  distance: number = 250
): [number, number, number] {
  const altRad = degToRad(Math.max(0.1, altDeg));
  const azRad = degToRad(azDeg);

  // In our local 3D frame:
  // X = East = sin(az) * cos(alt)
  // Z = South (pointing opposite to North) = -cos(az) * cos(alt)
  // Y = Up = sin(alt)
  const x = Math.sin(azRad) * Math.cos(altRad) * distance;
  const y = Math.sin(altRad) * distance;
  const z = -Math.cos(azRad) * Math.cos(altRad) * distance;

  return [x, y, z];
}
