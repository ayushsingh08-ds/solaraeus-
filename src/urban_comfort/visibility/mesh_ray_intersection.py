"""
Deterministic CPU Ray-Triangle Intersection routines for SOLARAEUS.

Implements the Möller-Trumbore (1997) intersection algorithm with configurable
tolerances, parallel-ray handling, robust edge checking, two-sided evaluation,
and vectorized batch intersection for pedestrian-grid receivers.
"""

from __future__ import annotations
from typing import Tuple, Optional, List
import numpy as np

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.visibility.ray_intersection import intersect_ray_aabb, intersect_rays_aabb_batch


EPS_ORIGIN_DEFAULT = 1e-6   # Minimum distance t from ray origin to ignore surface self-hits (m)
EPS_DET_DEFAULT = 1e-10      # Parallel ray / coplanar determinant threshold
EPS_BARY_DEFAULT = 1e-9      # Barycentric coordinate boundary tolerance for shared edges


def intersect_ray_triangle(origin: Tuple[float, float, float],
                           direction: Tuple[float, float, float],
                           v0: Tuple[float, float, float] | np.ndarray,
                           v1: Tuple[float, float, float] | np.ndarray,
                           v2: Tuple[float, float, float] | np.ndarray,
                           eps_origin: float = EPS_ORIGIN_DEFAULT,
                           eps_det: float = EPS_DET_DEFAULT,
                           eps_bary: float = EPS_BARY_DEFAULT,
                           cull_backfaces: bool = False) -> Optional[Tuple[float, float, float]]:
    """
    Computes ray-triangle intersection using the Möller-Trumbore algorithm.
    
    Parameters:
        origin: (ox, oy, oz) ray starting point.
        direction: (dx, dy, dz) ray propagation direction vector.
        v0, v1, v2: 3D coordinates of triangle vertices.
        eps_origin: Minimum positive hit distance to prevent self-intersection.
        eps_det: Threshold below which ray is considered parallel to triangle plane.
        eps_bary: Tolerance for edge inclusion to prevent seam dropouts.
        cull_backfaces: If True, only intersections where ray opposes normal are accepted.
        
    Returns:
        (t, u, v) if an intersection occurs with t >= eps_origin, otherwise None.
    """
    ox, oy, oz = origin
    dx, dy, dz = direction

    # Check for non-finite or zero-length direction
    dir_len_sq = dx * dx + dy * dy + dz * dz
    if not np.isfinite(dir_len_sq) or dir_len_sq < 1e-14:
        return None

    # Triangle edges
    e1_x = v1[0] - v0[0]
    e1_y = v1[1] - v0[1]
    e1_z = v1[2] - v0[2]

    e2_x = v2[0] - v0[0]
    e2_y = v2[1] - v0[1]
    e2_z = v2[2] - v0[2]

    # pvec = cross(dir, e2)
    p_x = dy * e2_z - dz * e2_y
    p_y = dz * e2_x - dx * e2_z
    p_z = dx * e2_y - dy * e2_x

    det = e1_x * p_x + e1_y * p_y + e1_z * p_z

    if cull_backfaces:
        if det < eps_det:
            return None
    else:
        if abs(det) < eps_det:
            return None  # Ray is parallel or coplanar to triangle plane

    inv_det = 1.0 / det

    # tvec = origin - v0
    t_x = ox - v0[0]
    t_y = oy - v0[1]
    t_z = oz - v0[2]

    # Barycentric u = dot(tvec, pvec) * inv_det
    u = (t_x * p_x + t_y * p_y + t_z * p_z) * inv_det
    if u < -eps_bary or u > (1.0 + eps_bary):
        return None

    # qvec = cross(tvec, e1)
    q_x = t_y * e1_z - t_z * e1_y
    q_y = t_z * e1_x - t_x * e1_z
    q_z = t_x * e1_y - t_y * e1_x

    # Barycentric v = dot(dir, qvec) * inv_det
    v = (dx * q_x + dy * q_y + dz * q_z) * inv_det
    if v < -eps_bary or (u + v) > (1.0 + eps_bary):
        return None

    # Hit distance t = dot(e2, qvec) * inv_det
    t = (e2_x * q_x + e2_y * q_y + e2_z * q_z) * inv_det
    if t < eps_origin:
        return None

    return (float(t), float(u), float(v))


