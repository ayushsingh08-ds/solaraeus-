import { useEffect, useRef } from 'react';
import { useAppStore } from '../stores/appStore';
import { worldToGrid } from '../utils/geoTransform';

export function useAvatarMovement() {
  const {
    avatarMode,
    avatarSpeed,
  } = useAppStore();

  const keysPressed = useRef<{ [key: string]: boolean }>({});
  const animFrameId = useRef<number | null>(null);
  const lastTime = useRef<number>(performance.now());

  // Listen to keyboard inputs across the window
  useEffect(() => {
    if (!avatarMode) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'shift'].includes(key)) {
        keysPressed.current[key] = true;
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      delete keysPressed.current[key];
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      keysPressed.current = {};
    };
  }, [avatarMode]);

  // Movement physics and terrain elevation loop
  useEffect(() => {
    if (!avatarMode) return;

    lastTime.current = performance.now();

    const updateLoop = (now: number) => {
      const dt = Math.min((now - lastTime.current) / 1000, 0.1);
      lastTime.current = now;

      // Always read live state to guarantee instant response and avoid stale closures
      const state = useAppStore.getState();
      let [x, y, z] = state.avatarPosition;
      let heading = state.avatarHeading;
      const speed = state.avatarSpeed;
      const walkableGrid = state.walkableGrid;
      const dsmData = state.currentMetrics.dsm;

      const keys = keysPressed.current;
      const isSprint = !!keys['shift'];
      const currentSpeed = isSprint ? speed * 1.8 : speed;
      const turnRate = 2.4; // radians/sec

      let moved = false;

      // 1. Turning (A/D or Left/Right arrows)
      if (keys['a'] || keys['arrowleft']) {
        heading += turnRate * dt;
        moved = true;
      }
      if (keys['d'] || keys['arrowright']) {
        heading -= turnRate * dt;
        moved = true;
      }

      // 2. Forward/Backward (W/S or Up/Down arrows)
      let forward = 0;
      if (keys['w'] || keys['arrowup']) forward += 1;
      if (keys['s'] || keys['arrowdown']) forward -= 1;

      if (forward !== 0) {
        // Forward vector in Three.js coordinate space (North = -Z, East = +X)
        const dx = Math.sin(heading) * forward * currentSpeed * dt;
        const dz = -Math.cos(heading) * forward * currentSpeed * dt;

        const candidateX = x + dx;
        const candidateZ = z + dz;

        // Accurate collision detection against walkable pedestrian terrain
        let isWalkable = true;

        if (walkableGrid && walkableGrid.walkable.length > 0) {
          const [row, col] = worldToGrid(candidateX, candidateZ, {
            rows: walkableGrid.shape ? walkableGrid.shape[0] : 673,
            cols: walkableGrid.shape ? walkableGrid.shape[1] : 599,
          });

          // 1 = Walkable outdoor ground/street, 0 = Building interior
          isWalkable = (walkableGrid.walkable[row]?.[col] ?? 1) === 1;

          if (isWalkable) {
            const elev = walkableGrid.groundElevation[row]?.[col] ?? 9.0;
            y = Math.max(0, elev - (walkableGrid.baseElevation ?? 6.0));
            x = candidateX;
            z = candidateZ;
            moved = true;
          }
        } else if (dsmData && dsmData.values.length > 0) {
          // Robust fallback before walkableGrid finishes streaming:
          // In Washington Square Park, natural terrain is 6.0m - 12.5m ASL.
          // Buildings are >= 15.0m ASL.
          const [row, col] = worldToGrid(candidateX, candidateZ, {
            rows: dsmData.shape[0],
            cols: dsmData.shape[1],
          });
          const groundZ = dsmData.values[row]?.[col] ?? 9.0;
          if (groundZ <= 14.0) {
            y = Math.max(0, groundZ - 6.0);
            x = candidateX;
            z = candidateZ;
            moved = true;
          }
        } else {
          // Open movement if rasters not loaded yet
          x = candidateX;
          z = candidateZ;
          moved = true;
        }
      }

      if (moved) {
        state.setAvatarPosition([x, y, z]);
        state.setAvatarHeading(heading);
      }

      animFrameId.current = requestAnimationFrame(updateLoop);
    };

    animFrameId.current = requestAnimationFrame(updateLoop);

    return () => {
      if (animFrameId.current) cancelAnimationFrame(animFrameId.current);
    };
  }, [avatarMode, avatarSpeed]);
}
