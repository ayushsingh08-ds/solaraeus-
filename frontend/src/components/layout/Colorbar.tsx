import React, { useMemo } from 'react';
import { useAppStore } from '../../stores/appStore';
import { COLORMAPS } from '../../utils/colorScales';

export const Colorbar: React.FC = () => {
  const { activeLayer, currentMetrics } = useAppStore();
  const metricData = currentMetrics[activeLayer];

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

  const gradientCss = useMemo(() => {
    const stops = COLORMAPS[paletteName] || COLORMAPS.magma;
    const parts = stops.map(
      (s) => `rgb(${s.color[0]}, ${s.color[1]}, ${s.color[2]}) ${Math.round(s.pos * 100)}%`
    );
    return `linear-gradient(to right, ${parts.join(', ')})`;
  }, [paletteName]);

  const vmin = metricData?.vmin ?? 0;
  const vmax = metricData?.vmax ?? 100;
  const units = metricData?.units || '';

  return (
    <div className="colorbar-container">
      <div className="colorbar-header">
        <span className="colorbar-title">
          {metricData?.description || activeLayer.toUpperCase()}
        </span>
        <span className="colorbar-units">({units})</span>
      </div>

      <div className="colorbar-strip" style={{ background: gradientCss }} />

      {/* Numerical and Categorical Axis Ticks */}
      <div className="colorbar-ticks">
        {activeLayer === 'utci' ? (
          <>
            <span>20°C (Neutral)</span>
            <span>26°C (Mod)</span>
            <span>32°C (Strong)</span>
            <span>38°C (V.Strong)</span>
            <span>46°C (Extreme)</span>
          </>
        ) : activeLayer === 'shadows' ? (
          <>
            <span>Shaded (0)</span>
            <span>Sunlit (1)</span>
          </>
        ) : (
          <>
            <span>{vmin.toFixed(1)} {units}</span>
            <span>{((vmin + vmax) / 2).toFixed(1)} {units}</span>
            <span>{vmax.toFixed(1)} {units}</span>
          </>
        )}
      </div>
    </div>
  );
};
