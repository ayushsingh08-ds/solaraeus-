"""
Stage 6: Urban Microclimate Optimization Problem Formulation.

Defines decision variables, geometric parameterizations, spatial constraints,
feasibility validation, and radiative microclimate objective evaluation for
overhead shade canopy placement in the Berlin Friedrichstraße corridor.
"""

from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import shapely
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate

from solaraeus.core.geometry.mesh import create_rotated_box_mesh, TriangleMesh
from solaraeus.core.geometry.scene import Scene
from solaraeus.incremental.mesh_update import AddMeshEdit, AddMultiMeshEdit
from solaraeus.reference.full_recompute import full_recompute, SimulationResult
from benchmarks.run_stage_5_performance_suite import build_scene_b_berlin


@dataclass
class CanopySpec:
    """Individual canopy geometric specification."""
    x: float          # Center Easting (m)
    y: float          # Center Northing (m)
    length: float     # Dimension along local axis (m)
    width: float      # Dimension perpendicular to local axis (m)
    heading_deg: float # Bearing orientation in degrees [0, 180]
    height: float     # Underside clearance above ground plane (m)
    thickness: float = 0.15 # Structural panel thickness (m)

    @property
    def area(self) -> float:
        return self.length * self.width

    def to_shapely_polygon(self) -> Polygon:
        """Constructs 2D rotated bounding polygon in world coordinates."""
        hx = self.length / 2.0
        hy = self.width / 2.0
        local_box = box(-hx, -hy, hx, hy)
        rotated = rotate(local_box, self.heading_deg, origin=(0.0, 0.0), use_radians=False)
        return translate(rotated, self.x, self.y)

    def to_mesh(self, mesh_id: str) -> TriangleMesh:
        """Constructs watertight 3D triangle mesh for radiative ray-tracing."""
        return create_rotated_box_mesh(
            box_id=mesh_id,
            center_x=self.x,
            center_y=self.y,
            width_x=self.length,
            width_y=self.width,
            height=self.thickness,
            angle_deg=self.heading_deg,
            zmin=self.height,
            material_id="default_wall"
        )


@dataclass
class OptimizationBounds:
    """Bounded hypercube for decision variables."""
    x_min: float = -7.0
    x_max: float = 7.0
    y_min: float = -35.0
    y_max: float = 35.0
    length_min: float = 4.0
    length_max: float = 8.0
    width_min: float = 2.0
    width_max: float = 4.0
    heading_min: float = 0.0
    heading_max: float = 180.0
    height_min: float = 3.0
    height_max: float = 4.5
    max_total_area_m2: float = 50.0  # Budget for K=2 canopies
    min_setback_from_walls_m: float = 1.0 # Setback from building facades at x = +/- 10m


@dataclass
class EvaluationRecord:
    """Record of a single physics simulation evaluation."""
    candidate_id: int
    params_vector: np.ndarray
    canopy_specs: List[CanopySpec]
    is_feasible: bool
    rejection_reason: str
    mean_tmrt_c: float
    p90_tmrt_c: float
    max_tmrt_c: float
    mean_utci_c: float
    cooling_delta_mean_k: float
    cooling_delta_p90_k: float
    wall_time_s: float
    timestamp: float = field(default_factory=time.time)


