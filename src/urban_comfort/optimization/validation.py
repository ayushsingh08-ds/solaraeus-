"""
Multi-Path Physical Solver Validation for Selected Intervention Candidates.

Validates candidate proposals across all three execution paths:
  1. CPU Full Recompute (Trusted Reference)
  2. GPU Full Recompute (High-Throughput Full Physics)
  3. GPU Incremental Recompute (Certified Selective Update)

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
from urban_comfort.incremental.mesh_update import AddMeshEdit
from urban_comfort.backend.gpu_incremental import GPUIncrementalEngine
from urban_comfort.optimization.parameters import ShadePanelParams, build_panel_geometry
from urban_comfort.optimization.ledger import CandidateRecord, CandidateLedger


# Documented Project Physical Tolerances
TOLERANCES_INCREMENTAL = {
    "shadow_mask": {"name": "Direct Shadow Mask", "tol": 0.0, "unit": "-", "desc": "Binary obstacle projection"},
    "svf": {"name": "Sky View Factor (SVF)", "tol": 0.05, "unit": "-", "desc": "Certified SVF bound (B_T <= 0.50 K)"},
    "direct_irradiance": {"name": "Direct Shortwave Irradiance", "tol": 1e-4, "unit": "W/m2", "desc": "Direct beam flux"},
    "shortwave_flux": {"name": "Total Shortwave Flux", "tol": 2.00, "unit": "W/m2", "desc": "Absorbed shortwave flux (B_T <= 0.50 K)"},
    "longwave_flux": {"name": "Total Longwave Flux", "tol": 2.00, "unit": "W/m2", "desc": "Absorbed longwave flux (B_T <= 0.50 K)"},
    "tmrt": {"name": "Mean Radiant Temperature (Tmrt)", "tol": 0.50, "unit": "K", "desc": "Certified Tmrt tolerance"},
    "utci": {"name": "Thermal Comfort (UTCI)", "tol": 0.50, "unit": "degC", "desc": "Certified UTCI tolerance"},
}

TOLERANCES_SOLVER_EQUIVALENCE = {
    "shadow_mask": {"name": "Direct Shadow Mask", "tol": 0.0, "unit": "-", "desc": "Exact bit match"},
    "svf": {"name": "Sky View Factor (SVF)", "tol": 1e-12, "unit": "-", "desc": "Double precision machine epsilon"},
    "direct_irradiance": {"name": "Direct Shortwave Irradiance", "tol": 1e-12, "unit": "W/m2", "desc": "Machine precision"},
    "shortwave_flux": {"name": "Total Shortwave Flux", "tol": 1e-10, "unit": "W/m2", "desc": "Machine precision"},
    "longwave_flux": {"name": "Total Longwave Flux", "tol": 1e-10, "unit": "W/m2", "desc": "Machine precision"},
    "tmrt": {"name": "Mean Radiant Temperature (Tmrt)", "tol": 1e-10, "unit": "K", "desc": "Machine precision"},
    "utci": {"name": "Thermal Comfort (UTCI)", "tol": 0.0, "unit": "degC", "desc": "Exact bit match"},
}


@dataclass
class PathComparisonMetrics:
    """Pairwise field-by-field audit between two solver results."""
    path_a: str
    path_b: str
    comparison_type: str
    shadow_mismatches: int
    max_svf_diff: float
    mean_svf_diff: float
    max_dir_sw_diff: float
    max_tot_sw_diff: float
    max_tot_lw_diff: float
    max_tmrt_diff_k: float
    mean_tmrt_diff_k: float
    max_utci_diff_c: float
    mean_utci_diff_c: float
    passed_all: bool
    field_details: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_a": self.path_a,
            "path_b": self.path_b,
            "comparison_type": self.comparison_type,
            "shadow_mismatches": self.shadow_mismatches,
            "max_svf_diff": self.max_svf_diff,
            "mean_svf_diff": self.mean_svf_diff,
            "max_dir_sw_diff": self.max_dir_sw_diff,
            "max_tot_sw_diff": self.max_tot_sw_diff,
            "max_tot_lw_diff": self.max_tot_lw_diff,
            "max_tmrt_diff_k": self.max_tmrt_diff_k,
            "mean_tmrt_diff_k": self.mean_tmrt_diff_k,
            "max_utci_diff_c": self.max_utci_diff_c,
            "mean_utci_diff_c": self.mean_utci_diff_c,
            "passed_all": self.passed_all,
            "field_details": self.field_details,
        }


@dataclass
class CandidateValidationReport:
    """Multi-path audit report for a specific intervention candidate."""
    candidate_id: str
    role: str
    params: Dict[str, float]
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
class MultiPathValidationSummary:
    """Comprehensive summary of multi-path audits across all selected candidates."""
    reports: List[CandidateValidationReport]
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


def _compare_results(res_a: SimulationResult,
                     res_b: SimulationResult,
                     path_a_name: str,
                     path_b_name: str,
                     tolerances: Dict[str, Dict[str, Any]],
                     comparison_type: str) -> PathComparisonMetrics:
    """Computes field differences and compares against strict tolerances."""
    field_pairs = {
        "shadow_mask": (res_a.shadow_mask, res_b.shadow_mask),
        "svf": (res_a.svf, res_b.svf),
        "direct_irradiance": (res_a.direct_irradiance, res_b.direct_irradiance),
        "shortwave_flux": (res_a.shortwave_flux, res_b.shortwave_flux),
        "longwave_flux": (res_a.longwave_flux, res_b.longwave_flux),
        "tmrt": (res_a.tmrt, res_b.tmrt),
        "utci": (res_a.utci, res_b.utci),
    }

    field_details = {}
    passed_all = True

    for key, (arr_a, arr_b) in field_pairs.items():
        diff = arr_a - arr_b
        valid_mask = np.isfinite(diff)
        abs_diff = np.abs(diff[valid_mask])
        cfg = tolerances[key]
        tol = cfg["tol"]

        max_val = float(np.max(abs_diff)) if len(abs_diff) > 0 else 0.0
        mean_val = float(np.mean(abs_diff)) if len(abs_diff) > 0 else 0.0
        discrepancies = int(np.sum(abs_diff > (tol + 1e-14)))
        passed = (discrepancies == 0)

        if not passed:
            passed_all = False

        field_details[key] = {
            "field_name": cfg["name"],
            "unit": cfg["unit"],
            "tolerance": tol,
            "max_abs_diff": max_val,
            "mean_abs_diff": mean_val,
            "discrepancies": discrepancies,
            "passed": passed,
        }

    return PathComparisonMetrics(
        path_a=path_a_name,
        path_b=path_b_name,
        comparison_type=comparison_type,
        shadow_mismatches=field_details["shadow_mask"]["discrepancies"],
        max_svf_diff=field_details["svf"]["max_abs_diff"],
        mean_svf_diff=field_details["svf"]["mean_abs_diff"],
        max_dir_sw_diff=field_details["direct_irradiance"]["max_abs_diff"],
        max_tot_sw_diff=field_details["shortwave_flux"]["max_abs_diff"],
        max_tot_lw_diff=field_details["longwave_flux"]["max_abs_diff"],
        max_tmrt_diff_k=field_details["tmrt"]["max_abs_diff"],
        mean_tmrt_diff_k=field_details["tmrt"]["mean_abs_diff"],
        max_utci_diff_c=field_details["utci"]["max_abs_diff"],
        mean_utci_diff_c=field_details["utci"]["mean_abs_diff"],
        passed_all=passed_all,
        field_details=field_details,
    )


def validate_candidate_multi_path(
    candidate_id: str,
    params: ShadePanelParams,
    role: str,
    baseline_scene: Scene,
    baseline_result: SimulationResult,
    weather: Weather,
    config: SimulationConfig,
    gpu_engine: Optional[GPUIncrementalEngine] = None,
) -> CandidateValidationReport:
    """
    Executes CPU full, GPU full, and GPU incremental solvers for a single candidate,
    and conducts complete cross-path parity audits against reference tolerances.
    """
    # 1. Geometry and Edit
    mesh, poly = build_panel_geometry(params, mesh_id=f"VAL_{candidate_id}")
    edit = AddMeshEdit(mesh)
    intervention_scene, edit_bounds = edit.apply(baseline_scene)

    mat_panel = Material(
        id="SHADE_PANEL_ASSUMED_001",
        albedo=float(params.albedo),
        emissivity=0.90,
        surface_temperature=308.15,
        is_opaque=True,
    )
    materials = dict(baseline_scene.materials)
    materials["SHADE_PANEL_ASSUMED_001"] = mat_panel
    intervention_scene.materials = materials

    # 2. Path 1: CPU Full Recompute (Reference)
    cfg_cpu = SimulationConfig(
        latitude=config.latitude,
        longitude=config.longitude,
        date=config.date,
        local_time=config.local_time,
        pedestrian_height=config.pedestrian_height,
        grid_resolution=config.grid_resolution,
        tmrt_tolerance=config.tmrt_tolerance,
        sky_patch_configuration=config.sky_patch_configuration,
        max_svf_search_dist_m=config.max_svf_search_dist_m,
        backend="cpu",
    )
    t0_cpu = time.perf_counter()
    cpu_full_res = full_recompute(intervention_scene, weather, cfg_cpu, backend="cpu")
    t_cpu_full = time.perf_counter() - t0_cpu

    # 3. Path 2: GPU Full Recompute
    cfg_gpu = SimulationConfig(
        latitude=config.latitude,
        longitude=config.longitude,
        date=config.date,
        local_time=config.local_time,
        pedestrian_height=config.pedestrian_height,
        grid_resolution=config.grid_resolution,
        tmrt_tolerance=config.tmrt_tolerance,
        sky_patch_configuration=config.sky_patch_configuration,
        max_svf_search_dist_m=config.max_svf_search_dist_m,
        backend="gpu",
    )
    t0_gpu = time.perf_counter()
    gpu_full_res = full_recompute(intervention_scene, weather, cfg_gpu, backend="gpu")
    t_gpu_full = time.perf_counter() - t0_gpu

    # 4. Path 3: GPU Incremental Recompute
    engine = gpu_engine or GPUIncrementalEngine()
    grid = PedestrianGrid(baseline_scene.pedestrian_grid)
    if not engine._resident_state.is_resident:
        engine.preload_resident_baseline(baseline_scene, grid, baseline_result)

    t0_inc = time.perf_counter()
    inc_update_res, cert = engine.execute_certified_update(
        previous_scene=baseline_scene,
        updated_scene=intervention_scene,
        previous_result=baseline_result,
        edit=edit,
        weather=weather,
        config=cfg_gpu,
    )
    t_gpu_inc = time.perf_counter() - t0_inc
    gpu_inc_res = inc_update_res.result

    total_cells = inc_update_res.total_cells
    recomputed_cells = inc_update_res.recomputed_cells
    reused_cells = total_cells - recomputed_cells
    reused_pct = inc_update_res.reused_fraction * 100.0
    ray_reduction_pct = (reused_cells / total_cells * 100.0) if total_cells > 0 else 0.0

    last_m = engine.last_metrics
    kernel_ms = last_m.gpu_kernel_time_ms if last_m else (inc_update_res.time_selective_recompute_sec * 1000.0)

    # 5. Parity Audits
    # CPU Full vs GPU Full (Full solver equivalence)
    cmp_cpu_gpu_full = _compare_results(
        cpu_full_res, gpu_full_res,
        path_a_name="CPU Full", path_b_name="GPU Full",
        tolerances=TOLERANCES_SOLVER_EQUIVALENCE,
        comparison_type="full_solver_equivalence"
    )

    # CPU Full vs GPU Incremental (Incremental certified bounds)
    cmp_cpu_gpu_inc = _compare_results(
        cpu_full_res, gpu_inc_res,
        path_a_name="CPU Full", path_b_name="GPU Incremental",
        tolerances=TOLERANCES_INCREMENTAL,
        comparison_type="incremental_vs_cpu_full"
    )

    # GPU Full vs GPU Incremental (Incremental certified bounds)
    cmp_gpu_full_gpu_inc = _compare_results(
        gpu_full_res, gpu_inc_res,
        path_a_name="GPU Full", path_b_name="GPU Incremental",
        tolerances=TOLERANCES_INCREMENTAL,
        comparison_type="incremental_vs_gpu_full"
    )

    all_passed = cmp_cpu_gpu_full.passed_all and cmp_cpu_gpu_inc.passed_all and cmp_gpu_full_gpu_inc.passed_all

    return CandidateValidationReport(
        candidate_id=candidate_id,
        role=role,
        params=params.to_dict(),
        cpu_full_wall_s=t_cpu_full,
        gpu_full_wall_s=t_gpu_full,
        gpu_inc_wall_s=t_gpu_inc,
        gpu_inc_kernel_ms=kernel_ms,
        recomputed_cells=recomputed_cells,
        reused_cells=reused_cells,
        reused_fraction_pct=reused_pct,
        ray_reduction_pct=ray_reduction_pct,
        certificate_status=cert.status,
        certificate_violations=0 if cert.is_certified else int(getattr(cert, "violations_count", 1)),
        max_predicted_bound_k=float(np.max(cert.predicted_error_bound)),
        cpu_full_vs_gpu_full=cmp_cpu_gpu_full,
        cpu_full_vs_gpu_inc=cmp_cpu_gpu_inc,
        gpu_full_vs_gpu_inc=cmp_gpu_full_gpu_inc,
        all_passed=all_passed,
    )


def run_multi_path_validation_suite(
    ledger: CandidateLedger,
    baseline_scene: Scene,
    baseline_result: SimulationResult,
    weather: Weather,
    config: SimulationConfig,
    gpu_engine: Optional[GPUIncrementalEngine] = None,
    rng: Optional[np.random.Generator] = None,
) -> MultiPathValidationSummary:
    """
    Selects required candidate subset for complete multi-path validation:
      1. Best candidate
      2. Top 5 candidates (ranks 1..5)
      3. One random feasible candidate
      4. One candidate near a feasibility boundary
    Executes and summarizes physical audits for each.
    """
    feasible = ledger.get_feasible()
    if not feasible:
        return MultiPathValidationSummary(reports=[], total_validated=0, total_passed=0, all_passed=False)

    generator = rng or np.random.default_rng(42)
    selected_targets: List[Tuple[CandidateRecord, str]] = []
    seen_ids = set()

    # 1. Top 5 candidates (including best)
    top_5 = ledger.get_top_n(5)
    for rank, cand in enumerate(top_5, start=1):
        role = "best_candidate" if rank == 1 else f"top_{rank}_candidate"
        selected_targets.append((cand, role))
        seen_ids.add(cand.candidate_id)

    # 2. One random feasible candidate (excluding already selected)
    remaining_feasible = [c for c in feasible if c.candidate_id not in seen_ids]
    if remaining_feasible:
        rand_cand = generator.choice(remaining_feasible)
        selected_targets.append((rand_cand, "random_feasible_candidate"))
        seen_ids.add(rand_cand.candidate_id)
    else:
        selected_targets.append((feasible[-1], "random_feasible_candidate"))

    # 3. One candidate near a feasibility boundary (e.g. closest to height limit 2.5m or boundary)
    boundary_candidates = sorted(
        feasible,
        key=lambda c: abs(c.params.get("height", 3.0) - 2.50)
    )
    boundary_cand = boundary_candidates[0]
    for bc in boundary_candidates:
        if bc.candidate_id not in seen_ids:
            boundary_cand = bc
            break
    selected_targets.append((boundary_cand, "boundary_candidate"))

    reports: List[CandidateValidationReport] = []
    engine = gpu_engine or GPUIncrementalEngine()

    for cand_rec, role in selected_targets:
        params = ShadePanelParams.from_dict(cand_rec.params)
        rep = validate_candidate_multi_path(
            candidate_id=cand_rec.candidate_id,
            params=params,
            role=role,
            baseline_scene=baseline_scene,
            baseline_result=baseline_result,
            weather=weather,
            config=config,
            gpu_engine=engine,
        )
        reports.append(rep)

    total_validated = len(reports)
    total_passed = sum(1 for r in reports if r.all_passed)
    all_passed = (total_passed == total_validated)

    return MultiPathValidationSummary(
        reports=reports,
        total_validated=total_validated,
        total_passed=total_passed,
        all_passed=all_passed,
    )
