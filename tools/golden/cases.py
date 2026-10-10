"""Golden-master case definitions.

Every case is a deterministic function of fixed inputs: no wall-clock, no RNG
without a seed, no network, no file writes outside the golden output directory.

Each case returns a dict of named NumPy arrays (the *physical fields*) and a dict
of scalar metrics. `capture.py` stores them; `compare.py` checks them.

Comparison contract (from the overhaul brief):
    * field arrays        equal within rtol=1e-9, atol=1e-12
    * certificate counts  exactly equal
    * GPU cases           compared only when a CUDA device exists, else UNVERIFIED-GPU
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

# The package is installed (editable); no sys.path manipulation is needed.
from urban_comfort.config import SimulationConfig, Weather
from urban_comfort.geometry.mesh import (
    create_box_mesh,
    create_pitched_roof_mesh,
)
from urban_comfort.geometry.primitives import BoundingBox2D, Building
from urban_comfort.geometry.scene import (
    PedestrianGridConfig,
    Scene,
    create_canyon_scene,
    create_occlusion_scene,
    create_single_box_scene,
)
from urban_comfort.incremental.certificate import verify_certificate
from urban_comfort.incremental.edits import AddBuildingEdit, ChangeHeightEdit, RemoveBuildingEdit
from urban_comfort.incremental.mesh_update import AddMeshEdit
from urban_comfort.incremental.update import incremental_update_certified, incremental_update_exact
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.terrain.dtm import TerrainGrid
from urban_comfort.terrain.terrain_scene import TerrainAwareScene
from urban_comfort.vegetation.tree import get_core_trees
from urban_comfort.vegetation.tree_scene import TreeAwareScene
from urban_comfort.vegetation.tree_solver import TreeAwareCPUSolver

# ---------------------------------------------------------------------------
# Fixed, small, fast settings.  These are deliberately tiny so the whole golden
# suite runs in well under a minute, while still exercising every code path.
# ---------------------------------------------------------------------------
GOLDEN_WEATHER = Weather(
    air_temperature=301.15,
    relative_humidity=50.0,
    wind_speed=2.0,
    wind_direction=180.0,
    direct_normal_irradiance=800.0,
    diffuse_horizontal_irradiance=160.0,
)

GOLDEN_CONFIG = SimulationConfig(
    latitude=40.7128,
    longitude=-74.0060,
    date="2024-07-15",
    local_time="12:00:00",
    grid_resolution=1.0,
    sky_patch_configuration=16,
    max_svf_search_dist_m=30.0,
    tmrt_tolerance=0.5,
)

EPS_TOLERANCE_K = 0.5


@dataclass
class GoldenCase:
    """One captureable behaviour of the engine."""

    name: str
    area: str
    fn: Callable[[], tuple[dict[str, np.ndarray], dict[str, Any]]]
    note: str = ""
    requires_gpu: bool = False
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _fields_from_result(result) -> dict[str, np.ndarray]:
    """Extract the canonical field set from a SimulationResult."""
    return {
        "shadow_mask": np.asarray(result.shadow_mask, dtype=np.float64),
        "svf": np.asarray(result.svf, dtype=np.float64),
        "shortwave_flux": np.asarray(result.shortwave_flux, dtype=np.float64),
        "longwave_flux": np.asarray(result.longwave_flux, dtype=np.float64),
        "tmrt": np.asarray(result.tmrt, dtype=np.float64),
        "utci": np.asarray(result.utci, dtype=np.float64),
    }


def _stats(arr: np.ndarray) -> dict[str, float]:
    """Compact deterministic summary of an array."""
    return {
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "sum": float(np.sum(arr)),
    }


def _certificate_metrics(cert, verification=None) -> dict[str, Any]:
    """Counts that must match exactly, plus bound statistics."""
    out: dict[str, Any] = {
        "status": cert.status,
        "tolerance": float(cert.tolerance),
        "total_cells": int(cert.total_cells),
        "reused_cells": int(cert.reused_cells),
        "affected_cells": int(cert.affected_cells),
        "max_predicted_bound": float(cert.max_predicted_bound),
        "bound_stats": _stats(cert.predicted_error_bound),
    }
    if verification is not None:
        out["num_violations"] = int(verification.num_violations)
        out["is_within_tolerance"] = bool(verification.is_within_tolerance)
        out["reused_max_error"] = float(verification.reused_max_error)
    return out


# ---------------------------------------------------------------------------
# Cases: core physics
# ---------------------------------------------------------------------------
def case_single_box_full() -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Full recomputation of the canonical single-box scene (configs/baseline_scene.json equivalent)."""
    scene = create_single_box_scene(extent_m=80.0, box_size=16.0, box_height=18.0)
    result = full_recompute(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)
    return _fields_from_result(result), {
        "grid_cells": int(result.metadata["total_cells"]),
        "solar_altitude_deg": float(result.metadata["solar_altitude_deg"]),
        "solar_azimuth_deg": float(result.metadata["solar_azimuth_deg"]),
        "num_buildings": int(result.metadata["num_buildings"]),
        "tmrt_stats": _stats(result.tmrt),
        "utci_stats": _stats(result.utci),
    }