class UrbanOptimizationProblem:
    """
    Mathematical optimization problem for urban shade canopy intervention.
    
    Evaluates pedestrian comfort in the Berlin Friedrichstraße corridor:
    - Primary Objective: Minimise mean Tmrt across the pedestrian canyon corridor.
    - Constraints: Non-overlap between canopies, total area budget <= max_total_area,
      boundary containment in pedestrian right-of-way, wall facade setbacks >= 1m.
    """

    def __init__(self,
                 num_canopies: int = 2,
                 bounds: Optional[OptimizationBounds] = None,
                 backend: str = "gpu"):
        self.num_canopies = num_canopies
        self.bounds = bounds or OptimizationBounds()
        self.backend = backend

        # Load reference baseline scene and weather
        self.scene_base, _, self.weather, self.sim_config = build_scene_b_berlin()

        # Extract pedestrian corridor calculation receptor mask (x in [-10, 10], y in [-40, 40])
        grid_cfg = self.scene_base.pedestrian_grid
        xs = np.linspace(grid_cfg.origin_x, grid_cfg.origin_x + grid_cfg.extent_x, grid_cfg.nx)
        ys = np.linspace(grid_cfg.origin_y, grid_cfg.origin_y + grid_cfg.extent_y, grid_cfg.ny)
        X, Y = np.meshgrid(xs, ys)
        self.corridor_mask = (X >= -10.0) & (X <= 10.0) & (Y >= -40.0) & (Y <= 40.0)
        self.corridor_cells_count = int(np.sum(self.corridor_mask))

        # Evaluate no-intervention baseline once
        t0 = time.perf_counter()
        self.baseline_result = full_recompute(self.scene_base, self.weather, self.sim_config, backend=self.backend)
        self.baseline_sim_time = time.perf_counter() - t0

        base_corridor_tmrt = self.baseline_result.tmrt[self.corridor_mask]
        self.baseline_mean_tmrt = float(np.mean(base_corridor_tmrt))
        self.baseline_p90_tmrt = float(np.percentile(base_corridor_tmrt, 90))
        self.baseline_max_tmrt = float(np.max(base_corridor_tmrt))
        self.baseline_mean_utci = float(np.mean(self.baseline_result.utci[self.corridor_mask]))

        # State tracking
        self.evaluations: List[EvaluationRecord] = []
        self.eval_count = 0

    @property
    def dimension(self) -> int:
        """Total number of decision variables (6 per canopy)."""
        return self.num_canopies * 6

    def get_parameter_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns lower and upper bounding vectors in R^D."""
        b = self.bounds
        lower = []
        upper = []
        for _ in range(self.num_canopies):
            lower.extend([b.x_min, b.y_min, b.length_min, b.width_min, b.heading_min, b.height_min])
            upper.extend([b.x_max, b.y_max, b.length_max, b.width_max, b.heading_max, b.height_max])
        return np.array(lower, dtype=np.float64), np.array(upper, dtype=np.float64)

    def vector_to_specs(self, vec: np.ndarray) -> List[CanopySpec]:
        """Unpacks flat parameter vector into list of CanopySpec instances."""
        specs = []
        for i in range(self.num_canopies):
            offset = i * 6
            specs.append(CanopySpec(
                x=float(vec[offset + 0]),
                y=float(vec[offset + 1]),
                length=float(vec[offset + 2]),
                width=float(vec[offset + 3]),
                heading_deg=float(vec[offset + 4]),
                height=float(vec[offset + 5]),
                thickness=0.15
            ))
        return specs

    def specs_to_vector(self, specs: List[CanopySpec]) -> np.ndarray:
        """Packs list of CanopySpec instances into flat parameter vector."""
        vec = []
        for s in specs:
            vec.extend([s.x, s.y, s.length, s.width, s.heading_deg, s.height])
        return np.array(vec, dtype=np.float64)

    def check_feasibility(self, specs: List[CanopySpec]) -> Tuple[bool, str, float]:
        """
        Validates spatial, geometric, and urbanistic feasibility constraints.
        Returns (is_feasible, reason, penalty_magnitude).
        """
        total_area = sum(s.area for s in specs)
        if total_area > self.bounds.max_total_area_m2 + 1e-4:
            excess = total_area - self.bounds.max_total_area_m2
            return False, f"AREA_EXCEEDED (Total {total_area:.1f} m2 > {self.bounds.max_total_area_m2:.1f} m2)", excess * 2.0

        polys = [s.to_shapely_polygon() for s in specs]

        # 1. Check boundary containment & setback from facades
        # Buildings are at x <= -10 and x >= 10. Allowed x in [-9, 9] (1m setback).
        # Street corridor y in [-40, 40].
        allowed_boundary = box(-9.0, -39.0, 9.0, 39.0)
        for idx, p in enumerate(polys):
            if not allowed_boundary.contains(p):
                # Calculate extent of violation
                diff = p.difference(allowed_boundary)
                return False, f"BOUNDARY_VIOLATION (Canopy {idx+1} violates street setback)", diff.area * 5.0 + 1.0

        # 2. Check pairwise non-overlap constraint
        if len(polys) > 1:
            for i in range(len(polys)):
                for j in range(i + 1, len(polys)):
                    inter = polys[i].intersection(polys[j])
                    if inter.area > 1e-3:
                        return False, f"OVERLAP_VIOLATION (Canopy {i+1} and {j+1} overlap by {inter.area:.2f} m2)", inter.area * 10.0 + 2.0

        return True, "FEASIBLE", 0.0

    def evaluate(self, candidate_vector: np.ndarray) -> Tuple[float, EvaluationRecord]:
        """
        Executes a physics simulation evaluation for the candidate design.
        
        Returns:
            (objective_value, evaluation_record)
            where objective_value is to be MINIMISED.
        """
        t0 = time.perf_counter()
        self.eval_count += 1
        specs = self.vector_to_specs(candidate_vector)
        is_feasible, reason, penalty = self.check_feasibility(specs)

        if not is_feasible:
            # Penalized objective: baseline + 5.0K penalty + severity
            obj_val = self.baseline_mean_tmrt + 5.0 + penalty
            rec = EvaluationRecord(
                candidate_id=self.eval_count,
                params_vector=np.copy(candidate_vector),
                canopy_specs=specs,
                is_feasible=False,
                rejection_reason=reason,
                mean_tmrt_c=round(obj_val, 4),
                p90_tmrt_c=round(self.baseline_p90_tmrt + penalty, 4),
                max_tmrt_c=round(self.baseline_max_tmrt + penalty, 4),
                mean_utci_c=round(self.baseline_mean_utci + penalty, 4),
                cooling_delta_mean_k=-round(5.0 + penalty, 4),
                cooling_delta_p90_k=-round(penalty, 4),
                wall_time_s=round(time.perf_counter() - t0, 4)
            )
            self.evaluations.append(rec)
            return obj_val, rec

        # Build watertight 3D meshes and execute forward physics simulation
        meshes = [s.to_mesh(f"canopy_{idx+1}") for idx, s in enumerate(specs)]
        if len(meshes) == 1:
            edit = AddMeshEdit(meshes[0])
        else:
            edit = AddMultiMeshEdit(meshes)

        scene_interv, _ = edit.apply(self.scene_base)
        sim_res = full_recompute(scene_interv, self.weather, self.sim_config, backend=self.backend)

        wall_time = time.perf_counter() - t0

        # Extract thermal metrics over pedestrian corridor
        corridor_tmrt = sim_res.tmrt[self.corridor_mask]
        corridor_utci = sim_res.utci[self.corridor_mask]

        m_tmrt = float(np.mean(corridor_tmrt))
        p90_tmrt = float(np.percentile(corridor_tmrt, 90))
        max_tmrt = float(np.max(corridor_tmrt))
        m_utci = float(np.mean(corridor_utci))

        delta_m = self.baseline_mean_tmrt - m_tmrt
        delta_p90 = self.baseline_p90_tmrt - p90_tmrt

        rec = EvaluationRecord(
            candidate_id=self.eval_count,
            params_vector=np.copy(candidate_vector),
            canopy_specs=specs,
            is_feasible=True,
            rejection_reason="FEASIBLE",
            mean_tmrt_c=round(m_tmrt, 4),
            p90_tmrt_c=round(p90_tmrt, 4),
            max_tmrt_c=round(max_tmrt, 4),
            mean_utci_c=round(m_utci, 4),
            cooling_delta_mean_k=round(delta_m, 4),
            cooling_delta_p90_k=round(delta_p90, 4),
            wall_time_s=round(wall_time, 4)
        )
        self.evaluations.append(rec)
        return m_tmrt, rec
