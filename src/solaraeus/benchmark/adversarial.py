"""
Adversarial scenario definitions for stress-testing Certified Incremental SOLWEIG.
Covers:
- Low sun angle (long stretching shadows)
- Perpendicular wide walls
- Hidden-surface occlusion reveal
- Dense urban canyon infill
- Building translation (MoveBuilding)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import numpy as np

from solaraeus.core.geometry import (
    UrbanGrid, GeometricEdit, AddBuilding, RemoveBuilding, ChangeHeight, MoveBuilding
)
from solaraeus.core.solweig import WeatherParameters, SOLWEIGConfig


@dataclass
class AdversarialCase:
    name: str
    description: str
    grid: UrbanGrid
    edit: GeometricEdit
    weather: WeatherParameters
    config: SOLWEIGConfig


def create_adversarial_suite(grid_size: int = 100, dx: float = 1.0) -> List[AdversarialCase]:
    """Generates the full suite of adversarial stress test cases."""
    suite = []

    # Case 1: Low sun angle (15 deg) - Extreme shadow reach
    grid1 = UrbanGrid(np.zeros((grid_size, grid_size), dtype=np.float64), dx=dx)
    weather1 = WeatherParameters(sun_altitude_deg=15.0, sun_azimuth_deg=180.0)  # South
    config1 = SOLWEIGConfig(num_azimuth_svf=32, max_search_dist_m=80.0)
    # Add a 15m building in the southern half (row 60..70), shadow stretches far north
    edit1 = AddBuilding(xmin=45, xmax=55, ymin=65, ymax=75, height=15.0)
    suite.append(AdversarialCase(
        name="low_sun_angle_15deg",
        description="Low sun altitude (15 deg) casting a 55m shadow across the domain",
        grid=grid1,
        edit=edit1,
        weather=weather1,
        config=config1
    ))

    # Case 2: Perpendicular wide wall
    grid2 = UrbanGrid(np.zeros((grid_size, grid_size), dtype=np.float64), dx=dx)
    weather2 = WeatherParameters(sun_altitude_deg=40.0, sun_azimuth_deg=180.0)
    config2 = SOLWEIGConfig(num_azimuth_svf=32, max_search_dist_m=80.0)
    # Wide East-West wall: 40m wide, 18m tall
    edit2 = AddBuilding(xmin=30, xmax=70, ymin=55, ymax=58, height=18.0)
    suite.append(AdversarialCase(
        name="perpendicular_wide_wall",
        description="40m wide East-West wall perpendicular to solar azimuth",
        grid=grid2,
        edit=edit2,
        weather=weather2,
        config=config2
    ))

    # Case 3: Hidden-surface reveal (Occlusion Reveal)
    # Background building at rows 30..40, height 25m
    # Foreground building at rows 50..60, height 12m
    # Sun at South (180 deg). Remove foreground building to reveal background occlusion.
    h3 = np.zeros((grid_size, grid_size), dtype=np.float64)
    h3[30:40, 45:55] = 25.0  # Tall background building
    h3[50:60, 45:55] = 12.0  # Shorter foreground building
    grid3 = UrbanGrid(h3, dx=dx)
    weather3 = WeatherParameters(sun_altitude_deg=35.0, sun_azimuth_deg=180.0)
    config3 = SOLWEIGConfig(num_azimuth_svf=32, max_search_dist_m=80.0)
    edit3 = RemoveBuilding(xmin=45, xmax=55, ymin=50, ymax=60)
    suite.append(AdversarialCase(
        name="hidden_surface_reveal",
        description="Removal of foreground building revealing occlusion from taller background building",
        grid=grid3,
        edit=edit3,
        weather=weather3,
        config=config3
    ))

    # Case 4: Dense urban canyon infill
    # Two parallel rows of buildings (rows 35..40 and 60..65)
    h4 = np.zeros((grid_size, grid_size), dtype=np.float64)
    h4[35:45, 20:80] = 20.0
    h4[65:75, 20:80] = 20.0
    grid4 = UrbanGrid(h4, dx=dx)
    weather4 = WeatherParameters(sun_altitude_deg=50.0, sun_azimuth_deg=225.0)  # South-West
    config4 = SOLWEIGConfig(num_azimuth_svf=32, max_search_dist_m=80.0)
    # Insert infill building in the canyon
    edit4 = AddBuilding(xmin=45, xmax=55, ymin=45, ymax=65, height=18.0)
    suite.append(AdversarialCase(
        name="urban_canyon_infill",
        description="Infill building inserted between two tall parallel building rows",
        grid=grid4,
        edit=edit4,
        weather=weather4,
        config=config4
    ))

    # Case 5: Move building (Translation)
    h5 = np.zeros((grid_size, grid_size), dtype=np.float64)
    h5[40:50, 40:50] = 16.0
    grid5 = UrbanGrid(h5, dx=dx)
    weather5 = WeatherParameters(sun_altitude_deg=45.0, sun_azimuth_deg=135.0)  # South-East
    config5 = SOLWEIGConfig(num_azimuth_svf=32, max_search_dist_m=80.0)
    edit5 = MoveBuilding(xmin=40, xmax=50, ymin=40, ymax=50, shift_x=15, shift_y=15)
    suite.append(AdversarialCase(
        name="move_building_translation",
        description="Compound translation edit with simultaneous negative and positive height steps",
        grid=grid5,
        edit=edit5,
        weather=weather5,
        config=config5
    ))

    return suite
