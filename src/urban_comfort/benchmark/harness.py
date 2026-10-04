"""
Reproducible Benchmark Harness for Certified Incremental SOLWEIG Evaluation.

Implements Work Package 1 requirements:
- End-to-end timing comparison: full recomputation vs. incremental update.
- Granular phase timing: certificate creation, dependency analysis, affected-region projection,
  selective recomputation, result assembly, and cache maintenance.
- Strict 30-field schema recording all physical, numerical, and software metadata.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, field
import hashlib
import json
import time
import os
import psutil
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.reference.full_recompute import full_recompute, SimulationResult
from urban_comfort.incremental.update import GeometricEdit, incremental_update_certified
from urban_comfort.incremental.certificate import verify_certificate, ErrorCertificate
from urban_comfort.incremental.cache import SimulationCache, compute_scene_hash, compute_config_hash, compute_weather_hash
from urban_comfort.incremental.dependency_graph import DependencyGraph


SOFTWARE_VERSION = "0.2.0-research-prototype"


@dataclass
class BenchmarkRecord:
    """Standardized 30-field schema for reproducible SOLWEIG benchmark runs."""
    scene_id: str
    domain_width: float
    domain_height: float
    grid_resolution: float
    grid_cell_count: int
    building_count: int
    geometry_count: int
    edit_type: str
    edit_magnitude: float
    solar_altitude: float
    solar_azimuth: float
    weather_configuration: str
    tmrt_tolerance: float
    full_recompute_time: float
    incremental_total_time: float
    certificate_time: float
    dependency_analysis_time: float
    affected_region_time: float
    selective_recompute_time: float
    result_assembly_time: float
    reused_cell_count: int
    recomputed_cell_count: int
    maximum_tmrt_error: float
    mean_absolute_tmrt_error: float
    maximum_utci_error: float
    certificate_bound_maximum: float
    certificate_violations: int
    fallback_status: bool
    memory_usage_if_available: float   # Process RSS in Megabytes (MB)
    software_version: str
    configuration_hash: str

    @property
    def speedup(self) -> float:
        return self.full_recompute_time / self.incremental_total_time if self.incremental_total_time > 0 else 1.0

    @property
    def reused_fraction(self) -> float:
        return self.reused_cell_count / float(self.grid_cell_count) if self.grid_cell_count > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_current_rss_mb() -> float:
    """Returns current process resident memory size (RSS) in MB."""
    try:
        process = psutil.Process(os.getpid())
        return float(process.memory_info().rss) / (1024.0 * 1024.0)
    except Exception:
        return -1.0


def compute_combined_hash(scene: Scene, edit: GeometricEdit, weather: Weather, config: SimulationConfig) -> str:
    """Computes a deterministic SHA-256 hash identifying the experimental scenario."""
    s_hash = compute_scene_hash(scene)
    w_hash = compute_weather_hash(weather)
    c_hash = compute_config_hash(config)
    e_str = f"{edit.edit_type}_{getattr(edit, 'building_id', '')}_{getattr(edit, 'new_height', '')}"
    raw = f"{s_hash}_{w_hash}_{c_hash}_{e_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def run_benchmark_trial(scene_before: Scene,
                        edit: GeometricEdit,
                        weather: Weather,
                        config: SimulationConfig,
                        scene_id: str = "custom_scene",
                        edit_magnitude: float = 1.0,
                        cache: Optional[SimulationCache] = None) -> Tuple[BenchmarkRecord, SimulationResult, SimulationResult, ErrorCertificate]:
    """
    Executes a complete, instrumented benchmark trial comparing full recomputation
    against certified incremental update with granular phase timing.
    """
    # 0. Setup and baseline cache
    grid = PedestrianGrid(scene_before.pedestrian_grid)
    nx, ny = grid.nx, grid.ny
    total_cells = grid.total_cells

    # Baseline run
    res_baseline = full_recompute(scene_before, weather, config)
    if cache is not None:
        cache.populate(scene_before, weather, config, res_baseline)

    # Apply edit
    scene_after, _ = edit.apply(scene_before)

    # 1. Full End-to-End Recomputation Timing
    t0_full = time.perf_counter()
    res_full = full_recompute(scene_after, weather, config)
    full_recompute_time = time.perf_counter() - t0_full

    # 2. Incremental End-to-End Update with Microsecond Instrumentation
    t0_inc_total = time.perf_counter()

    # 2a. Dependency analysis and cache check
    t0_dep = time.perf_counter()
    dep_graph = DependencyGraph()
    invalidated_fields = dep_graph.get_invalidated_fields("geometry")
    t_dep = time.perf_counter() - t0_dep

    # 2b. Certified Incremental Update (includes certificate, affected-region, selective recompute, assembly)
    inc_update_res, cert = incremental_update_certified(
        scene_before, scene_after, res_baseline, edit, weather, config
    )
    incremental_total_time = time.perf_counter() - t0_inc_total

    res_inc = inc_update_res.result

    # Exact phase timings extracted directly from incremental instrumentation
    t_cert = float(res_inc.metadata.get("timing_certificate_sec", 0.0))
    t_recomp = float(res_inc.metadata.get("timing_selective_recompute_sec", 0.0))
    t_affected = float(res_inc.metadata.get("timing_candidate_region_sec", 0.0))
    t_assembly = float(res_inc.metadata.get("timing_assembly_sec", 0.0))

    # 3. Verification & Error Audit
    verif = verify_certificate(cert, res_inc.tmrt, res_full.tmrt)

    actual_tmrt_err = np.abs(res_inc.tmrt - res_full.tmrt)
    max_tmrt_err = float(np.max(actual_tmrt_err))
    mean_abs_tmrt_err = float(np.mean(actual_tmrt_err))

    actual_utci_err = np.abs(res_inc.utci - res_full.utci)
    max_utci_err = float(np.max(actual_utci_err))

    solar_alt = float(res_full.metadata.get("solar_altitude_deg", 0.0))
    solar_az = float(res_full.metadata.get("solar_azimuth_deg", 0.0))
    cfg_hash = compute_combined_hash(scene_before, edit, weather, config)

    weather_desc = f"Tair={weather.air_temperature-273.15:.1f}C_DNI={weather.direct_normal_irradiance:.0f}_DHI={weather.diffuse_horizontal_irradiance:.0f}"

    rec = BenchmarkRecord(
        scene_id=scene_id,
        domain_width=scene_before.pedestrian_grid.extent_x,
        domain_height=scene_before.pedestrian_grid.extent_y,
        grid_resolution=scene_before.pedestrian_grid.resolution,
        grid_cell_count=total_cells,
        building_count=len(scene_after.get_active_buildings()),
        geometry_count=len(scene_after.buildings),
        edit_type=edit.edit_type,
        edit_magnitude=edit_magnitude,
        solar_altitude=solar_alt,
        solar_azimuth=solar_az,
        weather_configuration=weather_desc,
        tmrt_tolerance=config.tmrt_tolerance,
        full_recompute_time=full_recompute_time,
        incremental_total_time=incremental_total_time,
        certificate_time=t_cert,
        dependency_analysis_time=t_dep,
        affected_region_time=t_affected,
        selective_recompute_time=t_recomp,
        result_assembly_time=t_assembly,
        reused_cell_count=cert.reused_cells,
        recomputed_cell_count=cert.affected_cells,
        maximum_tmrt_error=max_tmrt_err,
        mean_absolute_tmrt_error=mean_abs_tmrt_err,
        maximum_utci_error=max_utci_err,
        certificate_bound_maximum=float(cert.max_predicted_bound),
        certificate_violations=verif.num_violations,
        fallback_status=(cert.status == "fallback"),
        memory_usage_if_available=get_current_rss_mb(),
        software_version=SOFTWARE_VERSION,
        configuration_hash=cfg_hash
    )

    return rec, res_full, res_inc, cert


@dataclass
class ReproducibilityRecord:
    """Aggregated statistical metrics across N benchmark repetitions."""
    scene_id: str
    num_trials: int
    full_time_mean_sec: float
    full_time_std_sec: float
    full_time_median_sec: float
    full_time_min_sec: float
    full_time_max_sec: float
    full_time_ci95_sec: float
    inc_time_mean_sec: float
    inc_time_std_sec: float
    inc_time_median_sec: float
    inc_time_min_sec: float
    inc_time_max_sec: float
    inc_time_ci95_sec: float
    speedup_median: float
    speedup_mean: float
    reused_cells: int
    recomputed_cells: int
    reused_fraction: float
    max_actual_error_k: float
    violations_observed: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimingBreakdownRecord:
    """Detailed median phase timing audit for incremental vs full recomputation."""
    scene_id: str
    full_recompute_median_sec: float
    dependency_analysis_median_sec: float
    candidate_region_median_sec: float
    certificate_eval_median_sec: float
    selective_recompute_median_sec: float
    result_assembly_median_sec: float
    total_incremental_median_sec: float
    primary_end_to_end_speedup: float
    certificate_and_overhead_percentage: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def run_repeated_benchmark_trials(scene_before: Scene,
                                  edit: GeometricEdit,
                                  weather: Weather,
                                  config: SimulationConfig,
                                  n_trials: int = 5,
                                  scene_id: str = "custom_scene",
                                  edit_magnitude: float = 1.0) -> Tuple[ReproducibilityRecord, TimingBreakdownRecord, BenchmarkRecord, SimulationResult, SimulationResult, ErrorCertificate]:
    """
    Executes N identical trials of a benchmark scenario to measure statistical
    reproducibility and granular timing distributions.
    """
    full_times: List[float] = []
    inc_times: List[float] = []
    dep_times: List[float] = []
    cand_times: List[float] = []
    cert_times: List[float] = []
    recomp_times: List[float] = []
    assembly_times: List[float] = []

    last_rec: Optional[BenchmarkRecord] = None
    last_res_full: Optional[SimulationResult] = None
    last_res_inc: Optional[SimulationResult] = None
    last_cert: Optional[ErrorCertificate] = None

    for _ in range(n_trials):
        rec, res_full, res_inc, cert = run_benchmark_trial(
            scene_before, edit, weather, config,
            scene_id=scene_id, edit_magnitude=edit_magnitude
        )
        full_times.append(rec.full_recompute_time)
        inc_times.append(rec.incremental_total_time)
        dep_times.append(rec.dependency_analysis_time)
        cand_times.append(rec.affected_region_time)
        cert_times.append(rec.certificate_time)
        recomp_times.append(rec.selective_recompute_time)
        assembly_times.append(rec.result_assembly_time)

        last_rec = rec
        last_res_full = res_full
        last_res_inc = res_inc
        last_cert = cert

    # Statistical aggregations
    full_arr = np.array(full_times)
    inc_arr = np.array(inc_times)
    speedup_arr = full_arr / np.maximum(inc_arr, 1e-9)

    # 95% confidence interval half-width: 1.96 * std / sqrt(N)
    full_ci95 = float(1.96 * np.std(full_arr, ddof=1) / np.sqrt(n_trials)) if n_trials > 1 else 0.0
    inc_ci95 = float(1.96 * np.std(inc_arr, ddof=1) / np.sqrt(n_trials)) if n_trials > 1 else 0.0

    med_full = float(np.median(full_arr))
    med_inc = float(np.median(inc_arr))
    med_speedup = med_full / med_inc if med_inc > 0 else 1.0

    repro_rec = ReproducibilityRecord(
        scene_id=scene_id,
        num_trials=n_trials,
        full_time_mean_sec=float(np.mean(full_arr)),
        full_time_std_sec=float(np.std(full_arr, ddof=1)) if n_trials > 1 else 0.0,
        full_time_median_sec=med_full,
        full_time_min_sec=float(np.min(full_arr)),
        full_time_max_sec=float(np.max(full_arr)),
        full_time_ci95_sec=full_ci95,
        inc_time_mean_sec=float(np.mean(inc_arr)),
        inc_time_std_sec=float(np.std(inc_arr, ddof=1)) if n_trials > 1 else 0.0,
        inc_time_median_sec=med_inc,
        inc_time_min_sec=float(np.min(inc_arr)),
        inc_time_max_sec=float(np.max(inc_arr)),
        inc_time_ci95_sec=inc_ci95,
        speedup_median=med_speedup,
        speedup_mean=float(np.mean(speedup_arr)),
        reused_cells=last_rec.reused_cell_count,
        recomputed_cells=last_rec.recomputed_cell_count,
        reused_fraction=last_rec.reused_fraction,
        max_actual_error_k=last_rec.maximum_tmrt_error,
        violations_observed=last_rec.certificate_violations
    )

    med_cand = float(np.median(cand_times))
    med_cert = float(np.median(cert_times))
    med_dep = float(np.median(dep_times))
    med_recomp = float(np.median(recomp_times))
    med_assembly = float(np.median(assembly_times))
    overhead_sum = med_cand + med_cert + med_dep + med_assembly
    overhead_pct = (overhead_sum / med_inc * 100.0) if med_inc > 0 else 0.0

    timing_rec = TimingBreakdownRecord(
        scene_id=scene_id,
        full_recompute_median_sec=med_full,
        dependency_analysis_median_sec=med_dep,
        candidate_region_median_sec=med_cand,
        certificate_eval_median_sec=med_cert,
        selective_recompute_median_sec=med_recomp,
        result_assembly_median_sec=med_assembly,
        total_incremental_median_sec=med_inc,
        primary_end_to_end_speedup=med_speedup,
        certificate_and_overhead_percentage=overhead_pct
    )

    return repro_rec, timing_rec, last_rec, last_res_full, last_res_inc, last_cert
