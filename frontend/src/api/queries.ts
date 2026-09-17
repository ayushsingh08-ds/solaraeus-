import { fetchJson } from './client';
import type { BuildingMesh, MetricData, SimulationConfig, TimeStep } from './types';

export async function fetchConfig(): Promise<SimulationConfig> {
  return fetchJson<SimulationConfig>('data/simulation_config.json');
}

export async function fetchAvailableTimes(): Promise<TimeStep[]> {
  return fetchJson<TimeStep[]>('data/available_times.json');
}

export async function fetchMetric(
  metric: MetricData['metric'],
  timeUtc: string,
  dateStr: string = '20240715'
): Promise<MetricData> {
  const cleanDate = dateStr.replace(/-/g, '');

  if (metric === 'dsm') {
    return fetchJson<MetricData>(`json/dsm_${cleanDate}_0000.json`);
  }
  if (metric === 'svf') {
    return fetchJson<MetricData>(`json/svf_${cleanDate}_0000.json`);
  }

  // timeUtc format: "2024-07-15T18:00:00"
  const timePart = timeUtc.split('T')[1] || '18:00:00';
  const hhmm = timePart.slice(0, 5).replace(':', ''); // e.g. "1800"

  return fetchJson<MetricData>(`json/${metric}_${cleanDate}_${hhmm}.json`);
}

export async function fetchDsm(dateStr: string = '20240715'): Promise<MetricData> {
  return fetchMetric('dsm', '2024-07-15T00:00:00', dateStr);
}

export async function fetch3DMesh(): Promise<BuildingMesh> {
  return fetchJson<BuildingMesh>('meshes/buildings_3d.json');
}

export async function fetchWalkableGrid(): Promise<any> {
  return fetchJson<any>('data/walkable_grid.json');
}
