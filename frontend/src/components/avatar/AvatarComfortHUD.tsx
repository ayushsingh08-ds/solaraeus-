import React from 'react';
import { Camera, Compass, Eye, ShieldAlert, Sun, Wind, X } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { formatTemp } from '../../utils/formatters';

export const AvatarComfortHUD: React.FC = () => {
  const {
    avatarMode,
    setAvatarMode,
    cameraMode,
    setCameraMode,
    avatarComfort,
  } = useAppStore();

  if (!avatarMode) return null;

  const stressColor = avatarComfort?.stressColor || '#38bdf8';
  const stressCategory = avatarComfort?.stressCategory || 'Evaluating...';
  const isSunlit = avatarComfort?.isSunlit ?? true;

  const toggleCamera = () => {
    setCameraMode(cameraMode === 'third-person' ? 'first-person' : 'third-person');
  };

  return (
    <div className="avatar-hud-card">
      <div className="avatar-hud-header">
        <div className="avatar-hud-title">
          <span className="pulse-dot" style={{ backgroundColor: stressColor }} />
          <span>STREET WALK MODE</span>
        </div>
        <div className="avatar-hud-actions">
          <button
            className="hud-btn"
            onClick={toggleCamera}
            title={cameraMode === 'third-person' ? 'Switch to First-Person' : 'Switch to Third-Person'}
          >
            {cameraMode === 'third-person' ? <Eye size={15} /> : <Camera size={15} />}
            <span>{cameraMode === 'third-person' ? '3rd Person' : '1st Person'}</span>
          </button>
          <button
            className="hud-btn-close"
            onClick={() => setAvatarMode(false)}
            title="Exit Walk Mode (Orbit Camera)"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Live Comfort Status Pill */}
      <div className="avatar-stress-badge" style={{ borderColor: stressColor, color: stressColor }}>
        <ShieldAlert size={16} />
        <span className="stress-badge-text">{stressCategory}</span>
      </div>

      {/* Metric Readings Grid */}
      <div className="avatar-hud-grid">
        <div className="hud-metric-box">
          <span className="hud-metric-label">Apparent Temp (UTCI)</span>
          <span className="hud-metric-val" style={{ color: stressColor }}>
            {formatTemp(avatarComfort?.utci)}
          </span>
        </div>

        <div className="hud-metric-box">
          <span className="hud-metric-label">Radiant Temp (Tmrt)</span>
          <span className="hud-metric-val">
            {formatTemp(avatarComfort?.tmrt)}
          </span>
        </div>

        <div className="hud-metric-box">
          <span className="hud-metric-label">Illumination</span>
          <span className={`hud-metric-pill ${isSunlit ? 'sunlit' : 'shaded'}`}>
            {isSunlit ? <Sun size={13} /> : <Wind size={13} />}
            <span>{isSunlit ? 'Sunlit' : 'Building Shade'}</span>
          </span>
        </div>

        <div className="hud-metric-box">
          <span className="hud-metric-label">Sky View (SVF)</span>
          <span className="hud-metric-val">
            {avatarComfort?.svf ? avatarComfort.svf.toFixed(2) : '—'}
          </span>
        </div>
      </div>

      {/* Controls helper footer */}
      <div className="avatar-hud-footer">
        <Compass size={13} />
        <span>Use <b>W A S D</b> or <b>Arrows</b> to walk. <b>Shift</b> to sprint.</span>
      </div>
    </div>
  );
};
