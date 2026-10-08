"""
SOLARAEUS Terrain Extension Module (Version 2.1.0-terrain).
"""

from urban_comfort.terrain.dtm import TerrainGrid
from urban_comfort.terrain.terrain_scene import TerrainAwareScene
from urban_comfort.terrain.terrain_solver import TerrainAwareCPUSolver
from urban_comfort.terrain.gpu_terrain import TerrainAwareGPUBackend

__all__ = [
    "TerrainGrid",
    "TerrainAwareScene",
    "TerrainAwareCPUSolver",
    "TerrainAwareGPUBackend",
]
