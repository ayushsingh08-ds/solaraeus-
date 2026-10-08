"""
Simulation Backend Abstraction and Scene Geometry Flattening for SOLARAEUS.

Provides abstract backend interfaces and contiguous array flattening for CPU and GPU
execution pipelines.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from urban_comfort.geometry.scene import Scene
from urban_comfort.geometry.mesh import TriangleMesh, create_box_mesh
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import SolarPosition
from urban_comfort.config import Weather, SimulationConfig


@dataclass
class FlattenedSceneGeometry:
    """
    Contiguous array representation of 3D scene geometry suitable for GPU buffers.
    
    Attributes:
        vertices: (N_v, 3) float64 array of 3D vertex positions in local coordinates.
        triangles: (N_t, 3) int32 array of vertex indices (0-based) for each triangle.
        triangle_object_ids: (N_t,) int32 index mapping each triangle to object_names.
        triangle_material_ids: (N_t,) int32 index mapping each triangle to material_names.
        object_names: List of string identifiers for objects in scene.
        material_names: List of string identifiers for materials.
        bldg_boxes: (N_b, 6) float64 array of building bounding boxes (xmin, xmax, ymin, ymax, zmin, zmax).
        bldg_ids: List of string identifiers for AABB buildings.
        bldg_material_ids: (N_b,) int32 index mapping each building to material_names.
        bounds_3d: Overall bounding box (xmin, xmax, ymin, ymax, zmin, zmax) across all objects.
    """
    vertices: np.ndarray
    triangles: np.ndarray
    triangle_object_ids: np.ndarray
    triangle_material_ids: np.ndarray
    object_names: List[str]
    material_names: List[str]
    bldg_boxes: np.ndarray
    bldg_ids: List[str]
    bldg_material_ids: np.ndarray
    bounds_3d: Tuple[float, float, float, float, float, float]

    @property
    def num_vertices(self) -> int:
        return len(self.vertices)

    @property
    def num_triangles(self) -> int:
        return len(self.triangles)

    @property
    def num_buildings(self) -> int:
        return len(self.bldg_boxes)

    @classmethod
    def from_scene(cls, scene: Scene,
                   convert_buildings_to_triangles: bool = False) -> FlattenedSceneGeometry:
        """
        Extracts and flattens all active geometry from a Scene into contiguous arrays.
        
        Parameters:
            scene: Scene instance containing meshes and/or buildings.
            convert_buildings_to_triangles: If True, converts AABB buildings into 12-triangle
                                           meshes in addition to or instead of bldg_boxes.
        """
        active_meshes = scene.get_active_meshes()
        active_buildings = scene.get_active_buildings()

        # Material lookup
        material_names: List[str] = list(scene.materials.keys()) if hasattr(scene, "materials") and scene.materials else ["default_wall", "default_ground"]
        mat_to_idx = {name: i for i, name in enumerate(material_names)}

        object_names: List[str] = []
        obj_to_idx: Dict[str, int] = {}

        verts_list: List[np.ndarray] = []
        tris_list: List[np.ndarray] = []
        tri_obj_list: List[np.ndarray] = []
        tri_mat_list: List[np.ndarray] = []

        v_offset = 0

        # 1. Process active triangular meshes
        for mesh in active_meshes:
            if not mesh.enabled or mesh.num_triangles == 0:
                continue
            obj_idx = len(object_names)
            object_names.append(mesh.id)
            obj_to_idx[mesh.id] = obj_idx

            mat_idx = mat_to_idx.setdefault(mesh.material_id, len(material_names))
            if mesh.material_id not in material_names:
                material_names.append(mesh.material_id)

            n_v = len(mesh.vertices)
            n_t = len(mesh.triangles)

            verts_list.append(mesh.vertices.astype(np.float64))
            tris_list.append((mesh.triangles + v_offset).astype(np.int32))
            tri_obj_list.append(np.full(n_t, obj_idx, dtype=np.int32))
            tri_mat_list.append(np.full(n_t, mat_idx, dtype=np.int32))

            v_offset += n_v

        # 2. Process active AABB buildings
        bldg_boxes_list: List[Tuple[float, float, float, float, float, float]] = []
        bldg_ids: List[str] = []
        bldg_mat_list: List[int] = []

        for bldg in active_buildings:
            if not bldg.enabled:
                continue
            bldg_ids.append(bldg.id)
            bldg_boxes_list.append(bldg.bounds_3d)

            mat_idx = mat_to_idx.setdefault(bldg.material_id, len(material_names))
            if bldg.material_id not in material_names:
                material_names.append(bldg.material_id)
            bldg_mat_list.append(mat_idx)

            if convert_buildings_to_triangles:
                box_mesh = create_box_mesh(
                    bldg.id,
                    bldg.xmin, bldg.xmax, bldg.ymin, bldg.ymax, bldg.zmin, bldg.zmax,
                    material_id=bldg.material_id
                )
                obj_idx = len(object_names)
                object_names.append(bldg.id)
                obj_to_idx[bldg.id] = obj_idx

                n_v = len(box_mesh.vertices)
                n_t = len(box_mesh.triangles)

                verts_list.append(box_mesh.vertices.astype(np.float64))
                tris_list.append((box_mesh.triangles + v_offset).astype(np.int32))
                tri_obj_list.append(np.full(n_t, obj_idx, dtype=np.int32))
                tri_mat_list.append(np.full(n_t, mat_idx, dtype=np.int32))

                v_offset += n_v

        # Assemble contiguous arrays
        if verts_list:
            all_verts = np.vstack(verts_list)
            all_tris = np.vstack(tris_list)
            all_tri_objs = np.concatenate(tri_obj_list)
            all_tri_mats = np.concatenate(tri_mat_list)
        else:
            all_verts = np.zeros((0, 3), dtype=np.float64)
            all_tris = np.zeros((0, 3), dtype=np.int32)
            all_tri_objs = np.zeros((0,), dtype=np.int32)
            all_tri_mats = np.zeros((0,), dtype=np.int32)

        if bldg_boxes_list:
            all_bldg_boxes = np.array(bldg_boxes_list, dtype=np.float64)
            all_bldg_mats = np.array(bldg_mat_list, dtype=np.int32)
        else:
            all_bldg_boxes = np.zeros((0, 6), dtype=np.float64)
            all_bldg_mats = np.zeros((0,), dtype=np.int32)

        # Compute scene bounding box
        if len(all_verts) > 0 and len(all_bldg_boxes) > 0:
            xmin = min(float(np.min(all_verts[:, 0])), float(np.min(all_bldg_boxes[:, 0])))
            xmax = max(float(np.max(all_verts[:, 0])), float(np.max(all_bldg_boxes[:, 1])))
            ymin = min(float(np.min(all_verts[:, 1])), float(np.min(all_bldg_boxes[:, 2])))
            ymax = max(float(np.max(all_verts[:, 1])), float(np.max(all_bldg_boxes[:, 3])))
            zmin = min(float(np.min(all_verts[:, 2])), float(np.min(all_bldg_boxes[:, 4])))
            zmax = max(float(np.max(all_verts[:, 2])), float(np.max(all_bldg_boxes[:, 5])))
        elif len(all_verts) > 0:
            xmin = float(np.min(all_verts[:, 0]))
            xmax = float(np.max(all_verts[:, 0]))
            ymin = float(np.min(all_verts[:, 1]))
            ymax = float(np.max(all_verts[:, 1]))
            zmin = float(np.min(all_verts[:, 2]))
            zmax = float(np.max(all_verts[:, 2]))
        elif len(all_bldg_boxes) > 0:
            xmin = float(np.min(all_bldg_boxes[:, 0]))
            xmax = float(np.max(all_bldg_boxes[:, 1]))
            ymin = float(np.min(all_bldg_boxes[:, 2]))
            ymax = float(np.max(all_bldg_boxes[:, 3]))
            zmin = float(np.min(all_bldg_boxes[:, 4]))
            zmax = float(np.max(all_bldg_boxes[:, 5]))
        else:
            xmin, xmax, ymin, ymax, zmin, zmax = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        return cls(
            vertices=all_verts,
            triangles=all_tris,
            triangle_object_ids=all_tri_objs,
            triangle_material_ids=all_tri_mats,
            object_names=object_names,
            material_names=material_names,
            bldg_boxes=all_bldg_boxes,
            bldg_ids=bldg_ids,
            bldg_material_ids=all_bldg_mats,
            bounds_3d=(xmin, xmax, ymin, ymax, zmin, zmax)
        )


@dataclass
class BackendProfileMetrics:
    """Runtime and memory metrics for simulation backend execution."""
    backend_name: str
    scene_upload_time_s: float = 0.0
    kernel_runtime_s: float = 0.0
    transfer_to_host_time_s: float = 0.0
    total_runtime_s: float = 0.0
    shadow_runtime_s: float = 0.0
    svf_runtime_s: float = 0.0
    radiation_runtime_s: float = 0.0
    utci_runtime_s: float = 0.0
    peak_gpu_memory_bytes: int = 0
    shadow_ray_count: int = 0
    svf_ray_count: int = 0
    total_ray_count: int = 0
    num_triangles: int = 0
    num_buildings: int = 0
    device_name: str = "CPU"


class SimulationBackend(ABC):
    """Abstract base class for urban microclimate simulation backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of backend ('cpu' or 'gpu')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the backend is functional in the current environment."""
        pass

    @abstractmethod
    def compute_direct_shadow(self, scene: Scene,
                              grid: PedestrianGrid,
                              solar_pos: SolarPosition,
                              roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Computes 2D binary direct shadow mask (1.0 = lit, 0.0 = shadow)."""
        pass

    @abstractmethod
    def compute_sky_view_factor(self, scene: Scene,
                                grid: PedestrianGrid,
                                num_azimuths: int = 32,
                                max_search_dist_m: float = 120.0,
                                roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Computes 2D Sky View Factor in [0.0, 1.0]."""
        pass

    @abstractmethod
    def full_simulate(self, scene: Scene,
                      weather: Weather,
                      config: SimulationConfig) -> Any:
        """Executes full microclimate simulation across all physical fields."""
        pass
