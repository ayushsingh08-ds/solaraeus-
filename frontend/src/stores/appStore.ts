import { create } from 'zustand';
import type {
  AvatarComfortMetrics,
  BuildingMesh,
  MetricData,
  SimulationConfig,
  TimeStep,
} from '../api/types';

export type ActiveLayerType = 'tmrt' | 'utci' | 'svf' | 'shadows' | 'dsm';
export type CameraModeType = 'third-person' | 'first-person';

export interface AppState {
  // Config & Times
  config: SimulationConfig | null;
  availableTimes: TimeStep[];
  currentUtcTime: string;
  isPlayingTimeline: boolean;

  // Datasets
  currentMetrics: {
    dsm: MetricData | null;
    shadows: MetricData | null;
    svf: MetricData | null;
    tmrt: MetricData | null;
    utci: MetricData | null;
  };
  buildingMesh: BuildingMesh | null;
  walkableGrid: {
    shape?: [number, number];
    baseElevation?: number;
    walkable: number[][];
    groundElevation: number[][];
  } | null;

  // View Options
  activeLayer: ActiveLayerType;
  layerOpacity: number;
  showBuildings: boolean;
  showSunIndicator: boolean;
  showShadowOverlay: boolean;
  isWireframe: boolean;

  // Avatar Walk Mode (Step 7.3)
  avatarMode: boolean;
  avatarEnabled: boolean; // Alias for avatarMode
  cameraMode: CameraModeType;
  avatarPosition: [number, number, number]; // [x, y, z] in Three world coords
  avatarHeading: number;                    // angle in radians
  avatarSpeed: number;                      // walking speed in m/s
  avatarComfort: AvatarComfortMetrics | null;

  // UI state
  hoveredCell: { row: number; col: number; val: number; metric: string } | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setConfig: (cfg: SimulationConfig) => void;
  setAvailableTimes: (times: TimeStep[]) => void;
  setCurrentUtcTime: (timeUtc: string) => void;
  setIsPlayingTimeline: (playing: boolean) => void;
  setMetric: (name: keyof AppState['currentMetrics'], data: MetricData) => void;
  setBuildingMesh: (mesh: BuildingMesh) => void;
  setWalkableGrid: (grid: AppState['walkableGrid']) => void;
  setActiveLayer: (layer: ActiveLayerType) => void;
  setLayerOpacity: (opacity: number) => void;
  setShowBuildings: (show: boolean) => void;
  setShowSunIndicator: (show: boolean) => void;
  setShowShadowOverlay: (show: boolean) => void;
  setIsWireframe: (wf: boolean) => void;

  setAvatarMode: (active: boolean) => void;
  setAvatarEnabled: (enabled: boolean) => void;
  setCameraMode: (mode: CameraModeType) => void;
  setAvatarPosition: (pos: [number, number, number]) => void;
  setAvatarHeading: (heading: number) => void;
  setAvatarSpeed: (speed: number) => void;
  setAvatarComfort: (comfort: AvatarComfortMetrics | null) => void;
  teleportAvatar: (pos: [number, number, number], heading?: number) => void;
  resetAvatarPosition: () => void;

  setHoveredCell: (cell: AppState['hoveredCell']) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (err: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  config: null,
  availableTimes: [],
  currentUtcTime: '2024-07-15T18:00:00',
  isPlayingTimeline: false,

  currentMetrics: {
    dsm: null,
    shadows: null,
    svf: null,
    tmrt: null,
    utci: null,
  },
  buildingMesh: null,
  walkableGrid: null,

  activeLayer: 'tmrt',
  layerOpacity: 0.9,
  showBuildings: true,
  showSunIndicator: true,
  showShadowOverlay: true,
  isWireframe: false,

  avatarMode: false,
  avatarEnabled: false,
  cameraMode: 'third-person',
  avatarPosition: [-27, 3.0, 13], // Washington Square Park open center fountain lawn
  avatarHeading: 0,
  avatarSpeed: 3.0,
  avatarComfort: null,

  hoveredCell: null,
  isLoading: true,
  error: null,

  setConfig: (cfg) => set({ config: cfg }),
  setAvailableTimes: (times) => set({ availableTimes: times }),
  setCurrentUtcTime: (timeUtc) => set({ currentUtcTime: timeUtc }),
  setIsPlayingTimeline: (playing) => set({ isPlayingTimeline: playing }),
  setMetric: (name, data) =>
    set((state) => ({
      currentMetrics: { ...state.currentMetrics, [name]: data },
    })),
  setBuildingMesh: (mesh) => set({ buildingMesh: mesh }),
  setWalkableGrid: (grid) => set({ walkableGrid: grid }),
  setActiveLayer: (layer) => set({ activeLayer: layer }),
  setLayerOpacity: (opacity) => set({ layerOpacity: opacity }),
  setShowBuildings: (show) => set({ showBuildings: show }),
  setShowSunIndicator: (show) => set({ showSunIndicator: show }),
  setShowShadowOverlay: (show) => set({ showShadowOverlay: show }),
  setIsWireframe: (wf) => set({ isWireframe: wf }),

  setAvatarMode: (active) => set({ avatarMode: active, avatarEnabled: active }),
  setAvatarEnabled: (enabled) => set({ avatarMode: enabled, avatarEnabled: enabled }),
  setCameraMode: (mode) => set({ cameraMode: mode }),
  setAvatarPosition: (pos) => set({ avatarPosition: pos }),
  setAvatarHeading: (heading) => set({ avatarHeading: heading }),
  setAvatarSpeed: (speed) => set({ avatarSpeed: speed }),
  setAvatarComfort: (comfort) => set({ avatarComfort: comfort }),
  teleportAvatar: (pos, heading = 0) => set({ avatarPosition: pos, avatarHeading: heading }),
  resetAvatarPosition: () => set({ avatarPosition: [-27, 3.0, 13], avatarHeading: 0 }),

  setHoveredCell: (cell) => set({ hoveredCell: cell }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  setError: (err) => set({ error: err }),
}));
