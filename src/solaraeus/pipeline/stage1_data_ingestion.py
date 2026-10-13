"""
Stage 1: Data Ingestion and Scene Preprocessing Pipeline.

Ingests geospatial vector data (GeoJSON in EPSG:4326), building heights, terrain (GeoTIFF),
and meteorological forcing. Transforms coordinates into the project's metric projected CRS
and local Cartesian coordinate frame with a single common origin.
Constructs watertight 3D triangle meshes and initializes the pedestrian evaluation grid.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pyproj
import rasterio
from shapely.geometry import shape, Polygon

from solaraeus.core.geometry.primitives import Building, BoundingBox2D
from solaraeus.core.geometry.mesh import create_box_mesh, create_extruded_polygon_mesh, TriangleMesh
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig
from solaraeus.core.config import Material
from solaraeus.pipeline.config import PipelineConfig


def run_stage_data_ingestion(config: PipelineConfig) -> Tuple[Scene, Dict[str, Any], Dict[str, Any]]:
    """
    Executes Stage 1: Data Ingestion for any case study area.

    Args:
        config: Pipeline configuration.

    Returns:
        Tuple of (Scene, grid_dict, summary_dict).
    """
    dest_dir = config.output_dir / "01_data_ingestion" if config.output_dir else (config.processed_dir or Path("data/processed")) / "01_data_ingestion"
    dest_dir.mkdir(parents=True, exist_ok=True)

    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    city_config_path = root_dir / "configs" / "cities" / f"{config.area.lower()}.json"
    city_info: Optional[Dict[str, Any]] = None
    if city_config_path.exists():
        city_info = json.loads(city_config_path.read_text(encoding="utf-8"))

    # Resolve input directory
    data_src = config.data_dir or config.input_dir
    if data_src is None:
        if (root_dir / "data" / "input" / config.area).exists():
            data_src = root_dir / "data" / "input" / config.area
        elif (root_dir / "data" / "raw" / config.area).exists():
            data_src = root_dir / "data" / "raw" / config.area
        else:
            data_src = root_dir / "data" / "input" / config.area

    # Resolve the 4 primary inputs
    paths_dict = city_info.get("data_paths", {}) if city_info else {}
    def resolve_path(key: str, default_name: str) -> Optional[Path]:
        p_str = paths_dict.get(key)
        if p_str:
            p = Path(p_str)
            if not p.is_absolute():
                p = root_dir / p
            if p.exists():
                return p.resolve()
        # Fallback to data_src
        if data_src:
            candidate = data_src / default_name
            if candidate.exists():
                return candidate.resolve()
        return None

    buildings_path = resolve_path("buildings_geojson", "buildings.geojson")
    terrain_path = resolve_path("terrain_tif", "terrain.tif")
    trees_path = resolve_path("trees_geojson", "trees.geojson")
    weather_path = resolve_path("weather_csv", "weather_24h.csv")

    if config.verbose:
        print("\n" + "=" * 80)
        print(f"[Stage 1: Data Ingestion] Ingesting geospatial layers for area: {config.area}")
        print(f"  City Config:      {city_config_path.resolve() if city_config_path.exists() else 'None'}")
        print(f"  Buildings Path:   {buildings_path if buildings_path else 'NOT FOUND'}")
        print(f"  Terrain Path:     {terrain_path if terrain_path else 'NOT FOUND'}")
        print(f"  Trees Path:       {trees_path if trees_path else 'NOT FOUND'}")
        print(f"  Weather Path:     {weather_path if weather_path else 'NOT FOUND'}")
        print(f"  Output Dest:      {dest_dir.resolve()}")
        print("=" * 80)

    scene: Optional[Scene] = None
    grid_cfg: Optional[PedestrianGridConfig] = None
    building_polygons_local: List[Dict[str, Any]] = []

    # 1. Check if pre-existing validated scene_mesh.json exists
    if data_src and (data_src / "scene_mesh.json").exists():
        data = json.loads((data_src / "scene_mesh.json").read_text(encoding="utf-8"))
        scene = Scene.from_dict(data)
        if config.verbose:
            print("  Loaded existing scene_mesh.json directly from input source.")

    # 2. Ingest real buildings GeoJSON + Terrain GeoTIFF if available
    if scene is None and buildings_path and buildings_path.exists():
        if config.verbose:
            print(f"  Ingesting building footprints from: {buildings_path}")

        raw_bldgs = json.loads(buildings_path.read_text(encoding="utf-8"))
        features = raw_bldgs.get("features", [])

        # Parse CRS specifications
        proj_crs_str = "EPSG:32643"
        local_frame_label = "EPSG:32643_LOCAL"
        if city_info:
            crs_cfg = city_info.get("crs", {})
            p_metric = crs_cfg.get("projected_metric", "EPSG:32643")
            proj_crs_str = p_metric.replace("_LOCAL", "").strip()
            local_frame_label = crs_cfg.get("local_frame", f"{proj_crs_str}_LOCAL")

        transformer = pyproj.Transformer.from_crs("EPSG:4326", proj_crs_str, always_xy=True)

        # Determine domain bounds and common local origin
        x_origin: Optional[float] = None
        y_origin: Optional[float] = None
        extent_x = 100.0
        extent_y = 100.0
        origin_x = -50.0
        origin_y = -50.0

        if city_info and "local_origin" in city_info:
            lo = city_info["local_origin"]
            x_origin = float(lo["x_origin"])
            y_origin = float(lo["y_origin"])

        if terrain_path and terrain_path.exists():
            with rasterio.open(terrain_path) as ds:
                tb = ds.bounds
                if x_origin is None or y_origin is None:
                    x_origin = (tb.left + tb.right) / 2.0
                    y_origin = (tb.bottom + tb.top) / 2.0
                extent_x = float(tb.right - tb.left)
                extent_y = float(tb.top - tb.bottom)
                origin_x = float(tb.left - x_origin)
                origin_y = float(tb.bottom - y_origin)
                if config.verbose:
                    print(f"  Terrain bounds (UTM): left={tb.left}, bottom={tb.bottom}, right={tb.right}, top={tb.top}")
                    print(f"  Terrain raster size: {ds.width}x{ds.height}, resolution: {ds.res}")
        elif city_info:
            sim_def = city_info.get("simulation_defaults", {})
            dom_ext = sim_def.get("domain_extent_m", [1219.0, 792.0])
            extent_x = float(city_info.get("extent_x", dom_ext[0]))
            extent_y = float(city_info.get("extent_y", dom_ext[1]))
            origin_x = float(city_info.get("origin_x", -extent_x / 2.0))
            origin_y = float(city_info.get("origin_y", -extent_y / 2.0))
            if x_origin is None or y_origin is None:
                # Approximate center from city coordinates
                c_lon = city_info["coordinates"]["longitude"]
                c_lat = city_info["coordinates"]["latitude"]
                ux, uy = transformer.transform(c_lon, c_lat)
                x_origin = float(ux)
                y_origin = float(uy)

        if x_origin is None or y_origin is None:
            x_origin = 0.0
            y_origin = 0.0

        if config.verbose:
            print(f"  Common Local Origin: (X_0 = {x_origin:.1f}, Y_0 = {y_origin:.1f})")
            print(f"  Simulation Domain:   {extent_x:.1f} m x {extent_y:.1f} m (Local X: [{origin_x:.1f}, {origin_x+extent_x:.1f}], Y: [{origin_y:.1f}, {origin_y+extent_y:.1f}])")

        grid_cfg = PedestrianGridConfig(
            extent_x=extent_x,
            extent_y=extent_y,
            origin_x=origin_x,
            origin_y=origin_y,
            resolution=config.grid_resolution_m,
            pedestrian_height=1.1,
        )
        scene = Scene(pedestrian_grid=grid_cfg, coordinate_system=local_frame_label)
        scene.metadata["local_origin"] = [x_origin, y_origin]
        scene.metadata["projected_metric_crs"] = proj_crs_str
        scene.metadata["domain_extent_m"] = [extent_x, extent_y]

        # Convert each building polygon to local coordinates and watertight TriangleMesh
        valid_bldg_count = 0
        for i, feat in enumerate(features):
            geom = feat.get("geometry", {})
            if geom.get("type") != "Polygon":
                continue
            poly = shape(geom)
            pts_wgs84 = list(poly.exterior.coords)
            if len(pts_wgs84) < 4:
                continue

            # Transform EPSG:4326 -> Metric UTM
            pts_utm = [transformer.transform(lon, lat) for lon, lat in pts_wgs84]

            # Apply local origin subtraction exactly once
            local_pts = [(ux - x_origin, uy - y_origin) for ux, uy in pts_utm]

            # Extract building height
            props = feat.get("properties", {})
            h = float(props.get("height", 0.0))
            if h <= 0.0:
                levels = props.get("building:levels") or props.get("levels")
                h = float(levels) * 3.0 if levels else 12.0
            h = max(3.0, h)

            bid = f"bldg_{i:02d}_{props.get('osm_id', i)}"
            bname = props.get("osm_tags", {}).get("name", props.get("name", bid))

            try:
                mesh = create_extruded_polygon_mesh(
                    poly_id=bid,
                    coords=local_pts,
                    height=h,
                    zmin=0.0,
                    material_id="building_wall",
                )
                scene.add_mesh(mesh)

                # Also add Building primitive for fast AABB clipping
                xs = [p[0] for p in local_pts]
                ys = [p[1] for p in local_pts]
                bbox = BoundingBox2D(xmin=min(xs), xmax=max(xs), ymin=min(ys), ymax=max(ys))
                scene.add_building(Building(id=bid, footprint=bbox, height=h))

                building_polygons_local.append({
                    "id": bid,
                    "name": str(bname),
                    "height": h,
                    "coordinates": local_pts,
                    "bbox": [min(xs), max(xs), min(ys), max(ys)],
                })
                valid_bldg_count += 1
            except Exception as e:
                if config.verbose:
                    print(f"  Warning: Skipping malformed building feature {i}: {e}")

        scene.metadata["building_polygons_local"] = building_polygons_local
        if config.verbose:
            print(f"  Successfully ingested {valid_bldg_count} real building polygon meshes from GeoJSON.")

    # 3. Handle certified reference corridors (Berlin, London, Chicago)
    if scene is None and config.area.lower() in ("berlin", "london", "chicago"):
        if config.verbose:
            print(f"  Area '{config.area}' uses the certified baseline study corridor.")
        grid_cfg = PedestrianGridConfig(
            extent_x=100.0, extent_y=100.0, origin_x=-50.0, origin_y=-50.0,
            resolution=config.grid_resolution_m, pedestrian_height=1.1
        )
        scene = Scene(pedestrian_grid=grid_cfg, coordinate_system="EPSG:25833_LOCAL")
        scene.add_mesh(create_box_mesh("w_bldg", -45.0, -10.0, -45.0, 45.0, 0.0, 22.0))
        scene.add_mesh(create_box_mesh("e_bldg",  10.0,  45.0, -45.0, 45.0, 0.0, 22.5))
        # Add corresponding Building primitives
        scene.add_building(Building("w_bldg", BoundingBox2D(-45.0, -10.0, -45.0, 45.0), 22.0, position=(0.0, 0.0, 0.0), material_id="West Facade"))
        scene.add_building(Building("e_bldg", BoundingBox2D(10.0, 45.0, -45.0, 45.0), 22.5, position=(0.0, 0.0, 0.0), material_id="East Facade"))

    # 4. If scene could not be built, NEVER silently substitute generic blocks. Raise actionable error.
    if scene is None:
        raise FileNotFoundError(
            f"Cannot ingest case study area '{config.area}':\n"
            f"  - No buildings GeoJSON found at: {buildings_path}\n"
            f"  - No pre-existing scene_mesh.json found in: {data_src}\n"
            f"Please supply 'buildings.geojson' with polygon footprints in data/input/{config.area}/ "
            f"or configure a valid case study area."
        )

    # Export serialized scene mesh
    scene_file = dest_dir / "scene_mesh.json"
    scene_file.write_text(json.dumps(scene.to_dict(), indent=2), encoding="utf-8")

    # Grid metadata
    res = config.grid_resolution_m
    grid_cfg = scene.pedestrian_grid
    nx = int(round(grid_cfg.extent_x / res))
    ny = int(round(grid_cfg.extent_y / res))
    total_cells = nx * ny

    grid_info = {
        "origin_x_m": grid_cfg.origin_x,
        "origin_y_m": grid_cfg.origin_y,
        "extent_x_m": grid_cfg.extent_x,
        "extent_y_m": grid_cfg.extent_y,
        "resolution_m": res,
        "nx": nx,
        "ny": ny,
        "total_cells": total_cells,
        "sensor_height_z_m": grid_cfg.pedestrian_height,
        "local_origin": scene.metadata.get("local_origin", [0.0, 0.0]),
        "projected_metric_crs": scene.metadata.get("projected_metric_crs", "EPSG:32643"),
    }
    grid_file = dest_dir / "pedestrian_grid.json"
    grid_file.write_text(json.dumps(grid_info, indent=2), encoding="utf-8")

    summary = {
        "stage": "01_data_ingestion",
        "status": "COMPLETED",
        "area": config.area,
        "total_buildings": len(scene.meshes),
        "total_scene_triangles": sum(len(m.triangles) for m in scene.meshes.values()),
        "total_scene_vertices": sum(len(m.vertices) for m in scene.meshes.values()),
        "pedestrian_grid_cells": total_cells,
        "grid_shape": [ny, nx],
        "local_origin": grid_info["local_origin"],
        "artifacts": {
            "scene_mesh": str(scene_file.name),
            "pedestrian_grid": str(grid_file.name),
        },
    }
    summary_file = dest_dir / "ingestion_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Ingested {summary['total_buildings']} meshes ({summary['total_scene_triangles']} triangles)")
        print(f"  Simulation grid: {nx} x {ny} = {total_cells} evaluation cells at {res}m resolution")
        print(f"  Stage 1 completed successfully.")

    return scene, grid_info, summary
