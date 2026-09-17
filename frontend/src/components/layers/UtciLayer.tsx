import React from 'react';
import type { MetricData } from '../../api/types';
import { GroundHeatmap } from '../map/GroundHeatmap';

interface LayerProps {
  data: MetricData | null;
  visible: boolean;
  opacity?: number;
}

export const UtciLayer: React.FC<LayerProps> = ({ data, visible, opacity = 0.9 }) => {
  if (!visible || !data) return null;
  return <GroundHeatmap metricData={data} paletteName="utci" opacity={opacity} />;
};
