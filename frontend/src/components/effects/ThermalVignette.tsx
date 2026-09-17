import React from 'react';
import { Flame, ShieldCheck, Sun } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { formatTemp } from '../../utils/formatters';

export const ThermalVignette: React.FC = () => {
  const { avatarMode, avatarComfort } = useAppStore();

  if (!avatarMode || !avatarComfort) return null;

  const isSunlit = avatarComfort.isSunlit;
  const tmrt = avatarComfort.tmrt;
  const utci = avatarComfort.utci;
  const stressColor = avatarComfort.stressColor;

  // Determine somatic thermal sensation mode:
  // 'heat' = high direct solar radiation & apparent heat
  // 'cool' = comfortable relief in building or tree canopy shade
  const isHeatStress = isSunlit && (utci >= 34.0 || tmrt >= 48.0);
  const isShadeRelief = !isSunlit;

  return (
    <div className={`thermal-vignette-container ${isHeatStress ? 'vignette-heat' : isShadeRelief ? 'vignette-cool' : 'vignette-neutral'}`}>
      {/* 1. Fullscreen Radial Thermal Edge Aura */}
      <div
        className="thermal-vignette-edge"
        style={{
          boxShadow: isHeatStress
            ? `inset 0 0 100px 30px rgba(239, 68, 68, 0.28), inset 0 0 180px 70px rgba(245, 158, 11, 0.18)`
            : isShadeRelief
            ? `inset 0 0 100px 30px rgba(14, 165, 233, 0.25), inset 0 0 180px 70px rgba(56, 189, 248, 0.14)`
            : `inset 0 0 80px 20px rgba(56, 189, 248, 0.1)`,
        }}
      />

      {/* 2. Top-Center Somatic Status Pill (Instant Heat vs Shade Awareness) */}
      <div className="thermal-somatic-pill" style={{ borderColor: stressColor }}>
        <div className="somatic-icon-wrapper" style={{ backgroundColor: `${stressColor}25`, color: stressColor }}>
          {isHeatStress ? (
            <Flame className="somatic-pulse-icon" size={15} />
          ) : isShadeRelief ? (
            <ShieldCheck size={15} />
          ) : (
            <Sun size={15} />
          )}
        </div>

        <div className="somatic-text">
          <span className="somatic-title">
            {isHeatStress
              ? 'DIRECT SOLAR HEAT LOAD'
              : isShadeRelief
              ? 'BUILDING SHADE RADIANT RELIEF'
              : 'STABLE MICROCLIMATE'}
          </span>
          <span className="somatic-subtitle">
            {isHeatStress
              ? `Tmrt ${formatTemp(tmrt)} • +14.7°C Radiant Excess`
              : isShadeRelief
              ? `Tmrt ${formatTemp(tmrt)} • -14.7°C Cooler in Shade`
              : `UTCI ${formatTemp(utci)}`}
          </span>
        </div>
      </div>
    </div>
  );
};
