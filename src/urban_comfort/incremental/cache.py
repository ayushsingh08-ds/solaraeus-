"""
Simulation cache and field metadata tracking for certified incremental reuse.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List, Optional, Set, Any
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import Scene
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.reference.full_recompute import SimulationResult
from urban_comfort.incremental.dependency_graph import DependencyGraph


def compute_scene_hash(scene: Scene) -> str:
    """Computes a deterministic SHA-256 hash of the canonical scene configuration."""
    scene_dict = scene.to_dict()
    canonical_json = json.dumps(scene_dict, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_weather_hash(weather: Weather) -> str:
    """Computes a deterministic SHA-256 hash of weather boundary conditions."""
    data = (
        weather.air_temperature,
        weather.relative_humidity,
        weather.wind_speed,
        weather.wind_direction,
        weather.direct_normal_irradiance,
        weather.diffuse_horizontal_irradiance
    )
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


def compute_config_hash(config: SimulationConfig) -> str:
    """Computes a deterministic SHA-256 hash of simulation control parameters."""
    data = (
        config.latitude,
        config.longitude,
        config.date,
        config.local_time,
        config.pedestrian_height,
        config.grid_resolution,
        config.sky_patch_configuration
    )
    return hashlib.sha256(str(data).encode("utf-8")).hexdigest()


@dataclass
class FieldMetadata:
    """Audit metadata recording lineage and spatial validity of a cached field."""
    field_name: str
    dependencies: List[str]
    source_scene_hash: str
    source_config_hash: str
    source_weather_hash: str
    valid_mask: np.ndarray       # Shape (ny, nx) boolean mask indicating valid cells
    exact_or_approximate: str    # "exact" or "approximate"
    error_bound: Optional[np.ndarray] = None # Optional upper bound B(x) if approximate

    @property
    def is_fully_valid(self) -> bool:
        return bool(np.all(self.valid_mask))

    @property
    def valid_fraction(self) -> float:
        return float(np.mean(self.valid_mask))


class SimulationCache:
    """
    Maintains cached simulation fields, spatial validity masks, and input hashes.
    Guarantees that cached fields are only reused when dependencies remain provably valid.
    """

    def __init__(self, dep_graph: Optional[DependencyGraph] = None):
        self.dep_graph = dep_graph or DependencyGraph()

        # Input hashes
        self.scene_hash: Optional[str] = None
        self.config_hash: Optional[str] = None
        self.weather_hash: Optional[str] = None
        self.solar_position: Optional[SolarPosition] = None

        # Cached spatial arrays
        self.fields: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, FieldMetadata] = {}

    def populate(self, scene: Scene, weather: Weather, config: SimulationConfig,
                 result: SimulationResult, exact: bool = True):
        """Populates the cache with newly computed ground-truth simulation fields."""
        self.scene_hash = compute_scene_hash(scene)
        self.weather_hash = compute_weather_hash(weather)
        self.config_hash = compute_config_hash(config)

        ny = scene.pedestrian_grid.ny
        nx = scene.pedestrian_grid.nx
        full_valid_mask = np.ones((ny, nx), dtype=bool)

        field_data = {
            "shadow_mask": result.shadow_mask,
            "svf": result.svf,
            "direct_irradiance": result.direct_irradiance,
            "shortwave_flux": result.shortwave_flux,
            "longwave_flux": result.longwave_flux,
            "tmrt": result.tmrt,
            "utci": result.utci,
        }

        exact_str = "exact" if exact else "approximate"

        for name, arr in field_data.items():
            self.fields[name] = arr.copy()
            upstream = list(self.dep_graph.get_upstream_dependencies(name))
            self.metadata[name] = FieldMetadata(
                field_name=name,
                dependencies=upstream,
                source_scene_hash=self.scene_hash,
                source_config_hash=self.config_hash,
                source_weather_hash=self.weather_hash,
                valid_mask=full_valid_mask.copy(),
                exact_or_approximate=exact_str,
                error_bound=np.zeros_like(arr) if exact else None
            )

    def invalidate_fields(self, field_names: Set[str],
                          dirty_spatial_mask: Optional[np.ndarray] = None):
        """
        Invalidates specified fields either globally or within a candidate spatial region.
        """
        for name in field_names:
            if name in self.metadata:
                meta = self.metadata[name]
                if dirty_spatial_mask is None:
                    # Invalidate entire domain
                    meta.valid_mask[:] = False
                else:
                    # Mark candidate dirty region as invalid
                    meta.valid_mask[dirty_spatial_mask] = False

    def can_reuse_cell(self, field_name: str, iy: int, ix: int,
                       target_scene_hash: str, target_weather_hash: str,
                       target_config_hash: str) -> bool:
        """
        Checks whether cell (iy, ix) of a field can be safely reused for the target state.
        """
        if field_name not in self.metadata:
            return False

        meta = self.metadata[field_name]
        if not meta.valid_mask[iy, ix]:
            return False

        # If hashes match exactly, field is completely valid
        if (meta.source_scene_hash == target_scene_hash and
            meta.source_weather_hash == target_weather_hash and
            meta.source_config_hash == target_config_hash):
            return True

        return False

    def get_valid_reusable_mask(self, field_name: str) -> np.ndarray:
        """Returns boolean mask of spatial cells that remain valid for reuse."""
        if field_name not in self.metadata:
            return np.array([], dtype=bool)
        return self.metadata[field_name].valid_mask.copy()
