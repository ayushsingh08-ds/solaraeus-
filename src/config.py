"""
Solaraeus Central Configuration — Study Area, Paths, and Physics Parameters.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Tuple


@dataclass(frozen=True)
class StudyArea:
    """
    Geographic bounding boxes and UTM coordinates for a simulation area.

    Note the three coordinate order conventions:
      - bbox_latlon: (S, W, N, E) -> Solaraeus internal convention
      - bbox_overture: (W, S, E, N) -> min_lon, min_lat, max_lon, max_lat
      - area_era5: (N, W, S, E) -> north, west, south, east
    """
    name: str
    lat_center: float
    lon_center: float
    bbox_latlon: Tuple[float, float, float, float]    # (S, W, N, E)
    bbox_overture: Tuple[float, float, float, float]  # (W, S, E, N)
    area_era5: Tuple[float, float, float, float]      # (N, W, S, E)
    utm_zone: int
    utm_bounds: Tuple[float, float, float, float]     # (xmin, ymin, xmax, ymax) in meters
    resolution_m: float = 1.0


# Study Area A — Washington Square Park, NYC
WASHINGTON_SQUARE_PARK = StudyArea(
    name="Washington Square Park",
    lat_center=40.7308,
    lon_center=-73.9975,
    # Internal order: south, west, north, east
    bbox_latlon=(40.7280, -73.9990, 40.7340, -73.9920),
    # Overture order: west, south, east, north
    bbox_overture=(-73.9990, 40.7280, -73.9920, 40.7340),
    # ERA5 order: north, west, south, east
    area_era5=(40.7340, -73.9990, 40.7280, -73.9920),
    utm_zone=32618,
    # Recalculated from the full geographic bbox to avoid 1km offset
    utm_bounds=(584523.82, 4509045.01, 585122.55, 4509717.82),
    resolution_m=1.0,
)


# Study Area B — Lower Manhattan / Financial District
LOWER_MANHATTAN = StudyArea(
    name="Lower Manhattan / Financial District",
    lat_center=40.7080,
    lon_center=-74.0120,
    # Internal order: south, west, north, east
    bbox_latlon=(40.7005, -74.0185, 40.7155, -74.0050),
    # Overture order: west, south, east, north
    bbox_overture=(-74.0185, 40.7005, -74.0050, 40.7155),
    # ERA5 order: north, west, south, east
    area_era5=(40.7155, -74.0185, 40.7005, -74.0050),
    utm_zone=32618,
    utm_bounds=(582900.18, 4505973.75, 584059.31, 4507651.67),
    resolution_m=1.0,
)


def get_latest_safe_era5_date(lag_days: int = 6) -> Tuple[str, int]:
    """
    Returns (YYYY-MM-DD, day_of_year) for a safe ERA5 query date.
    ERA5T is typically available ~5 days behind real-time; 6 days provides safety.
    """
    today = datetime.now(timezone.utc).date()
    safe_date = today - timedelta(days=lag_days)
    return safe_date.strftime("%Y-%m-%d"), safe_date.timetuple().tm_yday


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation run parameters."""
    study_area: StudyArea = WASHINGTON_SQUARE_PARK
    date: str = "2024-07-15"            # Default reproducibility date
    day_of_year: int = 196
    utc_hour: int = 18                  # 14:00 EDT = 18:00 UTC
    pedestrian_height_m: float = 1.1

    # Radiative physics parameters
    n_svf_directions: int = 360
    svf_max_radius_m: int = 200
    atmospheric_transmission: float = 0.75  # Clear-sky direct beam transmission
    sky_emissivity: float = 0.85
    ground_emissivity: float = 0.95
    cloud_fraction: float = 0.1

    @classmethod
    def recent_experiment(cls, study_area: StudyArea = WASHINGTON_SQUARE_PARK) -> "SimulationConfig":
        """Factory for running the recent-observation experiment (e.g. 2026-09-11)."""
        safe_date, day_of_year = get_latest_safe_era5_date(lag_days=6)
        return cls(
            study_area=study_area,
            date=safe_date,
            day_of_year=day_of_year,
            utc_hour=18,
        )


@dataclass(frozen=True)
class DataConfig:
    """Project filesystem paths."""
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    raw_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "raw")
    processed_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "processed")
    cache_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data" / "cache")
    output_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs")
    figure_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "figures")
    json_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "json")
    data_out_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "data")
    meshes_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "meshes")
    netcdf_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "netcdf")
    reports_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "outputs" / "reports")

    def ensure_dirs(self) -> None:
        """Ensure all required directories exist."""
        for path in [
            self.raw_dir, self.processed_dir, self.cache_dir,
            self.figure_dir, self.json_dir, self.data_out_dir, self.meshes_dir,
            self.netcdf_dir, self.reports_dir
        ]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class ProjectConfig:
    """Composite configuration object."""
    study_area: StudyArea = WASHINGTON_SQUARE_PARK
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    data: DataConfig = field(default_factory=DataConfig)
