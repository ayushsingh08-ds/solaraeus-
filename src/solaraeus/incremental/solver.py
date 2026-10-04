"""
Certified Incremental SOLWEIG Solver.
Executes certificate evaluation and selective recomputation with provable error bounds.
"""

from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Optional
import numpy as np

from solaraeus.core.geometry import UrbanGrid, GeometricEdit, EditBoundingBox
from solaraeus.core.solweig import (
    ReferenceSOLWEIGSolver, WeatherParameters, SOLWEIGConfig, SOLWEIGState
)
from solaraeus.incremental.bounds import evaluate_certificate, CertificateResult


@dataclass
class IncrementalUpdateResult:
    """Detailed telemetry and fields resulting from a certified incremental update."""
    grid: UrbanGrid
    state: SOLWEIGState
    certificate: CertificateResult
    tolerance_k: float
    time_cert_sec: float
    time_recompute_sec: float
    time_total_sec: float
    num_dirty_cells: int
    total_cells: int

    @property
    def fraction_recomputed(self) -> float:
        return self.num_dirty_cells / float(self.total_cells) if self.total_cells > 0 else 0.0

    @property
    def fraction_reused(self) -> float:
        return 1.0 - self.fraction_recomputed


class IncrementalSOLWEIGSolver:
    """
    Maintains cached simulation state and applies certified incremental updates
    with guaranteed error bounds |T_mrt_inc - T_mrt_full| <= tolerance_k.
    """

    def __init__(self, initial_grid: UrbanGrid,
                 weather: Optional[WeatherParameters] = None,
                 config: Optional[SOLWEIGConfig] = None):
        self.weather = weather or WeatherParameters()
        self.config = config or SOLWEIGConfig()
        self.reference_solver = ReferenceSOLWEIGSolver(self.weather, self.config)

        # Baseline initialization
        self.current_grid = initial_grid.copy()
        self.cached_state = self.reference_solver.solve(self.current_grid)

    def apply_edit(self, edit: GeometricEdit, tolerance_k: float = 0.5) -> IncrementalUpdateResult:
        """
        Applies a geometric edit incrementally with certification:
        1. Computes certificate B_T(x) in O(1) per cell.
        2. Reuses state wherever B_T(x) <= tolerance_k.
        3. Selectively recomputes only dirty cells.
        """
        # Apply edit to geometry
        new_grid, bbox = self.current_grid.apply_edit(edit)

        # Step 1: Certificate Generation
        t0_cert = time.perf_counter()
        cert = evaluate_certificate(
            new_grid, self.cached_state, bbox, self.weather, self.config, tolerance_k
        )
        t_cert = time.perf_counter() - t0_cert

        # Step 2: Selective Recomputation
        t0_recompute = time.perf_counter()
        new_state = self.reference_solver.solve_dirty_cells(
            new_grid, self.cached_state, cert.dirty_mask
        )
        t_recompute = time.perf_counter() - t0_recompute

        # Update cache for subsequent chained edits
        self.current_grid = new_grid
        self.cached_state = new_state

        total_cells = new_grid.ny * new_grid.nx
        num_dirty = int(np.sum(cert.dirty_mask))

        return IncrementalUpdateResult(
            grid=new_grid,
            state=new_state,
            certificate=cert,
            tolerance_k=tolerance_k,
            time_cert_sec=t_cert,
            time_recompute_sec=t_recompute,
            time_total_sec=t_cert + t_recompute,
            num_dirty_cells=num_dirty,
            total_cells=total_cells
        )
