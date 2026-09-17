import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { useAppStore } from '../../stores/appStore';
import { AvatarAura } from './AvatarAura';

export const PedestrianAvatar: React.FC = () => {
  const {
    avatarMode,
    cameraMode,
    avatarPosition,
    avatarHeading,
    avatarComfort,
  } = useAppStore();

  const groupRef = useRef<THREE.Group>(null);
  const targetCamPos = useRef(new THREE.Vector3());
  const lookTarget = useRef(new THREE.Vector3());

  // Camera Follow Rig (Third-person follow or First-person eye-level)
  useFrame(({ camera }) => {
    if (!avatarMode) return;

    const [x, y, z] = avatarPosition;

    if (cameraMode === 'third-person') {
      // Third person follow camera smoothly orbiting behind avatar
      const distBehind = 7.2;
      const heightAbove = 3.6;

      const camX = x - Math.sin(avatarHeading) * distBehind;
      const camZ = z + Math.cos(avatarHeading) * distBehind;
      const camY = y + heightAbove;

      targetCamPos.current.set(camX, camY, camZ);
      lookTarget.current.set(x, y + 1.25, z);

      // Smooth camera interpolation
      camera.position.lerp(targetCamPos.current, 0.12);
      camera.lookAt(lookTarget.current);
    } else {
      // First person eye-level view
      const eyeHeight = 1.65;
      camera.position.set(x, y + eyeHeight, z);

      // Look along avatar heading
      lookTarget.current.set(
        x + Math.sin(avatarHeading) * 20,
        y + eyeHeight,
        z - Math.cos(avatarHeading) * 20
      );
      camera.lookAt(lookTarget.current);
    }
  });

  if (!avatarMode) return null;

  const [x, y, z] = avatarPosition;
  const stressColor = avatarComfort?.stressColor || '#38bdf8';
  const isSunlit = avatarComfort?.isSunlit ?? true;

  return (
    <group ref={groupRef} position={[x, y, z]} rotation={[0, avatarHeading, 0]}>
      {/* 1. Footprint Comfort Aura Ring */}
      <AvatarAura color={stressColor} radius={1.4} />

      {/* 2. Stylized Humanoid Mannequin Mesh (Visible in Third-Person) */}
      {cameraMode === 'third-person' && (
        <group>
          {/* Floating overhead 3D indicator tag */}
          <Html position={[0, 2.05, 0]} center distanceFactor={30}>
            <div className="avatar-overhead-tag" style={{ borderColor: stressColor }}>
              <span className="dot" style={{ backgroundColor: stressColor }} />
              <span>
                {avatarComfort
                  ? `${avatarComfort.utci.toFixed(1)}°C (${isSunlit ? 'Sun' : 'Shade'})`
                  : 'Pedestrian'}
              </span>
            </div>
          </Html>

          {/* Torso */}
          <mesh position={[0, 0.95, 0]} castShadow>
            <boxGeometry args={[0.42, 0.65, 0.26]} />
            <meshStandardMaterial color="#0284c7" roughness={0.3} metalness={0.2} />
          </mesh>

          {/* Microclimate Telemetry Sensor Backpack */}
          <mesh position={[0, 0.96, 0.17]} castShadow>
            <boxGeometry args={[0.26, 0.38, 0.14]} />
            <meshStandardMaterial color="#0f172a" roughness={0.6} metalness={0.5} />
          </mesh>
          <mesh position={[0, 1.05, 0.24]}>
            <boxGeometry args={[0.06, 0.06, 0.03]} />
            <meshBasicMaterial color={stressColor} />
          </mesh>

          {/* Head & Protective Visor */}
          <mesh position={[0, 1.45, 0]} castShadow>
            <sphereGeometry args={[0.18, 16, 16]} />
            <meshStandardMaterial color="#e0f2fe" roughness={0.1} metalness={0.8} />
          </mesh>

          {/* Visor glowing strip */}
          <mesh position={[0, 1.46, -0.16]}>
            <boxGeometry args={[0.22, 0.07, 0.05]} />
            <meshBasicMaterial color={stressColor} />
          </mesh>

          {/* Left & Right Legs */}
          <mesh position={[-0.12, 0.32, 0]} castShadow>
            <boxGeometry args={[0.14, 0.64, 0.16]} />
            <meshStandardMaterial color="#1e293b" roughness={0.5} />
          </mesh>
          <mesh position={[0.12, 0.32, 0]} castShadow>
            <boxGeometry args={[0.14, 0.64, 0.16]} />
            <meshStandardMaterial color="#1e293b" roughness={0.5} />
          </mesh>

          {/* Left & Right Arms */}
          <mesh position={[-0.28, 0.95, 0]} castShadow>
            <boxGeometry args={[0.11, 0.58, 0.14]} />
            <meshStandardMaterial color="#0284c7" roughness={0.4} />
          </mesh>
          <mesh position={[0.28, 0.95, 0]} castShadow>
            <boxGeometry args={[0.11, 0.58, 0.14]} />
            <meshStandardMaterial color="#0284c7" roughness={0.4} />
          </mesh>
        </group>
      )}
    </group>
  );
};
