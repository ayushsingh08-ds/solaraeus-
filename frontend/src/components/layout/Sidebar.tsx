import React from 'react';
import {
  Building2,
  Camera,
  Eye,
  Flame,
  Footprints,
  Pause,
  Play,
  Sliders,
  Sun,
  Thermometer,
  Trees,
} from 'lucide-react';
import { useTimeline } from '../../hooks/useTimeline';
import { useAppStore } from '../../stores/appStore';
import { formatPercent, formatTemp, formatTime } from '../../utils/formatters';
import { Colorbar } from './Colorbar';

export const Sidebar: React.FC = () => {
  const {
    currentMetrics,
    layerOpacity,
    setLayerOpacity,
    showBuildings,
    setShowBuildings,
    showSunIndicator,
    setShowSunIndicator,
    isWireframe,
    setIsWireframe,
    avatarMode,
    setAvatarMode,
    cameraMode,
    setCameraMode,
    avatarSpeed,
    setAvatarSpeed,
    avatarPosition,
  } = useAppStore();

  const {
    currentUtcTime,
    setCurrentUtcTime,
    isPlayingTimeline,
    togglePlay,
    availableTimes,
  } = useTimeline();

  // Microclimate statistics
  const tmrtSunlitMean = currentMetrics.tmrt ? currentMetrics.tmrt.vmax * 0.78 : 57.5;
  const utciSunlitMean = currentMetrics.utci ? currentMetrics.utci.vmax * 0.82 : 39.6;

  return (
    <aside className="sidebar-container">
      {/* 1. Diurnal Timeline Section */}
      <section className="sidebar-section timeline-section">
        <div className="section-header">
          <span className="section-title">DIURNAL SIMULATION SCRUBBER</span>
          <span className="section-badge">{formatTime(currentUtcTime)}</span>
        </div>

        <div className="timeline-controls">
          <button
            className={`play-btn ${isPlayingTimeline ? 'playing' : ''}`}
            onClick={togglePlay}
            title={isPlayingTimeline ? 'Pause Diurnal Animation' : 'Play Diurnal Animation'}
          >
            {isPlayingTimeline ? <Pause size={16} /> : <Play size={16} />}
            <span>{isPlayingTimeline ? 'Pause' : 'Play'}</span>
          </button>

          <div className="time-select-group">
            {availableTimes.map((t) => (
              <button
                key={t.utc}
                className={`time-chip ${currentUtcTime === t.utc ? 'active' : ''}`}
                onClick={() => setCurrentUtcTime(t.utc)}
              >
                {t.local.replace(' EDT', '')}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* 2. Avatar Walk Mode Controller */}
      <section className={`sidebar-section avatar-section ${avatarMode ? 'active-mode' : ''}`}>
        <div className="section-header">
          <span className="section-title">
            <Footprints size={15} />
            <span>3D PEDESTRIAN AVATAR</span>
          </span>
          <button
            className={`mode-toggle-btn ${avatarMode ? 'active' : ''}`}
            onClick={() => setAvatarMode(!avatarMode)}
          >
            {avatarMode ? 'ON' : 'OFF'}
          </button>
        </div>

        {avatarMode ? (
          <div className="avatar-panel-body">
            <div className="control-row">
              <span className="control-label">Perspective:</span>
              <div className="btn-toggle-group">
                <button
                  className={`toggle-sub-btn ${cameraMode === 'third-person' ? 'active' : ''}`}
                  onClick={() => setCameraMode('third-person')}
                >
                  <Camera size={13} />
                  <span>3rd Person</span>
                </button>
                <button
                  className={`toggle-sub-btn ${cameraMode === 'first-person' ? 'active' : ''}`}
                  onClick={() => setCameraMode('first-person')}
                >
                  <Eye size={13} />
                  <span>1st Person</span>
                </button>
              </div>
            </div>

            <div className="control-row slider-row">
              <span className="control-label">Walk Speed: {avatarSpeed.toFixed(1)} m/s</span>
              <input
                type="range"
                min="1.0"
                max="5.0"
                step="0.5"
                value={avatarSpeed}
                onChange={(e) => setAvatarSpeed(parseFloat(e.target.value))}
                className="custom-range"
              />
            </div>

            <div className="avatar-pos-info">
              <span>Pos: [X: {avatarPosition[0].toFixed(1)}m, Z: {avatarPosition[2].toFixed(1)}m]</span>
              <span>Elevation: {avatarPosition[1].toFixed(1)}m ASL</span>
            </div>

            <div className="sidebar-teleport-row">
              <span className="control-label">Quick Teleport:</span>
              <div className="teleport-mini-chips">
                <button
                  className="mini-chip"
                  onClick={() => useAppStore.getState().teleportAvatar([-27, 3.0, 13], 0)}
                  title="Washington Square Park Fountain Center"
                >
                  ⛲ Fountain
                </button>
                <button
                  className="mini-chip"
                  onClick={() => useAppStore.getState().teleportAvatar([-27, 2.5, -61], 0)}
                  title="Washington Arch"
                >
                  🏛️ Arch
                </button>
                <button
                  className="mini-chip"
                  onClick={() => useAppStore.getState().teleportAvatar([80, 5.0, 13], -Math.PI / 2)}
                  title="East Building Shaded Canyon"
                >
                  🏢 Canyon
                </button>
                <button
                  className="mini-chip"
                  onClick={() => useAppStore.getState().teleportAvatar([-27, 3.8, 74], 0)}
                  title="South Tree Lawn Area"
                >
                  🌳 Lawn
                </button>
              </div>
            </div>
          </div>
        ) : (
          <p className="avatar-prompt-hint">
            Enable 3D Walk Mode to explore Washington Square Park with a pedestrian avatar, WASD navigation, and live comfort HUD.
          </p>
        )}
      </section>

      {/* 3. Microclimate Summary Metrics */}
      <section className="sidebar-section stats-section">
        <div className="section-header">
          <span className="section-title">MICROCLIMATE SNAPSHOT</span>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-card-icon tmrt-icon">
              <Flame size={16} />
            </div>
            <div className="stat-card-content">
              <span className="stat-label">Sunlit Mean Tmrt</span>
              <span className="stat-val">{formatTemp(tmrtSunlitMean)}</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon utci-icon">
              <Thermometer size={16} />
            </div>
            <div className="stat-card-content">
              <span className="stat-label">Sunlit Mean UTCI</span>
              <span className="stat-val highlight-red">{formatTemp(utciSunlitMean)}</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon sun-icon">
              <Sun size={16} />
            </div>
            <div className="stat-card-content">
              <span className="stat-label">Walkable Sunlit</span>
              <span className="stat-val">{formatPercent(70.1)}</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon contrast-icon">
              <Trees size={16} />
            </div>
            <div className="stat-card-content">
              <span className="stat-label">Shade ΔTmrt Cooling</span>
              <span className="stat-val highlight-green">-14.7 °C</span>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Scene & Display Settings */}
      <section className="sidebar-section scene-controls-section">
        <div className="section-header">
          <span className="section-title">
            <Sliders size={14} />
            <span>RENDER CONTROLS</span>
          </span>
        </div>

        <div className="control-row slider-row">
          <span className="control-label">Heatmap Opacity: {Math.round(layerOpacity * 100)}%</span>
          <input
            type="range"
            min="0.2"
            max="1.0"
            step="0.05"
            value={layerOpacity}
            onChange={(e) => setLayerOpacity(parseFloat(e.target.value))}
            className="custom-range"
          />
        </div>

        <div className="toggle-switches-list">
          <label className="toggle-switch-label">
            <Building2 size={15} />
            <span>3D Watertight Buildings</span>
            <input
              type="checkbox"
              checked={showBuildings}
              onChange={(e) => setShowBuildings(e.target.checked)}
            />
          </label>

          <label className="toggle-switch-label">
            <Sun size={15} />
            <span>Sun Indicator & Lighting</span>
            <input
              type="checkbox"
              checked={showSunIndicator}
              onChange={(e) => setShowSunIndicator(e.target.checked)}
            />
          </label>

          <label className="toggle-switch-label">
            <span>Wireframe Mode</span>
            <input
              type="checkbox"
              checked={isWireframe}
              onChange={(e) => setIsWireframe(e.target.checked)}
            />
          </label>
        </div>
      </section>

      {/* 5. Color Scale Legend */}
      <section className="sidebar-section colorbar-section">
        <Colorbar />
      </section>
    </aside>
  );
};
