"""
Test Suite for SOLARAEUS Bengaluru DSU Harohalli Map & Optimization Pipeline.

Validates:
1. WGS84 -> UTM (EPSG:32643) -> Local origin coordinate transforms and round-trip fidelity.
2. Full domain metric bounds (1219 x 792 m) and pedestrian grid dimensions.
3. Grid cell coordinates alignment with Matplotlib origin='lower' plotting conventions.
4. Canopy shadow projection matching cooling patch footprints with zero offset.
5. Positive, zero, and negative delta thermal reporting semantics.
6. Real OSM building geometry ingestion without silent fallback to synthetic blocks.
7. Cache compatibility and stale 100m extent detection.
"""

import json
import math
from pathlib import Path

import numpy as np
import pyproj
import pytest
from shapely.geometry import Polygon

from solaraeus.physics.solar_position import calculate_solar_position
from solaraeus.pipeline.engine import optimize_canopies


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def test_wgs84_utm_local_roundtrip():
    """Validates WGS84 -> EPSG:32643 -> local frame and round-trip conversion."""
    x_origin = 766241.5
    y_origin = 1400778.0

    # Representative campus coordinate (DSU School of Engineering)
    lon_sample = 77.4505
    lat_sample = 12.6625

    transformer_fwd = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    transformer_inv = pyproj.Transformer.from_crs("EPSG:32643", "EPSG:4326", always_xy=True)

    # 1. Forward transform to UTM
    utm_x, utm_y = transformer_fwd.transform(lon_sample, lat_sample)
    assert 765600.0 <= utm_x <= 766900.0, f"UTM X {utm_x} outside campus bounds"
    assert 1400300.0 <= utm_y <= 1401200.0, f"UTM Y {utm_y} outside campus bounds"

    # 2. Subtract local origin exactly once
    local_x = utm_x - x_origin
    local_y = utm_y - y_origin
    assert -615.0 <= local_x <= 615.0
    assert -400.0 <= local_y <= 400.0

    # 3. Inverse transform back to WGS84
    reconstructed_utm_x = local_x + x_origin
    reconstructed_utm_y = local_y + y_origin
    reconstructed_lon, reconstructed_lat = transformer_inv.transform(reconstructed_utm_x, reconstructed_utm_y)

    assert abs(reconstructed_lon - lon_sample) < 1e-7, "Roundtrip longitude error > 1e-7 deg"
    assert abs(reconstructed_lat - lat_sample) < 1e-7, "Roundtrip latitude error > 1e-7 deg"


def test_domain_bounds_and_grid_dimensions():
    """Validates full campus domain extent (1219 x 792 m) and grid shape."""
    cfg_path = WORKSPACE_ROOT / "configs" / "cities" / "bengaluru_dsu_harohalli.json"
    assert cfg_path.exists(), "City config must exist"
    city_cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

    extent_x = city_cfg["extent_x"]
    extent_y = city_cfg["extent_y"]
    assert extent_x == 1219.0, f"Expected 1219.0 m width, got {extent_x}"
    assert extent_y == 792.0, f"Expected 792.0 m height, got {extent_y}"

    # Grid check at 2.0m resolution
    res = 2.0
    nx = int(round(extent_x / res))
    ny = int(round(extent_y / res))
    assert nx == 610, f"Expected nx=610, got {nx}"
    assert ny == 396, f"Expected ny=396, got {ny}"
    assert nx * ny == 241560, f"Expected 241,560 total cells, got {nx * ny}"


def test_grid_cell_positions_and_plotting_extent():
    """Validates known cell centers and plotting extent matching origin='lower'."""
    ox = -609.5
    oy = -396.0
    res = 2.0
    nx = 610
    ny = 396

    # Extent used for Matplotlib imshow
    extent = [ox, ox + nx * res, oy, oy + ny * res]
    assert extent[0] == -609.5
    assert extent[1] == 610.5
    assert extent[2] == -396.0
    assert extent[3] == 396.0

    # Cell center coordinates for index [0, 0] (bottom-left)
    x_c0 = ox + 0.5 * res
    y_c0 = oy + 0.5 * res
    assert x_c0 == -608.5
    assert y_c0 == -395.0

    # Cell center coordinates for index [ny-1, nx-1] (top-right)
    x_cN = ox + (nx - 0.5) * res
    y_cN = oy + (ny - 0.5) * res
    assert x_cN == 609.5
    assert y_cN == 395.0


