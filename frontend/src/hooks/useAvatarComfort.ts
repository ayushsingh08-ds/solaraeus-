import { useEffect } from 'react';
import { useAppStore } from '../stores/appStore';
import { getUtciStressInfo } from '../utils/colorScales';
import { worldToGrid } from '../utils/geoTransform';

export function useAvatarComfort() {
  const {
    avatarMode,
    avatarPosition,
    currentMetrics,
    setAvatarComfort,
  } = useAppStore();

  useEffect(() => {
    if (!avatarMode) return;

    const [x, , z] = avatarPosition;
    const { dsm, tmrt, utci, shadows, svf } = currentMetrics;

    if (!tmrt || !utci || tmrt.values.length === 0) return;

    const [row, col] = worldToGrid(x, z, {
      rows: tmrt.shape[0],
      cols: tmrt.shape[1],
    });

    const localTmrt = tmrt.values[row]?.[col] ?? 50.0;
    const localUtci = utci.values[row]?.[col] ?? 38.0;
    const isSunlit = (shadows?.values[row]?.[col] ?? 1) === 1;
    const localSvf = svf?.values[row]?.[col] ?? 0.8;
    const localElev = dsm?.values[row]?.[col] ?? 6.0;

    const stress = getUtciStressInfo(localUtci);

    setAvatarComfort({
      tmrt: localTmrt,
      utci: localUtci,
      stressCategory: stress.label,
      stressColor: stress.color,
      isSunlit,
      svf: localSvf,
      elevation: localElev,
    });
  }, [avatarMode, avatarPosition, currentMetrics, setAvatarComfort]);
}
