import { useEffect, useRef } from 'react';
import { fetchMetric } from '../api/queries';
import { useAppStore } from '../stores/appStore';

export function useTimeline() {
  const {
    currentUtcTime,
    setCurrentUtcTime,
    availableTimes,
    isPlayingTimeline,
    setIsPlayingTimeline,
    setMetric,
    config,
  } = useAppStore();

  const isFetchingRef = useRef(false);

  // 1. Fetch metrics when currentUtcTime changes
  useEffect(() => {
    if (!config || isFetchingRef.current) return;

    let isMounted = true;
    async function updateTimeStep() {
      try {
        isFetchingRef.current = true;
        const [shadowsData, tmrtData, utciData] = await Promise.all([
          fetchMetric('shadows', currentUtcTime, config?.simulation.date),
          fetchMetric('tmrt', currentUtcTime, config?.simulation.date),
          fetchMetric('utci', currentUtcTime, config?.simulation.date),
        ]);

        if (!isMounted) return;
        setMetric('shadows', shadowsData);
        setMetric('tmrt', tmrtData);
        setMetric('utci', utciData);
      } catch (err: any) {
        if (isMounted) {
          console.warn(`Could not load time step ${currentUtcTime}:`, err);
        }
      } finally {
        isFetchingRef.current = false;
      }
    }

    updateTimeStep();

    return () => {
      isMounted = false;
    };
  }, [currentUtcTime, config]);

  // 2. Auto-play loop across available times
  useEffect(() => {
    if (!isPlayingTimeline || availableTimes.length <= 1) return;

    const timer = setInterval(() => {
      const currentIndex = availableTimes.findIndex((t) => t.utc === currentUtcTime);
      const nextIndex = (currentIndex + 1) % availableTimes.length;
      setCurrentUtcTime(availableTimes[nextIndex].utc);
    }, 2800);

    return () => clearInterval(timer);
  }, [isPlayingTimeline, availableTimes, currentUtcTime, setCurrentUtcTime]);

  const togglePlay = () => setIsPlayingTimeline(!isPlayingTimeline);

  return {
    currentUtcTime,
    setCurrentUtcTime,
    isPlayingTimeline,
    togglePlay,
    availableTimes,
  };
}