def case_canyon_full() -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Full recomputation of the two-row urban canyon scene."""
    scene = create_canyon_scene(extent_m=80.0, canyon_width=16.0, building_height=20.0)
    result = full_recompute(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)
    return _fields_from_result(result), {
        "grid_cells": int(result.metadata["total_cells"]),
        "num_buildings": int(result.metadata["num_buildings"]),
        "tmrt_stats": _stats(result.tmrt),
    }


def case_occlusion_full() -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Full recomputation of the occlusion-reveal scene."""
    scene = create_occlusion_scene(extent_m=80.0)
    result = full_recompute(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)
    return _fields_from_result(result), {
        "grid_cells": int(result.metadata["total_cells"]),
        "shadow_ratio": float(np.mean(result.shadow_mask)),
    }


# ---------------------------------------------------------------------------
# Cases: certified incremental over each atomic edit type
# ---------------------------------------------------------------------------
def _incremental_edit_case(edit, tag: str):
    """Shared driver: baseline -> edit -> ground truth -> certified incremental -> verify."""
    scene_before = create_single_box_scene()
    baseline = full_recompute(scene_before, GOLDEN_WEATHER, GOLDEN_CONFIG)

    scene_after, _ = edit.apply(scene_before)
    ground_truth = full_recompute(scene_after, GOLDEN_WEATHER, GOLDEN_CONFIG)

    inc_result, cert = incremental_update_certified(
        scene_before, scene_after, baseline, edit, GOLDEN_WEATHER, GOLDEN_CONFIG
    )
    verification = verify_certificate(cert, inc_result.result.tmrt, ground_truth.tmrt)

    fields = _fields_from_result(inc_result.result)
    # the certificate bound is itself a golden artefact
    fields["certificate_bound"] = np.asarray(cert.predicted_error_bound, dtype=np.float64)
    fields["ground_truth_tmrt"] = np.asarray(ground_truth.tmrt, dtype=np.float64)
    fields["actual_error"] = np.abs(fields["tmrt"] - fields["ground_truth_tmrt"])

    metrics: dict[str, Any] = {"edit": tag}
    metrics.update(_certificate_metrics(cert, verification))
    metrics["incremental_tmrt_stats"] = _stats(fields["tmrt"])
    metrics["ground_truth_tmrt_stats"] = _stats(fields["ground_truth_tmrt"])
    metrics["max_actual_error"] = float(np.max(fields["actual_error"]))
    return fields, metrics


def case_incremental_add_building():
    """Certified incremental update after adding a 14x14x15 m building."""
    edit = AddBuildingEdit(
        Building("bldg_infill", BoundingBox2D(14.0, 28.0, 46.0, 60.0), height=15.0)
    )
    return _incremental_edit_case(edit, "AddBuilding")


def case_incremental_remove_building():
    """Certified incremental update after removing a building."""
    return _incremental_edit_case(RemoveBuildingEdit("bldg_center"), "RemoveBuilding")


def case_incremental_change_height():
    """Certified incremental update after a 8 m height increase."""
    return _incremental_edit_case(ChangeHeightEdit("bldg_center", 26.0), "ChangeHeight")


def case_incremental_exact_add_building():
    """Exact (non-certified) incremental update - must match ground truth to machine precision."""
    edit = AddBuildingEdit(
        Building("bldg_infill", BoundingBox2D(14.0, 28.0, 46.0, 60.0), height=15.0)
    )
    scene_before = create_single_box_scene()
    baseline = full_recompute(scene_before, GOLDEN_WEATHER, GOLDEN_CONFIG)
    scene_after, _ = edit.apply(scene_before)
    ground_truth = full_recompute(scene_after, GOLDEN_WEATHER, GOLDEN_CONFIG)

    inc = incremental_update_exact(
        scene_before, scene_after, baseline, edit, GOLDEN_WEATHER, GOLDEN_CONFIG
    )
    fields = _fields_from_result(inc.result)
    fields["ground_truth_tmrt"] = np.asarray(ground_truth.tmrt, dtype=np.float64)
    return fields, {
        "edit": "AddBuildingExact",
        "max_actual_error_vs_ground_truth": float(
            np.max(np.abs(fields["tmrt"] - fields["ground_truth_tmrt"]))
        ),
    }


