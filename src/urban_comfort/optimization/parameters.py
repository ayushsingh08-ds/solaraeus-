"""
Intervention Parameterization for Geographically Constrained AI Optimization.

Defines the mathematical representation, parameter bounds, vector transformations,
and 3D geometric mesh construction for rectangular overhead shade structures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from shapely.geometry import Polygon

from urban_comfort.geometry.mesh import TriangleMesh


@dataclass
class ShadePanelParams:
    """
    Mathematical parameterization of a single rectangular overhead shade panel.
    
    Attributes:
        x: Center Easting coordinate in local grid coordinates (m).
        y: Center Northing coordinate in local grid coordinates (m).
        length: Panel dimension along local heading axis (m).
        width: Panel dimension perpendicular to heading axis (m).
        height: Underside clearance height above ground plane (m).
        heading_deg: Bearing orientation angle in degrees clockwise from local grid North (+Y).
        albedo: Solar reflectance of shade panel material [0.10, 0.90].
        tilt: Inclination angle from horizontal in degrees (default 0.0).
        emissivity: Thermal longwave emissivity of canopy surface (default 0.90).
    """
    x: float
    y: float
    length: float
    width: float
    height: float
    heading_deg: float = 90.0
    albedo: float = 0.60
    tilt: float = 0.0
    emissivity: float = 0.90

    def __init__(self,
                 x: float,
                 y: float,
                 length: float,
                 width: float,
                 height: float,
                 heading_deg: Optional[float] = None,
                 albedo: float = 0.60,
                 tilt: float = 0.0,
                 emissivity: float = 0.90,
                 azimuth: Optional[float] = None):
        self.x = float(x)
        self.y = float(y)
        self.length = float(length)
        self.width = float(width)
        self.height = float(height)
        if heading_deg is not None:
            self.heading_deg = float(heading_deg)
        elif azimuth is not None:
            self.heading_deg = float(azimuth)
        else:
            self.heading_deg = 90.0
        self.albedo = float(albedo)
        self.tilt = float(tilt)
        self.emissivity = float(emissivity)

    @property
    def azimuth(self) -> float:
        """Alias for heading_deg (bearing clockwise from North in degrees)."""
        return self.heading_deg

    @azimuth.setter
    def azimuth(self, val: float) -> None:
        self.heading_deg = float(val)

    @property
    def area(self) -> float:
        """2D planar footprint area in square meters."""
        return float(self.length * self.width)

    def is_finite(self) -> bool:
        """Returns True if all parameter values are finite numbers."""
        vals = [self.x, self.y, self.length, self.width, self.height, self.heading_deg, self.albedo, self.tilt, self.emissivity]
        return all(math.isfinite(v) for v in vals)

    def to_dict(self) -> Dict[str, float]:
        """Serializes parameters to a standard JSON-compatible dictionary."""
        return {
            "x": float(self.x),
            "y": float(self.y),
            "length": float(self.length),
            "width": float(self.width),
            "height": float(self.height),
            "heading_deg": float(self.heading_deg),
            "azimuth": float(self.heading_deg),
            "albedo": float(self.albedo),
            "tilt": float(self.tilt),
            "emissivity": float(self.emissivity),
            "area_m2": float(self.area),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ShadePanelParams:
        """Instantiates parameters from dictionary."""
        heading = data.get("heading_deg")
        if heading is None:
            heading = data.get("azimuth", 90.0)
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            length=float(data["length"]),
            width=float(data["width"]),
            height=float(data["height"]),
            heading_deg=float(heading),
            albedo=float(data.get("albedo", 0.60)),
            tilt=float(data.get("tilt", 0.0)),
            emissivity=float(data.get("emissivity", 0.90)),
        )


@dataclass
class ParameterBounds:
    """Configurable box bounds for candidate shade panel parameterization."""
    x_min: float = 100.0
    x_max: float = 160.0
    y_min: float = 50.0
    y_max: float = 75.0
    length_min: float = 3.0
    length_max: float = 12.0
    width_min: float = 2.0
    width_max: float = 5.0
    height_min: float = 2.5
    height_max: float = 5.0
    heading_min: float = 80.0
    heading_max: float = 125.0
    albedo_min: float = 0.20
    albedo_max: float = 0.85

    def contains(self, p: ShadePanelParams) -> bool:
        """Checks if parameters fall strictly within bounds."""
        if not p.is_finite():
            return False
        return (
            self.x_min <= p.x <= self.x_max and
            self.y_min <= p.y <= self.y_max and
            self.length_min <= p.length <= self.length_max and
            self.width_min <= p.width <= self.width_max and
            self.height_min <= p.height <= self.height_max and
            self.heading_min <= p.heading_deg <= self.heading_max and
            self.albedo_min <= p.albedo <= self.albedo_max
        )

    def clip(self, p: Any) -> Any:
        """Clips parameter values or parameter vector into valid box bounds."""
        if isinstance(p, np.ndarray):
            vec = np.empty_like(p)
            vec[0] = np.clip(p[0], self.x_min, self.x_max)
            vec[1] = np.clip(p[1], self.y_min, self.y_max)
            vec[2] = np.clip(p[2], self.length_min, self.length_max)
            vec[3] = np.clip(p[3], self.width_min, self.width_max)
            vec[4] = np.clip(p[4], self.height_min, self.height_max)
            vec[5] = np.clip(p[5], self.heading_min, self.heading_max)
            vec[6] = np.clip(p[6], self.albedo_min, self.albedo_max)
            return vec
        return ShadePanelParams(
            x=float(np.clip(p.x, self.x_min, self.x_max)),
            y=float(np.clip(p.y, self.y_min, self.y_max)),
            length=float(np.clip(p.length, self.length_min, self.length_max)),
            width=float(np.clip(p.width, self.width_min, self.width_max)),
            height=float(np.clip(p.height, self.height_min, self.height_max)),
            heading_deg=float(np.clip(p.heading_deg, self.heading_min, self.heading_max)),
            albedo=float(np.clip(p.albedo, self.albedo_min, self.albedo_max)),
        )

    def sample_uniform(self, rng: np.random.Generator, n_samples: Optional[int] = None) -> Any:
        """Samples random candidate(s) uniformly within parameter bounds."""
        if n_samples is not None:
            return [
                ShadePanelParams(
                    x=float(rng.uniform(self.x_min, self.x_max)),
                    y=float(rng.uniform(self.y_min, self.y_max)),
                    length=float(rng.uniform(self.length_min, self.length_max)),
                    width=float(rng.uniform(self.width_min, self.width_max)),
                    height=float(rng.uniform(self.height_min, self.height_max)),
                    heading_deg=float(rng.uniform(self.heading_min, self.heading_max)),
                    albedo=float(rng.uniform(self.albedo_min, self.albedo_max)),
                )
                for _ in range(n_samples)
            ]
        return ShadePanelParams(
            x=float(rng.uniform(self.x_min, self.x_max)),
            y=float(rng.uniform(self.y_min, self.y_max)),
            length=float(rng.uniform(self.length_min, self.length_max)),
            width=float(rng.uniform(self.width_min, self.width_max)),
            height=float(rng.uniform(self.height_min, self.height_max)),
            heading_deg=float(rng.uniform(self.heading_min, self.heading_max)),
            albedo=float(rng.uniform(self.albedo_min, self.albedo_max)),
        )

    def sample_lhs(self, *args, **kwargs) -> List[ShadePanelParams]:
        """
        Samples candidates using Latin Hypercube Sampling (LHS) across all 7 dimensions.
        Supports both (n_samples, rng) and (rng, n_samples) argument styles.
        """
        rng: Optional[np.random.Generator] = None
        n_samples: int = 1
        if len(args) == 2:
            if isinstance(args[0], int):
                n_samples, rng = args[0], args[1]
            else:
                rng, n_samples = args[0], args[1]
        elif len(args) == 1:
            if isinstance(args[0], int):
                n_samples = args[0]
            else:
                rng = args[0]

        if "rng" in kwargs:
            rng = kwargs["rng"]
        if "n_samples" in kwargs:
            n_samples = kwargs["n_samples"]

        if rng is None:
            rng = np.random.default_rng(42)

        d = 7
        result: List[ShadePanelParams] = []
        bounds_arr = np.array([
            [self.x_min, self.x_max],
            [self.y_min, self.y_max],
            [self.length_min, self.length_max],
            [self.width_min, self.width_max],
            [self.height_min, self.height_max],
            [self.heading_min, self.heading_max],
            [self.albedo_min, self.albedo_max],
        ], dtype=np.float64)

        # Generate Latin Hypercube intervals
        lhs_matrix = np.zeros((n_samples, d), dtype=np.float64)
        for j in range(d):
            perm = rng.permutation(n_samples)
            u = rng.uniform(0.0, 1.0, size=n_samples)
            lhs_matrix[:, j] = (perm + u) / float(n_samples)

        # Scale to bounds
        scaled = bounds_arr[:, 0] + lhs_matrix * (bounds_arr[:, 1] - bounds_arr[:, 0])
        for i in range(n_samples):
            result.append(ShadePanelParams(
                x=float(scaled[i, 0]),
                y=float(scaled[i, 1]),
                length=float(scaled[i, 2]),
                width=float(scaled[i, 3]),
                height=float(scaled[i, 4]),
                heading_deg=float(scaled[i, 5]),
                albedo=float(scaled[i, 6]),
            ))
        return result

    def to_vector(self, p: ShadePanelParams) -> np.ndarray:
        """Extracts 7-element float array [x, y, length, width, height, heading, albedo]."""
        return np.array([p.x, p.y, p.length, p.width, p.height, p.heading_deg, p.albedo], dtype=np.float64)

    def from_vector(self, v: np.ndarray) -> ShadePanelParams:
        """Instantiates ShadePanelParams from 7-element vector."""
        return ShadePanelParams(
            x=float(v[0]),
            y=float(v[1]),
            length=float(v[2]),
            width=float(v[3]),
            height=float(v[4]),
            heading_deg=float(v[5]),
            albedo=float(v[6]),
        )

    def to_dict(self) -> Dict[str, Tuple[float, float]]:
        return {
            "x": (self.x_min, self.x_max),
            "y": (self.y_min, self.y_max),
            "length": (self.length_min, self.length_max),
            "width": (self.width_min, self.width_max),
            "height": (self.height_min, self.height_max),
            "heading_deg": (self.heading_min, self.heading_max),
            "albedo": (self.albedo_min, self.albedo_max),
        }

    @classmethod
    def get_canonical_church_street_bounds(cls) -> ParameterBounds:
        """Preconfigured realistic intervention bounds for Church Street pedestrian corridor."""
        return cls(
            x_min=110.0,
            x_max=155.0,
            y_min=55.0,
            y_max=72.0,
            length_min=3.0,
            length_max=12.0,
            width_min=2.0,
            width_max=4.5,
            height_min=2.8,
            height_max=4.5,
            heading_min=90.0,
            heading_max=115.0,
            albedo_min=0.20,
            albedo_max=0.85,
        )

    @classmethod
    def get_canonical_church_street_baseline_params(cls) -> ShadePanelParams:
        """Parameters corresponding to canonical CANOPY_001 / BLR_SHADE_001 intervention."""
        return ShadePanelParams(
            x=131.789,
            y=64.007,
            length=6.0,
            width=3.0,
            height=3.5,
            heading_deg=102.44,
            albedo=0.60,
        )


def build_panel_geometry(params: ShadePanelParams,
                         thickness_m: float = 0.1,
                         mesh_id: str = "SHADE_PANEL") -> Tuple[TriangleMesh, Polygon]:
    """
    Constructs a watertight 3D TriangleMesh (8 vertices, 12 triangles) and 2D Shapely Polygon footprint
    for a rectangular overhead shade panel.
    
    Coordinates:
    - Heading is clockwise angle from local grid North (+Y).
    - Longitudinal axis (length L) points along heading vector (sin theta, cos theta).
    - Transversal axis (width W) points along orthogonal vector (cos theta, -sin theta).
    - Vertices wound with CCW outward-pointing face normals.
    - Underside positioned at params.height; top surface at params.height + thickness_m.
    """
    theta = math.radians(params.heading_deg)
    u_len = np.array([math.sin(theta), math.cos(theta)], dtype=np.float64)
    u_wid = np.array([math.cos(theta), -math.sin(theta)], dtype=np.float64)

    center = np.array([params.x, params.y], dtype=np.float64)
    hl = params.length / 2.0
    hw = params.width / 2.0

    # 4 corners in clockwise winding: C0 (-hl, -hw), C1 (+hl, -hw), C2 (+hl, +hw), C3 (-hl, +hw)
    c0 = center - hl * u_len - hw * u_wid
    c1 = center + hl * u_len - hw * u_wid
    c2 = center + hl * u_len + hw * u_wid
    c3 = center - hl * u_len + hw * u_wid

    # Counter-Clockwise (CCW) polygon for standard 2D geometry
    ccw_pts = np.array([c0, c3, c2, c1], dtype=np.float64)
    polygon_2d = Polygon(ccw_pts)

    z_under = float(params.height)
    z_top = float(params.height + thickness_m)

    # 3D vertices (8): 0..3 bottom underside, 4..7 top roof
    v_bottom = np.column_stack([ccw_pts, np.full(4, z_under)])
    v_top = np.column_stack([ccw_pts, np.full(4, z_top)])
    vertices_3d = np.vstack([v_bottom, v_top])

    # 12 triangles with outward face normals
    triangles_list = []
    # 4 side walls (8 triangles)
    for i in range(4):
        j = (i + 1) % 4
        triangles_list.append([i, j, j + 4])
        triangles_list.append([i, j + 4, i + 4])
    # Top roof (+Z)
    triangles_list.append([4, 5, 6])
    triangles_list.append([4, 6, 7])
    # Bottom underside (-Z)
    triangles_list.append([0, 2, 1])
    triangles_list.append([0, 3, 2])
    triangles_3d = np.array(triangles_list, dtype=np.int64)

    mesh = TriangleMesh(
        id=mesh_id,
        vertices=vertices_3d,
        triangles=triangles_3d,
        material_id="SHADE_PANEL_ASSUMED_001",
        enabled=True,
        metadata={
            "length_m": params.length,
            "width_m": params.width,
            "thickness_m": thickness_m,
            "underside_height_m": z_under,
            "top_height_m": z_top,
            "footprint_area_m2": params.area,
            "bearing_grid_north_deg": params.heading_deg,
            "albedo": params.albedo,
            "emissivity": 0.90,
            "initial_surface_temp_c": 35.0,
            "supporting_posts_included": False,
        }
    )

    return mesh, polygon_2d
