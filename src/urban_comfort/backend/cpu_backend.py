"""
CPU Reference Simulation Backend for SOLARAEUS.

Wraps the trusted, validated CPU reference implementations for direct shadows,
directional visibility / SVF, and full thermal comfort recomputations.
"""

from __future__ import annotations
import time
from typing import Optional, Any
import numpy as np

from urban_comfort.backend.base import SimulationBackend, BackendProfileMetrics
from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.visibility.shadow import compute_direct_shadow_mask
from urban_comfort.visibility.directional_visibility import compute_sky_view_factor


class CPUBackend(SimulationBackend):
    """
    Trusted CPU simulation backend utilizing vectorized NumPy and CPU ray-mesh intersections.
    """

    def __init__(self):
        self._profile_metrics: Optional[BackendProfileMetrics] = None

    @property
    def name(self) -> str:
        return "cpu"

    def is_available(self) -> bool:
        return True

    @property
    def last_profile_metrics(self) -> Optional[BackendProfileMetrics]:
        return self._profile_metrics

    def compute_direct_shadow(self, scene: Scene,
                              grid: PedestrianGrid,
                              solar_pos: SolarPosition,
                              roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes direct solar shadow mask using the trusted CPU solver.
        """
        t0 = time.perf_counter()
        shadow_mask = compute_direct_shadow_mask(scene, grid, solar_pos, roi_mask=roi_mask)
        t_shadow = time.perf_counter() - t0

        n_rays = int(np.sum(roi_mask)) if roi_mask is not None else grid.total_cells
        n_tris = sum(len(m.triangles) for m in scene.get_active_meshes())
        n_bldgs = len(scene.get_active_buildings())

        self._profile_metrics = BackendProfileMetrics(
            backend_name="cpu",
            shadow_runtime_s=t_shadow,
            total_runtime_s=t_shadow,
            shadow_ray_count=n_rays,
            total_ray_count=n_rays,
            num_triangles=n_tris,
            num_buildings=n_bldgs,
            device_name="CPU"
        )
        return shadow_mask

    def compute_sky_view_factor(self, scene: Scene,
                                grid: PedestrianGrid,
                                num_azimuths: int = 32,
                                max_search_dist_m: float = 120.0,
                                roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes Sky View Factor using the trusted CPU horizon scan solver.
        """
        t0 = time.perf_counter()
        svf = compute_sky_view_factor(
            scene, grid,
            num_azimuths=num_azimuths,
            max_search_dist_m=max_search_dist_m,
            roi_mask=roi_mask
        )
        t_svf = time.perf_counter() - t0

        n_pts = int(np.sum(roi_mask)) if roi_mask is not None else grid.total_cells
        svf_rays = n_pts * num_azimuths
        n_tris = sum(len(m.triangles) for m in scene.get_active_meshes())
        n_bldgs = len(scene.get_active_buildings())

        self._profile_metrics = BackendProfileMetrics(
            backend_name="cpu",
            svf_runtime_s=t_svf,
            total_runtime_s=t_svf,
            svf_ray_count=svf_rays,
            total_ray_count=svf_rays,
            num_triangles=n_tris,
            num_buildings=n_bldgs,
            device_name="CPU"
        )
        return svf

    def full_simulate(self, scene: Scene,
                      weather: Weather,
                      config: SimulationConfig) -> Any:
        """
        Executes full simulation using the trusted CPU reference solver.
        """
        from urban_comfort.reference.full_recompute import full_recompute
        return full_recompute(scene, weather, config)