# ---------------------------------------------------------------------------
# Cases: mesh geometry path
# ---------------------------------------------------------------------------
def case_mesh_pitched_roof_incremental():
    """Certified incremental update using a triangular-mesh edit (pitched roof)."""
    scene = Scene(
        pedestrian_grid=PedestrianGridConfig(
            extent_x=60.0, extent_y=60.0, resolution=1.0, pedestrian_height=1.1
        )
    )
    scene.add_building(Building("bldg_a", BoundingBox2D(10.0, 26.0, 10.0, 26.0), height=12.0))
    baseline = full_recompute(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)

    roof = create_pitched_roof_mesh(
        "roof_new", 30.0, 46.0, 30.0, 46.0, eave_height=10.0, ridge_height=16.0
    )
    edit = AddMeshEdit(roof)
    scene_after, _ = edit.apply(scene)
    ground_truth = full_recompute(scene_after, GOLDEN_WEATHER, GOLDEN_CONFIG)

    inc, cert = incremental_update_certified(
        scene, scene_after, baseline, edit, GOLDEN_WEATHER, GOLDEN_CONFIG
    )
    verification = verify_certificate(cert, inc.result.tmrt, ground_truth.tmrt)
    fields = _fields_from_result(inc.result)
    fields["certificate_bound"] = np.asarray(cert.predicted_error_bound, dtype=np.float64)
    metrics = {"edit": "AddMeshPitchedRoof"}
    metrics.update(_certificate_metrics(cert, verification))
    metrics["max_actual_error"] = float(np.max(np.abs(fields["tmrt"] - ground_truth.tmrt)))
    return fields, metrics


def case_box_mesh_geometry():
    """Pure geometry invariants of the 12-triangle box mesh constructor."""
    mesh = create_box_mesh("box", 0.0, 4.0, 0.0, 6.0, 0.0, 8.0)
    return {
        "vertices": np.asarray(mesh.vertices, dtype=np.float64),
        "triangles": np.asarray(mesh.triangles, dtype=np.float64),
        "face_normals": np.asarray(mesh.face_normals, dtype=np.float64),
        "face_areas": np.asarray(mesh.face_areas, dtype=np.float64),
    }, {
        "num_vertices": int(mesh.num_vertices),
        "num_triangles": int(mesh.num_triangles),
        "bounds_3d": [float(v) for v in mesh.bounds_3d],
        "total_surface_area": float(mesh.total_surface_area),
    }


# ---------------------------------------------------------------------------
# Cases: extension areas (terrain, vegetation)
# ---------------------------------------------------------------------------
def case_terrain_flat_parity():
    """Terrain solver on a FLAT terrain must equal the flat-ground reference bit-for-bit."""
    base = create_single_box_scene()
    flat = TerrainGrid.create_flat(
        BoundingBox2D(0.0, 80.0, 0.0, 80.0), elevation_val=0.0, nx=80, ny=80
    )
    terr_scene = TerrainAwareScene(base_scene=base, terrain=flat)
    terr_result = TreeAwareCPUSolver.simulate(
        TreeAwareScene.from_base_scene(base, terrain=flat, trees=[]),
        GOLDEN_WEATHER,
        GOLDEN_CONFIG,
        pedestrian_height_m=1.1,
    )
    flat_result = full_recompute(base, GOLDEN_WEATHER, GOLDEN_CONFIG)
    fields = _fields_from_result(terr_result)
    fields["flat_reference_tmrt"] = np.asarray(flat_result.tmrt, dtype=np.float64)

    # sample_elevation returns (elevation, valid_mask); probe a 5x5 lattice
    probe_x, probe_y = np.meshgrid(np.linspace(0.0, 79.0, 5), np.linspace(0.0, 79.0, 5))
    elevation, valid_mask = flat.sample_elevation(
        probe_x.ravel().astype(np.float64), probe_y.ravel().astype(np.float64)
    )
    fields["flat_probe_elevation"] = np.asarray(elevation, dtype=np.float64)
    fields["flat_probe_valid"] = np.asarray(valid_mask, dtype=np.float64)

    return fields, {
        "max_tmrt_diff_vs_flat_reference": float(
            np.max(np.abs(fields["tmrt"] - fields["flat_reference_tmrt"]))
        ),
        "terrain_has_terrain": bool(terr_scene.has_terrain),
        "flat_probe_elevation_max": float(np.nanmax(elevation)),
        "flat_probe_all_valid": bool(np.all(valid_mask)),
    }


