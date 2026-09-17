import React from 'react';
import { Canvas } from '@react-three/fiber';
import { Loader, Move3d } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { formatTemp } from '../../utils/formatters';
import { AvatarComfortHUD } from '../avatar/AvatarComfortHUD';
import { AvatarControls } from '../avatar/AvatarControls';
import { ThermalVignette } from '../effects/ThermalVignette';
import { FloatingBottomDock } from '../layout/FloatingBottomDock';
import { FloatingLeftPanel } from '../layout/FloatingLeftPanel';
import { Map3D } from './Map3D';

export const MapViewport: React.FC = () => {
  const {
    isLoading,
    error,
    hoveredCell,
    avatarMode,
  } = useAppStore();

  return (
    <div className="map-viewport-container">
      {/* 3D React Three Fiber Canvas with Dynamic Atmospheric Sky */}
      <Canvas
        shadows
        camera={{ position: [0, 220, 280], fov: 48, near: 1, far: 2000 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <Map3D />
      </Canvas>

      {/* Somatic Thermal Feedback Screen Vignette (Phase 1) */}
      <ThermalVignette />

      {/* Floating Left Analytics Card (Reference 4) */}
      <FloatingLeftPanel />

      {/* Floating Bottom Control Dock with Scrubber & D-Pad (Reference 4) */}
      <FloatingBottomDock />

      {/* Floating Walk Mode Avatar HUD & Virtual Controls */}
      {avatarMode && (
        <div className="viewport-overlay-hud">
          <AvatarComfortHUD />
          <AvatarControls />
        </div>
      )}

      {/* Hover Inspection Tooltip */}
      {!avatarMode && hoveredCell && (
        <div className="viewport-inspection-badge">
          <div className="inspection-title">SURFACE INSPECTION</div>
          <div className="inspection-row">
            <span>Coordinate:</span>
            <b>[R: {hoveredCell.row}, C: {hoveredCell.col}]</b>
          </div>
          <div className="inspection-row">
            <span>{hoveredCell.metric.toUpperCase()}:</span>
            <b className="highlight-text">
              {['tmrt', 'utci'].includes(hoveredCell.metric)
                ? formatTemp(hoveredCell.val)
                : hoveredCell.metric === 'shadows'
                ? hoveredCell.val === 1 ? '☀️ Sunlit' : '🕶️ Shaded'
                : hoveredCell.metric === 'svf'
                ? hoveredCell.val.toFixed(3)
                : `${hoveredCell.val.toFixed(1)} m`}
            </b>
          </div>
        </div>
      )}

      {/* Scene Navigation Hint (Orbit Mode) */}
      {!avatarMode && (
        <div className="viewport-orbit-hint">
          <Move3d size={13} />
          <span>Left click + drag to rotate • Right click to pan • Scroll to zoom</span>
        </div>
      )}

      {/* Loading & Error Overlays */}
      {isLoading && (
        <div className="viewport-loading-overlay">
          <Loader className="spin-icon" size={32} />
          <p>Synthesizing Washington Square Park Microclimate...</p>
        </div>
      )}

      {error && (
        <div className="viewport-error-banner">
          <p>⚠️ {error}</p>
        </div>
      )}
    </div>
  );
};
