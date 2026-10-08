"""
Two-Panel Intervention Parameterization for Geographically Constrained AI Optimization.

Defines the mathematical representation, bounds, vector transformations, canonicalization,
and 3D geometric mesh construction for dual rectangular overhead shade structures.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from shapely.geometry import Polygon

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.optimization.parameters import ShadePanelParams, ParameterBounds, build_panel_geometry


@dataclass
class TwoPanelParams:
    """
    Mathematical parameterization of two rectangular overhead shade panels.

    Panel 1: (x1, y1, length1, width1, height1, heading1, albedo1)
    Panel 2: (x2, y2, length2, width2, height2, heading2, albedo2)
    """
    x1: float
    y1: float
    length1: float
    width1: float
    height1: float
    heading_deg1: float
    albedo1: float

    x2: float
    y2: float
    length2: float
    width2: float
    height2: float
    heading_deg2: float
    albedo2: float

    @property
    def panel1(self) -> ShadePanelParams:
        """Extracts ShadePanelParams for Panel 1."""
        return ShadePanelParams(
            x=self.x1,
            y=self.y1,
            length=self.length1,
            width=self.width1,
            height=self.height1,
            heading_deg=self.heading_deg1,
            albedo=self.albedo1,
        )

    @property
    def panel2(self) -> ShadePanelParams:
        """Extracts ShadePanelParams for Panel 2."""
        return ShadePanelParams(
            x=self.x2,
            y=self.y2,
            length=self.length2,
            width=self.width2,
            height=self.height2,
            heading_deg=self.heading_deg2,
            albedo=self.albedo2,
        )

    @classmethod
    def from_panels(cls, p1: ShadePanelParams, p2: ShadePanelParams) -> TwoPanelParams:
        """Constructs TwoPanelParams from two single panel instances."""
        return cls(
            x1=p1.x, y1=p1.y, length1=p1.length, width1=p1.width,
            height1=p1.height, heading_deg1=p1.heading_deg, albedo1=p1.albedo,
            x2=p2.x, y2=p2.y, length2=p2.length, width2=p2.width,
            height2=p2.height, heading_deg2=p2.heading_deg, albedo2=p2.albedo,
        )

    @property
    def area1(self) -> float:
        """Planar footprint area of Panel 1 in m2."""
        return float(self.length1 * self.width1)

    @property
    def area2(self) -> float:
        """Planar footprint area of Panel 2 in m2."""
        return float(self.length2 * self.width2)

    @property
    def total_area(self) -> float:
        """Total planar footprint area of both panels in m2."""
        return float(self.area1 + self.area2)

    def is_finite(self) -> bool:
        """Returns True if all 14 parameter values are finite numbers."""
        vals = [
            self.x1, self.y1, self.length1, self.width1, self.height1, self.heading_deg1, self.albedo1,
            self.x2, self.y2, self.length2, self.width2, self.height2, self.heading_deg2, self.albedo2,
        ]
        return all(math.isfinite(v) for v in vals)

    def canonicalize(self) -> TwoPanelParams:
        """
        Orders panels canonically so (panel1, panel2) is unique under permutation symmetry.
        Ordering rule: panel with smaller x coordinate comes first; tie-break by y.
        """
        if (self.x1 > self.x2) or (math.isclose(self.x1, self.x2, abs_tol=1e-5) and self.y1 > self.y2):
            return TwoPanelParams(
                x1=self.x2, y1=self.y2, length1=self.length2, width1=self.width2,
                height1=self.height2, heading_deg1=self.heading_deg2, albedo1=self.albedo2,
                x2=self.x1, y2=self.y1, length2=self.length1, width2=self.width1,
                height2=self.height1, heading_deg2=self.heading_deg1, albedo2=self.albedo1,
            )
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes parameters to a standard JSON-compatible dictionary."""
        return {
            "panel1": self.panel1.to_dict(),
            "panel2": self.panel2.to_dict(),
            "x1": float(self.x1),
            "y1": float(self.y1),
            "length1": float(self.length1),
            "width1": float(self.width1),
            "height1": float(self.height1),
            "heading_deg1": float(self.heading_deg1),
            "albedo1": float(self.albedo1),
            "area1_m2": float(self.area1),
            "x2": float(self.x2),
            "y2": float(self.y2),
            "length2": float(self.length2),
            "width2": float(self.width2),
            "height2": float(self.height2),
            "heading_deg2": float(self.heading_deg2),
            "albedo2": float(self.albedo2),
            "area2_m2": float(self.area2),
            "total_area_m2": float(self.total_area),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TwoPanelParams:
        """Instantiates parameters from dictionary."""
        if "panel1" in data and "panel2" in data:
            p1 = ShadePanelParams.from_dict(data["panel1"])
            p2 = ShadePanelParams.from_dict(data["panel2"])
            return cls.from_panels(p1, p2)
        return cls(
            x1=float(data["x1"]),
            y1=float(data["y1"]),
            length1=float(data["length1"]),
            width1=float(data["width1"]),
            height1=float(data["height1"]),
            heading_deg1=float(data["heading_deg1"]),
            albedo1=float(data["albedo1"]),
            x2=float(data["x2"]),
            y2=float(data["y2"]),
            length2=float(data["length2"]),
            width2=float(data["width2"]),
            height2=float(data["height2"]),
            heading_deg2=float(data["heading_deg2"]),
            albedo2=float(data["albedo2"]),
        )

    def to_vector(self) -> np.ndarray:
        """Extracts 14-element float array."""
        return np.array([
            self.x1, self.y1, self.length1, self.width1, self.height1, self.heading_deg1, self.albedo1,
            self.x2, self.y2, self.length2, self.width2, self.height2, self.heading_deg2, self.albedo2,
        ], dtype=np.float64)

    @classmethod
    def from_vector(cls, v: np.ndarray) -> TwoPanelParams:
        """Instantiates TwoPanelParams from 14-element vector."""
        return cls(
            x1=float(v[0]), y1=float(v[1]), length1=float(v[2]), width1=float(v[3]),
            height1=float(v[4]), heading_deg1=float(v[5]), albedo1=float(v[6]),
            x2=float(v[7]), y2=float(v[8]), length2=float(v[9]), width2=float(v[10]),
            height2=float(v[11]), heading_deg2=float(v[12]), albedo2=float(v[13]),
        )

    def build_geometries(self,
                         thickness_m: float = 0.1,
                         id_prefix: str = "SHADE_PANEL") -> Tuple[Tuple[TriangleMesh, Polygon], Tuple[TriangleMesh, Polygon]]:
        """
        Builds 3D watertight TriangleMeshes and 2D Shapely Polygons for both panels.
        """
        mesh1, poly1 = build_panel_geometry(self.panel1, thickness_m=thickness_m, mesh_id=f"{id_prefix}_1")
        mesh2, poly2 = build_panel_geometry(self.panel2, thickness_m=thickness_m, mesh_id=f"{id_prefix}_2")
        return (mesh1, poly1), (mesh2, poly2)

    def separation_distance(self) -> float:
        """Computes minimum 2D Euclidean distance between the two panel polygons (0.0 if intersecting)."""
        _, poly1 = build_panel_geometry(self.panel1)
        _, poly2 = build_panel_geometry(self.panel2)
        return float(poly1.distance(poly2))


@dataclass
class TwoPanelBounds:
    """
    Configurable bounds and construction constraints for two-panel optimization.
    """
    panel_bounds: ParameterBounds = field(default_factory=ParameterBounds.get_canonical_church_street_bounds)
    min_separation_m: float = 2.0
    max_individual_area_m2: float = 40.0
    max_total_area_m2: float = 60.0
    min_total_area_m2: float = 10.0

    def contains(self, p: TwoPanelParams) -> bool:
        """Checks if both panels satisfy individual parameter bounds."""
        if not p.is_finite():
            return False
        return self.panel_bounds.contains(p.panel1) and self.panel_bounds.contains(p.panel2)

    def clip(self, p: TwoPanelParams) -> TwoPanelParams:
        """Clips both panels into allowable box bounds."""
        c1 = self.panel_bounds.clip(p.panel1)
        c2 = self.panel_bounds.clip(p.panel2)
        return TwoPanelParams.from_panels(c1, c2)

    def sample_uniform(self, rng: np.random.Generator, n_samples: Optional[int] = None) -> Any:
        """Samples random two-panel candidate(s) uniformly within parameter bounds."""
        def _sample_one() -> TwoPanelParams:
            p1 = self.panel_bounds.sample_uniform(rng)
            p2 = self.panel_bounds.sample_uniform(rng)
            return TwoPanelParams.from_panels(p1, p2).canonicalize()

        if n_samples is not None:
            return [_sample_one() for _ in range(n_samples)]
        return _sample_one()

    def sample_lhs(self, n_samples: int, rng: Optional[np.random.Generator] = None) -> List[TwoPanelParams]:
        """
        Samples candidates using Latin Hypercube Sampling across all 14 dimensions.
        """
        if rng is None:
            rng = np.random.default_rng(42)

        pb = self.panel_bounds
        bounds_arr = np.array([
            # Panel 1
            [pb.x_min, pb.x_max],
            [pb.y_min, pb.y_max],
            [pb.length_min, pb.length_max],
            [pb.width_min, pb.width_max],
            [pb.height_min, pb.height_max],
            [pb.heading_min, pb.heading_max],
            [pb.albedo_min, pb.albedo_max],
            # Panel 2
            [pb.x_min, pb.x_max],
            [pb.y_min, pb.y_max],
            [pb.length_min, pb.length_max],
            [pb.width_min, pb.width_max],
            [pb.height_min, pb.height_max],
            [pb.heading_min, pb.heading_max],
            [pb.albedo_min, pb.albedo_max],
        ], dtype=np.float64)

        d = 14
        lhs_matrix = np.zeros((n_samples, d), dtype=np.float64)
        for j in range(d):
            perm = rng.permutation(n_samples)
            u = rng.uniform(0.0, 1.0, size=n_samples)
            lhs_matrix[:, j] = (perm + u) / float(n_samples)

        scaled = bounds_arr[:, 0] + lhs_matrix * (bounds_arr[:, 1] - bounds_arr[:, 0])
        result = []
        for i in range(n_samples):
            candidate = TwoPanelParams.from_vector(scaled[i]).canonicalize()
            result.append(candidate)
        return result

    @classmethod
    def get_canonical_church_street_bounds(cls) -> TwoPanelBounds:
        """Preconfigured realistic bounds for Church Street two-panel optimization."""
        return cls(
            panel_bounds=ParameterBounds.get_canonical_church_street_bounds(),
            min_separation_m=2.0,
            max_individual_area_m2=40.0,
            max_total_area_m2=60.0,
            min_total_area_m2=10.0,
        )
