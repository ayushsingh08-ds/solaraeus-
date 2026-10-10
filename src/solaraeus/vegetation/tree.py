"""
SOLARAEUS Vegetation Geometry Module
Implements Level 1 tree geometry: trunk cylinder and crown ellipsoid representations.
Tracks provisional uncertainty states: CONSERVATIVE_SMALL, NOMINAL_PROVISIONAL, CONSERVATIVE_LARGE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class Tree:
    tree_id: str
    species: str
    x: float
    y: float
    z_ground: float
    height: float
    crown_radius_x: float
    crown_radius_y: float
    crown_base_height: float  # elevation above ground where crown starts
    trunk_radius: float       # DBH / 2
    transmissivity: float = 0.0
    geometry_state: str = "NOMINAL_PROVISIONAL"
    status: str = "PROVISIONAL_PHOTO_ESTIMATED"
    confidence: str = "PHOTO_ESTIMATED_ONLY"
    uncertainty_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    @property
    def crown_top_z(self) -> float:
        return self.z_ground + self.height

    @property
    def crown_base_z(self) -> float:
        return self.z_ground + self.crown_base_height

    @property
    def crown_center_z(self) -> float:
        return (self.crown_base_z + self.crown_top_z) / 2.0

    @property
    def crown_radius_z(self) -> float:
        return max(0.1, (self.crown_top_z - self.crown_base_z) / 2.0)

    def intersects_ray(
        self,
        ray_origin: Tuple[float, float, float],
        ray_dir: Tuple[float, float, float],
    ) -> bool:
        """
        Tests intersection between a ray (origin + t * dir, t > 0) and the Level 1 tree geometry
        (trunk cylinder + crown ellipsoid).
        """
        ox, oy, oz = ray_origin
        dx, dy, dz = ray_dir

        # Normalize direction
        norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        if norm <= 1e-9:
            return False
        dx, dy, dz = dx / norm, dy / norm, dz / norm

        # 1. Test Trunk Cylinder
        # Equation: (ox + t*dx - x)^2 + (oy + t*dy - y)^2 = r_trunk^2
        # for z in [z_ground, crown_base_z]
        if self.trunk_radius > 0:
            rel_ox = ox - self.x
            rel_oy = oy - self.y
            a_cyl = dx * dx + dy * dy
            if a_cyl > 1e-9:
                b_cyl = 2.0 * (rel_ox * dx + rel_oy * dy)
                c_cyl = rel_ox * rel_ox + rel_oy * rel_oy - self.trunk_radius * self.trunk_radius
                disc_cyl = b_cyl * b_cyl - 4.0 * a_cyl * c_cyl
                if disc_cyl >= 0:
                    sqrt_disc = math.sqrt(disc_cyl)
                    t1 = (-b_cyl - sqrt_disc) / (2.0 * a_cyl)
                    t2 = (-b_cyl + sqrt_disc) / (2.0 * a_cyl)
                    for t in (t1, t2):
                        if t > 1e-4:
                            z_hit = oz + t * dz
                            if self.z_ground <= z_hit <= self.crown_base_z:
                                return True

        # 2. Test Crown Ellipsoid
        # Equation: ((ox + t*dx - x) / rx)^2 + ((oy + t*dy - y) / ry)^2 + ((oz + t*dz - cz) / rz)^2 = 1
        rx = max(0.1, self.crown_radius_x)
        ry = max(0.1, self.crown_radius_y)
        rz = self.crown_radius_z
        cz = self.crown_center_z

        scaled_ox = (ox - self.x) / rx
        scaled_oy = (oy - self.y) / ry
        scaled_oz = (oz - cz) / rz

        scaled_dx = dx / rx
        scaled_dy = dy / ry
        scaled_dz = dz / rz

        a_ell = scaled_dx * scaled_dx + scaled_dy * scaled_dy + scaled_dz * scaled_dz
        b_ell = 2.0 * (scaled_ox * scaled_dx + scaled_oy * scaled_dy + scaled_oz * scaled_dz)
        c_ell = scaled_ox * scaled_ox + scaled_oy * scaled_oy + scaled_oz * scaled_oz - 1.0

        disc_ell = b_ell * b_ell - 4.0 * a_ell * c_ell
        if disc_ell >= 0:
            sqrt_disc = math.sqrt(disc_ell)
            t1 = (-b_ell - sqrt_disc) / (2.0 * a_ell)
            t2 = (-b_ell + sqrt_disc) / (2.0 * a_ell)
            if t1 > 1e-4 or t2 > 1e-4:
                return True

        return False


def get_core_trees(
    geometry_state: str = "NOMINAL_PROVISIONAL",
    ground_elevations: Optional[Dict[str, float]] = None,
    transmissivity: float = 0.0,
) -> List[Tree]:
    """
    Returns the six Church Street core trees (T08 to T13) in the requested geometric state.
    States:
      - 'CONSERVATIVE_SMALL' (min bounds)
      - 'NOMINAL_PROVISIONAL' (central estimates)
      - 'CONSERVATIVE_LARGE' (max bounds)
    """
    if ground_elevations is None:
        ground_elevations = {f"T{i:02d}": 0.0 for i in range(8, 14)}

    # [min, nom, max] bounds from photo review
    raw_specs = {
        "T08": {
            "species": "Ficus religiosa",
            "x": 20.07, "y": 4.12,
            "height": [11.0, 13.5, 16.0],
            "crown_dia": [9.5, 12.0, 15.0],
            "crown_base": [3.8, 4.2, 4.5],
            "dbh": [0.45, 0.55, 0.65],
        },
        "T09": {
            "species": "Syzygium cumini",
            "x": 34.82, "y": 4.05,
            "height": [9.0, 11.0, 13.0],
            "crown_dia": [7.0, 8.5, 10.5],
            "crown_base": [3.2, 3.8, 4.2],
            "dbh": [0.35, 0.45, 0.55],
        },
        "T10": {
            "species": "Syzygium cumini",
            "x": 50.15, "y": 4.21,
            "height": [7.5, 9.5, 11.5],
            "crown_dia": [6.0, 7.5, 9.0],
            "crown_base": [2.8, 3.2, 3.6],
            "dbh": [0.30, 0.40, 0.50],
        },
        "T11": {
            "species": "Saraca asoca",
            "x": 65.40, "y": 3.98,
            "height": [6.5, 8.0, 9.5],
            "crown_dia": [4.2, 5.5, 6.8],
            "crown_base": [2.4, 2.8, 3.2],
            "dbh": [0.20, 0.28, 0.35],
        },
        "T12": {
            "species": "Saraca asoca",
            "x": 80.20, "y": 4.10,
            "height": [6.0, 7.5, 9.0],
            "crown_dia": [3.8, 5.0, 6.2],
            "crown_base": [2.2, 2.6, 3.0],
            "dbh": [0.18, 0.25, 0.32],
        },
        "T13": {
            "species": "Tecoma stans",
            "x": 97.09, "y": 4.02,
            "height": [3.8, 5.0, 6.5],
            "crown_dia": [2.6, 3.5, 4.5],
            "crown_base": [1.4, 1.8, 2.2],
            "dbh": [0.12, 0.18, 0.25],
        },
    }

    idx = 1
    if geometry_state == "CONSERVATIVE_SMALL":
        idx = 0
    elif geometry_state == "CONSERVATIVE_LARGE":
        idx = 2

    trees = []
    for tid, s in raw_specs.items():
        h = s["height"][idx]
        cd = s["crown_dia"][idx]
        cb = s["crown_base"][idx]
        dbh = s["dbh"][idx]
        z_g = ground_elevations.get(tid, 0.0)

        t = Tree(
            tree_id=tid,
            species=s["species"],
            x=s["x"],
            y=s["y"],
            z_ground=z_g,
            height=h,
            crown_radius_x=cd / 2.0,
            crown_radius_y=cd / 2.0,
            crown_base_height=cb,
            trunk_radius=dbh / 2.0,
            transmissivity=transmissivity,
            geometry_state=geometry_state,
            status="PROVISIONAL_PHOTO_ESTIMATED",
            confidence="PHOTO_ESTIMATED_ONLY",
            uncertainty_bounds={
                "height": (s["height"][0], s["height"][2]),
                "crown_diameter": (s["crown_dia"][0], s["crown_dia"][2]),
                "crown_base": (s["crown_base"][0], s["crown_base"][2]),
            },
        )
        trees.append(t)

    return trees
