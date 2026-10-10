"""
Triangular mesh representation and synthetic urban mesh constructors for SOLARAEUS.

Provides a minimal, fully validated 3D triangle mesh data structure for controlled
geometric generalization beyond axis-aligned bounding boxes (AABBs).
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np


@dataclass
class TriangleMesh:
    """
    Controlled 3D triangular surface mesh representation.
    
    Attributes:
        id: Unique object identifier.
        vertices: Shape (N, 3) float64 array of vertex coordinates in meters.
        triangles: Shape (M, 3) integer array of 0-based vertex indices.
        material_id: Material identifier for radiative properties.
        enabled: Toggle for active simulation inclusion.
        metadata: Custom descriptive metadata dictionary.
    """
    id: str
    vertices: np.ndarray
    triangles: np.ndarray
    material_id: str = "default_wall"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        # 1. Type and shape validation
        if not isinstance(self.vertices, np.ndarray):
            self.vertices = np.asarray(self.vertices, dtype=np.float64)
        else:
            self.vertices = self.vertices.astype(np.float64)

        if not isinstance(self.triangles, np.ndarray):
            self.triangles = np.asarray(self.triangles, dtype=np.int64)
        else:
            self.triangles = self.triangles.astype(np.int64)

        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError(
                f"Vertices array must have shape (N, 3), got shape {self.vertices.shape}."
            )
        if self.vertices.shape[0] < 3:
            raise ValueError(
                f"Mesh must have at least 3 vertices, got {self.vertices.shape[0]}."
            )

        if self.triangles.ndim != 2 or self.triangles.shape[1] != 3:
            raise ValueError(
                f"Triangles array must have shape (M, 3), got shape {self.triangles.shape}."
            )
        if self.triangles.shape[0] < 1:
            raise ValueError(
                f"Mesh must contain at least 1 triangle, got {self.triangles.shape[0]}."
            )

        # 2. Coordinate sanity: must be finite
        if not np.all(np.isfinite(self.vertices)):
            raise ValueError("All vertex coordinates must be finite real numbers.")

        # 3. Index range validation
        n_verts = self.vertices.shape[0]
        min_idx = np.min(self.triangles)
        max_idx = np.max(self.triangles)
        if min_idx < 0 or max_idx >= n_verts:
            raise ValueError(
                f"Triangle indices out of bounds: range [{min_idx}, {max_idx}] "
                f"exceeds vertex count {n_verts}."
            )

        # 4. Check for duplicate indices within any triangle
        has_duplicate_indices = (
            (self.triangles[:, 0] == self.triangles[:, 1]) |
            (self.triangles[:, 1] == self.triangles[:, 2]) |
            (self.triangles[:, 0] == self.triangles[:, 2])
        )
        if np.any(has_duplicate_indices):
            bad_idx = np.where(has_duplicate_indices)[0][0]
            raise ValueError(
                f"Degenerate triangle at index {bad_idx} contains duplicate vertex indices: "
                f"{self.triangles[bad_idx]}."
            )

        # 5. Degenerate area check (near-collinear vertices)
        v0 = self.vertices[self.triangles[:, 0]]
        v1 = self.vertices[self.triangles[:, 1]]
        v2 = self.vertices[self.triangles[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        double_areas = np.linalg.norm(cross, axis=1)

        degenerate_mask = double_areas < 1e-12
        if np.any(degenerate_mask):
            bad_idx = np.where(degenerate_mask)[0][0]
            raise ValueError(
                f"Degenerate triangle at index {bad_idx} has zero surface area "
                f"({0.5 * double_areas[bad_idx]:.2e} m^2)."
            )

    @property
    def num_vertices(self) -> int:
        return self.vertices.shape[0]

    @property
    def num_triangles(self) -> int:
        return self.triangles.shape[0]

    @property
    def xmin(self) -> float:
        return float(np.min(self.vertices[:, 0]))

    @property
    def xmax(self) -> float:
        return float(np.max(self.vertices[:, 0]))

    @property
    def ymin(self) -> float:
        return float(np.min(self.vertices[:, 1]))

    @property
    def ymax(self) -> float:
        return float(np.max(self.vertices[:, 1]))

    @property
    def zmin(self) -> float:
        return float(np.min(self.vertices[:, 2]))

    @property
    def zmax(self) -> float:
        return float(np.max(self.vertices[:, 2]))

    @property
    def bounds_3d(self) -> Tuple[float, float, float, float, float, float]:
        """Returns tight 3D bounding box (xmin, xmax, ymin, ymax, zmin, zmax)."""
        return (self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)

    @property
    def footprint_bounds_2d(self) -> Tuple[float, float, float, float]:
        """Returns 2D horizontal bounding box (xmin, xmax, ymin, ymax)."""
        return (self.xmin, self.xmax, self.ymin, self.ymax)

    @property
    def face_normals(self) -> np.ndarray:
        """Returns normalized face normals of shape (M, 3)."""
        v0 = self.vertices[self.triangles[:, 0]]
        v1 = self.vertices[self.triangles[:, 1]]
        v2 = self.vertices[self.triangles[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        lengths = np.linalg.norm(cross, axis=1, keepdims=True)
        return cross / np.maximum(1e-15, lengths)

    @property
    def face_areas(self) -> np.ndarray:
        """Returns surface area of each triangle in square meters, shape (M,)."""
        v0 = self.vertices[self.triangles[:, 0]]
        v1 = self.vertices[self.triangles[:, 1]]
        v2 = self.vertices[self.triangles[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        return 0.5 * np.linalg.norm(cross, axis=1)

    @property
    def total_surface_area(self) -> float:
        """Returns total exterior surface area in square meters."""
        return float(np.sum(self.face_areas))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes mesh to JSON-compatible dictionary."""
        return {
            "id": self.id,
            "material_id": self.material_id,
            "enabled": self.enabled,
            "metadata": self.metadata,
            "vertices": self.vertices.tolist(),
            "triangles": self.triangles.tolist(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TriangleMesh:
        """Constructs TriangleMesh from serialized dictionary."""
        return cls(
            id=data["id"],
            vertices=np.array(data["vertices"], dtype=np.float64),
            triangles=np.array(data["triangles"], dtype=np.int64),
            material_id=data.get("material_id", "default_wall"),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {})
        )


# =============================================================================
# Synthetic Mesh Constructors
# =============================================================================

def create_box_mesh(box_id: str,
                    xmin: float, xmax: float,
                    ymin: float, ymax: float,
                    zmin: float, zmax: float,
                    material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs an axis-aligned box represented as a 12-triangle watertight mesh.
    Vertices (8):
        0: (xmin, ymin, zmin)
        1: (xmax, ymin, zmin)
        2: (xmax, ymax, zmin)
        3: (xmin, ymax, zmin)
        4: (xmin, ymin, zmax)
        5: (xmax, ymin, zmax)
        6: (xmax, ymax, zmax)
        7: (xmin, ymax, zmax)
    """
    vertices = np.array([
        [xmin, ymin, zmin],
        [xmax, ymin, zmin],
        [xmax, ymax, zmin],
        [xmin, ymax, zmin],
        [xmin, ymin, zmax],
        [xmax, ymin, zmax],
        [xmax, ymax, zmax],
        [xmin, ymax, zmax],
    ], dtype=np.float64)

    # 12 triangles with outward-pointing normals
    triangles = np.array([
        # Bottom (-Z)
        [0, 2, 1], [0, 3, 2],
        # Top (+Z)
        [4, 5, 6], [4, 6, 7],
        # South (-Y)
        [0, 1, 5], [0, 5, 4],
        # East (+X)
        [1, 2, 6], [1, 6, 5],
        # North (+Y)
        [2, 3, 7], [2, 7, 6],
        # West (-X)
        [3, 0, 4], [3, 4, 7],
    ], dtype=np.int64)

    return TriangleMesh(
        id=box_id,
        vertices=vertices,
        triangles=triangles,
        material_id=material_id,
        metadata={"generator": "create_box_mesh", "type": "axis_aligned_box"}
    )


def create_rotated_box_mesh(box_id: str,
                            center_x: float, center_y: float,
                            width_x: float, width_y: float,
                            height: float,
                            angle_deg: float,
                            zmin: float = 0.0,
                            material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs a rectangular prism rotated about the vertical Z-axis by angle_deg.
    """
    hx = width_x / 2.0
    hy = width_y / 2.0
    zmax = zmin + height

    # Unrotated local coordinates centered at origin
    local_corners = np.array([
        [-hx, -hy],
        [ hx, -hy],
        [ hx,  hy],
        [-hx,  hy],
    ], dtype=np.float64)

    # Rotate in 2D
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    rot_matrix = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=np.float64)
    rot_corners = local_corners @ rot_matrix.T

    # World vertices
    bottom = np.column_stack([rot_corners + [center_x, center_y], np.full(4, zmin)])
    top = np.column_stack([rot_corners + [center_x, center_y], np.full(4, zmax)])
    vertices = np.vstack([bottom, top])

    triangles = np.array([
        # Bottom (-Z)
        [0, 2, 1], [0, 3, 2],
        # Top (+Z)
        [4, 5, 6], [4, 6, 7],
        # Side 0-1
        [0, 1, 5], [0, 5, 4],
        # Side 1-2
        [1, 2, 6], [1, 6, 5],
        # Side 2-3
        [2, 3, 7], [2, 7, 6],
        # Side 3-0
        [3, 0, 4], [3, 4, 7],
    ], dtype=np.int64)

    return TriangleMesh(
        id=box_id,
        vertices=vertices,
        triangles=triangles,
        material_id=material_id,
        metadata={
            "generator": "create_rotated_box_mesh",
            "angle_deg": angle_deg,
            "center": (center_x, center_y)
        }
    )


def create_pitched_roof_mesh(building_id: str,
                             xmin: float, xmax: float,
                             ymin: float, ymax: float,
                             eave_height: float,
                             ridge_height: float,
                             ridge_orientation: str = "x",
                             zmin: float = 0.0,
                             material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs a building with vertical walls and a dual-pitch gable roof.
    
    If ridge_orientation == "x":
        Ridge runs parallel to X-axis at y_mid = (ymin + ymax) / 2.
    If ridge_orientation == "y":
        Ridge runs parallel to Y-axis at x_mid = (xmin + xmax) / 2.
    """
    if ridge_height <= eave_height:
        raise ValueError(
            f"ridge_height ({ridge_height}) must be greater than eave_height ({eave_height})."
        )

    # 4 ground vertices (0-3)
    # 4 eave vertices (4-7)
    # 2 ridge vertices (8-9)
    if ridge_orientation == "x":
        ymid = (ymin + ymax) / 2.0
        vertices = np.array([
            # Ground (0..3)
            [xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymax, zmin], [xmin, ymax, zmin],
            # Eaves (4..7)
            [xmin, ymin, eave_height], [xmax, ymin, eave_height],
            [xmax, ymax, eave_height], [xmin, ymax, eave_height],
            # Ridge (8..9)
            [xmin, ymid, ridge_height], [xmax, ymid, ridge_height]
        ], dtype=np.float64)

        triangles = np.array([
            # Bottom
            [0, 2, 1], [0, 3, 2],
            # South wall (ymin)
            [0, 1, 5], [0, 5, 4],
            # North wall (ymax)
            [2, 3, 7], [2, 7, 6],
            # West gable wall (xmin): 1 quad + 1 triangular peak
            [3, 0, 4], [3, 4, 7], [7, 4, 8],
            # East gable wall (xmax): 1 quad + 1 triangular peak
            [1, 2, 6], [1, 6, 5], [5, 6, 9],
            # South roof pitch (between eaves 4,5 and ridge 8,9)
            [4, 5, 9], [4, 9, 8],
            # North roof pitch (between eaves 6,7 and ridge 9,8)
            [9, 6, 7], [9, 7, 8],
        ], dtype=np.int64)

    elif ridge_orientation == "y":
        xmid = (xmin + xmax) / 2.0
        vertices = np.array([
            # Ground (0..3)
            [xmin, ymin, zmin], [xmax, ymin, zmin], [xmax, ymax, zmin], [xmin, ymax, zmin],
            # Eaves (4..7)
            [xmin, ymin, eave_height], [xmax, ymin, eave_height],
            [xmax, ymax, eave_height], [xmin, ymax, eave_height],
            # Ridge (8..9)
            [xmid, ymin, ridge_height], [xmid, ymax, ridge_height]
        ], dtype=np.float64)

        triangles = np.array([
            # Bottom
            [0, 2, 1], [0, 3, 2],
            # West wall (xmin)
            [3, 0, 4], [3, 4, 7],
            # East wall (xmax)
            [1, 2, 6], [1, 6, 5],
            # South gable (ymin)
            [0, 1, 5], [0, 5, 4], [4, 5, 8],
            # North gable (ymax)
            [2, 3, 7], [2, 7, 6], [7, 6, 9],
            # West roof pitch (between eaves 7,4 and ridge 9,8)
            [7, 4, 8], [7, 8, 9],
            # East roof pitch (between eaves 5,6 and ridge 8,9)
            [5, 6, 9], [5, 9, 8],
        ], dtype=np.int64)
    else:
        raise ValueError(f"ridge_orientation must be 'x' or 'y', got '{ridge_orientation}'.")

    return TriangleMesh(
        id=building_id,
        vertices=vertices,
        triangles=triangles,
        material_id=material_id,
        metadata={"generator": "create_pitched_roof_mesh", "ridge_orientation": ridge_orientation}
    )


def create_overhang_mesh(building_id: str,
                         xmin: float, xmax: float,
                         ymin: float, ymax: float,
                         base_height: float,
                         overhang_depth: float,
                         overhang_direction: str = "north",
                         overhang_thickness: float = 3.0,
                         zmin: float = 0.0,
                         material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs a building with a cantilevered upper-level overhang extending beyond
    its ground footprint, creating shaded open ground beneath the projection.
    """
    if overhang_thickness >= base_height:
        raise ValueError("overhang_thickness must be strictly less than base_height.")

    # Base building box from zmin to base_height
    # Overhang slab extends from (base_height - overhang_thickness) to base_height
    z_overhang_bottom = base_height - overhang_thickness
    z_top = base_height

    if overhang_direction == "north":
        # Overhang extends in +Y direction from ymax to ymax + overhang_depth
        oh_ymin, oh_ymax = ymax, ymax + overhang_depth
        oh_xmin, oh_xmax = xmin, xmax
    elif overhang_direction == "south":
        oh_ymin, oh_ymax = ymin - overhang_depth, ymin
        oh_xmin, oh_xmax = xmin, xmax
    elif overhang_direction == "east":
        oh_xmin, oh_xmax = xmax, xmax + overhang_depth
        oh_ymin, oh_ymax = ymin, ymax
    elif overhang_direction == "west":
        oh_xmin, oh_xmax = xmin - overhang_depth, xmin
        oh_ymin, oh_ymax = ymin, ymax
    else:
        raise ValueError(f"Unknown overhang_direction '{overhang_direction}'.")

    # Combine main building box and overhang slab box into a unified multi-box mesh
    box1 = create_box_mesh("temp_base", xmin, xmax, ymin, ymax, zmin, z_top, material_id)
    box2 = create_box_mesh("temp_oh", oh_xmin, oh_xmax, oh_ymin, oh_ymax, z_overhang_bottom, z_top, material_id)

    combined_vertices = np.vstack([box1.vertices, box2.vertices])
    combined_triangles = np.vstack([box1.triangles, box2.triangles + len(box1.vertices)])

    return TriangleMesh(
        id=building_id,
        vertices=combined_vertices,
        triangles=combined_triangles,
        material_id=material_id,
        metadata={
            "generator": "create_overhang_mesh",
            "overhang_direction": overhang_direction,
            "overhang_depth": overhang_depth
        }
    )


def create_wall_mesh(wall_id: str,
                     start_pt: Tuple[float, float],
                     end_pt: Tuple[float, float],
                     thickness: float,
                     height: float,
                     zmin: float = 0.0,
                     material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs a thin, vertical wall oriented along an arbitrary 2D line segment.
    """
    x1, y1 = start_pt
    x2, y2 = end_pt
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length < 1e-6:
        raise ValueError("start_pt and end_pt cannot be identical.")

    # Unit vector along wall and unit normal perpendicular to wall
    ux = dx / length
    uy = dy / length
    nx = -uy
    ny = ux
    half_t = thickness / 2.0

    # 4 2D corner vertices
    c0 = np.array([x1 - nx * half_t, y1 - ny * half_t])
    c1 = np.array([x2 - nx * half_t, y2 - ny * half_t])
    c2 = np.array([x2 + nx * half_t, y2 + ny * half_t])
    c3 = np.array([x1 + nx * half_t, y1 + ny * half_t])

    zmax = zmin + height
    bottom = np.column_stack([np.vstack([c0, c1, c2, c3]), np.full(4, zmin)])
    top = np.column_stack([np.vstack([c0, c1, c2, c3]), np.full(4, zmax)])
    vertices = np.vstack([bottom, top])

    triangles = np.array([
        # Bottom
        [0, 2, 1], [0, 3, 2],
        # Top
        [4, 5, 6], [4, 6, 7],
        # Face 0-1
        [0, 1, 5], [0, 5, 4],
        # Face 1-2
        [1, 2, 6], [1, 6, 5],
        # Face 2-3
        [2, 3, 7], [2, 7, 6],
        # Face 3-0
        [3, 0, 4], [3, 4, 7],
    ], dtype=np.int64)

    return TriangleMesh(
        id=wall_id,
        vertices=vertices,
        triangles=triangles,
        material_id=material_id,
        metadata={"generator": "create_wall_mesh", "length": length, "thickness": thickness}
    )


def create_l_shaped_mesh(building_id: str,
                         xmin: float, ymin: float,
                         total_width: float, total_length: float,
                         wing_width: float, wing_length: float,
                         height: float,
                         zmin: float = 0.0,
                         material_id: str = "default_wall") -> TriangleMesh:
    """
    Constructs a concave L-shaped building composed of two orthogonal intersecting blocks:
    - Base wing along X: [xmin, xmin + total_width] x [ymin, ymin + wing_length]
    - Corner wing along Y: [xmin, xmin + wing_width] x [ymin + wing_length, ymin + total_length]
    """
    if wing_width >= total_width:
        raise ValueError("wing_width must be less than total_width.")
    if wing_length >= total_length:
        raise ValueError("wing_length must be less than total_length.")

    zmax = zmin + height

    # 6 2D footprint boundary vertices in counter-clockwise order:
    # 0: (xmin, ymin)
    # 1: (xmin + total_width, ymin)
    # 2: (xmin + total_width, ymin + wing_length)
    # 3: (xmin + wing_width, ymin + wing_length)  <- inner concave corner
    # 4: (xmin + wing_width, ymin + total_length)
    # 5: (xmin, ymin + total_length)
    poly_2d = np.array([
        [xmin, ymin],
        [xmin + total_width, ymin],
        [xmin + total_width, ymin + wing_length],
        [xmin + wing_width, ymin + wing_length],
        [xmin + wing_width, ymin + total_length],
        [xmin, ymin + total_length],
    ], dtype=np.float64)

    bottom = np.column_stack([poly_2d, np.full(6, zmin)])
    top = np.column_stack([poly_2d, np.full(6, zmax)])
    vertices = np.vstack([bottom, top])

    # 4 triangles for bottom (partitioned into 2 rectangles: [0,1,2,3] and [0,3,4,5])
    # 0,1,2,3 -> (0,2,1) and (0,3,2)
    # 0,3,4,5 -> (0,4,3) and (0,5,4)
    # Bottom:
    # 4 triangles for top:
    # 6 side quads (12 triangles) connecting (i, (i+1)%6) to (i+6, (i+1)%6+6)
    side_triangles = []
    for i in range(6):
        i_next = (i + 1) % 6
        b0, b1 = i, i_next
        t0, t1 = i + 6, i_next + 6
        # Quad (b0, b1, t1, t0) -> (b0, b1, t1) and (b0, t1, t0)
        side_triangles.append([b0, b1, t1])
        side_triangles.append([b0, t1, t0])

    triangles = np.array([
        # Bottom (-Z)
        [0, 2, 1], [0, 3, 2],
        [0, 4, 3], [0, 5, 4],
        # Top (+Z)
        [6, 7, 8], [6, 8, 9],
        [6, 9, 10], [6, 10, 11],
    ] + side_triangles, dtype=np.int64)

    return TriangleMesh(
        id=building_id,
        vertices=vertices,
        triangles=triangles,
        material_id=material_id,
        metadata={"generator": "create_l_shaped_mesh", "type": "concave_l_shape"}
    )
