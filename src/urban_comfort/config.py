"""
Configuration schemas, physical constants, and boundary condition data models.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
import json

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant (W / m^2 K^4)


@dataclass(frozen=True)
class Material:
    """Material radiative properties and thermal boundary state."""
    id: str
    albedo: float
    emissivity: float
    surface_temperature: float  # Kelvin
    is_opaque: bool = True

    def __post_init__(self):
        if not (0.0 <= self.albedo <= 1.0):
            raise ValueError(f"Albedo must be in [0, 1], got {self.albedo}")
        if not (0.0 <= self.emissivity <= 1.0):
            raise ValueError(f"Emissivity must be in [0, 1], got {self.emissivity}")
        if self.surface_temperature < 0.0:
            raise ValueError(f"Surface temperature must be >= 0 K, got {self.surface_temperature}")


@dataclass(frozen=True)
class Weather:
    """Atmospheric and meteorological conditions for a single timestep."""
    air_temperature: float               # Kelvin
    relative_humidity: float             # Percentage [0, 100]
    wind_speed: float                    # m/s
    wind_direction: float                # Degrees [0, 360) clockwise from North
    direct_normal_irradiance: float      # W / m^2
    diffuse_horizontal_irradiance: float # W / m^2

    def __post_init__(self):
        if self.air_temperature < 0.0:
            raise ValueError(f"Air temperature must be >= 0 K, got {self.air_temperature}")
        if not (0.0 <= self.relative_humidity <= 100.0):
            raise ValueError(f"Relative humidity must be in [0, 100], got {self.relative_humidity}")
        if self.wind_speed < 0.0:
            raise ValueError(f"Wind speed must be >= 0 m/s, got {self.wind_speed}")
        if not (0.0 <= self.wind_direction <= 360.0):
            raise ValueError(f"Wind direction must be in [0, 360] degrees, got {self.wind_direction}")
        if self.direct_normal_irradiance < 0.0:
            raise ValueError(f"DNI must be >= 0 W/m^2, got {self.direct_normal_irradiance}")
        if self.diffuse_horizontal_irradiance < 0.0:
            raise ValueError(f"DHI must be >= 0 W/m^2, got {self.diffuse_horizontal_irradiance}")


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation control parameters, spatial resolution, and numerical tolerances."""
    latitude: float = 40.7128            # Degrees North (-90 to +90)
    longitude: float = -74.0060          # Degrees East (-180 to +180)
    date: str = "2024-07-15"             # YYYY-MM-DD
    local_time: str = "12:00:00"         # HH:MM:SS
    pedestrian_height: float = 1.1       # Ground-relative height z (m)
    grid_resolution: float = 1.0         # Spatial cell size dx (m)
    tmrt_tolerance: float = 0.5          # User tolerance epsilon_T (K)
    numerical_tolerance: float = 1e-6    # Numerical floating point slack
    sky_patch_configuration: int = 32    # Number of horizon search azimuths
    max_svf_search_dist_m: float = 60.0  # Maximum horizon search distance for SVF (m)
    backend: str = "cpu"                 # Backend engine: 'cpu', 'gpu', or 'auto'

    def __post_init__(self):
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be in [-90, 90], got {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude must be in [-180, 180], got {self.longitude}")
        if self.pedestrian_height < 0.0:
            raise ValueError(f"Pedestrian height must be >= 0, got {self.pedestrian_height}")
        if self.grid_resolution <= 0.0:
            raise ValueError(f"Grid resolution must be > 0, got {self.grid_resolution}")
        if self.tmrt_tolerance <= 0.0:
            raise ValueError(f"T_mrt tolerance must be > 0, got {self.tmrt_tolerance}")
        if self.sky_patch_configuration < 4:
            raise ValueError(f"Sky patch configuration must be >= 4, got {self.sky_patch_configuration}")
        if self.backend.lower() not in ("cpu", "gpu", "auto"):
            raise ValueError(f"Backend must be 'cpu', 'gpu', or 'auto', got {self.backend}")


# Default canonical materials
DEFAULT_WALL_MATERIAL = Material(
    id="default_wall",
    albedo=0.20,
    emissivity=0.90,
    surface_temperature=305.15,  # 32 C
    is_opaque=True
)

DEFAULT_GROUND_MATERIAL = Material(
    id="default_ground",
    albedo=0.15,
    emissivity=0.95,
    surface_temperature=308.15,  # 35 C
    is_opaque=True
)
