import React, { useEffect, useMemo, useRef } from 'react';
import { OrbitControls } from '@react-three/drei';
import { useThree } from '@react-three/fiber';
import { useAppStore } from '../../stores/appStore';
import { worldToGrid } from '../../utils/geoTransform';
import { PedestrianAvatar } from '../avatar/PedestrianAvatar';
import { AtmosphericSky } from './AtmosphericSky';
import { BuildingMeshComponent } from './BuildingMeshComponent';
import { GroundHeatmap } from './GroundHeatmap';
import { SunIndicator } from './SunIndicator';

export const Map3D: React.FC = () => {
  const { camera } = useThree();
  const controlsRef = useRef<any>(null);

  const {
    currentMetrics,
    activeLayer,
    layerOpacity,
    showBuildings,
    showSunIndicator,
    isWireframe,
    buildingMesh,
    avatarMode,
    setHoveredCell,
  } = useAppStore();

  // Listen for navigation D-pad and camera preset events from floating UI
  useEffect(() => {
    const handleNudge = (e: any) => {
      if (!controlsRef.current || avatarMode) return;
      const { dir } = e.detail || {};

      if (dir === 'left') {
        const x = camera.position.x;
        const z = camera.position.z;
        const angle = 0.2;
        camera.position.x = x * Math.cos(angle) - z * Math.sin(angle);
        camera.position.z = x * Math.sin(angle) + z * Math.cos(angle);
      } else if (dir === 'right') {
        const x = camera.position.x;
        const z = camera.position.z;
        const angle = -0.2;
        camera.position.x = x * Math.cos(angle) - z * Math.sin(angle);
        camera.position.z = x * Math.sin(angle) + z * Math.cos(angle);
      } else if (dir === 'up') {
        camera.position.y = Math.min(camera.position.y + 35, 480);
      } else if (dir === 'down') {
        camera.position.y = Math.max(camera.position.y - 35, 40);
      }
      camera.lookAt(0, 5, 0);
      controlsRef.current.update();
    };

    const handleReset = () => {
      if (avatarMode) return;
      camera.position.set(0, 220, 280);
      camera.lookAt(0, 5, 0);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 5, 0);
        controlsRef.current.update();
      }
    };

    const handleTopDown = () => {
      if (avatarMode) return;
      camera.position.set(0, 500, 1);
      camera.lookAt(0, 0, 0);
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
        controlsRef.current.update();
      }
    };

    window.addEventListener('map-camera-nudge', handleNudge);
    window.addEventListener('map-camera-reset', handleReset);
    window.addEventListener('map-camera-topdown', handleTopDown);

    return () => {
      window.removeEventListener('map-camera-nudge', handleNudge);
      window.removeEventListener('map-camera-reset', handleReset);
      window.removeEventListener('map-camera-topdown', handleTopDown);
    };
  }, [camera, avatarMode]);


  const activeMetricData = currentMetrics[activeLayer];

  // Palette selection matching metric
  const paletteName = useMemo(() => {
    switch (activeLayer) {
      case 'tmrt':
        return 'magma';
      case 'utci':
        return 'utci';
      case 'svf':
        return 'cividis';
      case 'dsm':
        return 'viridis';
      case 'shadows':
        return 'shadows';
      default:
        return 'magma';
    }
  }, [activeLayer]);

  // Solar angles from current time-varying metrics
  const solarAlt = currentMetrics.shadows?.solarAltitudeDeg ?? 67.15;
  const solarAz = currentMetrics.shadows?.solarAzimuthDeg ?? 142.83;

  // Hover raycast handling on the ground plane
  const handlePointerMove = (e: any) => {
    if (avatarMode || !activeMetricData) return;
    e.stopPropagation();

    const pt = e.point;
    const [row, col] = worldToGrid(pt.x, pt.z, {
      rows: activeMetricData.shape[0],
      cols: activeMetricData.shape[1],
    });

    const val = activeMetricData.values[row]?.[col];
    if (val !== undefined) {
      setHoveredCell({
        row,
        col,
        val,
        metric: activeLayer,
      });
    }
  };

  const handlePointerOut = () => {
    if (!avatarMode) {
      setHoveredCell(null);
    }
  };

  return (
    <>
      {/* Dynamic Celestial Sky & Diurnal Environmental Lighting (Phase 1) */}
      <AtmosphericSky altDeg={solarAlt} azDeg={solarAz} />

      {/* Sun Indicator & Dynamic Directional Sun Light */}
      {showSunIndicator && (
        <SunIndicator altDeg={solarAlt} azDeg={solarAz} />
      )}

      {/* Ground Heatmap Mesh */}
      <group onPointerMove={handlePointerMove} onPointerOut={handlePointerOut}>
        <GroundHeatmap
          metricData={activeMetricData}
          paletteName={paletteName}
          opacity={layerOpacity}
        />
      </group>

      {/* 3D Extruded Buildings */}
      {showBuildings && buildingMesh && (
        <BuildingMeshComponent
          meshData={buildingMesh}
          isWireframe={isWireframe}
        />
      )}

      {/* 3D Pedestrian Avatar (Active in Walk Mode) */}
      <PedestrianAvatar />

      {/* Camera Orbit Controls (Disabled during Avatar Walk Mode) */}
      {!avatarMode && (
        <OrbitControls
          ref={controlsRef}
          makeDefault
          enableDamping
          dampingFactor={0.06}
          maxPolarAngle={Math.PI / 2 - 0.05} // Do not clip under ground
          minDistance={15}
          maxDistance={850}
          target={[0, 5, 0]}
        />
      )}


      {/* Studio Porcelain Base Table (Reference 1 & 2) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]} receiveShadow>
        <planeGeometry args={[1800, 1800]} />
        <meshStandardMaterial color="#f8fafc" roughness={0.9} metalness={0.02} />
      </mesh>

      {/* Spatial Cartesian Architectural CAD Grid (Reference 2) */}
      <gridHelper
        args={[700, 70, '#cbd5e1', '#e2e8f0']}
        position={[0, -0.05, 0]}
      />
    </>
  );
};

