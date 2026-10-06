"""
Church Street urban dataset adapter and geometric preprocessor for SOLARAEUS.

Converts Bengaluru Church Street geospatial footprints (EPSG:4326) and researcher-reviewed
building height models into validated 3D triangular-mesh scenes in local metric coordinates
(EPSG:32643 UTM Zone 43N projected, translated to local Cartesian meters).

Scientific note:
"The Church Street scene has been converted into an exploratory local-coordinate
triangular-mesh representation using approved but partly uncertain building-height estimates."
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mapbox_earcut
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Polygon, MultiPolygon

from urban_comfort.config import (
    Material,
    DEFAULT_GROUND_MATERIAL,
    DEFAULT_WALL_MATERIAL,
)
from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.geometry.scene import GroundPlane, PedestrianGridConfig, Scene


@dataclass
class PreprocessingConfig:
    """Configuration parameters for Church Street preprocessing."""

    handoff_dir: Path = field(
        default_factory=lambda: Path(
            "bengaluru_church_street_manual_handoff_v2/bengaluru_church_street_manual_handoff_v2/data/processed"
        )
    )
    approved_heights_path: Path = field(
        default_factory=lambda: Path("data/processed/approved_building_heights.csv")
    )
    researcher_signoff_path: Path = field(
        default_factory=lambda: Path("data/processed/researcher_signoff.json")
    )
    source_crs: str = "EPSG:4326"
    metric_crs: str = "EPSG:32643"
    # Local coordinate origin in EPSG:32643 (UTM Zone 43N meters)
    local_origin_x: float = 782541.8055380594
    local_origin_y: float = 1435736.1103432046
    local_origin_z: float = 0.0
    # Grid convergence at site center (degrees)
    grid_convergence_deg: float = 0.585366
    # Fallback height for buildings with no height data (3 commercial stories * 3.2m)
    commercial_canyon_fallback_m: float = 9.6
    # Material definitions
    wall_albedo: float = 0.25
    wall_emissivity: float = 0.90
    wall_temp_k: float = 308.15
    roof_albedo: float = 0.20
    roof_emissivity: float = 0.90
    roof_temp_k: float = 313.15


@dataclass
class PreprocessedSceneResult:
    """Result of preprocessing containing scenes, meshes, and audit metadata."""

    main_scene: Scene
    shadow_context_scene: Scene
    core_meshes: Dict[str, TriangleMesh]
    context_meshes: Dict[str, TriangleMesh]
    mesh_statistics: List[Dict[str, Any]]
    uncertain_buildings: List[Dict[str, Any]]
    rejected_or_failed_features: List[Dict[str, Any]]
    coordinate_validation: Dict[str, Any]
    height_policy_summary: Dict[str, Any]


class ChurchStreetAdapter:
    """
    Adapter for processing Church Street geospatial data into SOLARAEUS TriangleMesh scenes.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self.transformer = Transformer.from_crs(
            self.config.source_crs, self.config.metric_crs, always_xy=True
        )

        # Materials
        self.wall_material = Material(
            id="building_wall",
            albedo=self.config.wall_albedo,
            emissivity=self.config.wall_emissivity,
            surface_temperature=self.config.wall_temp_k,
            is_opaque=True,
        )
        self.roof_material = Material(
            id="building_roof",
            albedo=self.config.roof_albedo,
            emissivity=self.config.roof_emissivity,
            surface_temperature=self.config.roof_temp_k,
            is_opaque=True,
        )

    def to_local_xy(self, lon: float, lat: float) -> Tuple[float, float]:
        """Projects (lon, lat) to UTM 43N meters and subtracts local Cartesian origin."""
        utm_x, utm_y = self.transformer.transform(lon, lat)
        local_x = utm_x - self.config.local_origin_x
        local_y = utm_y - self.config.local_origin_y
        return local_x, local_y

    def load_core_heights(self) -> Dict[str, Dict[str, Any]]:
        """Loads approved height policy for the 37 core study buildings."""
        path = self.config.approved_heights_path
        if not path.exists():
            candidate = self.config.handoff_dir / path.name
            if candidate.exists():
                path = candidate
            else:
                raise FileNotFoundError(f"Core approved heights file not found at: {path}")

        heights: Dict[str, Dict[str, Any]] = {}
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                b_id = str(row["building_id"])
                assigned_h = float(row["assigned_model_height_m"])
                status = row.get("decision_status", "approved").upper()
                uncertainty = row.get("uncertainty_level", "moderate").upper()
                method = row.get("height_source_type", "Google/ML-estimated")
                notes = row.get("decision_rationale", "")

                heights[b_id] = {
                    "building_id": b_id,
                    "approved_height_m": assigned_h,
                    "uncertainty_flag": uncertainty,
                    "status": status,
                    "method": method,
                    "notes": notes,
                }
        return heights

    def load_context_heights(self) -> Dict[str, Dict[str, Any]]:
        """Loads context building heights from review CSV."""
        path = self.config.handoff_dir / "context_height_review.csv"
        if not path.exists():
            raise FileNotFoundError(f"Context height review file not found at: {path}")

        heights: Dict[str, Dict[str, Any]] = {}
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                b_id = str(row["building_id"])
                ml_val = row.get("google_2023_estimated_height_m", "").strip()
                fl_val = row.get("proposed_height_from_floors_m", "").strip()
                prio = row.get("google_height_review_priority", "normal")
                pix = row.get("google_height_valid_pixel_fraction", "")

                if ml_val:
                    accepted_h = float(ml_val)
                    uncertainty = "HIGH" if prio == "high" else "MODERATE"
                    status = "ACCEPTED"
                    method = "google_ml_estimate"
                    notes = f"Google 2023 ML estimate ({accepted_h}m, pixel coverage {pix})"
                elif fl_val:
                    accepted_h = float(fl_val)
                    uncertainty = "HIGH"
                    status = "ACCEPTED"
                    method = "floor_count_fallback"
                    notes = f"Floor count fallback ({row.get('source_num_floors')} floors = {accepted_h}m)"
                else:
                    accepted_h = self.config.commercial_canyon_fallback_m
                    uncertainty = "EXTREME"
                    status = "UNCERTAIN"
                    method = "commercial_canyon_fallback"
                    notes = "Missing both ML estimate and floor count in context; assigned 9.6m canyon fallback"

                heights[b_id] = {
                    "building_id": b_id,
                    "accepted_height_m": accepted_h,
                    "uncertainty_flag": uncertainty,
                    "status": status,
                    "method": method,
                    "notes": notes,
                }
        return heights

    def triangulate_and_extrude(
        self,
        polygon: Polygon,
        height: float,
        mesh_id: str,
        material_id: str = "building_wall",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TriangleMesh:
        """
        Extrudes a 2D local polygon into a watertight 3D TriangleMesh.

        - Base vertices at z = 0.0
        - Roof vertices at z = height
        - Outward-pointing wall triangles
        - Upward-pointing roof triangles
        - Downward-pointing floor triangles (ensuring a closed 2-manifold)
        """
        if height <= 0.0:
            raise ValueError(f"Building height must be strictly positive, got {height}m")

        ext_coords = list(polygon.exterior.coords)
        # Drop redundant closing coordinate if present
        if len(ext_coords) > 1 and np.allclose(ext_coords[0], ext_coords[-1]):
            ext_coords = ext_coords[:-1]

        n_verts = len(ext_coords)
        if n_verts < 3:
            raise ValueError(f"Polygon must have at least 3 distinct vertices, got {n_verts}")

        # Compute signed area to enforce counter-clockwise (CCW) winding
        signed_area = 0.0
        for i in range(n_verts):
            x1, y1 = ext_coords[i]
            x2, y2 = ext_coords[(i + 1) % n_verts]
            signed_area += (x1 * y2 - x2 * y1)
        signed_area *= 0.5

        if abs(signed_area) < 1e-6:
            raise ValueError(f"Polygon has near-zero 2D footprint area: {abs(signed_area):.4e} m^2")

        if signed_area < 0:
            # Clockwise -> reverse to make CCW
            ext_coords.reverse()

        coords_arr = np.array(ext_coords, dtype=np.float64)  # Shape (N, 2)

        # Triangulate 2D footprint using mapbox_earcut
        ring_indices = np.array([n_verts], dtype=np.uint32)
        tri_indices = mapbox_earcut.triangulate_float64(coords_arr, ring_indices)
        tri_2d = tri_indices.reshape(-1, 3)

        if len(tri_2d) == 0:
            raise ValueError(f"Ear-clipping triangulation produced 0 triangles for mesh {mesh_id}")

        # Construct 3D vertices:
        # 0 .. N-1: Base vertices at z = 0.0
        # N .. 2N-1: Top/roof vertices at z = height
        v_base = np.column_stack([coords_arr, np.zeros(n_verts, dtype=np.float64)])
        v_top = np.column_stack([coords_arr, np.full(n_verts, height, dtype=np.float64)])
        vertices_3d = np.vstack([v_base, v_top])  # Shape (2N, 3)

        triangles_list: List[Tuple[int, int, int]] = []

        # 1. Side wall quads triangulated as two triangles with outward normals
        for i in range(n_verts):
            j = (i + 1) % n_verts
            # Triangle 1: [i, j, j + N]
            triangles_list.append((i, j, j + n_verts))
            # Triangle 2: [i, j + N, i + N]
            triangles_list.append((i, j + n_verts, i + n_verts))

        # 2. Roof triangles (+Z normal, same winding as CCW 2D)
        for tri in tri_2d:
            triangles_list.append((int(tri[0] + n_verts), int(tri[1] + n_verts), int(tri[2] + n_verts)))

        # 3. Floor/Base triangles (-Z normal, reversed winding)
        for tri in tri_2d:
            triangles_list.append((int(tri[0]), int(tri[2]), int(tri[1])))

        triangles_3d = np.array(triangles_list, dtype=np.int64)

        mesh_meta = metadata.copy() if metadata else {}
        mesh_meta["height_m"] = height
        mesh_meta["footprint_vertices"] = n_verts
        mesh_meta["polygon_area_m2"] = abs(signed_area)

        return TriangleMesh(
            id=mesh_id,
            vertices=vertices_3d,
            triangles=triangles_3d,
            material_id=material_id,
            enabled=True,
            metadata=mesh_meta,
        )

    def process(self) -> PreprocessedSceneResult:
        """
        Executes the full preprocessing pipeline:
        1. Loads footprints for core and context buildings.
        2. Assigns heights adhering to approved policy.
        3. Projects coordinates to local Cartesian system.
        4. Triangulates and extrudes geometries into watertight 3D TriangleMeshes.
        5. Performs geometric and coordinate audits.
        6. Constructs SOLARAEUS Scene objects for main scene and shadow context.
        """
        # Load height policies
        core_height_policy = self.load_core_heights()
        context_height_policy = self.load_context_heights()

        # Load GeoJSON files
        site_geojson_path = self.config.handoff_dir / "buildings_site.geojson"
        context_geojson_path = self.config.handoff_dir / "buildings_shadow_context.geojson"

        with open(site_geojson_path, mode="r", encoding="utf-8") as f:
            site_geojson = json.load(f)
        with open(context_geojson_path, mode="r", encoding="utf-8") as f:
            context_geojson = json.load(f)

        core_meshes: Dict[str, TriangleMesh] = {}
        context_meshes: Dict[str, TriangleMesh] = {}
        mesh_statistics: List[Dict[str, Any]] = []
        uncertain_buildings: List[Dict[str, Any]] = []
        rejected_or_failed_features: List[Dict[str, Any]] = []

        all_local_xs: List[float] = []
        all_local_ys: List[float] = []

        # Helper to process a single feature
        def process_feature(feat: Dict[str, Any], is_core: bool) -> Optional[TriangleMesh]:
            props = feat.get("properties", {})
            b_id = str(props.get("building_id") or props.get("id"))
            geom = shape(feat.get("geometry", {}))

            # Determine polygon geometry
            if isinstance(geom, Polygon):
                poly = geom
            elif isinstance(geom, MultiPolygon):
                # Take largest polygon part if MultiPolygon
                poly = max(geom.geoms, key=lambda p: p.area)
            else:
                rejected_or_failed_features.append({
                    "building_id": b_id,
                    "reason": f"Unsupported geometry type: {geom.geom_type}",
                    "is_core": is_core,
                })
                return None

            # Height assignment
            if is_core or (b_id in core_height_policy):
                h_info = core_height_policy.get(b_id)
                if h_info is None:
                    rejected_or_failed_features.append({
                        "building_id": b_id,
                        "reason": "Missing from approved core heights table",
                        "is_core": is_core,
                    })
                    return None
                height_m = h_info["approved_height_m"]
                status = h_info["status"]
                uncertainty = h_info["uncertainty_flag"]
                method = "core_approved_table"
                notes = h_info.get("notes", "")
            else:
                h_info = context_height_policy.get(b_id)
                if h_info is not None:
                    height_m = h_info["accepted_height_m"]
                    status = h_info["status"]
                    uncertainty = h_info["uncertainty_flag"]
                    method = h_info["method"]
                    notes = h_info.get("notes", "")
                else:
                    height_m = self.config.commercial_canyon_fallback_m
                    status = "ACCEPTED"
                    uncertainty = "EXTREME"
                    method = "commercial_canyon_fallback"
                    notes = "Not present in context height table; assigned default canyon height"

            # Transform footprint to local Cartesian coordinates
            ext_lon_lats = list(poly.exterior.coords)
            local_ring = [self.to_local_xy(lon, lat) for lon, lat in ext_lon_lats]
            local_poly = Polygon(local_ring)

            for lx, ly in local_ring:
                all_local_xs.append(lx)
                all_local_ys.append(ly)

            meta = {
                "building_id": b_id,
                "is_core": is_core,
                "height_m": height_m,
                "status": status,
                "uncertainty_flag": uncertainty,
                "method": method,
                "notes": notes,
                "original_properties": props,
            }

            try:
                mesh = self.triangulate_and_extrude(
                    polygon=local_poly,
                    height=height_m,
                    mesh_id=f"building_{b_id}",
                    material_id="building_wall",
                    metadata=meta,
                )
            except Exception as e:
                rejected_or_failed_features.append({
                    "building_id": b_id,
                    "reason": f"Triangulation/extrusion failure: {str(e)}",
                    "is_core": is_core,
                })
                return None

            # Calculate geometric statistics
            roof_area = float(np.sum(mesh.face_areas[2 * mesh.metadata["footprint_vertices"] : 2 * mesh.metadata["footprint_vertices"] + (mesh.metadata["footprint_vertices"] - 2)]))
            poly_area = mesh.metadata["polygon_area_m2"]
            area_discrepancy = abs(roof_area - poly_area)

            stat_entry = {
                "building_id": b_id,
                "is_core": is_core,
                "height_m": height_m,
                "status": status,
                "uncertainty_flag": uncertainty,
                "method": method,
                "num_vertices": mesh.num_vertices,
                "num_triangles": mesh.num_triangles,
                "footprint_area_m2": round(poly_area, 2),
                "roof_area_m2": round(roof_area, 2),
                "total_surface_area_m2": round(mesh.total_surface_area, 2),
                "area_discrepancy_m2": round(area_discrepancy, 6),
                "xmin": round(mesh.xmin, 2),
                "xmax": round(mesh.xmax, 2),
                "ymin": round(mesh.ymin, 2),
                "ymax": round(mesh.ymax, 2),
                "zmin": round(mesh.zmin, 2),
                "zmax": round(mesh.zmax, 2),
            }
            mesh_statistics.append(stat_entry)

            if status == "UNCERTAIN" or uncertainty in ("HIGH", "EXTREME"):
                uncertain_buildings.append({
                    "building_id": b_id,
                    "is_core": is_core,
                    "height_m": height_m,
                    "uncertainty_flag": uncertainty,
                    "status": status,
                    "method": method,
                    "notes": notes,
                })

            return mesh

        # Process site buildings (core 37)
        for feat in site_geojson.get("features", []):
            mesh = process_feature(feat, is_core=True)
            if mesh:
                core_meshes[mesh.id] = mesh

        # Process context buildings (123 total: include core + context-only)
        for feat in context_geojson.get("features", []):
            props = feat.get("properties", {})
            b_id = str(props.get("building_id") or props.get("id"))
            mesh_id = f"building_{b_id}"

            if mesh_id in core_meshes:
                context_meshes[mesh_id] = core_meshes[mesh_id]
            else:
                mesh = process_feature(feat, is_core=False)
                if mesh:
                    context_meshes[mesh.id] = mesh

        # Coordinate domain validations
        min_lx = min(all_local_xs) if all_local_xs else 0.0
        max_lx = max(all_local_xs) if all_local_xs else 0.0
        min_ly = min(all_local_ys) if all_local_ys else 0.0
        max_ly = max(all_local_ys) if all_local_ys else 0.0

        coord_val = {
            "source_crs": self.config.source_crs,
            "metric_crs": self.config.metric_crs,
            "local_origin": {
                "x_utm_m": self.config.local_origin_x,
                "y_utm_m": self.config.local_origin_y,
                "z_m": self.config.local_origin_z,
            },
            "grid_convergence_degrees": self.config.grid_convergence_deg,
            "grid_convergence_arcmin": round(self.config.grid_convergence_deg * 60, 2),
            "study_area_extent_local_m": {
                "xmin": round(min_lx, 2),
                "xmax": round(max_lx, 2),
                "ymin": round(min_ly, 2),
                "ymax": round(max_ly, 2),
                "width_m": round(max_lx - min_lx, 2),
                "length_m": round(max_ly - min_ly, 2),
            },
            "terrain_policy": {
                "model_ground_elevation_z": 0.0,
                "terrain_status": "retained_for_metadata_only_flat_model_ground_in_solver",
            },
        }

        # Height policy summary with clear distinction between Decision Status and Uncertainty Tier
        approved_core = sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "APPROVED")
        uncertain_core = sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "UNCERTAIN")
        accepted_context = sum(1 for m in mesh_statistics if not m["is_core"] and m["status"] == "ACCEPTED")
        uncertain_context = sum(1 for m in mesh_statistics if not m["is_core"] and m["status"] == "UNCERTAIN")

        moderate_cnt = sum(1 for m in mesh_statistics if m["uncertainty_flag"] == "MODERATE")
        high_cnt = sum(1 for m in mesh_statistics if m["uncertainty_flag"] == "HIGH")
        extreme_cnt = sum(1 for m in mesh_statistics if m["uncertainty_flag"] == "EXTREME")
        high_or_extreme_cohort = high_cnt + extreme_cnt  # 40 buildings

        height_summary = {
            "total_buildings_processed": len(mesh_statistics),
            "core_buildings_count": len(core_meshes),
            "context_buildings_count": len(context_meshes),
            "decision_status_classification": {
                "approved_core_count": approved_core,
                "accepted_context_count": accepted_context,
                "total_approved_or_accepted": approved_core + accepted_context,  # 107
                "uncertain_core_count": uncertain_core,
                "uncertain_context_count": uncertain_context,
                "total_uncertain_status": uncertain_core + uncertain_context,  # 16
                "rejected_count": len(rejected_or_failed_features),  # 0
            },
            "uncertainty_tier_classification": {
                "moderate_uncertainty_count": moderate_cnt,  # 83
                "high_uncertainty_count": high_cnt,  # 29
                "extreme_uncertainty_count": extreme_cnt,  # 11
                "high_or_extreme_sensitivity_cohort": high_or_extreme_cohort,  # 40
            },
            "cross_tabulation": {
                "approved_core_moderate": sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "APPROVED" and m["uncertainty_flag"] == "MODERATE"),
                "approved_core_high": sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "APPROVED" and m["uncertainty_flag"] == "HIGH"),
                "accepted_context_moderate": sum(1 for m in mesh_statistics if not m["is_core"] and m["status"] == "ACCEPTED" and m["uncertainty_flag"] == "MODERATE"),
                "accepted_context_high": sum(1 for m in mesh_statistics if not m["is_core"] and m["status"] == "ACCEPTED" and m["uncertainty_flag"] == "HIGH"),
                "uncertain_core_high": sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "UNCERTAIN" and m["uncertainty_flag"] == "HIGH"),
                "uncertain_core_extreme": sum(1 for m in mesh_statistics if m["is_core"] and m["status"] == "UNCERTAIN" and m["uncertainty_flag"] == "EXTREME"),
                "uncertain_context_extreme": sum(1 for m in mesh_statistics if not m["is_core"] and m["status"] == "UNCERTAIN" and m["uncertainty_flag"] == "EXTREME"),
            },
            "commercial_canyon_fallback_height_m": self.config.commercial_canyon_fallback_m,
            "scientific_framing": (
                "The Church Street scene has been converted into an exploratory "
                "local-coordinate triangular-mesh representation using approved but "
                "partly uncertain building-height estimates."
            ),
        }

        # Construct Scenes
        materials_dict = {
            "default_wall": DEFAULT_WALL_MATERIAL,
            "default_ground": DEFAULT_GROUND_MATERIAL,
            "building_wall": self.wall_material,
            "building_roof": self.roof_material,
        }

        # Pedestrian grid covers core domain with a margin (230m x 145m at 1m res = 33,350 cells)
        ped_grid = PedestrianGridConfig(
            extent_x=230.0,
            extent_y=145.0,
            origin_x=-10.0,
            origin_y=-5.0,
            resolution=1.0,
            pedestrian_height=1.1,
        )

        main_scene = Scene(
            meshes=core_meshes,
            ground=GroundPlane(z_elevation=0.0, material_id="default_ground"),
            pedestrian_grid=ped_grid,
            materials=materials_dict,
            coordinate_system="EPSG:32643_LOCAL",
            metadata={
                "site": "Church Street central/eastern study block",
                "city": "Bengaluru, Karnataka, India",
                "simulation_status": "preprocessing_only",
                "building_count": len(core_meshes),
                "local_origin": coord_val["local_origin"],
                "grid_convergence_deg": self.config.grid_convergence_deg,
            },
        )

        # Context pedestrian grid covers expanded 75m buffer:
        # 380m x 296m at 2m resolution gives exactly nx=190, ny=148, total_cells = 190 * 148 = 28,120 cells
        # (380.0 * 296.0) / 2.0^2 = 112,480 / 4 = 28,120 cells with zero rounding error.
        context_ped_grid = PedestrianGridConfig(
            extent_x=380.0,
            extent_y=296.0,
            origin_x=-85.0,
            origin_y=-80.0,
            resolution=2.0,
            pedestrian_height=1.1,
        )

        shadow_context_scene = Scene(
            meshes=context_meshes,
            ground=GroundPlane(z_elevation=0.0, material_id="default_ground"),
            pedestrian_grid=context_ped_grid,
            materials=materials_dict,
            coordinate_system="EPSG:32643_LOCAL",
            metadata={
                "site": "Church Street shadow context domain (75m expanded)",
                "city": "Bengaluru, Karnataka, India",
                "simulation_status": "preprocessing_only",
                "building_count": len(context_meshes),
                "local_origin": coord_val["local_origin"],
                "grid_convergence_deg": self.config.grid_convergence_deg,
            },
        )

        return PreprocessedSceneResult(
            main_scene=main_scene,
            shadow_context_scene=shadow_context_scene,
            core_meshes=core_meshes,
            context_meshes=context_meshes,
            mesh_statistics=mesh_statistics,
            uncertain_buildings=uncertain_buildings,
            rejected_or_failed_features=rejected_or_failed_features,
            coordinate_validation=coord_val,
            height_policy_summary=height_summary,
        )
