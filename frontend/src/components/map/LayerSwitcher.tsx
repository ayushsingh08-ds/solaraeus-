import React from 'react';
import { Eye, Flame, Layers, Mountain, Sun, Thermometer } from 'lucide-react';
import type { ActiveLayerType } from '../../stores/appStore';
import { useAppStore } from '../../stores/appStore';

interface LayerOption {
  id: ActiveLayerType;
  label: string;
  icon: React.ReactNode;
  unit: string;
}

const LAYERS: LayerOption[] = [
  { id: 'tmrt', label: 'Tmrt (Radiant)', icon: <Flame size={15} />, unit: '°C' },
  { id: 'utci', label: 'UTCI (Comfort)', icon: <Thermometer size={15} />, unit: '°C' },
  { id: 'shadows', label: 'Direct Shadows', icon: <Sun size={15} />, unit: 'binary' },
  { id: 'svf', label: 'Sky View (SVF)', icon: <Eye size={15} />, unit: '0–1' },
  { id: 'dsm', label: 'Elevation (DSM)', icon: <Mountain size={15} />, unit: 'm' },
];

export const LayerSwitcher: React.FC = () => {
  const { activeLayer, setActiveLayer } = useAppStore();

  return (
    <div className="layer-switcher-bar">
      <div className="layer-switcher-label">
        <Layers size={14} />
        <span>LAYERS</span>
      </div>
      <div className="layer-switcher-pills">
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
    </div>
  );
};
