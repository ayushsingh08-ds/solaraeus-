"""
Geographic Feasibility Validator for Intervention Candidates.

Evaluates candidates before expensive physics simulations, rejecting designs that:
- Leave the allowed intervention boundary.
- Collide with building geometry or violate wall setbacks.
- Violate pedestrian underside clearance.
- Obstruct prohibited vehicle or pedestrian corridors.
- Exceed dimensional or structural construction constraints.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from urban_comfort.optimization.parameters import ShadePanelParams, build_panel_geometry
from urban_comfort.geometry.scene import Scene


class RejectionReason(str, Enum):
    """Machine-readable rejection categories for infeasible designs."""
    VALID = "VALID"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    BUILDING_COLLISION = "BUILDING_COLLISION"
    INSUFFICIENT_CLEARANCE = "INSUFFICIENT_CLEARANCE"
    EXCEEDS_MAX_DIMENSIONS = "EXCEEDS_MAX_DIMENSIONS"
    BELOW_MIN_DIMENSIONS = "BELOW_MIN_DIMENSIONS"
    PROHIBITED_ZONE_OBSTRUCTION = "PROHIBITED_ZONE_OBSTRUCTION"
    CONSTRUCTION_CONSTRAINT_VIOLATION = "CONSTRUCTION_CONSTRAINT_VIOLATION"


@dataclass
class FeasibilityResult:
    """Evaluation outcome from the geographic feasibility validator."""
    is_valid: bool
    rejection_reason: RejectionReason
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
class FeasibilityConstraints:
    """Configurable geometric, urbanistic, and clearance constraints."""
    allowed_area: Optional[Polygon] = None
    prohibited_areas: List[Polygon] = field(default_factory=list)
    building_footprints: Optional[MultiPolygon] = None
    min_underside_height_m: float = 2.50
    max_underside_height_m: float = 5.50
    min_building_setback_m: float = 0.50
    min_area_m2: float = 5.0
    max_area_m2: float = 50.0
    min_length_m: float = 2.5
    max_length_m: float = 14.0
    min_width_m: float = 1.5
    max_width_m: float = 5.0
    min_aspect_ratio: float = 1.0
    max_aspect_ratio: float = 5.0
    containment_tolerance_m: float = 0.05

    @classmethod
    def from_scene(cls,
                   scene: Scene,
                   allowed_area: Optional[Polygon] = None,
                   prohibited_areas: Optional[List[Polygon]] = None,
                   min_underside_height_m: float = 2.50,
                   max_underside_height_m: float = 5.50,
                   min_building_setback_m: float = 0.50) -> FeasibilityConstraints:
        """Constructs constraints automatically from a 3D Scene container."""
        bldg_polys: List[Polygon] = []

        # From AABB buildings
        for b in scene.buildings.values():
            bp = Polygon([
                (b.xmin, b.ymin), (b.xmax, b.ymin),
                (b.xmax, b.ymax), (b.xmin, b.ymax)
            ])
            bldg_polys.append(bp)

        # From TriangleMeshes
        for m in scene.meshes.values():
            if m.num_vertices > 0:
                v = m.vertices[:, :2]
                from shapely.geometry import MultiPoint
                hull = MultiPoint(v).convex_hull
                if isinstance(hull, Polygon) and hull.area > 0.01:
                    bldg_polys.append(hull)

        combined_bldgs = unary_union(bldg_polys) if bldg_polys else None
        if isinstance(combined_bldgs, Polygon):
            combined_bldgs = MultiPolygon([combined_bldgs])

        return cls(
            allowed_area=allowed_area,
            prohibited_areas=prohibited_areas or [],
            building_footprints=combined_bldgs,
            min_underside_height_m=min_underside_height_m,
            max_underside_height_m=max_underside_height_m,
            min_building_setback_m=min_building_setback_m,
        )


def check_feasibility(params: ShadePanelParams,
                      constraints: FeasibilityConstraints) -> FeasibilityResult:
    """
    Evaluates candidate parameters against geographic and regulatory feasibility rules.
    
    Returns:
        FeasibilityResult with machine-readable rejection reason and metric details.
    """
    # 1. Finite Coordinates Check
    if not params.is_finite():
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.INVALID_COORDINATES,
            message="Candidate parameter contains non-finite (NaN or Inf) coordinate values.",
            details={"params": params.to_dict()}
        )

    # 2. Dimensions and Aspect Ratio Check
    area = params.area
    if area < constraints.min_area_m2 or params.length < constraints.min_length_m or params.width < constraints.min_width_m:
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.BELOW_MIN_DIMENSIONS,
            message=f"Panel footprint area ({area:.2f} m2) or dimensions below minimum allowable threshold.",
            details={"area_m2": area, "min_area_m2": constraints.min_area_m2, "length": params.length, "width": params.width}
        )

    if area > constraints.max_area_m2 or params.length > constraints.max_length_m or params.width > constraints.max_width_m:
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.EXCEEDS_MAX_DIMENSIONS,
            message=f"Panel footprint area ({area:.2f} m2) or dimensions exceed maximum allowable threshold ({constraints.max_area_m2} m2).",
            details={"area_m2": area, "max_area_m2": constraints.max_area_m2, "length": params.length, "width": params.width}
        )

    aspect_ratio = max(params.length, params.width) / max(1e-6, min(params.length, params.width))
    if aspect_ratio > constraints.max_aspect_ratio or aspect_ratio < constraints.min_aspect_ratio:
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION,
            message=f"Aspect ratio ({aspect_ratio:.2f}) violates construction limits [{constraints.min_aspect_ratio}, {constraints.max_aspect_ratio}].",
            details={"aspect_ratio": aspect_ratio, "max_aspect_ratio": constraints.max_aspect_ratio}
        )

    # 3. Pedestrian Underside Clearance Check
    if params.height < constraints.min_underside_height_m:
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.INSUFFICIENT_CLEARANCE,
            message=f"Underside height ({params.height:.2f} m) violates minimum pedestrian clearance ({constraints.min_underside_height_m:.2f} m).",
            details={"height_m": params.height, "min_clearance_m": constraints.min_underside_height_m}
        )

    if params.height > constraints.max_underside_height_m:
        return FeasibilityResult(
            is_valid=False,
            rejection_reason=RejectionReason.CONSTRUCTION_CONSTRAINT_VIOLATION,
            message=f"Underside height ({params.height:.2f} m) exceeds structural maximum limit ({constraints.max_underside_height_m:.2f} m).",
            details={"height_m": params.height, "max_height_m": constraints.max_underside_height_m}
        )

    # 4. Construct 2D Footprint Polygon
    _, panel_polygon = build_panel_geometry(params)

    # 5. Building Footprint Collision & Setback Check
    if constraints.building_footprints is not None:
        if panel_polygon.intersects(constraints.building_footprints):
            overlap = panel_polygon.intersection(constraints.building_footprints).area
            return FeasibilityResult(
                is_valid=False,
                rejection_reason=RejectionReason.BUILDING_COLLISION,
                message=f"Panel footprint collides directly with building geometry ({overlap:.2f} m2 collision overlap).",
                details={"collision_overlap_m2": overlap}
            )

        dist_to_bldgs = panel_polygon.distance(constraints.building_footprints)
        if dist_to_bldgs < constraints.min_building_setback_m:
            return FeasibilityResult(
                is_valid=False,
                rejection_reason=RejectionReason.BUILDING_COLLISION,
                message=f"Panel distance to nearest building ({dist_to_bldgs:.3f} m) violates minimum setback ({constraints.min_building_setback_m:.2f} m).",
                details={"distance_to_building_m": dist_to_bldgs, "min_setback_m": constraints.min_building_setback_m}
            )

    # 6. Prohibited Zone Collision Check
    for i, prohibited_zone in enumerate(constraints.prohibited_areas):
        if panel_polygon.intersects(prohibited_zone):
            overlap_area = panel_polygon.intersection(prohibited_zone).area
            return FeasibilityResult(
                is_valid=False,
                rejection_reason=RejectionReason.PROHIBITED_ZONE_OBSTRUCTION,
                message=f"Panel footprint intersects prohibited exclusion zone #{i} with {overlap_area:.2f} m2 overlap.",
                details={"zone_index": i, "overlap_area_m2": overlap_area}
            )

    # 7. Allowed Area Containment Check
    if constraints.allowed_area is not None:
        buffered_allowed = constraints.allowed_area.buffer(constraints.containment_tolerance_m)
        if not buffered_allowed.contains(panel_polygon):
            inter_area = constraints.allowed_area.intersection(panel_polygon).area
            containment_pct = (inter_area / max(1e-6, panel_polygon.area)) * 100.0
            return FeasibilityResult(
                is_valid=False,
                rejection_reason=RejectionReason.OUT_OF_BOUNDS,
                message=f"Panel footprint extends outside allowed intervention boundary (only {containment_pct:.1f}% contained).",
                details={"containment_pct": containment_pct, "panel_area": panel_polygon.area, "contained_area": inter_area}
            )

    # Passed all feasibility checks
    return FeasibilityResult(
        is_valid=True,
        rejection_reason=RejectionReason.VALID,
        message="Candidate design satisfies all geographic, spatial setback, and urban clearance constraints.",
        details={
            "area_m2": area,
            "aspect_ratio": aspect_ratio,
            "underside_height_m": params.height,
            "distance_to_building_m": float(panel_polygon.distance(constraints.building_footprints)) if constraints.building_footprints is not None else float("inf")
        }
    )
