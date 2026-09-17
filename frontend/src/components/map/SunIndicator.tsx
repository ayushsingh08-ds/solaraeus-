import React, { useMemo } from 'react';
import { sunPositionToVector } from '../../utils/math';

interface SunIndicatorProps {
  altDeg?: number;
  azDeg?: number;
}

export const SunIndicator: React.FC<SunIndicatorProps> = ({
  altDeg = 67.15,
  azDeg = 142.83,
}) => {
  const sunPos = useMemo(() => {
    return sunPositionToVector(altDeg, azDeg, 280);
  }, [altDeg, azDeg]);

  // Sunlight intensity scales with solar altitude
  const intensity = useMemo(() => {
    const sinAlt = Math.sin((Math.max(0, altDeg) * Math.PI) / 180);
    return Math.max(0.2, sinAlt * 2.2);
  }, [altDeg]);

  return (
    <group>
      {/* Sun Directional Light with real-time shadow casting */}
      <directionalLight
        position={sunPos}
        intensity={intensity * 1.3}
        color="#fffbf0"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-near={10}
        shadow-camera-far={650}
        shadow-camera-left={-320}
        shadow-camera-right={320}
        shadow-camera-top={350}
        shadow-camera-bottom={-350}
        shadow-bias={-0.0004}
      />

      {/* Radiant Core Focal Hotspot (Reference 1) */}
      <mesh position={sunPos}>
        <sphereGeometry args={[9, 24, 24]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>

      {/* Radiant Solar Corona Halo (Golden Inner) */}
      <mesh position={sunPos}>
        <sphereGeometry args={[16, 24, 24]} />
        <meshBasicMaterial color="#f59e0b" transparent opacity={0.55} />
      </mesh>

      {/* Radiant Solar Atmospheric Corona (Solar Orange Outer Halo) */}
      <mesh position={sunPos}>
        <sphereGeometry args={[26, 24, 24]} />
        <meshBasicMaterial color="#ff7a00" transparent opacity={0.25} />
      </mesh>
    </group>
  );
};

