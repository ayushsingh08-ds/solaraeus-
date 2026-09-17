import React from 'react';
import { useAvatarComfort } from '../../hooks/useAvatarComfort';
import { useAvatarMovement } from '../../hooks/useAvatarMovement';
import { useSimulationData } from '../../hooks/useSimulationData';
import { MapViewport } from '../map/MapViewport';
import { TopBar } from './TopBar';

export const AppShell: React.FC = () => {
  // Initialize simulation data bootstrapping
  useSimulationData();

  // Initialize avatar hooks
  useAvatarMovement();
  useAvatarComfort();

  return (
    <div className="app-shell-root">
      {/* Top Application Bar */}
      <TopBar />

      {/* Main Workspace Body: Fullscreen Borderless 3D Digital Twin */}
      <main className="app-main-body">
        <MapViewport />
      </main>
    </div>
  );
};

