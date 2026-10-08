"""
Conservative candidate affected-region calculation for direct shadows.
Projects changed 3D geometry along the solar-ray trajectory onto the pedestrian plane,
including old projection, new projection, intermediate convex envelope, and numerical safety margins.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Tuple, Optional, List
import numpy as np

from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.incremental.update import (
    GeometricEdit, AddBuildingEdit, RemoveBuildingEdit,
    ChangeHeightEdit, MoveBuildingEdit
)


@dataclass
class AffectedRegionResult:
    """Candidate affected region output with fallback diagnostics."""
    candidate_mask: np.ndarray             # (ny, nx) boolean mask: True where candidate region applies
    candidate_bbox: Tuple[float, float, float, float] # (xmin, xmax, ymin, ymax) in world coordinates
    is_fallback: bool                      # True if numerical instability forces full recomputation
    fallback_reason: Optional[str]         # Descriptive reason when is_fallback is True
    shadow_length_m: float                 # Estimated maximum shadow plume length (m)
    safety_margin_m: float                 # Applied safety margin padding (m)
    old_projection_bbox: Tuple[float, float, float, float]
    new_projection_bbox: Tuple[float, float, float, float]


def project_box_shadow(box_3d: Tuple[float, float, float, float, float, float],
                       solar_pos: SolarPosition, z_ped: float) -> Tuple[float, float, float, float, float]:
    """
    Projects a 3D box along the anti-sun trajectory onto the horizontal plane at z_ped.
    Returns (proj_xmin, proj_xmax, proj_ymin, proj_ymax, shadow_length_m).
    """
    xmin, xmax, ymin, ymax, zmin, zmax = box_3d
    delta_h = max(0.0, zmax - z_ped)

    alt_rad = solar_pos.altitude_rad
    if delta_h <= 0.0 or alt_rad <= 0.0:
        return (xmin, xmax, ymin, ymax, 0.0)

    tan_alt = math.tan(alt_rad)
    shadow_len = delta_h / tan_alt

    # Solar unit vector components: sx (East, +X), sy (North, +Y)
    # Ground shadow plume projects in anti-sun direction (-sx, -sy)
    sx, sy, _ = solar_pos.sun_vector
    norm_h = math.hypot(sx, sy)
    if norm_h > 1e-6:
        dx = - (sx / norm_h) * shadow_len
        dy = - (sy / norm_h) * shadow_len
    else:
        dx = 0.0
        dy = 0.0

    proj_xmin = min(xmin, xmin + dx)
    proj_xmax = max(xmax, xmax + dx)
    proj_ymin = min(ymin, ymin + dy)
    proj_ymax = max(ymax, ymax + dy)

    return (proj_xmin, proj_xmax, proj_ymin, proj_ymax, shadow_len)


def compute_candidate_affected_region(scene_before: Scene,
                                      scene_after: Scene,
                                      edit: GeometricEdit,
                                      solar_pos: SolarPosition,
                                      grid: PedestrianGrid,
                                      safety_margin_cells: int = 2,
                                      min_altitude_deg: float = 5.0) -> AffectedRegionResult:
    """
    Computes a conservative candidate affected region on the pedestrian grid.
    
    Guarantees:
    - Encompasses the old geometry footprint and shadow projection.
    - Encompasses the new geometry footprint and shadow projection.
    - Covers the convex envelope between them.
    - Includes a configurable safety margin (default 2 cells).
    - Safely falls back to full recomputation if solar altitude is too low or unstable.
    """
    ny, nx = grid.shape
    empty_bbox = (0.0, 0.0, 0.0, 0.0)
    full_mask = np.ones((ny, nx), dtype=bool)

    # 1. Fallback Check: Low Solar Altitude or Nighttime
    if not solar_pos.is_daylight:
        return AffectedRegionResult(
            candidate_mask=np.zeros((ny, nx), dtype=bool),
            candidate_bbox=empty_bbox,
            is_fallback=False,
            fallback_reason=None,
            shadow_length_m=0.0,
            safety_margin_m=0.0,
            old_projection_bbox=empty_bbox,
            new_projection_bbox=empty_bbox
        )

    if solar_pos.altitude_deg < min_altitude_deg:
        return AffectedRegionResult(
            candidate_mask=full_mask,
            candidate_bbox=(grid.origin_x, grid.origin_x + grid.config.extent_x,
                            grid.origin_y, grid.origin_y + grid.config.extent_y),
            is_fallback=True,
            fallback_reason=(
                f"Solar altitude ({solar_pos.altitude_deg:.2f} deg) is below numerical "
                f"stability limit ({min_altitude_deg} deg). Shadow projection extends infinitely; "
                f"full recomputation safely mandated."
            ),
            shadow_length_m=float("inf"),
            safety_margin_m=0.0,
            old_projection_bbox=empty_bbox,
            new_projection_bbox=empty_bbox
        )

    # 2. Extract Geometry and Project Shadows
    if isinstance(edit, AddBuildingEdit):
        old_box = (edit.building.xmin, edit.building.xmax, edit.building.ymin, edit.building.ymax, 0.0, 0.0)
        new_box = edit.building.bounds_3d
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_box_shadow(old_box, solar_pos, grid.z_ped)
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_box_shadow(new_box, solar_pos, grid.z_ped)
    elif isinstance(edit, RemoveBuildingEdit):
        bldg_old = scene_before.buildings[edit.building_id]
        old_box = bldg_old.bounds_3d
        new_box = (bldg_old.xmin, bldg_old.xmax, bldg_old.ymin, bldg_old.ymax, 0.0, 0.0)
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_box_shadow(old_box, solar_pos, grid.z_ped)
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_box_shadow(new_box, solar_pos, grid.z_ped)
    elif isinstance(edit, ChangeHeightEdit):
        bldg_old = scene_before.buildings[edit.building_id]
        old_box = bldg_old.bounds_3d
        new_box = (bldg_old.xmin, bldg_old.xmax, bldg_old.ymin, bldg_old.ymax, bldg_old.zmin, edit.new_height)
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_box_shadow(old_box, solar_pos, grid.z_ped)
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_box_shadow(new_box, solar_pos, grid.z_ped)
    elif isinstance(edit, MoveBuildingEdit):
        bldg_old = scene_before.buildings[edit.building_id]
        old_box = bldg_old.bounds_3d
        new_box = (bldg_old.xmin + edit.shift_x, bldg_old.xmax + edit.shift_x,
                   bldg_old.ymin + edit.shift_y, bldg_old.ymax + edit.shift_y,
                   bldg_old.zmin, bldg_old.zmax)
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_box_shadow(old_box, solar_pos, grid.z_ped)
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_box_shadow(new_box, solar_pos, grid.z_ped)
    elif type(edit).__name__ in ("AddMeshEdit", "RemoveMeshEdit", "ReplaceMeshEdit", "MoveMeshEdit", "ChangeMeshHeightEdit"):
        from urban_comfort.incremental.mesh_affected_region import project_mesh_shadow
        if type(edit).__name__ == "AddMeshEdit":
            mesh_old = None
            mesh_new = getattr(edit, "mesh")
        elif type(edit).__name__ == "RemoveMeshEdit":
            mesh_old = scene_before.meshes.get(getattr(edit, "mesh_id"))
            mesh_new = None
        elif type(edit).__name__ == "ReplaceMeshEdit":
            mesh_old = scene_before.meshes.get(getattr(edit, "mesh_id"))
            mesh_new = getattr(edit, "new_mesh")
        else: # MoveMeshEdit, ChangeMeshHeightEdit
            mesh_old = scene_before.meshes.get(getattr(edit, "mesh_id"))
            new_scene, _ = edit.apply(scene_before)
            mesh_new = new_scene.meshes.get(getattr(edit, "mesh_id"))

        if mesh_old is not None and mesh_old.enabled:
            p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_mesh_shadow(mesh_old, solar_pos, grid.z_ped)
        else:
            p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = 0.0, 0.0, 0.0, 0.0, 0.0

        if mesh_new is not None and mesh_new.enabled:
            p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_mesh_shadow(mesh_new, solar_pos, grid.z_ped)
        else:
            p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = 0.0, 0.0, 0.0, 0.0, 0.0
    elif type(edit).__name__ == "AddMultiMeshEdit":
        from urban_comfort.incremental.mesh_affected_region import project_mesh_shadow
        meshes = getattr(edit, "meshes", [])
        margin_m = safety_margin_cells * grid.dx
        if not meshes:
            return AffectedRegionResult(
                candidate_mask=np.zeros((ny, nx), dtype=bool),
                candidate_bbox=empty_bbox,
                is_fallback=False,
                fallback_reason=None,
                shadow_length_m=0.0,
                safety_margin_m=margin_m,
                old_projection_bbox=empty_bbox,
                new_projection_bbox=empty_bbox
            )

        # Boolean union of candidate masks across all meshes
        combined_cand_mask = np.zeros((ny, nx), dtype=bool)
        p_new_x1, p_new_y1 = float("inf"), float("inf")
        p_new_x2, p_new_y2 = float("-inf"), float("-inf")
        len_new = 0.0

        for m in meshes:
            if m.enabled:
                px1, px2, py1, py2, m_len = project_mesh_shadow(m, solar_pos, grid.z_ped)
                p_new_x1 = min(p_new_x1, px1)
                p_new_x2 = max(p_new_x2, px2)
                p_new_y1 = min(p_new_y1, py1)
                p_new_y2 = max(p_new_y2, py2)
                len_new = max(len_new, m_len)

                m_cand_x1 = px1 - margin_m
                m_cand_x2 = px2 + margin_m
                m_cand_y1 = py1 - margin_m
                m_cand_y2 = py2 + margin_m
                s_y, s_x = grid.bounding_box_slices(m_cand_x1, m_cand_x2, m_cand_y1, m_cand_y2)
                combined_cand_mask[s_y, s_x] = True

        cand_x1 = p_new_x1 - margin_m
        cand_x2 = p_new_x2 + margin_m
        cand_y1 = p_new_y1 - margin_m
        cand_y2 = p_new_y2 + margin_m

        return AffectedRegionResult(
            candidate_mask=combined_cand_mask,
            candidate_bbox=(cand_x1, cand_x2, cand_y1, cand_y2),
            is_fallback=False,
            fallback_reason=None,
            shadow_length_m=len_new,
            safety_margin_m=margin_m,
            old_projection_bbox=empty_bbox,
            new_projection_bbox=(p_new_x1, p_new_x2, p_new_y1, p_new_y2)
        )
    else:
        # Fallback for unknown edit type
        return AffectedRegionResult(
            candidate_mask=full_mask,
            candidate_bbox=(grid.origin_x, grid.origin_x + grid.config.extent_x,
                            grid.origin_y, grid.origin_y + grid.config.extent_y),
            is_fallback=True,
            fallback_reason=f"Unsupported edit type '{type(edit).__name__}'; full recompute mandated.",
            shadow_length_m=0.0,
            safety_margin_m=0.0,
            old_projection_bbox=empty_bbox,
            new_projection_bbox=empty_bbox
        )

    old_proj_bbox = (p_old_x1, p_old_x2, p_old_y1, p_old_y2)
    new_proj_bbox = (p_new_x1, p_new_x2, p_new_y1, p_new_y2)

    # 4. Encompassing Envelope + Safety Margin
    margin_m = safety_margin_cells * grid.dx
    if old_proj_bbox != empty_bbox and new_proj_bbox != empty_bbox:
        comb_x1 = min(p_old_x1, p_new_x1)
        comb_x2 = max(p_old_x2, p_new_x2)
        comb_y1 = min(p_old_y1, p_new_y1)
        comb_y2 = max(p_old_y2, p_new_y2)
    elif old_proj_bbox != empty_bbox:
        comb_x1, comb_x2, comb_y1, comb_y2 = p_old_x1, p_old_x2, p_old_y1, p_old_y2
    else:
        comb_x1, comb_x2, comb_y1, comb_y2 = p_new_x1, p_new_x2, p_new_y1, p_new_y2

    cand_x1 = comb_x1 - margin_m
    cand_x2 = comb_x2 + margin_m
    cand_y1 = comb_y1 - margin_m
    cand_y2 = comb_y2 + margin_m

    slice_y, slice_x = grid.bounding_box_slices(cand_x1, cand_x2, cand_y1, cand_y2)
    candidate_mask = np.zeros((ny, nx), dtype=bool)
    candidate_mask[slice_y, slice_x] = True

    return AffectedRegionResult(
        candidate_mask=candidate_mask,
        candidate_bbox=(cand_x1, cand_x2, cand_y1, cand_y2),
        is_fallback=False,
        fallback_reason=None,
        shadow_length_m=max(len_old, len_new),
        safety_margin_m=margin_m,
        old_projection_bbox=old_proj_bbox,
        new_projection_bbox=new_proj_bbox
    )
