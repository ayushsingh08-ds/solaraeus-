"""
Longwave thermal radiation calculations from sky, walls, and ground onto a human cylinder.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np

from urban_comfort.config import Weather, Material, SIGMA


@dataclass
class LongwaveFluxes:
    """Longwave radiant flux densities incident on a standing human (W / m^2)."""
    l_sky: float
    l_wall: float
    l_ground: float
    l_up: np.ndarray
    l_down: np.ndarray
    l_side: np.ndarray
    l_total: np.ndarray


def compute_air_emissivity(air_temp_k: float, relative_humidity: float) -> float:
    """
    Computes clear-sky atmospheric emissivity using the Prata (1996) formulation.
    """
    temp_c = air_temp_k - 273.15
    # Saturation vapor pressure (hPa)
    e_sat = 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))
    e_act = e_sat * (relative_humidity / 100.0)

    # Precipitable water parameter
    w = 46.5 * (e_act / air_temp_k)
    eps_air = 1.0 - (1.0 + w) * np.exp(-np.sqrt(1.2 + 3.0 * w))
    return float(np.clip(eps_air, 0.70, 0.95))


def compute_longwave_fluxes(weather: Weather, svf: np.ndarray,
                            ground_material: Material,
                            wall_material: Material,
                            f_up: float = 0.06, f_down: float = 0.06,
                            f_side: float = 0.22) -> LongwaveFluxes:
    """
    Computes 6-directional longwave fluxes on a standing human model.
    """
    eps_air = compute_air_emissivity(weather.air_temperature, weather.relative_humidity)

    l_sky = eps_air * SIGMA * (weather.air_temperature ** 4)
    l_wall = wall_material.emissivity * SIGMA * (wall_material.surface_temperature ** 4)
    l_ground = ground_material.emissivity * SIGMA * (ground_material.surface_temperature ** 4)

    # Directional fluxes
    l_up = svf * l_sky + (1.0 - svf) * l_wall
    l_down = np.full_like(svf, l_ground)
    l_side = 0.5 * svf * l_sky + (1.0 - 0.5 * svf) * l_wall

    l_total = (
        f_up * l_up +
        f_down * l_down +
        f_side * 4.0 * l_side
    )

    return LongwaveFluxes(
        l_sky=l_sky,
        l_wall=l_wall,
        l_ground=l_ground,
        l_up=l_up,
        l_down=l_down,
        l_side=l_side,
        l_total=l_total
    )
