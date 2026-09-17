import React, { useMemo } from 'react';
import * as THREE from 'three';
import type { MetricData } from '../../api/types';
import { getColorRGB } from '../../utils/colorScales';

interface GroundHeatmapProps {
  metricData: MetricData | null;
  paletteName?: string;
  opacity?: number;
}

export const GroundHeatmap: React.FC<GroundHeatmapProps> = ({
  metricData,
  paletteName = 'magma',
  opacity = 0.9,
}) => {
  const texture = useMemo(() => {
    if (!metricData || !metricData.values || metricData.values.length === 0) {
      return null;
    }

    const rows = metricData.shape[0];
    const cols = metricData.shape[1];
    const data = new Uint8Array(rows * cols * 4);

    const vmin = metricData.vmin;
    const vmax = metricData.vmax;

    let ptr = 0;
    // Row 0 is North (top of map). In Three.js DataTexture, row 0 is at bottom unless flipped.
    // We iterate from row 0 to rows - 1 and set flipY = false so row 0 is at -Z (North).
    for (let r = 0; r < rows; r++) {
      const rowVals = metricData.values[r];
      for (let c = 0; c < cols; c++) {
        const val = rowVals ? rowVals[c] : 0;
        const [red, green, blue] = getColorRGB(val, vmin, vmax, paletteName);

        data[ptr] = red;
        data[ptr + 1] = green;
        data[ptr + 2] = blue;
        data[ptr + 3] = 255;
        ptr += 4;
      }
    }

    const tex = new THREE.DataTexture(
      data,
      cols,
      rows,
      THREE.RGBAFormat,
      THREE.UnsignedByteType
    );
    tex.magFilter = THREE.LinearFilter;
    tex.minFilter = THREE.LinearFilter;
    tex.generateMipmaps = false;
    tex.flipY = true; // Flips so row 0 is at top (-Z)
    tex.needsUpdate = true;

    return tex;
  }, [metricData, paletteName]);

  if (!texture || !metricData) return null;

  const width = metricData.shape[1];  // 599m
  const height = metricData.shape[0]; // 673m

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]} receiveShadow>
      <planeGeometry args={[width, height]} />
      <meshStandardMaterial
        map={texture}
        transparent
        opacity={opacity}
        roughness={0.8}
        metalness={0.05}
      />
    </mesh>
  );
};