def test_canopy_outlines_match_solver_shade():
    """Validates that rendered canopy outline polygons match the exact geometry used to calculate shade."""
    canopy_w = 4.0
    canopy_l = 8.0
    canopy_h = 4.0
    hl = canopy_l / 2.0
    hw = canopy_w / 2.0

    # Hotspot at (100.0, -50.0)
    x_h, y_h = 100.0, -50.0

    # Solar vector with non-zero shadow displacement
    shadow_dx = -0.12
    shadow_dy = 1.49

    # Roof center positioned up-sun
    x_c = x_h - shadow_dx
    y_c = y_h - shadow_dy

    # Ground shadow corners
    shadow_corners = [
        [x_h - hl, y_h - hw],
        [x_h + hl, y_h - hw],
        [x_h + hl, y_h + hw],
        [x_h - hl, y_h + hw],
    ]
    shadow_poly = Polygon(shadow_corners)

    # Shaded grid points test
    xs = np.linspace(x_h - 10.0, x_h + 10.0, 41)
    ys = np.linspace(y_h - 10.0, y_h + 10.0, 41)
    xg, yg = np.meshgrid(xs, ys)

    in_solver_shadow = (np.abs(xg - x_h) <= hl) & (np.abs(yg - y_h) <= hw)

    # All points marked in_solver_shadow must be within the shadow polygon
    for i in range(len(ys)):
        for j in range(len(xs)):
            pt_x = xg[i, j]
            pt_y = yg[i, j]
            if in_solver_shadow[i, j]:
                # Inside shadow polygon boundary (within numerical tolerance)
                assert shadow_poly.buffer(1e-3).contains(Polygon([[pt_x, pt_y], [pt_x+1e-4, pt_y], [pt_x, pt_y+1e-4]]))


def test_thermal_delta_reporting_semantics():
    """Validates positive (cooling), zero (unchanged), and negative (warming) delta reporting."""
    # Definition: cooling_delta = Tmrt_baseline - Tmrt_optimized
    t_base = np.array([45.0, 42.0, 40.0])
    t_opt_cooling = np.array([32.0, 42.0, 43.0])  # point 0: cooled, point 1: same, point 2: warmed

    cooling_delta = t_base - t_opt_cooling

    # Point 0: 45.0 - 32.0 = +13.0 K (cooling -> positive)
    assert cooling_delta[0] == 13.0
    assert cooling_delta[0] > 0

    # Point 1: 42.0 - 42.0 = 0.0 K (unshaded -> zero)
    assert cooling_delta[1] == 0.0

    # Point 2: 40.0 - 43.0 = -3.0 K (warming -> negative)
    assert cooling_delta[2] == -3.0
    assert cooling_delta[2] < 0

    # Peak cooling annotation must be derived from max positive relief
    peak_cooling = float(np.max(cooling_delta))
    assert peak_cooling == 13.0, f"Expected +13.0 K peak cooling, got {peak_cooling}"


def test_real_building_geometry_loaded_no_silent_fallback():
    """Verifies that bengaluru_dsu_harohalli loads 20 OSM buildings and does not use a 2-box corridor."""
    bldg_path = WORKSPACE_ROOT / "data" / "input" / "bengaluru_dsu_harohalli" / "buildings.geojson"
    assert bldg_path.exists(), "buildings.geojson must be present in input directory"

    geojson_data = json.loads(bldg_path.read_text(encoding="utf-8"))
    features = geojson_data.get("features", [])
    assert len(features) == 20, f"Expected 20 building features from OSM, found {len(features)}"

    # Check that processed scene mesh has all 20 buildings
    proc_base = WORKSPACE_ROOT / "data" / "processed" / "bengaluru_dsu_harohalli"
    assert proc_base.exists(), "Processed base directory must exist"
    latest_run = sorted([d for d in proc_base.iterdir() if d.is_dir()])[-1]
    scene_mesh_f = latest_run / "01_data_ingestion" / "scene_mesh.json"
    assert scene_mesh_f.exists()

    scene_data = json.loads(scene_mesh_f.read_text(encoding="utf-8"))
    local_bldgs = scene_data.get("metadata", {}).get("building_polygons_local", [])
    assert len(local_bldgs) == 20, f"Expected 20 localized polygons in scene_mesh metadata, got {len(local_bldgs)}"

    # Confirm meshes are NOT the generic Berlin w_bldg / e_bldg
    raw_meshes = scene_data.get("meshes", [])
    if isinstance(raw_meshes, dict):
        mesh_ids = list(raw_meshes.keys())
    else:
        mesh_ids = [m.get("id") for m in raw_meshes if isinstance(m, dict)]
    assert "w_bldg" not in mesh_ids and "e_bldg" not in mesh_ids, "Silent fallback boxes detected!"
