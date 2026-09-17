import React, { useState } from 'react';
import {
  Camera,
  Eye,
  Flame,
  Footprints,
  MapPin,
  Maximize2,
  ShieldAlert,
  Sun,
  Trees,
  TrendingUp,
} from 'lucide-react';
import { useTimeline } from '../../hooks/useTimeline';
import { useAppStore } from '../../stores/appStore';
import { formatTemp } from '../../utils/formatters';
import { Colorbar } from './Colorbar';


type TabType = 'thermal' | 'solar' | 'zones' | 'avatar';

export const FloatingLeftPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('thermal');
  const [isCollapsed, setIsCollapsed] = useState(false);

  const {
    activeLayer,
    currentMetrics,
    avatarMode,
    setAvatarMode,
    cameraMode,
    setCameraMode,
    avatarSpeed,
    setAvatarSpeed,
    avatarPosition,
    teleportAvatar,
  } = useAppStore();

  const {
    currentUtcTime,
    setCurrentUtcTime,
    availableTimes,
  } = useTimeline();

  // Microclimate statistics
  const tmrtSunlitMean = currentMetrics.tmrt ? currentMetrics.tmrt.vmax * 0.78 : 57.5;
  const utciSunlitMean = currentMetrics.utci ? currentMetrics.utci.vmax * 0.82 : 39.6;
  const solarAlt = currentMetrics.shadows?.solarAltitudeDeg ?? 67.2;
  const solarAz = currentMetrics.shadows?.solarAzimuthDeg ?? 142.8;

  // Diurnal sample curve data for the micro-bar chart
  const diurnalHourlyCurve = [
    { hour: '06:00', utc: '2026-06-21T10:00:00Z', val: 24.2, heightPercent: 25 },
    { hour: '07:00', utc: '2026-06-21T11:00:00Z', val: 27.5, heightPercent: 35 },
    { hour: '08:00', utc: '2026-06-21T12:00:00Z', val: 32.1, heightPercent: 50 },
    { hour: '09:00', utc: '2026-06-21T13:00:00Z', val: 37.8, heightPercent: 68 },
    { hour: '10:00', utc: '2026-06-21T14:00:00Z', val: 43.4, heightPercent: 82 },
    { hour: '11:00', utc: '2026-06-21T15:00:00Z', val: 48.9, heightPercent: 92 },
    { hour: '12:00', utc: '2026-06-21T16:00:00Z', val: 52.6, heightPercent: 98 },
    { hour: '13:00', utc: '2026-06-21T17:00:00Z', val: 55.4, heightPercent: 100 },
    { hour: '14:00', utc: '2026-06-21T18:00:00Z', val: 57.5, heightPercent: 99 },
    { hour: '15:00', utc: '2026-06-21T19:00:00Z', val: 54.2, heightPercent: 94 },
    { hour: '16:00', utc: '2026-06-21T20:00:00Z', val: 49.1, heightPercent: 84 },
    { hour: '17:00', utc: '2026-06-21T21:00:00Z', val: 42.0, heightPercent: 66 },
    { hour: '18:00', utc: '2026-06-21T22:00:00Z', val: 34.3, heightPercent: 48 },
    { hour: '19:00', utc: '2026-06-21T23:00:00Z', val: 26.8, heightPercent: 30 },
  ];

  const currentHourString = currentUtcTime.slice(11, 16);

  return (
    <div className={`floating-left-card ${isCollapsed ? 'collapsed' : ''}`}>
      {/* 1. Header Bar with Category Pill Tabs & Collapse Toggle */}
      <div className="card-header-bar">
        <div className="tab-pills-row">
          <button
            className={`tab-pill-btn ${activeTab === 'thermal' ? 'active' : ''}`}
            onClick={() => setActiveTab('thermal')}
          >
            <Flame size={13} />
            <span>Thermal</span>
          </button>

          <button
            className={`tab-pill-btn ${activeTab === 'solar' ? 'active' : ''}`}
            onClick={() => setActiveTab('solar')}
          >
            <Sun size={13} />
            <span>Solar & SVF</span>
          </button>

          <button
            className={`tab-pill-btn ${activeTab === 'zones' ? 'active' : ''}`}
            onClick={() => setActiveTab('zones')}
          >
            <MapPin size={13} />
            <span>Zones</span>
          </button>

          <button
            className={`tab-pill-btn ${activeTab === 'avatar' ? 'active' : ''}`}
            onClick={() => setActiveTab('avatar')}
          >
            <Footprints size={13} />
            <span>Walk</span>
          </button>
        </div>

        <button
          className="collapse-toggle-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand Panel' : 'Collapse Panel'}
        >
          <Maximize2 size={13} />
        </button>
      </div>

      {!isCollapsed && (
        <div className="card-content-body">
          {/* TAB 1: THERMAL DYNAMICS */}
          {activeTab === 'thermal' && (
            <div className="tab-pane">
              {/* Hero Metric Headline (Reference 4) */}
              <div className="hero-metric-box">
                <div className="hero-eyebrow">
                  <TrendingUp size={13} className="hero-icon" />
                  <span>WASHINGTON SQUARE PARK • PEAK RADIANT LOAD</span>
                </div>
                <div className="hero-headline-row">
                  <span className="hero-number">{formatTemp(tmrtSunlitMean)}</span>
                  <div className="hero-tag orange-tag">
                    <span>+14.7°C</span>
                    <span className="sub-text">vs shade</span>
                  </div>
                </div>
                <div className="hero-caption">
                  Active Metric: <b>{activeLayer.toUpperCase()}</b> • Diurnal Solar Peak at 2:00 PM EDT
                </div>
              </div>

              {/* Diurnal Micro-bar Chart (Reference 4) */}
              <div className="micro-chart-section">
                <div className="chart-header">
                  <span className="chart-title">DIURNAL RADIATION PROFILE (EDT)</span>
                  <span className="chart-status-chip">PEAK FLUX</span>
                </div>

                <div className="micro-bars-container">
                  {diurnalHourlyCurve.map((item) => {
                    const isActive = currentHourString.startsWith(item.hour.slice(0, 2));
                    return (
                      <div
                        key={item.hour}
                        className={`micro-bar-col ${isActive ? 'active' : ''}`}
                        onClick={() => {
                          const matchedTime = availableTimes.find((t) => t.utc === item.utc);
                          if (matchedTime) setCurrentUtcTime(matchedTime.utc);
                        }}
                        title={`${item.hour} EDT: ${item.val}°C`}
                      >
                        <div
                          className="micro-bar-fill"
                          style={{ height: `${item.heightPercent}%` }}
                        />
                        <span className="micro-bar-label">{item.hour.slice(0, 2)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Thermal Risk Alert Badges (Reference 4) */}
              <div className="risk-alerts-section">
                <div className="risk-alert-card warning">
                  <div className="alert-icon-col">
                    <ShieldAlert size={16} />
                  </div>
                  <div className="alert-details">
                    <div className="alert-title-row">
                      <span className="alert-title">Strong Heat Stress Alert</span>
                      <span className="alert-badge">{formatTemp(utciSunlitMean)}</span>
                    </div>
                    <p className="alert-desc">
                      Central Fountain Plaza unshaded pavement exceeds 38°C UTCI threshold.
                    </p>
                  </div>
                </div>

                <div className="risk-alert-card cooling">
                  <div className="alert-icon-col">
                    <Trees size={16} />
                  </div>
                  <div className="alert-details">
                    <div className="alert-title-row">
                      <span className="alert-title">Canopy Shade Oasis</span>
                      <span className="alert-badge green-badge">-14.7 °C ΔTmrt</span>
                    </div>
                    <p className="alert-desc">
                      Southwest tree grove maintains resilient comfort zone (24.8°C UTCI).
                    </p>
                  </div>
                </div>
              </div>

              {/* Color Scale Legend */}
              <div className="embedded-colorbar">
                <Colorbar />
              </div>
            </div>
          )}

          {/* TAB 2: SOLAR & SVF */}
          {activeTab === 'solar' && (
            <div className="tab-pane">
              <div className="hero-metric-box">
                <div className="hero-eyebrow">
                  <Sun size={13} className="hero-icon" />
                  <span>CELESTIAL SOLAR GEOMETRY • STEYN SVF</span>
                </div>
                <div className="hero-headline-row">
                  <span className="hero-number">{solarAlt.toFixed(1)}°</span>
                  <div className="hero-tag orange-tag">
                    <span>ALTITUDE</span>
                  </div>
                </div>
                <div className="hero-caption">
                  Solar Azimuth: <b>{solarAz.toFixed(1)}°</b> • Direct Insolation: <b>885 W/m²</b>
                </div>
              </div>

              <div className="stat-matrix-grid">
                <div className="matrix-stat-cell">
                  <span className="cell-label">Park Sky View Factor</span>
                  <span className="cell-value">0.82 mean</span>
                </div>
                <div className="matrix-stat-cell">
                  <span className="cell-label">Canyon Sky View Factor</span>
                  <span className="cell-value">0.31 canyon</span>
                </div>
                <div className="matrix-stat-cell">
                  <span className="cell-label">Walkable Sunlit Area</span>
                  <span className="cell-value highlight-orange">70.1%</span>
                </div>
                <div className="matrix-stat-cell">
                  <span className="cell-label">Building Shadow Extent</span>
                  <span className="cell-value">29.9%</span>
                </div>
              </div>

              <div className="quick-actions-row">
                <button
                  className="quick-action-pill"
                  onClick={() => useAppStore.getState().setActiveLayer('svf')}
                >
                  <Eye size={13} />
                  <span>Inspect SVF Contours</span>
                </button>
                <button
                  className="quick-action-pill"
                  onClick={() => useAppStore.getState().setActiveLayer('shadows')}
                >
                  <Sun size={13} />
                  <span>Direct Shadow Corridors</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 3: SPATIAL ZONES & PARCELS */}
          {activeTab === 'zones' && (
            <div className="tab-pane">
              <div className="zones-header-intro">
                <span>WASHINGTON SQUARE PARK PARCEL MATRIX</span>
                <p>Click any zone to teleport avatar or refocus viewpoint</p>
              </div>

              <div className="zone-parcel-cards-list">
                <div
                  className="zone-parcel-card"
                  onClick={() => teleportAvatar([-27, 3.0, 13], 0)}
                >
                  <div className="zone-badge fountain">⛲ PLAZA</div>
                  <div className="zone-info">
                    <span className="zone-name">Central Fountain Plaza</span>
                    <span className="zone-metrics">SVF: 0.88 • Tmrt: 58.2°C • Unshaded</span>
                  </div>
                </div>

                <div
                  className="zone-parcel-card"
                  onClick={() => teleportAvatar([-27, 2.5, -61], 0)}
                >
                  <div className="zone-badge arch">🏛️ ARCH</div>
                  <div className="zone-info">
                    <span className="zone-name">Washington Square Arch</span>
                    <span className="zone-metrics">SVF: 0.74 • Tmrt: 51.0°C • 5th Ave Axis</span>
                  </div>
                </div>

                <div
                  className="zone-parcel-card"
                  onClick={() => teleportAvatar([80, 5.0, 13], -Math.PI / 2)}
                >
                  <div className="zone-badge canyon">🏢 CANYON</div>
                  <div className="zone-info">
                    <span className="zone-name">East 4th St Street Canyon</span>
                    <span className="zone-metrics">SVF: 0.28 • Tmrt: 28.5°C • Deep Shade</span>
                  </div>
                </div>

                <div
                  className="zone-parcel-card"
                  onClick={() => teleportAvatar([-27, 3.8, 74], 0)}
                >
                  <div className="zone-badge lawn">🌳 LAWN</div>
                  <div className="zone-info">
                    <span className="zone-name">South Tree Canopy Oasis</span>
                    <span className="zone-metrics">SVF: 0.45 • Tmrt: 33.1°C • Vegetated</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: PEDESTRIAN AVATAR & WALK MODE */}
          {activeTab === 'avatar' && (
            <div className="tab-pane">
              <div className="avatar-quick-toggle-box">
                <div className="toggle-lead">
                  <Footprints size={18} className="toggle-icon" />
                  <div>
                    <span className="toggle-title">3D Pedestrian Simulation</span>
                    <span className="toggle-subtitle">Explore microclimate in 1st/3rd person</span>
                  </div>
                </div>
                <button
                  className={`avatar-main-btn ${avatarMode ? 'active' : ''}`}
                  onClick={() => setAvatarMode(!avatarMode)}
                >
                  {avatarMode ? 'Active (ON)' : 'Enter Walk'}
                </button>
              </div>

              {avatarMode ? (
                <div className="avatar-controls-cluster">
                  <div className="control-row">
                    <span className="row-label">Perspective:</span>
                    <div className="mode-segmented-control">
                      <button
                        className={`seg-btn ${cameraMode === 'third-person' ? 'active' : ''}`}
                        onClick={() => setCameraMode('third-person')}
                      >
                        <Camera size={13} />
                        <span>3rd Person</span>
                      </button>
                      <button
                        className={`seg-btn ${cameraMode === 'first-person' ? 'active' : ''}`}
                        onClick={() => setCameraMode('first-person')}
                      >
                        <Eye size={13} />
                        <span>1st Person</span>
                      </button>
                    </div>
                  </div>

                  <div className="control-row slider-block">
                    <span className="row-label">Walk Pace: {avatarSpeed.toFixed(1)} m/s</span>
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

                  <div className="avatar-coords-badge">
                    <span>X: {avatarPosition[0].toFixed(1)}m</span>
                    <span>Z: {avatarPosition[2].toFixed(1)}m</span>
                    <span>Elevation: {avatarPosition[1].toFixed(1)}m ASL</span>
                  </div>
                </div>
              ) : (
                <div className="avatar-instructions-card">
                  <p><b>WASD or Arrow keys</b> to walk.</p>
                  <p><b>Mouse look</b> to look around.</p>
                  <p>Real-time comfort HUD displays dynamic Tmrt, UTCI, and heat stress.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
