import React, { useMemo } from 'react';
import * as THREE from 'three';

interface AtmosphericSkyProps {
  altDeg?: number;
  azDeg?: number;
}

export const AtmosphericSky: React.FC<AtmosphericSkyProps> = ({
  altDeg = 67.15,
}) => {


  // Porcelain White Architectural Atmosphere (Reference 1 & 2)
  // Replaces dark murky fog with crisp misty miniature studio depth
  const { skyColor, groundColor, fogColor } = useMemo(() => {
    const clampedAlt = Math.max(0, altDeg);

    if (clampedAlt < 20) {
      // Golden dawn / twilight glow
      return {
        skyColor: new THREE.Color('#fff7ed'),
        groundColor: new THREE.Color('#e2e8f0'),
        fogColor: '#f1f5f9',
      };
    } else {
      // Clean pristine architectural daylight
      return {
        skyColor: new THREE.Color('#ffffff'),
        groundColor: new THREE.Color('#cbd5e1'),
        fogColor: '#f8fafc',
      };
    }
  }, [altDeg]);

  return (
    <>
      {/* 1. Pure Studio Clear Color */}
      <color attach="background" args={[fogColor]} />

      {/* 2. Diurnal Ambient & Sky Bounce Lighting for crisp architectural clay */}
      <ambientLight intensity={0.72} color="#ffffff" />
      <hemisphereLight
        args={[skyColor, groundColor, 0.45]}
        position={[0, 400, 0]}
      />

      {/* 3. Misty Architectural Studio Fog (Reference 1) */}
      <fog attach="fog" args={[fogColor, 380, 1150]} />
    </>
  );
};