def intersect_ray_mesh(origin: Tuple[float, float, float],
                       direction: Tuple[float, float, float],
                       mesh: TriangleMesh,
                       eps_origin: float = EPS_ORIGIN_DEFAULT,
                       eps_det: float = EPS_DET_DEFAULT,
                       eps_bary: float = EPS_BARY_DEFAULT,
                       cull_backfaces: bool = False) -> Optional[float]:
    """
    Computes the nearest valid positive intersection of a single ray against a TriangleMesh.
    
    Returns:
        Closest hit distance t >= eps_origin, or None if no intersection occurs.
    """
    if not mesh.enabled or mesh.num_triangles == 0:
        return None

    # Bounding box cull: if ray misses mesh AABB, skip all triangles
    aabb_hit = intersect_ray_aabb(origin, direction, mesh.bounds_3d)
    if aabb_hit is None:
        # Check if ray origin is inside bounding box
        ox, oy, oz = origin
        b = mesh.bounds_3d
        inside_box = (b[0] <= ox <= b[1]) and (b[2] <= oy <= b[3]) and (b[4] <= oz <= b[5])
        if not inside_box:
            return None

    nearest_t: Optional[float] = None
    verts = mesh.vertices
    tris = mesh.triangles

    for tri in tris:
        hit = intersect_ray_triangle(
            origin, direction,
            verts[tri[0]], verts[tri[1]], verts[tri[2]],
            eps_origin=eps_origin, eps_det=eps_det, eps_bary=eps_bary,
            cull_backfaces=cull_backfaces
        )
        if hit is not None:
            t = hit[0]
            if nearest_t is None or t < nearest_t:
                nearest_t = t

    return nearest_t


