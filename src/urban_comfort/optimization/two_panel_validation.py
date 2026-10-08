"""
Multi-Path Physical Solver Validation for Two-Panel Intervention Candidates.

Validates candidate proposals across all three execution paths:
  1. CPU Full Recompute (Trusted Reference)
  2. GPU Full Recompute (High-Throughput Full Physics)
  3. GPU Incremental Recompute (Certified Multi-Mesh Selective Update)

Verifies that:
  CPU Full ≈ GPU Full ≈ GPU Incremental
within documented project physical and numerical tolerances without loosening any criteria.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, Material
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.reference.full_recompute import SimulationResult, full_recompute
from urban_comfort.incremental.mesh_update import AddMultiMeshEdit
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.two_panel_parameters import TwoPanelParams
from urban_comfort.optimization.parameters import ShadePanelParams
from urban_comfort.optimization.validation import (
    TOLERANCES_INCREMENTAL,
    TOLERANCES_SOLVER_EQUIVALENCE,
    PathComparisonMetrics,
    _compare_results,
)


@dataclass
class TwoPanelValidationReport:
    """Multi-path audit report for a two-panel intervention candidate."""
    candidate_id: str
    role: str
    params: Dict[str, Any]
    cpu_full_wall_s: float
    gpu_full_wall_s: float
    gpu_inc_wall_s: float
    gpu_inc_kernel_ms: float
    recomputed_cells: int
    reused_cells: int
    reused_fraction_pct: float
    ray_reduction_pct: float
    certificate_status: str
    certificate_violations: int
    max_predicted_bound_k: float
    cpu_full_vs_gpu_full: PathComparisonMetrics
    cpu_full_vs_gpu_inc: PathComparisonMetrics
    gpu_full_vs_gpu_inc: PathComparisonMetrics
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "role": self.role,
            "params": self.params,
            "cpu_full_wall_s": round(self.cpu_full_wall_s, 4),
            "gpu_full_wall_s": round(self.gpu_full_wall_s, 4),
            "gpu_inc_wall_s": round(self.gpu_inc_wall_s, 4),
            "gpu_inc_kernel_ms": round(self.gpu_inc_kernel_ms, 3),
            "recomputed_cells": self.recomputed_cells,
            "reused_cells": self.reused_cells,
            "reused_fraction_pct": round(self.reused_fraction_pct, 4),
            "ray_reduction_pct": round(self.ray_reduction_pct, 4),
            "certificate_status": self.certificate_status,
            "certificate_violations": self.certificate_violations,
            "max_predicted_bound_k": round(self.max_predicted_bound_k, 6),
            "cpu_full_vs_gpu_full": self.cpu_full_vs_gpu_full.to_dict(),
            "cpu_full_vs_gpu_inc": self.cpu_full_vs_gpu_inc.to_dict(),
            "gpu_full_vs_gpu_inc": self.gpu_full_vs_gpu_inc.to_dict(),
            "all_passed": self.all_passed,
        }


@dataclass
class TwoPanelMultiPathSummary:
    """Comprehensive summary of multi-path audits across all selected two-panel candidates."""
    reports: List[TwoPanelValidationReport]
    total_validated: int
    total_passed: int
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_validated": self.total_validated,
            "total_passed": self.total_passed,
            "all_passed": self.all_passed,
            "reports": [r.to_dict() for r in self.reports],
        }


def validate_two_panel_multi_path(
    candidate_id: str,
    params: TwoPanelParams,
    role: str,
    baseline_scene: Scene,
    baseline_result: SimulationResult,
    weather: Weather,
    config: SimulationConfig,
    gpu_engine: Optional[GPUIncrementalEngine] = None,
) -> TwoPanelValidationReport:
    """
    Executes CPU full, GPU full, and GPU incremental solvers for a two-panel candidate,
    and conducts complete cross-path parity audits against reference tolerances.
    """
    params_canon = params.canonicalize()

    # 1. Build Both Meshes
    (m1, poly1), (m2, poly2) = params_canon.build_geometries(id_prefix=f"VAL_{candidate_id}")
    mat1_id = f"VAL_MAT_{candidate_id}_1"
    mat2_id = f"VAL_MAT_{candidate_id}_2"
    m1.material_id = mat1_id
    m2.material_id = mat2_id

    mat1 = Material(id=mat1_id, albedo=float(params_canon.albedo1), emissivity=0.90, surface_temperature=308.15, is_opaque=True)
    mat2 = Material(id=mat2_id, albedo=float(params_canon.albedo2), emissivity=0.90, surface_temperature=308.15, is_opaque=True)

    edit = AddMultiMeshEdit([m1, m2])
    intervention_scene, edit_bounds = edit.apply(baseline_scene)

    updated_materials = dict(baseline_scene.materials)
    updated_materials[mat1_id] = mat1
    updated_materials[mat2_id] = mat2
    intervention_scene.materials = updated_materials

    # 2. Path 1: CPU Full Reference Simulation
    t0_cpu = time.perf_counter()
    res_cpu_full = full_recompute(intervention_scene, weather, config, backend="cpu")
    t_cpu_full = time.perf_counter() - t0_cpu

    # 3. Path 2: GPU Full Simulation
    t0_gpu_full = time.perf_counter()
    res_gpu_full = full_recompute(intervention_scene, weather, config, backend="gpu")
    t_gpu_full = time.perf_counter() - t0_gpu_full

    # 4. Path 3: GPU Incremental Simulation
    if gpu_engine is None:
        gpu_engine = GPUIncrementalEngine()

    t0_gpu_inc = time.perf_counter()
    inc_update_res, cert = gpu_engine.execute_certified_update(
        previous_scene=baseline_scene,
        updated_scene=intervention_scene,
        previous_result=baseline_result,
        edit=edit,
        weather=weather,
        config=config,
    )
    t_gpu_inc = time.perf_counter() - t0_gpu_inc
    res_gpu_inc = inc_update_res.result

    # Telemetry and metrics
    telemetry = getattr(gpu_engine, "_last_telemetry", {})
    gpu_kernel_ms = telemetry.get("kernel_time_ms", 0.0)

    recomputed = inc_update_res.recomputed_cells
    total_cells = inc_update_res.total_cells
    reused = total_cells - recomputed
    reused_pct = (reused / total_cells) * 100.0 if total_cells > 0 else 0.0
    ray_reduction_pct = reused_pct

    max_bound = float(np.max(cert.predicted_error_bound)) if hasattr(cert, "predicted_error_bound") else 0.0
    n_violations = getattr(cert, "n_violations", 0)

    # 5. Pairwise Cross-Path Comparisons
    # Path A vs Path B (1): CPU Full vs GPU Full (Mathematical Solver Equivalence)
    cmp_cpu_gpu_full = _compare_results(
        res_cpu_full, res_gpu_full,
        path_a_name="CPU_Full",
        path_b_name="GPU_Full",
        tolerances=TOLERANCES_SOLVER_EQUIVALENCE,
        comparison_type="solver_equivalence",
    )

    # Path A vs Path B (2): GPU Full vs GPU Incremental (Incremental Tracing Correctness)
    cmp_gpu_full_gpu_inc = _compare_results(
        res_gpu_full, res_gpu_inc,
        path_a_name="GPU_Full",
        path_b_name="GPU_Incremental",
        tolerances=TOLERANCES_INCREMENTAL,
        comparison_type="incremental_accuracy",
    )

    # Path A vs Path B (3): CPU Full vs GPU Incremental (Full End-to-End Parity)
    cmp_cpu_full_gpu_inc = _compare_results(
        res_cpu_full, res_gpu_inc,
        path_a_name="CPU_Full",
        path_b_name="GPU_Incremental",
        tolerances=TOLERANCES_INCREMENTAL,
        comparison_type="three_path_parity",
    )

    all_passed = (
        cmp_cpu_gpu_full.passed_all and
        cmp_gpu_full_gpu_inc.passed_all and
        cmp_cpu_full_gpu_inc.passed_all and
        n_violations == 0
    )

    return TwoPanelValidationReport(
        candidate_id=candidate_id,
        role=role,
        params=params_canon.to_dict(),
        cpu_full_wall_s=t_cpu_full,
        gpu_full_wall_s=t_gpu_full,
        gpu_inc_wall_s=t_gpu_inc,
        gpu_inc_kernel_ms=gpu_kernel_ms,
        recomputed_cells=recomputed,
        reused_cells=reused,
        reused_fraction_pct=reused_pct,
        ray_reduction_pct=ray_reduction_pct,
        certificate_status=cert.status,
        certificate_violations=n_violations,
        max_predicted_bound_k=max_bound,
        cpu_full_vs_gpu_full=cmp_cpu_gpu_full,
        cpu_full_vs_gpu_inc=cmp_cpu_full_gpu_inc,
        gpu_full_vs_gpu_inc=cmp_gpu_full_gpu_inc,
        all_passed=all_passed,
    )
