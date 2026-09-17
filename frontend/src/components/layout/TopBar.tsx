import React from 'react';
import {
  ChevronRight,
  Clock,
  Compass,
  Footprints,
  Layers,
  RotateCcw,
  Sun,
  View,
  Zap,
} from 'lucide-react';

import { useAppStore } from '../../stores/appStore';
import { formatCompass, formatTime } from '../../utils/formatters';

export const TopBar: React.FC = () => {
  const {
    config,
    currentUtcTime,
    currentMetrics,
    avatarMode,
    setAvatarMode,
    setAvatarPosition,
    setAvatarHeading,
  } = useAppStore();

  const solarAlt = currentMetrics.shadows?.solarAltitudeDeg ?? 67.2;
  const solarAz = currentMetrics.shadows?.solarAzimuthDeg ?? 142.8;

  const handleResetAvatar = () => {
    setAvatarPosition([0, 0, 0]);
    setAvatarHeading(0);
  };

  const handleSetTopDown = () => {
    window.dispatchEvent(new CustomEvent('map-camera-topdown'));
  };

  const handleSetIsometric = () => {
    window.dispatchEvent(new CustomEvent('map-camera-reset'));
  };

  return (
    <header className="topbar-container">
      {/* Brand & Architectural Breadcrumbs (Reference 4) */}
      <div className="topbar-brand">
        <div className="brand-logo-disc">
          <Sun className="brand-icon" size={20} />
        </div>
        <div className="brand-text">
          <div className="brand-name">
            <span>SOLARAEUS</span>
            <span className="brand-badge">STAGE 1</span>
          </div>
          <div className="architectural-breadcrumbs">
            <span className="crumb-root">Urban Twin</span>
            <ChevronRight size={11} className="crumb-sep" />
            <span className="crumb-location">{config?.studyArea.name || 'Washington Sq Park'}</span>
            <ChevronRight size={11} className="crumb-sep" />
            <span className="crumb-active">Diurnal Microclimate</span>
          </div>
        </div>
      </div>

      {/* Center Metadata Bar: Time & Solar Celestial Vector */}
      <div className="topbar-meta">
        <div className="meta-chip">
          <Clock size={13} />
          <span>{formatTime(currentUtcTime)}</span>
          <span className="meta-sub">({currentUtcTime.split('T')[1]?.slice(0, 5)} UTC)</span>
        </div>

        <div className="meta-chip">
          <Compass size={13} />
          <span>Sun {solarAlt.toFixed(1)}° Alt</span>
          <span className="meta-sub">• {formatCompass(solarAz)}</span>
        </div>

        <div className="meta-chip engine-chip">
          <Zap size={13} />
          <span>Steyn SVF + UTCI</span>
        </div>
      </div>

      {/* Right Controls: View Modes & Walk Mode (Reference 4) */}
      <div className="topbar-actions">
        <div className="camera-presets-group">
          <button
            className="preset-btn"
            onClick={handleSetIsometric}
            title="Switch to 45° Perspective View"
          >
            <View size={14} />
            <span>45° Iso</span>
          </button>
          <button
            className="preset-btn"
            onClick={handleSetTopDown}
            title="Switch to Orthographic Top-Down Plan"
          >
            <Layers size={14} />
            <span>Top-Down</span>
          </button>
        </div>

        <button
          className={`action-btn walk-mode-btn ${avatarMode ? 'active' : ''}`}
          onClick={() => setAvatarMode(!avatarMode)}
        >
          <Footprints size={15} />
          <span>{avatarMode ? 'Exit Walk' : '3D Walk'}</span>
        </button>

        {avatarMode && (
          <button
            className="action-btn secondary"
            onClick={handleResetAvatar}
            title="Reset Avatar to Park Center"
          >
            <RotateCcw size={14} />
            <span>Reset Pos</span>
          </button>
        )}
      </div>
    </header>
  );
};