def case_terrain_inclined():
    """Terrain solver on an inclined synthetic slope."""
    base = create_single_box_scene()
    inclined = TerrainGrid.create_inclined(
        BoundingBox2D(0.0, 80.0, 0.0, 80.0), base_elevation=0.0, slope_x=0.03, nx=80, ny=80
    )
    scene = TreeAwareScene.from_base_scene(base, terrain=inclined, trees=[])
    result = TreeAwareCPUSolver.simulate(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)
    fields = _fields_from_result(result)
    fields["surface_normals"] = np.asarray(inclined.compute_surface_normals()[2], dtype=np.float64)
    return fields, {"tmrt_stats": _stats(result.tmrt), "slope_x": 0.03}


def case_vegetation_core_trees():
    """Six core trees (nominal provisional geometry) with the tree-aware CPU solver."""
    base = create_single_box_scene()
    trees = get_core_trees(geometry_state="NOMINAL_PROVISIONAL")
    scene = TreeAwareScene.from_base_scene(base, terrain=None, trees=trees)
    result = TreeAwareCPUSolver.simulate(scene, GOLDEN_WEATHER, GOLDEN_CONFIG)
    bare = TreeAwareCPUSolver.simulate(
        TreeAwareScene.from_base_scene(base, terrain=None, trees=[]),
        GOLDEN_WEATHER,
        GOLDEN_CONFIG,
    )
    fields = _fields_from_result(result)
    fields["bare_tmrt"] = np.asarray(bare.tmrt, dtype=np.float64)
    fields["tree_cooling_k"] = np.asarray(bare.tmrt - result.tmrt, dtype=np.float64)
    return fields, {
        "num_trees": len(trees),
        "tree_ids": [t.tree_id for t in trees],
        "max_cooling_k": float(np.max(bare.tmrt - result.tmrt)),
        "mean_cooling_k": float(np.mean(bare.tmrt - result.tmrt)),
    }


def case_vegetation_tree_states():
    """Geometry invariants of one tree across its three uncertainty states."""
    fields: dict[str, np.ndarray] = {}
    metrics: dict[str, Any] = {}
    for state in ("CONSERVATIVE_SMALL", "NOMINAL_PROVISIONAL", "CONSERVATIVE_LARGE"):
        trees = [t for t in get_core_trees(geometry_state=state) if t.tree_id == "T08"]
        tree = trees[0]
        fields[f"{state}_crown_top"] = np.asarray([tree.crown_top_z], dtype=np.float64)
        fields[f"{state}_crown_base"] = np.asarray([tree.crown_base_z], dtype=np.float64)
        metrics[state] = {
            "height": float(tree.height),
            "crown_radius_x": float(tree.crown_radius_x),
            "crown_radius_y": float(tree.crown_radius_y),
            "trunk_radius": float(tree.trunk_radius),
        }
    return fields, metrics


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
CASES: list[GoldenCase] = [
    GoldenCase(
        "core_single_box_full",
        "core",
        case_single_box_full,
        "canonical 80m scene, full recomputation",
    ),
    GoldenCase("core_canyon_full", "core", case_canyon_full, "urban canyon full recomputation"),
    GoldenCase("core_occlusion_full", "core", case_occlusion_full, "occlusion scene"),
    GoldenCase(
        "incr_add_building",
        "incremental",
        case_incremental_add_building,
        "certified incremental, AddBuildingEdit",
    ),
    GoldenCase(
        "incr_remove_building",
        "incremental",
        case_incremental_remove_building,
        "certified incremental, RemoveBuildingEdit",
    ),
    GoldenCase(
        "incr_change_height",
        "incremental",
        case_incremental_change_height,
        "certified incremental, ChangeHeightEdit",
    ),
    GoldenCase(
        "incr_exact_add_building",
        "incremental",
        case_incremental_exact_add_building,
        "exact incremental, AddBuildingEdit",
    ),
    GoldenCase(
        "mesh_pitched_roof_incremental",
        "mesh",
        case_mesh_pitched_roof_incremental,
        "certified incremental on a triangular mesh edit",
    ),
    GoldenCase("mesh_box_geometry", "mesh", case_box_mesh_geometry, "box mesh invariants"),
    GoldenCase(
        "terrain_flat_parity",
        "terrain",
        case_terrain_flat_parity,
        "flat terrain must match flat-ground reference",
    ),
    GoldenCase("terrain_inclined", "terrain", case_terrain_inclined, "inclined synthetic slope"),
    GoldenCase(
        "vegetation_core_trees",
        "vegetation",
        case_vegetation_core_trees,
        "six core trees, nominal geometry",
    ),
    GoldenCase(
        "vegetation_tree_states",
        "vegetation",
        case_vegetation_tree_states,
        "tree geometry across uncertainty states",
    ),
]


def cases_by_name() -> dict[str, GoldenCase]:
    """Registry keyed by case name."""
    return {c.name: c for c in CASES}