def intersect_rays_mesh_batch(origins: np.ndarray,
                              direction: Tuple[float, float, float],
                              mesh: TriangleMesh,
                              eps_origin: float = EPS_ORIGIN_DEFAULT,
                              eps_det: float = EPS_DET_DEFAULT,
                              eps_bary: float = EPS_BARY_DEFAULT,
                              cull_backfaces: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    Vectorized batch intersection of N rays along a shared direction against all triangles of a mesh.
    
    Parameters:
        origins: Shape (N, 3) float64 array of ray origins.
        direction: (dx, dy, dz) normalized ray propagation vector.
        mesh: TriangleMesh instance.
        eps_origin: Minimum positive hit distance.
        eps_det: Parallel ray threshold.
        eps_bary: Barycentric edge inclusion tolerance.
        cull_backfaces: Back-face culling toggle.
        
    Returns:
        hits: Shape (N,) boolean mask indicating intersections.
        t_hits: Shape (N,) float64 nearest hit distances (np.inf for misses).
    """
    n_rays = origins.shape[0]
    hits = np.zeros(n_rays, dtype=bool)
    t_hits = np.full(n_rays, np.inf, dtype=np.float64)

    if not mesh.enabled or mesh.num_triangles == 0 or n_rays == 0:
        return hits, t_hits

    dx, dy, dz = direction
    dir_vec = np.array([dx, dy, dz], dtype=np.float64)
    dir_len_sq = float(np.sum(dir_vec ** 2))
    if not np.isfinite(dir_len_sq) or dir_len_sq < 1e-14:
        return hits, t_hits

    # 1. Bounding box pre-filter for entire batch of rays
    box_hits, _ = intersect_rays_aabb_batch(origins, direction, mesh.bounds_3d)
    b = mesh.bounds_3d
    inside_box = (
        (origins[:, 0] >= b[0]) & (origins[:, 0] <= b[1]) &
        (origins[:, 1] >= b[2]) & (origins[:, 1] <= b[3]) &
        (origins[:, 2] >= b[4]) & (origins[:, 2] <= b[5])
    )
    active_ray_indices = np.where(box_hits | inside_box)[0]
    if len(active_ray_indices) == 0:
        return hits, t_hits

    sub_origins = origins[active_ray_indices]
    sub_t_hits = np.full(len(active_ray_indices), np.inf, dtype=np.float64)

    verts = mesh.vertices
    tris = mesh.triangles

    # 2. Iterate over triangles and evaluate against active rays
    for tri in tris:
        v0 = verts[tri[0]]
        v1 = verts[tri[1]]
        v2 = verts[tri[2]]

        e1 = v1 - v0
        e2 = v2 - v0
        pvec = np.cross(dir_vec, e2)
        det = float(np.dot(e1, pvec))

        if cull_backfaces:
            if det < eps_det:
                continue
        else:
            if abs(det) < eps_det:
                continue

        inv_det = 1.0 / det

        # tvec: shape (K, 3)
        tvec = sub_origins - v0

        # u = dot(tvec, pvec) * inv_det
        u = np.dot(tvec, pvec) * inv_det
        valid_u = (u >= -eps_bary) & (u <= (1.0 + eps_bary))
        if not np.any(valid_u):
            continue

        # qvec = cross(tvec, e1): shape (K, 3)
        qvec = np.cross(tvec, e1)

        # v = dot(dir_vec, qvec) * inv_det
        v = np.dot(qvec, dir_vec) * inv_det
        valid_v = valid_u & (v >= -eps_bary) & ((u + v) <= (1.0 + eps_bary))
        if not np.any(valid_v):
            continue

        # t = dot(e2, qvec) * inv_det
        t = np.dot(qvec, e2) * inv_det
        hit_mask = valid_v & (t >= eps_origin)

        if np.any(hit_mask):
            sub_t_hits[hit_mask] = np.minimum(sub_t_hits[hit_mask], t[hit_mask])

    # Re-map results back to global ray array
    valid_sub_hits = sub_t_hits < np.inf
    if np.any(valid_sub_hits):
        hit_indices = active_ray_indices[valid_sub_hits]
        hits[hit_indices] = True
        t_hits[hit_indices] = sub_t_hits[valid_sub_hits]

    return hits, t_hits


def intersect_rays_scene_meshes(origins: np.ndarray,
                                direction: Tuple[float, float, float],
                                meshes: List[TriangleMesh],
                                early_exit: bool = True,
                                eps_origin: float = EPS_ORIGIN_DEFAULT,
                                eps_det: float = EPS_DET_DEFAULT,
                                eps_bary: float = EPS_BARY_DEFAULT,
                                cull_backfaces: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    Tests an array of rays against all active meshes in a scene.
    
    If early_exit is True (e.g. for binary shadow occlusion), rays that have already
    found a hit are excluded from subsequent mesh intersection tests.
    """
    n_rays = origins.shape[0]
    hits = np.zeros(n_rays, dtype=bool)
    t_hits = np.full(n_rays, np.inf, dtype=np.float64)

    active_meshes = [m for m in meshes if m.enabled and m.num_triangles > 0]
    if not active_meshes or n_rays == 0:
        return hits, t_hits

    for mesh in active_meshes:
        if early_exit and np.all(hits):
            break

        if early_exit:
            unoccluded_idx = np.where(~hits)[0]
            if len(unoccluded_idx) == 0:
                break
            mesh_hits, mesh_t = intersect_rays_mesh_batch(
                origins[unoccluded_idx], direction, mesh,
                eps_origin=eps_origin, eps_det=eps_det, eps_bary=eps_bary,
                cull_backfaces=cull_backfaces
            )
            hit_sub_idx = unoccluded_idx[mesh_hits]
            hits[hit_sub_idx] = True
            t_hits[hit_sub_idx] = mesh_t[mesh_hits]
        else:
            mesh_hits, mesh_t = intersect_rays_mesh_batch(
                origins, direction, mesh,
                eps_origin=eps_origin, eps_det=eps_det, eps_bary=eps_bary,
                cull_backfaces=cull_backfaces
            )
            hits |= mesh_hits
            t_hits = np.minimum(t_hits, mesh_t)

    return hits, t_hits
