import React from 'react';
import {
  Building2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Eye,
  Flame,
  Layers,
  Mountain,
  Pause,
  Play,
  RotateCcw,
  Sun,
  Thermometer,
} from 'lucide-react';
import type { ActiveLayerType } from '../../stores/appStore';
import { useTimeline } from '../../hooks/useTimeline';
import { useAppStore } from '../../stores/appStore';
import { formatTime } from '../../utils/formatters';

interface LayerItem {
  id: ActiveLayerType;
  label: string;
  icon: React.ReactNode;
}

const LAYERS: LayerItem[] = [
  { id: 'tmrt', label: 'Tmrt Radiant', icon: <Flame size={14} /> },
  { id: 'utci', label: 'UTCI Comfort', icon: <Thermometer size={14} /> },
  { id: 'shadows', label: 'Direct Shadows', icon: <Sun size={14} /> },
  { id: 'svf', label: 'Sky View (SVF)', icon: <Eye size={14} /> },
  { id: 'dsm', label: 'Elevation (DSM)', icon: <Mountain size={14} /> },
];

export const FloatingBottomDock: React.FC = () => {
  const {
    activeLayer,
    setActiveLayer,
    showBuildings,
    setShowBuildings,
    avatarMode,
  } = useAppStore();


  const {
    currentUtcTime,
    setCurrentUtcTime,
    isPlayingTimeline,
    togglePlay,
    availableTimes,
  } = useTimeline();

  // Find index of current time
  const currentIndex = availableTimes.findIndex((t) => t.utc === currentUtcTime);
  const safeIndex = currentIndex >= 0 ? currentIndex : 0;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    if (availableTimes[idx]) {
      setCurrentUtcTime(availableTimes[idx].utc);
    }
  };

  const handlePrevTime = () => {
    const prevIdx = (safeIndex - 1 + availableTimes.length) % availableTimes.length;
    setCurrentUtcTime(availableTimes[prevIdx].utc);
  };

  const handleNextTime = () => {
    const nextIdx = (safeIndex + 1) % availableTimes.length;
    setCurrentUtcTime(availableTimes[nextIdx].utc);
  };

  return (
    <div className="floating-bottom-dock-container">
      {/* 1. LAYER SWITCHER ISLAND */}
      <div className="dock-island layer-island">
        <div className="island-label">
          <Layers size={13} />
          <span>LAYER</span>
        </div>

        <div className="layer-pills-row">
          {LAYERS.map((l) => (
            <button
              key={l.id}
              className={`layer-pill-btn ${activeLayer === l.id ? 'active' : ''}`}
              onClick={() => setActiveLayer(l.id)}
            >
              {l.icon}
              <span>{l.label}</span>
            </button>
          ))}
        </div>

        <div className="dock-divider" />

        {/* Quick 3D Building Toggle Pill */}
        <button
          className={`dock-tool-btn ${showBuildings ? 'active' : ''}`}
          onClick={() => setShowBuildings(!showBuildings)}
          title={showBuildings ? 'Hide 3D Buildings' : 'Show 3D Buildings'}
        >
          <Building2 size={14} />
          <span>3D Blocks</span>
        </button>
      </div>

      {/* 2. DIURNAL TIMELINE SCRUBBER ISLAND */}
      <div className="dock-island timeline-island">
        <button
          className={`timeline-play-btn ${isPlayingTimeline ? 'playing' : ''}`}
          onClick={togglePlay}
          title={isPlayingTimeline ? 'Pause Diurnal Scrub' : 'Play Diurnal Scrub'}
        >
          {isPlayingTimeline ? <Pause size={15} /> : <Play size={15} />}
        </button>

        <div className="timeline-slider-wrap">
          <div className="timeline-time-readout">
            <span className="time-primary">{formatTime(currentUtcTime)}</span>
            <span className="time-utc">({currentUtcTime.split('T')[1]?.slice(0, 5)} UTC)</span>
          </div>

          <div className="timeline-slider-track">
            <input
              type="range"
              min={0}
              max={Math.max(0, availableTimes.length - 1)}
              step={1}
              value={safeIndex}
              onChange={handleSliderChange}
              className="timeline-range-slider"
            />
          </div>
        </div>

        <div className="timeline-step-buttons">
          <button className="step-btn" onClick={handlePrevTime} title="Previous Hour">
            <ChevronLeft size={16} />
          </button>
          <button className="step-btn" onClick={handleNextTime} title="Next Hour">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* 3. ROUNDED SPATIAL NAVIGATION D-PAD & CAMERA (Reference 4) */}
      {!avatarMode && (
        <div className="dock-island dpad-island">
          <div className="dpad-disc">
            <button
              className="dock-dpad-btn dock-dpad-up"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('map-camera-nudge', { detail: { dir: 'up' } }));
              }}
              title="Look North / Pitch Up"
            >
              <ChevronUp size={14} />
            </button>
            <button
              className="dock-dpad-btn dock-dpad-right"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('map-camera-nudge', { detail: { dir: 'right' } }));
              }}
              title="Rotate East"
            >
              <ChevronRight size={14} />
            </button>
            <button
              className="dock-dpad-btn dock-dpad-down"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('map-camera-nudge', { detail: { dir: 'down' } }));
              }}
              title="Look South / Pitch Down"
            >
              <ChevronDown size={14} />
            </button>
            <button
              className="dock-dpad-btn dock-dpad-left"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('map-camera-nudge', { detail: { dir: 'left' } }));
              }}
              title="Rotate West"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              className="dock-dpad-btn dock-dpad-center"
              onClick={() => {
                window.dispatchEvent(new CustomEvent('map-camera-reset'));
              }}
              title="Reset 45° Perspective View"
            >
              <RotateCcw size={12} />
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
