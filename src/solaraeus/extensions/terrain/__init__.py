"""
SOLARAEUS Terrain Extension Module (Version 2.1.0-terrain).
"""

from solaraeus.extensions.terrain.dtm import TerrainGrid
from solaraeus.extensions.terrain.scene import TerrainAwareScene
from solaraeus.extensions.terrain.solver import TerrainAwareCPUSolver
from solaraeus.extensions.terrain.gpu import TerrainAwareGPUBackend

__all__ = [
    "TerrainGrid",
    "TerrainAwareScene",
    "TerrainAwareCPUSolver",
    "TerrainAwareGPUBackend",
]
