"""
Conservative candidate affected-region calculation for triangular meshes.

Projects 3D mesh vertices along the solar-ray trajectory onto the pedestrian plane,
providing mathematically guaranteed containment of all direct shadow changes
cast by arbitrary 3D triangular geometry.
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List
import numpy as np

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.incremental.affected_region import AffectedRegionResult


def project_mesh_shadow(mesh: TriangleMesh,
                        solar_pos: SolarPosition,
                        z_ped: float) -> Tuple[float, float, float, float, float]:
    """
    Projects all 3D vertices of a TriangleMesh along the anti-sun trajectory onto the plane at z_ped.
    
    Mathematical Soundness Guarantee:
    Since each triangle in the mesh is planar, any point in the triangle is an affine convex
    combination of its 3 vertices. Because projection along the sun vector is affine, the ground
    projection of every point on every triangle is strictly contained within the convex hull
    (and bounding box) of the projected vertices.
    
    Parameters:
        mesh: TriangleMesh instance.
        solar_pos: Current SolarPosition.
        z_ped: Pedestrian receptor plane height (m).
        
    Returns:
        (proj_xmin, proj_xmax, proj_ymin, proj_ymax, shadow_length_m)
    """
    if not mesh.enabled or mesh.num_vertices == 0:
        return (0.0, 0.0, 0.0, 0.0, 0.0)

    delta_h_max = max(0.0, mesh.zmax - z_ped)
    alt_rad = solar_pos.altitude_rad

    if delta_h_max <= 0.0 or alt_rad <= 0.0:
        return (mesh.xmin, mesh.xmax, mesh.ymin, mesh.ymax, 0.0)

    tan_alt = math.tan(alt_rad)
    shadow_length_m = delta_h_max / tan_alt

    # Solar unit vector components: sx (East, +X), sy (North, +Y)
    # Ground shadow plume projects in anti-sun direction (-sx, -sy)
    sx, sy, sz = solar_pos.sun_vector
    norm_h = math.hypot(sx, sy)
    if norm_h > 1e-6 and sz > 1e-6:
        # Ground displacement vector per meter of elevation difference:
        # dx = -sx / sz * delta_h, dy = -sy / sz * delta_h
        scale_x = -sx / sz
        scale_y = -sy / sz
    else:
        scale_x = 0.0
        scale_y = 0.0

    verts = mesh.vertices  # Shape (N, 3)
    vx = verts[:, 0]
    vy = verts[:, 1]
    vz = verts[:, 2]

    # Vertex elevation above pedestrian plane
    dh = np.maximum(0.0, vz - z_ped)

    # Projected ground coordinates
    proj_vx = vx + scale_x * dh
    proj_vy = vy + scale_y * dh

    # Tight encompassing bounding box over all vertex positions and their ground projections
    proj_xmin = float(min(np.min(vx), np.min(proj_vx)))
    proj_xmax = float(max(np.max(vx), np.max(proj_vx)))
    proj_ymin = float(min(np.min(vy), np.min(proj_vy)))
    proj_ymax = float(max(np.max(vy), np.max(proj_vy)))

    return (proj_xmin, proj_xmax, proj_ymin, proj_ymax, shadow_length_m)


def compute_mesh_candidate_affected_region(mesh_before: Optional[TriangleMesh],
                                          mesh_after: Optional[TriangleMesh],
                                          solar_pos: SolarPosition,
                                          grid: PedestrianGrid,
                                          safety_margin_cells: int = 2,
                                          min_altitude_deg: float = 5.0) -> AffectedRegionResult:
    """
    Computes a conservative candidate affected region on the pedestrian grid for mesh changes.
    
    Guarantees:
    - 100% containment of direct shadow differences between mesh_before and mesh_after.
    - Safety margin padding (+2 cells by default).
    - Conservative full-domain fallback if solar altitude is below min_altitude_deg.
    """
    ny, nx = grid.shape
    empty_bbox = (0.0, 0.0, 0.0, 0.0)
    full_mask = np.ones((ny, nx), dtype=bool)

    # 1. Daylight and Solar Altitude Checks
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
            candidate_bbox=(grid.origin_x, grid.origin_x + grid.extent_x,
                            grid.origin_y, grid.origin_y + grid.extent_y),
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

    # 2. Project Shadows of Mesh Before and Mesh After
    if mesh_before is not None and mesh_before.enabled:
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = project_mesh_shadow(mesh_before, solar_pos, grid.z_ped)
        old_proj_bbox = (p_old_x1, p_old_x2, p_old_y1, p_old_y2)
    else:
        p_old_x1, p_old_x2, p_old_y1, p_old_y2, len_old = 0.0, 0.0, 0.0, 0.0, 0.0
        old_proj_bbox = empty_bbox

    if mesh_after is not None and mesh_after.enabled:
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = project_mesh_shadow(mesh_after, solar_pos, grid.z_ped)
        new_proj_bbox = (p_new_x1, p_new_x2, p_new_y1, p_new_y2)
    else:
        p_new_x1, p_new_x2, p_new_y1, p_new_y2, len_new = 0.0, 0.0, 0.0, 0.0, 0.0
        new_proj_bbox = empty_bbox

    # If neither mesh exists, no region is affected
    if mesh_before is None and mesh_after is None:
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

    # Combine projection bounding boxes
    if old_proj_bbox != empty_bbox and new_proj_bbox != empty_bbox:
        comb_x1 = min(p_old_x1, p_new_x1)
        comb_x2 = max(p_old_x2, p_new_x2)
        comb_y1 = min(p_old_y1, p_new_y1)
        comb_y2 = max(p_old_y2, p_new_y2)
    elif old_proj_bbox != empty_bbox:
        comb_x1, comb_x2, comb_y1, comb_y2 = p_old_x1, p_old_x2, p_old_y1, p_old_y2
    else:
        comb_x1, comb_x2, comb_y1, comb_y2 = p_new_x1, p_new_x2, p_new_y1, p_new_y2

    # 3. Add Safety Margin
    margin_m = safety_margin_cells * grid.dx
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
