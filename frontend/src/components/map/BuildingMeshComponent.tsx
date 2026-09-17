import React, { useMemo } from 'react';
import * as THREE from 'three';
import type { BuildingMesh } from '../../api/types';
import { buildingVertexToWorld } from '../../utils/geoTransform';

interface BuildingMeshProps {
  meshData: BuildingMesh;
  isWireframe?: boolean;
}

export const BuildingMeshComponent: React.FC<BuildingMeshProps> = ({
  meshData,
  isWireframe = false,
}) => {
  const geometry = useMemo(() => {
    if (!meshData || !meshData.vertices || meshData.vertices.length === 0) {
      return null;
    }

    const geom = new THREE.BufferGeometry();
    const numVerts = meshData.numVertices;
    const posArray = new Float32Array(numVerts * 3);

    for (let i = 0; i < numVerts; i++) {
      const [wx, wy, wz] = buildingVertexToWorld(
        meshData.vertices[3 * i],
        meshData.vertices[3 * i + 1],
        meshData.vertices[3 * i + 2],
        { rows: 673, cols: 599, baseElevation: 6.0 }
      );
      posArray[3 * i] = wx;
      posArray[3 * i + 1] = wy;
      posArray[3 * i + 2] = wz;
    }

    geom.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    geom.setIndex(meshData.faces);
    geom.computeVertexNormals();

    return geom;
  }, [meshData]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#ffffff"
        roughness={0.4}
        metalness={0.03}
        wireframe={isWireframe}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
};

