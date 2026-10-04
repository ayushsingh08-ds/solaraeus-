"""
Unit tests for direct solar shadows and multi-azimuth sky view factor calculations.
"""

import math
import numpy as np
import pytest

from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor


def test_empty_scene_shadows():
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=40.0, extent_y=40.0, resolution=1.0))
    scene = Scene(pedestrian_grid=grid.config)
    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=(0.0, -math.cos(math.radians(45)), math.sin(math.radians(45))),
        is_daylight=True
    )

    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.all(shadow_mask == 1.0)


def test_nighttime_zero_shadow():
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=40.0, extent_y=40.0))
    scene = Scene(pedestrian_grid=grid.config)
    solar_pos = SolarPosition(
        altitude_deg=-10.0, azimuth_deg=180.0, zenith_deg=100.0,
        sun_vector=(0.0, 0.0, -1.0),
        is_daylight=False
    )

    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)
    assert np.all(shadow_mask == 0.0)


def test_analytical_shadow_length_and_direction():
    # Domain: 80x80m, resolution 1.0m. Building at center: [35, 45] x [35, 45], height 21.1m.
    # Pedestrian height = 1.1m. Delta H = 21.1 - 1.1 = 20.0m.
    # Solar altitude = 45.0 deg -> tan(45) = 1.0 -> Expected shadow length = 20.0m.
    # Sun azimuth = 180 deg (South) -> Sun vector points South (negative Y).
    # Rays from ground point point South (towards sun).
    # Ground points NORTH of building (Y > 45) looking South will have their ray intersect the building!
    # Expected shadowed Y range: Y in [45, 45 + 20] = [45, 65].
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1))
    scene = Scene(pedestrian_grid=grid.config)
    bldg = Building(
        id="test_bldg",
        footprint=BoundingBox2D(xmin=35.0, xmax=45.0, ymin=35.0, ymax=45.0),
        height=21.1
    )
    scene.add_building(bldg)

    alt_rad = math.radians(45.0)
    az_rad = math.radians(180.0)
    # Sun vector points TOWARDS the sun:
    # Azimuth 180 deg (South): East = sin(180)=0, North = cos(180)=-1
    sun_vec = (
        math.cos(alt_rad) * math.sin(az_rad),
        math.cos(alt_rad) * math.cos(az_rad),
        math.sin(alt_rad)
    )
    solar_pos = SolarPosition(
        altitude_deg=45.0, azimuth_deg=180.0, zenith_deg=45.0,
        sun_vector=sun_vec, is_daylight=True
    )

    shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos)

    # Building center X is 40. Cell index ix = 40.
    ix = 40
    # Inside shadow: Y = 55 (index iy = 55) -> must be shaded (0.0)
    assert shadow_mask[55, ix] == 0.0

    # Near shadow edge: Y = 64 (index iy = 64) -> shaded
    assert shadow_mask[64, ix] == 0.0

    # Outside shadow: Y = 67 (index iy = 67) -> illuminated (1.0)
    assert shadow_mask[67, ix] == 1.0

    # South of building: Y = 25 (index iy = 25) -> illuminated (1.0)
    assert shadow_mask[25, ix] == 1.0


def test_selective_masked_shadow_evaluation():
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=50.0, extent_y=50.0))
    scene = Scene(pedestrian_grid=grid.config)
    scene.add_building(Building("b1", BoundingBox2D(20, 30, 20, 30), height=15))

    solar_pos = SolarPosition(
        altitude_deg=50.0, azimuth_deg=220.0, zenith_deg=40.0,
        sun_vector=(-0.41, -0.49, 0.77), is_daylight=True
    )

    full_shadow = compute_direct_shadow_mask(scene, grid, solar_pos)

    # Selective ROI covering a 10x10 patch
    roi = np.zeros(grid.shape, dtype=bool)
    roi[25:35, 20:30] = True

    masked_shadow = compute_direct_shadow_mask(scene, grid, solar_pos, roi_mask=roi)

    # On ROI, masked_shadow must match full_shadow identically
    assert np.array_equal(masked_shadow[roi], full_shadow[roi])


def test_sky_view_factor():
    grid = PedestrianGrid(PedestrianGridConfig(extent_x=60.0, extent_y=60.0, resolution=1.0))
    scene = Scene(pedestrian_grid=grid.config)

    # Empty scene: SVF = 1.0 everywhere
    svf_empty = compute_sky_view_factor(scene, grid, num_azimuths=16)
    assert np.allclose(svf_empty, 1.0)

    # Add single building at center
    bldg = Building("b_svf", BoundingBox2D(25, 35, 25, 35), height=20.0)
    scene.add_building(bldg)

    svf = compute_sky_view_factor(scene, grid, num_azimuths=16, max_search_dist_m=30.0)

    # Near building wall (row 24, col 30), SVF must be noticeably reduced
    assert svf[24, 30] < 0.8
    # Far corner (row 5, col 5), SVF must remain high near 1.0
    assert svf[5, 5] > 0.95
    # Inside building footprint, SVF = 0.0
    assert svf[30, 30] == 0.0
