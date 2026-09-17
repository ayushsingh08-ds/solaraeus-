import { useEffect } from 'react';
import {
  fetch3DMesh,
  fetchAvailableTimes,
  fetchConfig,
  fetchDsm,
  fetchMetric,
  fetchWalkableGrid,
} from '../api/queries';
import { useAppStore } from '../stores/appStore';

export function useSimulationData() {
  const {
    setConfig,
    setAvailableTimes,
    setBuildingMesh,
    setWalkableGrid,
    setMetric,
    setIsLoading,
    setError,
    currentUtcTime,
  } = useAppStore();

  useEffect(() => {
    let isMounted = true;

    async function loadInitialData() {
      try {
        setIsLoading(true);
        setError(null);

        // 1. Fetch Config & Times
        const [config, times] = await Promise.all([
          fetchConfig(),
          fetchAvailableTimes(),
        ]);

        if (!isMounted) return;
        setConfig(config);
        setAvailableTimes(times);

        // 2. Fetch Static Datasets: DSM, SVF, 3D Mesh, and Walkable Grid
        const [dsmData, svfData, meshData, walkableData] = await Promise.all([
          fetchDsm(config.simulation.date),
          fetchMetric('svf', config.simulation.date),
          fetch3DMesh(),
          fetchWalkableGrid().catch(() => null),
        ]);

        if (!isMounted) return;
        setMetric('dsm', dsmData);
        setMetric('svf', svfData);
        setBuildingMesh(meshData);
        if (walkableData) {
          setWalkableGrid(walkableData);
        }

        // 3. Fetch Time-Varying Metrics for current time step (18:00 UTC)
        const [shadowsData, tmrtData, utciData] = await Promise.all([
          fetchMetric('shadows', currentUtcTime, config.simulation.date),
          fetchMetric('tmrt', currentUtcTime, config.simulation.date),
          fetchMetric('utci', currentUtcTime, config.simulation.date),
        ]);

        if (!isMounted) return;
        setMetric('shadows', shadowsData);
        setMetric('tmrt', tmrtData);
        setMetric('utci', utciData);
      } catch (err: any) {
        if (isMounted) {
          console.error('Failed to load simulation data:', err);
          setError(err.message || 'Failed to connect to simulation outputs');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadInitialData();

    return () => {
      isMounted = false;
    };
  }, []);
}
