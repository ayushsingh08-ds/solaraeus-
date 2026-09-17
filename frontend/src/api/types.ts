export interface GeoBounds {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface MetricData {
  metric: 'dsm' | 'shadows' | 'svf' | 'tmrt' | 'utci';
  date: string;
  timeUtc: string;
  solarAltitudeDeg?: number;
  solarAzimuthDeg?: number;
  bounds: GeoBounds;
  resolutionM: number;
  shape: [number, number]; // [rows, cols]
  values: number[][];      // 2D array [row][col], row 0 = north
  description: string;
  units: string;
  vmin: number;
  vmax: number;
}

export interface SimulationConfig {
  studyArea: {
    name: string;
    latCenter: number;
    lonCenter: number;
    utmZone: number;
    bounds: GeoBounds;
    resolutionM: number;
    shape: [number, number];
  };
  simulation: {
    date: string;
    dayOfYear: number;
    pedestrianHeightM: number;
    nSvFDirections: number;
    svfMaxRadiusM: number;
  };
  dataSources: {
    overtureVersion: string;
    era5Date: string;
    demSource: string;
  };
}

export interface TimeStep {
  utc: string;          // "2024-07-15T18:00:00"
  local: string;        // "14:00 EDT"
  hourFloat: number;    // 14.0
  utcHour: number;      // 18
}

export interface BuildingMesh {
  bounds: GeoBounds;
  origin: [number, number, number];
  numVertices: number;
  numFaces: number;
  isWatertight: boolean;
  vertices: number[];   // flat array [x,y,z, x,y,z, ...]
  faces: number[];      // flat array [i,j,k, i,j,k, ...]
}

export interface AvatarComfortMetrics {
  tmrt: number;
  utci: number;
  stressCategory: string;
  stressColor: string;
  isSunlit: boolean;
  svf: number;
  elevation: number;
}

export interface AvatarState {
  enabled: boolean;
  cameraMode: 'third-person' | 'first-person';
  position: [number, number, number];
  heading: number;
  walkSpeed: number;
  comfort: AvatarComfortMetrics | null;
}
