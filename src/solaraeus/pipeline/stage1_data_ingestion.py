"""
Stage 1: Data Ingestion and Scene Preprocessing Pipeline.

Ingests geospatial vector data (footprints, boundaries), approved building heights,
materials, terrain, and weather forcing to generate watertight 3D triangle meshes
and the pedestrian analysis grid in local Cartesian metric space.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from solaraeus.core.geometry.scene import Scene
from solaraeus.pipeline.config import PipelineConfig
from solaraeus.sites.church_street.scene_builder import (
    ChurchStreetAdapter,
    PreprocessingConfig,
    PreprocessedSceneResult,
)


def run_stage_data_ingestion(config: PipelineConfig) -> Tuple[Scene, Dict[str, Any], Dict[str, Any]]:
    """
    Executes Stage 1: Data Ingestion.

    Args:
        config: Pipeline configuration.

    Returns:
        Tuple of (Scene, grid_dict, summary_dict).
    """
    dest_dir = config.output_dir / "01_data_ingestion"
    dest_dir.mkdir(parents=True, exist_ok=True)

    if config.verbose:
        print(f"\n=========================================================================")
        print(f"[Stage 1: Data Ingestion] Ingesting geospatial layers for area: {config.area}")
        print(f"  Data Source: {config.data_dir}")
        print(f"  Destination: {dest_dir}")
        print(f"=========================================================================")

    prep_config = PreprocessingConfig(handoff_dir=config.data_dir)
    adapter = ChurchStreetAdapter(prep_config)
    result: PreprocessedSceneResult = adapter.process()

    scene_data = result.shadow_context_scene.to_dict()
    scene_file = dest_dir / "scene_mesh.json"
    scene_file.write_text(json.dumps(scene_data, indent=2), encoding="utf-8")

    # Reconcile pedestrian simulation grid
    # Analytical buffer: [-77.12, 292.87] x [-75.76, 210.81] m
    # Discrete grid origin: (-85.0, -80.0) m, extent: 380m x 296m at 2m res -> 190 x 148 = 28,120 cells
    res = config.grid_resolution_m
    origin_x = -85.0
    origin_y = -80.0
    extent_x = 380.0
    extent_y = 296.0
    nx = int(round(extent_x / res))
    ny = int(round(extent_y / res))
    total_cells = nx * ny

    grid_info = {
        "origin_x_m": origin_x,
        "origin_y_m": origin_y,
        "extent_x_m": extent_x,
        "extent_y_m": extent_y,
        "resolution_m": res,
        "nx": nx,
        "ny": ny,
        "total_cells": total_cells,
        "sensor_height_z_m": 1.5,
    }
    grid_file = dest_dir / "pedestrian_grid.json"
    grid_file.write_text(json.dumps(grid_info, indent=2), encoding="utf-8")

    summary = {
        "stage": "01_data_ingestion",
        "status": "COMPLETED",
        "area": config.area,
        "total_buildings": len(result.mesh_statistics),
        "total_core_buildings": len(result.core_meshes),
        "total_context_buildings": len(result.context_meshes),
        "total_scene_triangles": sum(len(m.triangles) for m in result.shadow_context_scene.meshes.values()),
        "total_scene_vertices": sum(len(m.vertices) for m in result.shadow_context_scene.meshes.values()),
        "pedestrian_grid_cells": total_cells,
        "artifacts": {
            "scene_mesh": str(scene_file.name),
            "pedestrian_grid": str(grid_file.name),
        },
    }
    summary_file = dest_dir / "ingestion_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if config.verbose:
        print(f"  Ingested {summary['total_buildings']} buildings ({summary['total_scene_triangles']} triangles)")
        print(f"  Discrete simulation grid: {nx} x {ny} = {total_cells} pedestrian evaluation cells")
        print(f"  Stage 1 completed successfully.")

    return result.shadow_context_scene, grid_info, summary
