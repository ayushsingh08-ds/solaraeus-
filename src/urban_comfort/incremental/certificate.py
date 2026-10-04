"""
Computable error certificate engine for certified incremental microclimate simulations.
Provides closed-form, mathematically sound upper bounds on T_mrt error prior to recomputation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Any
import math
import numpy as np

from urban_comfort.config import Weather, SimulationConfig, SIGMA
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.radiation.longwave import compute_air_emissivity
from urban_comfort.incremental.update import GeometricEdit, AddBuildingEdit, RemoveBuildingEdit, ChangeHeightEdit, MoveBuildingEdit
from urban_comfort.incremental.affected_region import compute_candidate_affected_region
from urban_comfort.reference.full_recompute import SimulationResult


class CertificateViolationError(Exception):
    """Raised when actual numerical error exceeds the predicted certificate upper bound."""
    pass


@dataclass
class ErrorCertificate:
    """Certified upper bound and audit contract for incremental reuse."""
    status: str                            # "certified", "uncertified", or "fallback"
    tolerance: float                       # User tolerance threshold epsilon_T (K)
    predicted_error_bound: np.ndarray      # Shape (ny, nx) B_T(x) in Kelvin
    max_predicted_bound: float             # Max B_T across domain (K)
    affected_cells: int                    # Cells where B_T > tolerance (dirty)
    reused_cells: int                      # Cells where B_T <= tolerance (safe for reuse)
    total_cells: int
    assumptions: List[str]                 # Documented physical and numerical assumptions
    reasons_for_fallback: Optional[str]    # Reason if status == "fallback"

    @property
    def is_certified(self) -> bool:
        return self.status == "certified"

    @property
    def reused_fraction(self) -> float:
        return self.reused_cells / float(self.total_cells) if self.total_cells > 0 else 0.0


@dataclass
class CertificateVerification:
    """Pointwise verification diagnostics comparing actual error against certificate bound."""
    is_valid: bool                         # True if actual_error <= predicted_bound + numerical_slack everywhere
    num_violations: int                    # Number of cells where actual > bound
    max_violation: float                   # Max (actual_error - predicted_bound) (K)
    reused_max_error: float                # Max actual error among reused cells (K)
    is_within_tolerance: bool              # True if reused_max_error <= tolerance
    actual_error_map: np.ndarray           # Shape (ny, nx) actual |T_inc - T_full|
    slack_map: np.ndarray                  # Shape (ny, nx) predicted_bound - actual_error (>= 0 for sound bound)


def compute_svf_decay_bound(grid: PedestrianGrid,
                            edit_bounds_3d: Tuple[float, float, float, float, float, float],
                            max_search_dist_m: float) -> np.ndarray:
    """
    Computes a conservative upper bound on |Delta SVF(x)| as a function of Euclidean
    distance from the edit bounding box.
    Delta SVF(x) <= min(1.0, (w_proj * delta_h) / (2 * pi * r^2)).
    Beyond max_search_dist_m, Delta SVF is strictly 0.
    """
    ny, nx = grid.shape
    dx = grid.dx
    xmin, xmax, ymin, ymax, zmin, zmax = edit_bounds_3d

    delta_h = max(0.0, zmax - zmin)
    if delta_h <= 1e-6:
        return np.zeros((ny, nx), dtype=np.float64)

    # 2D coordinates of pedestrian cell centers
    X = grid.X
    Y = grid.Y

    # Distance to axis-aligned bounding box (0 inside, Euclidean distance outside)
    dx_dist = np.maximum(0.0, np.maximum(xmin - X, X - xmax))
    dy_dist = np.maximum(0.0, np.maximum(ymin - Y, Y - ymax))
    dist = np.hypot(dx_dist, dy_dist)

    # Characteristic projected width
    width_m = max(xmax - xmin, ymax - ymin)
    w_proj = math.sqrt(2.0) * max(dx, width_m)

    # Solid angle bound: Delta_Omega <= min(2*pi, (w_proj * delta_h) / r^2)
    r_eff = np.maximum(dx, dist)
    svf_bound = (w_proj * delta_h) / (2.0 * math.pi * (r_eff ** 2))

    # Cells inside or adjacent to footprint can change up to 1.0
    svf_bound[dist < dx] = 1.0
    svf_bound = np.clip(svf_bound, 0.0, 1.0)

    # Strict zero cutoff beyond maximum horizon search distance
    box_radius = 0.5 * math.hypot(xmax - xmin, ymax - ymin)
    svf_bound[dist > (max_search_dist_m + box_radius)] = 0.0

    return svf_bound


def generate_error_certificate(scene_before: Scene,
                               scene_after: Scene,
                               edit: GeometricEdit,
                               cached_result: SimulationResult,
                               solar_pos: SolarPosition,
                               grid: PedestrianGrid,
                               weather: Weather,
                               config: SimulationConfig) -> ErrorCertificate:
    """
    Constructs a certified upper bound B_T(x) in O(1) vectorized operations per cell.
    """
    ny, nx = grid.shape
    tolerance_k = config.tmrt_tolerance

    # 1. Candidate affected region for direct shadows
    cand_res = compute_candidate_affected_region(scene_before, scene_after, edit, solar_pos, grid)
    if cand_res.is_fallback:
        return ErrorCertificate(
            status="fallback",
            tolerance=tolerance_k,
            predicted_error_bound=np.full((ny, nx), float("inf")),
            max_predicted_bound=float("inf"),
            affected_cells=ny * nx,
            reused_cells=0,
            total_cells=ny * nx,
            assumptions=["Low solar altitude or numerical instability mandated full fallback."],
            reasons_for_fallback=cand_res.fallback_reason
        )

    # 2. Direct shortwave potential perturbation
    alt_rad = solar_pos.altitude_rad
    sin_alt = math.sin(alt_rad)
    sx, sy, _ = solar_pos.sun_vector
    # Direct shortwave flux received by standing human in full sunlight
    f_up = 0.06
    f_down = 0.06
    f_side = 0.22
    a_k = 0.70
    a_l = 0.97

    # Extract materials from scene (or fall back to defaults)
    from urban_comfort.config import DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
    wall_mat = scene_after.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
    ground_mat = scene_after.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)
    albedo_ground = ground_mat.albedo
    albedo_wall = wall_mat.albedo

    # Human standing cylinder sums direct beam across exposed vertical cardinal faces: |sx| + |sy|
    side_direct_factor = abs(sx) + abs(sy)
    k_dir_max_step = weather.direct_normal_irradiance * (
        f_up * sin_alt +
        f_side * side_direct_factor +
        f_down * albedo_ground * sin_alt
    )
    delta_s_dir = np.where(cand_res.candidate_mask, a_k * k_dir_max_step, 0.0)

    # 3. SVF solid-angle decay bound
    _, edit_bounds_3d = edit.apply(scene_before)
    delta_svf_max = compute_svf_decay_bound(grid, edit_bounds_3d, config.max_svf_search_dist_m)

    # 4. Diffuse and Longwave sensitivity
    c_diff = (
        f_up * weather.diffuse_horizontal_irradiance +
        f_side * 4.0 * (0.5 * weather.diffuse_horizontal_irradiance +
                        0.5 * albedo_wall * (weather.direct_normal_irradiance + weather.diffuse_horizontal_irradiance)) +
        f_down * albedo_ground * weather.diffuse_horizontal_irradiance
    )
    delta_s_diff = a_k * c_diff * delta_svf_max

    eps_air = compute_air_emissivity(weather.air_temperature, weather.relative_humidity)
    l_sky = eps_air * SIGMA * (weather.air_temperature ** 4)
    l_wall = wall_mat.emissivity * SIGMA * (wall_mat.surface_temperature ** 4)
    l_contrast = abs(l_sky - l_wall)

    c_long = (f_up + 2.0 * f_side) * l_contrast
    delta_s_long = a_l * c_long * delta_svf_max

    # Total flux perturbation bound: Delta S_max(x)
    delta_s_total = delta_s_dir + delta_s_diff + delta_s_long

    # 5. Concave Interval Stefan-Boltzmann propagation:
    # S_cached = sigma * (T_mrt_cached + 273.15)^4
    s_cached = SIGMA * ((cached_result.tmrt + 273.15) ** 4)
    s_lower = np.maximum(1.0, s_cached - delta_s_total)

    t_cached = np.power(s_cached / SIGMA, 0.25)
    t_lower = np.power(s_lower / SIGMA, 0.25)
    b_t = t_cached - t_lower  # Conservative bound in Kelvin

    # Dirty mask: cells where bound exceeds tolerance
    dirty_mask = b_t > float(tolerance_k)
    affected_count = int(np.sum(dirty_mask))
    reused_count = (ny * nx) - affected_count

    assumptions = [
        "Standing rotationally symmetric cylinder with f_up=f_down=0.06, f_side=0.22",
        "Shortwave absorption a_k=0.70, longwave absorption a_l=0.97",
        "Direct shadow bounded by directional frustum Minkowski envelope + safety margin",
        "SVF bounded by solid-angle distance decay proportional to W*delta_h / (2*pi*r^2)",
        "Concave Stefan-Boltzmann interval propagation guarantees upper-bounding of both warming and cooling"
    ]

    return ErrorCertificate(
        status="certified",
        tolerance=tolerance_k,
        predicted_error_bound=b_t,
        max_predicted_bound=float(np.max(b_t)),
        affected_cells=affected_count,
        reused_cells=reused_count,
        total_cells=ny * nx,
        assumptions=assumptions,
        reasons_for_fallback=None
    )


def verify_certificate(certificate: ErrorCertificate,
                       incremental_tmrt: np.ndarray,
                       full_recomputed_tmrt: np.ndarray,
                       numerical_slack: float = 1e-10) -> CertificateVerification:
    """
    Verifies the mathematical soundness and tolerance compliance of an error certificate.
    """
    actual_error = np.abs(incremental_tmrt - full_recomputed_tmrt)
    predicted_bound = certificate.predicted_error_bound

    # Slack: bound - actual_error >= -numerical_slack
    slack = predicted_bound - actual_error
    violations_mask = (actual_error - predicted_bound) > numerical_slack
    num_violations = int(np.sum(violations_mask))
    max_violation = float(np.max(actual_error - predicted_bound)) if num_violations > 0 else 0.0

    # User contract check on reused cells: actual_error <= tolerance
    reused_mask = predicted_bound <= certificate.tolerance
    if np.any(reused_mask):
        reused_max_err = float(np.max(actual_error[reused_mask]))
        is_within_tol = reused_max_err <= (certificate.tolerance + numerical_slack)
    else:
        reused_max_err = 0.0
        is_within_tol = True

    is_valid = (num_violations == 0)

    if not is_valid:
        raise CertificateViolationError(
            f"Certificate violation detected! {num_violations} grid cells exceeded the predicted bound. "
            f"Maximum violation: {max_violation:.6e} K"
        )

    return CertificateVerification(
        is_valid=is_valid,
        num_violations=num_violations,
        max_violation=max_violation,
        reused_max_error=reused_max_err,
        is_within_tolerance=is_within_tol,
        actual_error_map=actual_error,
        slack_map=slack
    )
