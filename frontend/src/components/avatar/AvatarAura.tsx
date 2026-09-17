import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface AvatarAuraProps {
  color?: string;
  radius?: number;
}

export const AvatarAura: React.FC<AvatarAuraProps> = ({
  color = '#38bdf8',
  radius = 1.4,
}) => {
  const ringRef = useRef<THREE.Mesh>(null);
  const discRef = useRef<THREE.Mesh>(null);

  // Subtle rhythmic pulse animation showing live thermal sensor presence
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ringRef.current) {
      const scale = 1 + Math.sin(t * 3.5) * 0.06;
      ringRef.current.scale.set(scale, scale, 1);
      ringRef.current.rotation.z = t * 0.2;
    }
    if (discRef.current) {
      const scale = 1 + Math.cos(t * 2.5) * 0.08;
      discRef.current.scale.set(scale, scale, 1);
    }
  });

  return (
    <group position={[0, 0.06, 0]}>
      {/* Primary dynamic stress ring */}
      <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[radius * 0.75, radius, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.7} side={THREE.DoubleSide} />
      </mesh>

      {/* Ambient thermal footprint halo */}
      <mesh ref={discRef} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[radius * 1.5, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.18} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
};
