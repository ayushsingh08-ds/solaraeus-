"""
Unit tests for Bengaluru Church Street geospatial preprocessing and mesh generation.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import Polygon

from urban_comfort.geometry.mesh import TriangleMesh
from urban_comfort.geometry.scene import Scene
from urban_comfort.preprocessing.church_street_adapter import (
    ChurchStreetAdapter,
    PreprocessingConfig,
    PreprocessedSceneResult,
)


@pytest.fixture
def adapter() -> ChurchStreetAdapter:
    return ChurchStreetAdapter()


def test_church_street_config_and_adapter_init(adapter: ChurchStreetAdapter):
    assert adapter.config.source_crs == "EPSG:4326"
    assert adapter.config.metric_crs == "EPSG:32643"
    assert adapter.config.commercial_canyon_fallback_m == 9.6
    assert abs(adapter.config.grid_convergence_deg - 0.585366) < 1e-5
    assert adapter.wall_material.id == "building_wall"
    assert adapter.roof_material.id == "building_roof"


def test_church_street_coordinate_transformation(adapter: ChurchStreetAdapter):
    # Main boundary southwest corner (77.6044, 12.9743) should map to local origin (0.0, 0.0)
    lx, ly = adapter.to_local_xy(77.6044, 12.9743)
    assert abs(lx - 0.0) < 0.05
    assert abs(ly - 0.0) < 0.05


def test_church_street_height_loaders(adapter: ChurchStreetAdapter):
    core_heights = adapter.load_core_heights()
    assert len(core_heights) == 37

    # Check approved vs uncertain count in core
    approved_cnt = sum(1 for h in core_heights.values() if h["status"] == "APPROVED")
    uncertain_cnt = sum(1 for h in core_heights.values() if h["status"] == "UNCERTAIN")
    assert approved_cnt == 30
    assert uncertain_cnt == 7

    context_heights = adapter.load_context_heights()
    assert len(context_heights) == 123


def test_church_street_triangulate_and_extrude_synthetic(adapter: ChurchStreetAdapter):
    # Create simple 10m x 20m rectangular polygon
    rect_poly = Polygon([(0.0, 0.0), (10.0, 0.0), (10.0, 20.0), (0.0, 20.0)])
    h = 12.5

    mesh = adapter.triangulate_and_extrude(
        polygon=rect_poly,
        height=h,
        mesh_id="test_building_01",
        material_id="building_wall",
        metadata={"building_id": "test_01"},
    )

    assert isinstance(mesh, TriangleMesh)
    assert mesh.id == "test_building_01"
    assert mesh.num_vertices == 8  # 4 base + 4 roof
    assert mesh.num_triangles == 12  # 8 wall + 2 roof + 2 floor
    assert abs(mesh.xmin - 0.0) < 1e-6
    assert abs(mesh.xmax - 10.0) < 1e-6
    assert abs(mesh.ymin - 0.0) < 1e-6
    assert abs(mesh.ymax - 20.0) < 1e-6
    assert abs(mesh.zmin - 0.0) < 1e-6
    assert abs(mesh.zmax - h) < 1e-6

    # Watertightness check
    from collections import defaultdict
    edge_counts = defaultdict(int)
    for tri in mesh.triangles:
        for i in range(3):
            e = tuple(sorted((int(tri[i]), int(tri[(i + 1) % 3]))))
            edge_counts[e] += 1
    assert all(c == 2 for c in edge_counts.values())

    # Area conservation
    nv = mesh.metadata["footprint_vertices"]
    roof_areas = mesh.face_areas[2 * nv : 2 * nv + (nv - 2)]
    assert abs(float(roof_areas.sum()) - 200.0) < 1e-6


def test_church_street_process_pipeline(adapter: ChurchStreetAdapter):
    result = adapter.process()

    assert isinstance(result, PreprocessedSceneResult)
    assert len(result.core_meshes) == 37
    assert len(result.context_meshes) == 123
    assert len(result.mesh_statistics) == 123
    assert len(result.rejected_or_failed_features) == 0

    # Every core mesh must be present in context meshes
    for m_id in result.core_meshes:
        assert m_id in result.context_meshes

    # Verify all meshes in context are watertight and non-degenerate
    for m in result.context_meshes.values():
        nv = m.metadata["footprint_vertices"]
        poly_area = m.metadata["polygon_area_m2"]

        # Roof area conservation
        roof_areas = m.face_areas[2 * nv : 2 * nv + (nv - 2)]
        assert abs(float(roof_areas.sum()) - poly_area) < 1e-4

        # Non-degeneracy
        assert np.all(m.face_areas > 1e-12)

        # Normals orientation
        normals = m.face_normals
        assert np.all(np.abs(normals[: 2 * nv, 2]) < 1e-6)  # Walls horizontal
        assert np.all(normals[2 * nv : 2 * nv + (nv - 2), 2] > 0.999)  # Roof +Z
        assert np.all(normals[2 * nv + (nv - 2) :, 2] < -0.999)  # Floor -Z

    # Verify scene metadata and constraints
    assert result.main_scene.coordinate_system == "EPSG:32643_LOCAL"
    assert result.main_scene.ground.z_elevation == 0.0
    assert result.main_scene.metadata["simulation_status"] == "preprocessing_only"
    assert result.main_scene.metadata["building_count"] == 37

    assert result.shadow_context_scene.coordinate_system == "EPSG:32643_LOCAL"
    assert result.shadow_context_scene.metadata["building_count"] == 123

    # Exact grid mathematics verification (no rounding discrepancies)
    main_grid = result.main_scene.pedestrian_grid
    assert main_grid.nx == 230
    assert main_grid.ny == 145
    assert main_grid.total_cells == 33350
    assert (main_grid.extent_x * main_grid.extent_y) / (main_grid.resolution**2) == 33350

    ctx_grid = result.shadow_context_scene.pedestrian_grid
    assert ctx_grid.extent_x == 380.0
    assert ctx_grid.extent_y == 296.0
    assert ctx_grid.resolution == 2.0
    assert ctx_grid.nx == 190
    assert ctx_grid.ny == 148
    assert ctx_grid.total_cells == 28120
    assert (ctx_grid.extent_x * ctx_grid.extent_y) / (ctx_grid.resolution**2) == 28120

    # Height taxonomy verification: Decision Status vs Uncertainty Tiers
    h_sum = result.height_policy_summary
    assert h_sum["decision_status_classification"]["total_approved_or_accepted"] == 107
    assert h_sum["decision_status_classification"]["total_uncertain_status"] == 16
    assert h_sum["decision_status_classification"]["rejected_count"] == 0

    assert h_sum["uncertainty_tier_classification"]["moderate_uncertainty_count"] == 83
    assert h_sum["uncertainty_tier_classification"]["high_uncertainty_count"] == 29
    assert h_sum["uncertainty_tier_classification"]["extreme_uncertainty_count"] == 11
    assert h_sum["uncertainty_tier_classification"]["high_or_extreme_sensitivity_cohort"] == 40
    assert (
        h_sum["uncertainty_tier_classification"]["high_uncertainty_count"]
        + h_sum["uncertainty_tier_classification"]["extreme_uncertainty_count"]
        == 40
    )


def test_church_street_scene_serialization(adapter: ChurchStreetAdapter):
    result = adapter.process()
    main_dict = result.main_scene.to_dict()

    json_str = json.dumps(main_dict)
    reloaded_dict = json.loads(json_str)

    assert reloaded_dict["coordinate_system"] == "EPSG:32643_LOCAL"
    assert len(reloaded_dict["meshes"]) == 37
    assert reloaded_dict["metadata"]["simulation_status"] == "preprocessing_only"
