"""
SOLARAEUS Terrain Extension Module (Version 2.1.0-terrain).
"""

from solaraeus.terrain.dtm import TerrainGrid
from solaraeus.terrain.terrain_scene import TerrainAwareScene
from solaraeus.terrain.terrain_solver import TerrainAwareCPUSolver
from solaraeus.terrain.gpu_terrain import TerrainAwareGPUBackend

__all__ = [
    "TerrainGrid",
    "TerrainAwareScene",
    "TerrainAwareCPUSolver",
    "TerrainAwareGPUBackend",
]
