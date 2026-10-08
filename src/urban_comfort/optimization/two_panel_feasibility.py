"""
Geographic and Geometric Feasibility Validator for Two-Panel Interventions.

Evaluates candidates before expensive GPU/CPU simulations, enforcing:
1. Finite coordinates for both panels.
2. Individual panel dimension, area, and aspect ratio limits.
3. Pedestrian underside clearance for each panel.
4. Pedestrian corridor containment for each panel.
5. Prohibited zone obstruction checks for each panel.
6. Building collision and setback clearance for each panel.
7. Mutual panel non-intersection / collision avoidance.
8. Minimum panel-to-panel separation distance.
9. Combined maximum and minimum total canopy area.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
import shapely
from shapely.geometry import Polygon, MultiPolygon

from urban_comfort.optimization.parameters import build_panel_geometry
from urban_comfort.optimization.feasibility import (
    RejectionReason as SingleRejectionReason,
    FeasibilityConstraints,
    check_feasibility as check_single_feasibility,
)
from urban_comfort.optimization.two_panel_parameters import TwoPanelParams


class TwoPanelRejectionReason(str, Enum):
    """Machine-readable rejection categories for two-panel configurations."""
    VALID = "VALID"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    BUILDING_COLLISION = "BUILDING_COLLISION"
    INSUFFICIENT_CLEARANCE = "INSUFFICIENT_CLEARANCE"
    EXCEEDS_MAX_DIMENSIONS = "EXCEEDS_MAX_DIMENSIONS"
    BELOW_MIN_DIMENSIONS = "BELOW_MIN_DIMENSIONS"
    PROHIBITED_ZONE_OBSTRUCTION = "PROHIBITED_ZONE_OBSTRUCTION"
    CONSTRUCTION_CONSTRAINT_VIOLATION = "CONSTRUCTION_CONSTRAINT_VIOLATION"
    PANEL_COLLISION = "PANEL_COLLISION"
    INSUFFICIENT_PANEL_SEPARATION = "INSUFFICIENT_PANEL_SEPARATION"
    EXCEEDS_TOTAL_AREA = "EXCEEDS_TOTAL_AREA"
    BELOW_MIN_TOTAL_AREA = "BELOW_MIN_TOTAL_AREA"


@dataclass
class TwoPanelFeasibilityResult:
    """Outcome of geographic and geometric validation for a two-panel candidate."""
    is_valid: bool
    rejection_reason: TwoPanelRejectionReason
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": bool(self.is_valid),
            "rejection_reason": str(self.rejection_reason.value),
            "message": str(self.message),
            "details": self.details,
        }


@dataclass
class TwoPanelConstraints:
    """Configurable constraints for two-panel optimization."""
    single_constraints: FeasibilityConstraints = field(default_factory=FeasibilityConstraints)
    min_panel_separation_m: float = 2.0
    max_individual_area_m2: float = 40.0
    min_total_area_m2: float = 10.0
    max_total_area_m2: float = 60.0

    @classmethod
    def from_single_constraints(cls,
                                single: FeasibilityConstraints,
                                min_panel_separation_m: float = 2.0,
                                max_individual_area_m2: float = 40.0,
                                min_total_area_m2: float = 10.0,
                                max_total_area_m2: float = 60.0) -> TwoPanelConstraints:
        """Wraps single panel constraints with two-panel separation and aggregate area rules."""
        return cls(
            single_constraints=single,
            min_panel_separation_m=min_panel_separation_m,
            max_individual_area_m2=max_individual_area_m2,
            min_total_area_m2=min_total_area_m2,
            max_total_area_m2=max_total_area_m2,
        )


def check_two_panel_feasibility(params: TwoPanelParams,
                                constraints: TwoPanelConstraints) -> TwoPanelFeasibilityResult:
    """
    Evaluates two-panel parameters against geographic, pairwise, and regulatory rules.

    Returns:
        TwoPanelFeasibilityResult with machine-readable rejection category.
    """
    # 1. Finite Coordinates Check
    if not params.is_finite():
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.INVALID_COORDINATES,
            message="Two-panel parameters contain non-finite (NaN or Inf) values.",
            details={"params": params.to_dict()}
        )

    # 2. Total Area Limits
    total_area = params.total_area
    if total_area > constraints.max_total_area_m2:
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.EXCEEDS_TOTAL_AREA,
            message=f"Combined shade area ({total_area:.2f} m2) exceeds maximum allowable limit ({constraints.max_total_area_m2:.2f} m2).",
            details={"total_area_m2": total_area, "max_total_area_m2": constraints.max_total_area_m2}
        )
    if total_area < constraints.min_total_area_m2:
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.BELOW_MIN_TOTAL_AREA,
            message=f"Combined shade area ({total_area:.2f} m2) is below minimum allowable limit ({constraints.min_total_area_m2:.2f} m2).",
            details={"total_area_m2": total_area, "min_total_area_m2": constraints.min_total_area_m2}
        )

    # 3. Individual Panel Maximum Area Limits
    if params.area1 > constraints.max_individual_area_m2 or params.area2 > constraints.max_individual_area_m2:
        max_seen = max(params.area1, params.area2)
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.EXCEEDS_MAX_DIMENSIONS,
            message=f"Individual panel area ({max_seen:.2f} m2) exceeds individual limit ({constraints.max_individual_area_m2:.2f} m2).",
            details={"area1_m2": params.area1, "area2_m2": params.area2, "max_individual_m2": constraints.max_individual_area_m2}
        )

    # 4. Individual Feasibility Checks for Panel 1
    res1 = check_single_feasibility(params.panel1, constraints.single_constraints)
    if not res1.is_valid:
        # Map single rejection reason to two-panel enum
        reason_map = {
            SingleRejectionReason.INVALID_COORDINATES: TwoPanelRejectionReason.INVALID_COORDINATES,
            SingleRejectionReason.OUT_OF_BOUNDS: TwoPanelRejectionReason.OUT_OF_BOUNDS,
            SingleRejectionReason.BUILDING_COLLISION: TwoPanelRejectionReason.BUILDING_COLLISION,
            SingleRejectionReason.INSUFFICIENT_CLEARANCE: TwoPanelRejectionReason.INSUFFICIENT_CLEARANCE,
            SingleRejectionReason.EXCEEDS_MAX_DIMENSIONS: TwoPanelRejectionReason.EXCEEDS_MAX_DIMENSIONS,
            SingleRejectionReason.BELOW_MIN_DIMENSIONS: TwoPanelRejectionReason.BELOW_MIN_DIMENSIONS,
            SingleRejectionReason.PROHIBITED_ZONE_OBSTRUCTION: TwoPanelRejectionReason.PROHIBITED_ZONE_OBSTRUCTION,
            SingleRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION: TwoPanelRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION,
        }
        mapped_reason = reason_map.get(res1.rejection_reason, TwoPanelRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION)
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=mapped_reason,
            message=f"Panel 1 failed feasibility: {res1.message}",
            details={"failed_panel": 1, "panel1_result": res1.to_dict()}
        )

    # 5. Individual Feasibility Checks for Panel 2
    res2 = check_single_feasibility(params.panel2, constraints.single_constraints)
    if not res2.is_valid:
        reason_map = {
            SingleRejectionReason.INVALID_COORDINATES: TwoPanelRejectionReason.INVALID_COORDINATES,
            SingleRejectionReason.OUT_OF_BOUNDS: TwoPanelRejectionReason.OUT_OF_BOUNDS,
            SingleRejectionReason.BUILDING_COLLISION: TwoPanelRejectionReason.BUILDING_COLLISION,
            SingleRejectionReason.INSUFFICIENT_CLEARANCE: TwoPanelRejectionReason.INSUFFICIENT_CLEARANCE,
            SingleRejectionReason.EXCEEDS_MAX_DIMENSIONS: TwoPanelRejectionReason.EXCEEDS_MAX_DIMENSIONS,
            SingleRejectionReason.BELOW_MIN_DIMENSIONS: TwoPanelRejectionReason.BELOW_MIN_DIMENSIONS,
            SingleRejectionReason.PROHIBITED_ZONE_OBSTRUCTION: TwoPanelRejectionReason.PROHIBITED_ZONE_OBSTRUCTION,
            SingleRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION: TwoPanelRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION,
        }
        mapped_reason = reason_map.get(res2.rejection_reason, TwoPanelRejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION)
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=mapped_reason,
            message=f"Panel 2 failed feasibility: {res2.message}",
            details={"failed_panel": 2, "panel2_result": res2.to_dict()}
        )

    # 6. Panel-to-Panel Geometric Collision and Separation Checks
    _, poly1 = build_panel_geometry(params.panel1)
    _, poly2 = build_panel_geometry(params.panel2)

    # Collision (Overlap)
    if poly1.intersects(poly2):
        inter_area = float(poly1.intersection(poly2).area)
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.PANEL_COLLISION,
            message=f"Panels collide and overlap geometrically with {inter_area:.3f} m2 intersection.",
            details={"intersection_area_m2": inter_area}
        )

    # Minimum separation distance
    separation_dist = float(poly1.distance(poly2))
    if separation_dist < constraints.min_panel_separation_m:
        return TwoPanelFeasibilityResult(
            is_valid=False,
            rejection_reason=TwoPanelRejectionReason.INSUFFICIENT_PANEL_SEPARATION,
            message=f"Separation between panels ({separation_dist:.3f} m) is less than required minimum ({constraints.min_panel_separation_m:.2f} m).",
            details={
                "separation_distance_m": separation_dist,
                "min_separation_m": constraints.min_panel_separation_m,
            }
        )

    # Valid candidate
    return TwoPanelFeasibilityResult(
        is_valid=True,
        rejection_reason=TwoPanelRejectionReason.VALID,
        message="Candidate two-panel design satisfies all geographic, clearance, and pairwise separation rules.",
        details={
            "area1_m2": params.area1,
            "area2_m2": params.area2,
            "total_area_m2": total_area,
            "separation_distance_m": separation_dist,
        }
    )
