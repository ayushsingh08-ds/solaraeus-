"""
3D Watertight Building Mesh Extrusion Engine.
Converts 2D building footprint polygons with heights into 3D watertight polyhedral meshes.
Exports composite 3D geometry in OBJ and frontend JSON format.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import geopandas as gpd
import numpy as np
import shapely.geometry
import trimesh
from shapely.geometry import MultiPolygon, Polygon

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)


def _extrude_single_polygon(poly: Polygon, height_m: float, z_base: float = 0.0) -> Optional[trimesh.Trimesh]:
    """Extrudes a single 2D Shapely polygon into a 3D prism using trimesh."""
    if poly is None or poly.is_empty or poly.area < 1.0 or height_m <= 0.5:
        return None

    # Clean potential topological defects
    clean_poly = poly.buffer(0)
    if clean_poly.is_empty:
        return None

    if isinstance(clean_poly, MultiPolygon):
        sub_meshes = []
        for p in clean_poly.geoms:
            m = _extrude_single_polygon(p, height_m, z_base)
            if m is not None:
                sub_meshes.append(m)
        return trimesh.util.concatenate(sub_meshes) if sub_meshes else None

    try:
        # Extrude 2D polygon along Z
        mesh = trimesh.creation.extrude_polygon(clean_poly, height=height_m)
        # Shift base of extrusion to ground elevation
        if z_base != 0.0:
            mesh.apply_translation([0.0, 0.0, z_base])
        return mesh
    except Exception as e:
        logger.debug(f"Failed to extrude polygon: {e}")
        return None


def build_building_meshes(
    buildings_table: Optional[gpd.GeoDataFrame] = None,
    dem_array: Optional[np.ndarray] = None,
    config: Optional[ProjectConfig] = None,
    study_area: Optional[StudyArea] = None,
) -> trimesh.Trimesh:
    """
    Builds 3D extruded watertight meshes for all building footprints in the study area.

    Args:
        buildings_table: GeoDataFrame in target UTM coordinates with 'height_m'.
        dem_array: Optional ground DEM to position building foundations.
        config: Project configuration.
        study_area: Target study area.

    Returns:
        trimesh.Trimesh composite watertight mesh containing all 3D buildings.
    """
    if config is None:
        config = ProjectConfig()
    if study_area is None:
        study_area = config.study_area

    config.data.ensure_dirs()
    safe_name = study_area.name.lower().replace(" ", "_").replace("/", "_")

    # If buildings not passed, load from processed parquet
    if buildings_table is None:
        table_path = config.data.processed_dir / f"{safe_name}_buildings_utm.parquet"
        if table_path.exists():
            buildings_table = gpd.read_parquet(table_path)
        else:
            raise FileNotFoundError(f"Buildings table not found at {table_path}")

    logger.info(f"Extruding {len(buildings_table)} building footprints into 3D meshes...")

    mesh_list: List[trimesh.Trimesh] = []
    n_skipped = 0

    # Minimum base ground elevation
    z_ground_default = float(np.nanmin(dem_array)) if dem_array is not None else 0.0

    for idx, row in buildings_table.iterrows():
        geom = row.geometry
        height = float(row.get("height_m", 8.0))

        if geom is None or geom.is_empty:
            n_skipped += 1
            continue

        if isinstance(geom, MultiPolygon):
            for part in geom.geoms:
                m = _extrude_single_polygon(part, height, z_base=z_ground_default)
                if m is not None:
                    mesh_list.append(m)
        elif isinstance(geom, Polygon):
            m = _extrude_single_polygon(geom, height, z_base=z_ground_default)
            if m is not None:
                mesh_list.append(m)
        else:
            n_skipped += 1

    if not mesh_list:
        logger.warning("No valid building meshes could be extruded! Creating placeholder cube.")
        combined = trimesh.creation.box([10, 10, 10])
    else:
        combined = trimesh.util.concatenate(mesh_list)

    # Watertight & topology checks
    is_watertight = bool(combined.is_watertight)
    n_vertices = len(combined.vertices)
    n_faces = len(combined.faces)

    logger.info(
        f"Composite 3D Mesh built: {len(mesh_list)} prisms, {n_vertices:,} vertices, "
        f"{n_faces:,} faces. Watertight: {is_watertight} (Skipped: {n_skipped})"
    )

    # 1. Export Wavefront OBJ
    obj_path = config.data.meshes_dir / "buildings_3d.obj"
    combined.export(str(obj_path))
    logger.info(f"Saved 3D OBJ mesh to {obj_path}")

    # 2. Export frontend JSON contract
    json_mesh_path = config.data.meshes_dir / "buildings_3d.json"
    # To keep JSON size manageable and coordinates relative for browser rendering:
    # Offset coordinates by UTM bounds min
    origin_x = study_area.utm_bounds[0]
    origin_y = study_area.utm_bounds[1]

    rel_vertices = combined.vertices.copy()
    rel_vertices[:, 0] -= origin_x
    rel_vertices[:, 1] -= origin_y

    frontend_mesh_dict = {
        "bounds": {
            "xmin": float(study_area.utm_bounds[0]),
            "ymin": float(study_area.utm_bounds[1]),
            "xmax": float(study_area.utm_bounds[2]),
            "ymax": float(study_area.utm_bounds[3]),
        },
        "origin": [float(origin_x), float(origin_y), float(z_ground_default)],
        "numVertices": n_vertices,
        "numFaces": n_faces,
        "isWatertight": is_watertight,
        "vertices": np.round(rel_vertices, 2).flatten().tolist(),
        "faces": combined.faces.flatten().tolist(),
    }

    with open(json_mesh_path, "w") as f:
        json.dump(frontend_mesh_dict, f)
    logger.info(f"Saved frontend 3D JSON mesh to {json_mesh_path}")

    # 3. Cache binary mesh for Ray Tracer / Stage 2
    pkl_path = config.data.cache_dir / f"{safe_name}_building_mesh.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(combined, f)
    logger.info(f"Cached 3D mesh object to {pkl_path}")

    return combined


# Convenience alias matching mainbackendpart.md
build = build_building_meshes
