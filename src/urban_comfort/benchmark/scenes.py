"""
Synthetic Parametric Scene Generators for Scaling and Density Benchmarks.

Provides reproducible urban scenes:
- Domain sizes: 80m x 80m, 160m x 160m, 320m x 320m, 640m x 640m.
- Densities: Low (~10-15% coverage), Medium (~25-35% coverage), High (~45-60% coverage).
"""

from __future__ import annotations
import math
from typing import List, Tuple
import numpy as np

from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig


def create_scaling_scene(extent_m: float,
                         density: str = "medium",
                         grid_resolution: float = 1.0) -> Scene:
    """
    Constructs a reproducible synthetic urban scene with specified extent and density.
    
    Parameters:
        extent_m: Side length of the square domain in meters (e.g. 80, 160, 320).
        density: "low", "medium", or "high".
        grid_resolution: Grid resolution in meters (default 1.0m).
    """
    grid_cfg = PedestrianGridConfig(
        extent_x=extent_m,
        extent_y=extent_m,
        resolution=grid_resolution,
        pedestrian_height=1.1
    )
    scene = Scene(pedestrian_grid=grid_cfg)

    # Number of block subdivisions based on domain size
    # Base module: 40m blocks
    n_blocks = max(2, int(round(extent_m / 40.0)))
    block_pitch = extent_m / float(n_blocks)

    if density == "low":
        # Small footprint, wide setbacks (10-15% coverage)
        bldg_size = block_pitch * 0.35
        base_height = 15.0
    elif density == "medium":
        # Moderate footprint (25-35% coverage)
        bldg_size = block_pitch * 0.55
        base_height = 20.0
    elif density == "high":
        # Large footprint, narrow street canyons (45-60% coverage)
        bldg_size = block_pitch * 0.72
        base_height = 25.0
    else:
        raise ValueError(f"Unknown density level '{density}', choose 'low', 'medium', or 'high'.")

    margin = (block_pitch - bldg_size) / 2.0

    bldg_idx = 0
    for iy in range(n_blocks):
        for ix in range(n_blocks):
            # Center building in block
            x1 = ix * block_pitch + margin
            x2 = x1 + bldg_size
            y1 = iy * block_pitch + margin
            y2 = y1 + bldg_size

            # Modulate heights deterministically
            h_mod = ((ix * 7 + iy * 13) % 5) * 2.0  # Variation between 0 and 8m
            height = base_height + h_mod

            bldg = Building(
                id=f"bldg_{iy}_{ix}",
                footprint=BoundingBox2D(x1, x2, y1, y2),
                height=height
            )
            scene.add_building(bldg)
            bldg_idx += 1

    return scene
