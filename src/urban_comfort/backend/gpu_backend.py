"""
GPU Simulation Backend for SOLARAEUS using CUDA and CuPy.

Implements high-throughput GPU ray tracing for direct solar shadows and multi-azimuth
directional visibility / Sky View Factor (SVF) with strict numerical parity to the CPU reference.
"""

from __future__ import annotations
import math
import time
from typing import Optional, Tuple, Dict, Any, List
import numpy as np

from urban_comfort.backend.base import (
    SimulationBackend, FlattenedSceneGeometry, BackendProfileMetrics
)
from urban_comfort.backend.cpu_backend import CPUBackend
from urban_comfort.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from urban_comfort.geometry.scene import Scene
from urban_comfort.grid.pedestrian_grid import PedestrianGrid
from urban_comfort.solar.solar_position import calculate_solar_position, SolarPosition
from urban_comfort.radiation.shortwave import compute_shortwave_fluxes
from urban_comfort.radiation.longwave import compute_longwave_fluxes
from urban_comfort.radiation.tmrt import compute_tmrt
from urban_comfort.comfort.utci import compute_utci
from urban_comfort.reference.full_recompute import SimulationResult


# CUDA C++ Source Code for Ray-Triangle & Horizon Search Kernels
CUDA_KERNELS_SOURCE = r'''
extern "C" {

__global__
void moller_trumbore_shadow_kernel(
    const double* __restrict__ ray_origins,      // (N_rays, 3)
    const double* __restrict__ ray_dir,          // (3,)
    const double* __restrict__ vertices,         // (N_verts, 3)
    const int* __restrict__ triangles,           // (N_tris, 3)
    const double* __restrict__ bldg_boxes,       // (N_bldgs, 6)
    int has_roi,
    const unsigned char* __restrict__ roi_mask,  // (N_rays,)
    int n_rays,
    int n_tris,
    int n_bldgs,
    double eps_origin,
    double eps_det,
    double eps_bary,
    double* __restrict__ out_shadow_mask         // (N_rays,)
) {
    int ray_idx = blockDim.x * blockIdx.x + threadIdx.x;
    if (ray_idx >= n_rays) return;

    // Check ROI mask
    if (has_roi != 0 && roi_mask[ray_idx] == 0) {
        out_shadow_mask[ray_idx] = 1.0;
        return;
    }

    double ox = ray_origins[ray_idx * 3 + 0];
    double oy = ray_origins[ray_idx * 3 + 1];
    double oz = ray_origins[ray_idx * 3 + 2];

    double dx = ray_dir[0];
    double dy = ray_dir[1];
    double dz = ray_dir[2];

    double inv_dx = (fabs(dx) > 1e-14) ? (1.0 / dx) : 1e14;
    double inv_dy = (fabs(dy) > 1e-14) ? (1.0 / dy) : 1e14;
    double inv_dz = (fabs(dz) > 1e-14) ? (1.0 / dz) : 1e14;

    // 1. Test AABB buildings
    for (int b = 0; b < n_bldgs; ++b) {
        double xmin = bldg_boxes[b * 6 + 0];
        double xmax = bldg_boxes[b * 6 + 1];
        double ymin = bldg_boxes[b * 6 + 2];
        double ymax = bldg_boxes[b * 6 + 3];
        double zmin = bldg_boxes[b * 6 + 4];
        double zmax = bldg_boxes[b * 6 + 5];

        // Inside building footprint check
        if (ox >= xmin && ox <= xmax && oy >= ymin && oy <= ymax && oz <= zmax) {
            out_shadow_mask[ray_idx] = 0.0;
            return;
        }

        // Ray-AABB Kay-Kajiya slab test
        double t1 = (xmin - ox) * inv_dx;
        double t2 = (xmax - ox) * inv_dx;
        double t3 = (ymin - oy) * inv_dy;
        double t4 = (ymax - oy) * inv_dy;
        double t5 = (zmin - oz) * inv_dz;
        double t6 = (zmax - oz) * inv_dz;

        double tmin = fmax(fmax(fmin(t1, t2), fmin(t3, t4)), fmin(t5, t6));
        double tmax = fmin(fmin(fmax(t1, t2), fmax(t3, t4)), fmax(t5, t6));

        if (tmax >= tmin && tmax >= eps_origin) {
            out_shadow_mask[ray_idx] = 0.0;
            return;
        }
    }

    // 2. Test triangular meshes
    for (int t = 0; t < n_tris; ++t) {
        int i0 = triangles[t * 3 + 0];
        int i1 = triangles[t * 3 + 1];
        int i2 = triangles[t * 3 + 2];

        double v0x = vertices[i0 * 3 + 0];
        double v0y = vertices[i0 * 3 + 1];
        double v0z = vertices[i0 * 3 + 2];

        double v1x = vertices[i1 * 3 + 0];
        double v1y = vertices[i1 * 3 + 1];
        double v1z = vertices[i1 * 3 + 2];

        double v2x = vertices[i2 * 3 + 0];
        double v2y = vertices[i2 * 3 + 1];
        double v2z = vertices[i2 * 3 + 2];

        double e1x = v1x - v0x;
        double e1y = v1y - v0y;
        double e1z = v1z - v0z;

        double e2x = v2x - v0x;
        double e2y = v2y - v0y;
        double e2z = v2z - v0z;

        double px = dy * e2z - dz * e2y;
        double py = dz * e2x - dx * e2z;
        double pz = dx * e2y - dy * e2x;

        double det = e1x * px + e1y * py + e1z * pz;

        if (fabs(det) < eps_det) continue;

        double inv_det = 1.0 / det;

        double tx = ox - v0x;
        double ty = oy - v0y;
        double tz = oz - v0z;

        double u = (tx * px + ty * py + tz * pz) * inv_det;
        if (u < -eps_bary || u > (1.0 + eps_bary)) continue;

        double qx = ty * e1z - tz * e1y;
        double qy = tz * e1x - tx * e1z;
        double qz = tx * e1y - ty * e1x;

        double v = (dx * qx + dy * qy + dz * qz) * inv_det;
        if (v < -eps_bary || (u + v) > (1.0 + eps_bary)) continue;

        double dist = (e2x * qx + e2y * qy + e2z * qz) * inv_det;
        if (dist >= eps_origin) {
            out_shadow_mask[ray_idx] = 0.0;
            return;
        }
    }

    out_shadow_mask[ray_idx] = 1.0;
}

__global__
void rasterize_mesh_height_kernel(
    const double* __restrict__ vertices,         // (N_verts, 3)
    const int* __restrict__ triangles,           // (N_tris, 3)
    int n_tris,
    double origin_x,
    double origin_y,
    double dx,
    int nx,
    int ny,
    double z_high,
    double eps_origin,
    double eps_det,
    double eps_bary,
    double* __restrict__ out_height_grid         // (ny, nx)
) {
    int ix = blockDim.x * blockIdx.x + threadIdx.x;
    int iy = blockDim.y * blockIdx.y + threadIdx.y;
    if (ix >= nx || iy >= ny) return;

    double rx = origin_x + (ix + 0.5) * dx;
    double ry = origin_y + (iy + 0.5) * dx;
    double rz = z_high;

    double max_h = 0.0;

    for (int t = 0; t < n_tris; ++t) {
        int i0 = triangles[t * 3 + 0];
        int i1 = triangles[t * 3 + 1];
        int i2 = triangles[t * 3 + 2];

        double v0x = vertices[i0 * 3 + 0];
        double v0y = vertices[i0 * 3 + 1];
        double v0z = vertices[i0 * 3 + 2];

        double v1x = vertices[i1 * 3 + 0];
        double v1y = vertices[i1 * 3 + 1];
        double v1z = vertices[i1 * 3 + 2];

        double v2x = vertices[i2 * 3 + 0];
        double v2y = vertices[i2 * 3 + 1];
        double v2z = vertices[i2 * 3 + 2];

        // 2D bounding box test for triangle
        double min_tx = fmin(v0x, fmin(v1x, v2x));
        double max_tx = fmax(v0x, fmax(v1x, v2x));
        double min_ty = fmin(v0y, fmin(v1y, v2y));
        double max_ty = fmax(v0y, fmax(v1y, v2y));

        if (rx < min_tx - 1e-6 || rx > max_tx + 1e-6 || ry < min_ty - 1e-6 || ry > max_ty + 1e-6) {
            continue;
        }

        double e1x = v1x - v0x;
        double e1y = v1y - v0y;
        double e1z = v1z - v0z;

        double e2x = v2x - v0x;
        double e2y = v2y - v0y;
        double e2z = v2z - v0z;

        // pvec = (0, 0, -1) x e2 = (e2y, -e2x, 0)
        double px = e2y;
        double py = -e2x;

        double det = e1x * px + e1y * py;
        if (fabs(det) < eps_det) continue;

        double inv_det = 1.0 / det;

        double tx = rx - v0x;
        double ty = ry - v0y;
        double tz = rz - v0z;

        double u = (tx * px + ty * py) * inv_det;
        if (u < -eps_bary || u > (1.0 + eps_bary)) continue;

        // qvec = tvec x e1
        double qx = ty * e1z - tz * e1y;
        double qy = tz * e1x - tx * e1z;
        double qz = tx * e1y - ty * e1x;

        // v = (dir . qvec) * inv_det = -qz * inv_det
        double v = -qz * inv_det;
        if (v < -eps_bary || (u + v) > (1.0 + eps_bary)) continue;

        double dist = (e2x * qx + e2y * qy + e2z * qz) * inv_det;
        if (dist >= eps_origin) {
            double h = z_high - dist;
            if (h > max_h) {
                max_h = h;
            }
        }
    }

    out_height_grid[iy * nx + ix] = max_h;
}

__global__
void compute_svf_horizon_kernel(
    const double* __restrict__ height_grid,       // (ny, nx)
    const double* __restrict__ bldg_boxes,        // (n_bldgs, 6)
    int has_roi,
    const unsigned char* __restrict__ roi_mask,   // (ny, nx)
    int n_bldgs,
    double origin_x,
    double origin_y,
    double dx,
    int nx,
    int ny,
    double z_ped,
    int num_azimuths,
    double max_search_dist,
    double step_dx,
    double* __restrict__ out_svf                  // (ny, nx)
) {
    int ix = blockDim.x * blockIdx.x + threadIdx.x;
    int iy = blockDim.y * blockIdx.y + threadIdx.y;
    if (ix >= nx || iy >= ny) return;

    int cell_idx = iy * nx + ix;

    // Check ROI mask
    if (has_roi != 0 && roi_mask[cell_idx] == 0) {
        out_svf[cell_idx] = 1.0;
        return;
    }

    double bx = origin_x + (ix + 0.5) * dx;
    double by = origin_y + (iy + 0.5) * dx;

    // Check if receptor is inside or under building/mesh footprint
    double local_h = height_grid[cell_idx];
    if (local_h > z_ped) {
        out_svf[cell_idx] = 0.0;
        return;
    }

    for (int b = 0; b < n_bldgs; ++b) {
        double xmin = bldg_boxes[b * 6 + 0];
        double xmax = bldg_boxes[b * 6 + 1];
        double ymin = bldg_boxes[b * 6 + 2];
        double ymax = bldg_boxes[b * 6 + 3];
        if (bx >= xmin && bx <= xmax && by >= ymin && by <= ymax) {
            out_svf[cell_idx] = 0.0;
            return;
        }
    }

    int n_steps = (int)(max_search_dist / step_dx + 0.5);
    double extent_x = nx * dx;
    double extent_y = ny * dx;

    double cos2_sum = 0.0;
    const double PI = 3.14159265358979323846;

    for (int a = 0; a < num_azimuths; ++a) {
        double az_deg = (360.0 * a) / (double)num_azimuths;
        double az_rad = az_deg * (PI / 180.0);
        double dir_x = sin(az_rad);
        double dir_y = cos(az_rad);

        double max_tan_elev = 0.0;

        for (int s = 1; s <= n_steps; ++s) {
            double r = s * step_dx;
            if (r > max_search_dist) break;

            double sx = bx + dir_x * r;
            double sy = by + dir_y * r;

            // Height from height_grid
            if (sx >= origin_x && sx <= origin_x + extent_x &&
                sy >= origin_y && sy <= origin_y + extent_y) {
                int six = (int)floor((sx - origin_x) / dx);
                int siy = (int)floor((sy - origin_y) / dx);
                if (six < 0) six = 0;
                if (six >= nx) six = nx - 1;
                if (siy < 0) siy = 0;
                if (siy >= ny) siy = ny - 1;

                double sh = height_grid[siy * nx + six];
                if (sh > z_ped) {
                    double tan_e = (sh - z_ped) / r;
                    if (tan_e > max_tan_elev) {
                        max_tan_elev = tan_e;
                    }
                }
            }

            // Height from bldg_boxes
            for (int b = 0; b < n_bldgs; ++b) {
                double xmin = bldg_boxes[b * 6 + 0];
                double xmax = bldg_boxes[b * 6 + 1];
                double ymin = bldg_boxes[b * 6 + 2];
                double ymax = bldg_boxes[b * 6 + 3];
                double zmax = bldg_boxes[b * 6 + 5];

                if (sx >= xmin && sx <= xmax && sy >= ymin && sy <= ymax) {
                    if (zmax > z_ped) {
                        double tan_e = (zmax - z_ped) / r;
                        if (tan_e > max_tan_elev) {
                            max_tan_elev = tan_e;
                        }
                    }
                }
            }
        }

        cos2_sum += 1.0 / (1.0 + max_tan_elev * max_tan_elev);
    }

    double svf = cos2_sum / (double)num_azimuths;
    if (svf < 0.0) svf = 0.0;
    if (svf > 1.0) svf = 1.0;

    out_svf[cell_idx] = svf;
}

} // extern "C"
'''


def is_cupy_available() -> bool:
    """Checks whether CuPy is installed and can detect a functional CUDA GPU."""
    try:
        import cupy as cp
        return bool(cp.cuda.is_available() and cp.cuda.runtime.getDeviceCount() > 0)
    except Exception:
        return False


class GPUBackend(SimulationBackend):
    """
    High-performance GPU simulation backend implemented in CUDA C++ via CuPy.
    """

    def __init__(self, fallback_to_cpu: bool = False):
        self._fallback_to_cpu = fallback_to_cpu
        self._cuda_module = None
        self._cpu_backend = CPUBackend() if fallback_to_cpu else None
        self._profile_metrics: Optional[BackendProfileMetrics] = None

    @property
    def name(self) -> str:
        return "gpu"

    def is_available(self) -> bool:
        return is_cupy_available()

    @property
    def last_profile_metrics(self) -> Optional[BackendProfileMetrics]:
        return self._profile_metrics

    def _get_module(self):
        """Compiles or retrieves cached CUDA RawModule."""
        if self._cuda_module is None:
            if not self.is_available():
                raise RuntimeError(
                    "CUDA GPU backend is not available. Ensure an NVIDIA GPU with compatible "
                    "CUDA drivers and CuPy (cupy-cuda12x) are installed."
                )
            import cupy as cp
            self._cuda_module = cp.RawModule(code=CUDA_KERNELS_SOURCE)
        return self._cuda_module

    def compute_direct_shadow(self, scene: Scene,
                              grid: PedestrianGrid,
                              solar_pos: SolarPosition,
                              roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes 2D binary direct solar shadow mask on the GPU.
        """
        ny, nx = grid.shape
        n_rays = ny * nx

        # Nighttime check: zero solar illumination
        if not solar_pos.is_daylight:
            return np.zeros((ny, nx), dtype=np.float64)

        active_meshes = scene.get_active_meshes()
        active_buildings = scene.get_active_buildings()
        if not active_meshes and not active_buildings:
            return np.ones((ny, nx), dtype=np.float64)

        if not self.is_available():
            if self._fallback_to_cpu:
                return self._cpu_backend.compute_direct_shadow(scene, grid, solar_pos, roi_mask)
            raise RuntimeError("GPU execution requested but no compatible CUDA device detected.")

        import cupy as cp
        module = self._get_module()
        shadow_kernel = module.get_function("moller_trumbore_shadow_kernel")

        # Flatten geometry
        geom = FlattenedSceneGeometry.from_scene(scene)

        # Receptor coordinates
        eval_x = grid.X.ravel()
        eval_y = grid.Y.ravel()
        eval_z = np.full_like(eval_x, grid.z_ped)
        origins = np.column_stack([eval_x, eval_y, eval_z]).astype(np.float64)
        sun_dir = np.array(solar_pos.sun_vector, dtype=np.float64)

        # Upload arrays to GPU
        t0_upload = time.perf_counter()
        d_origins = cp.asarray(origins)
        d_dir = cp.asarray(sun_dir)
        d_verts = cp.asarray(geom.vertices)
        d_tris = cp.asarray(geom.triangles)
        d_boxes = cp.asarray(geom.bldg_boxes)
        d_out = cp.ones(n_rays, dtype=cp.float64)

        d_roi = cp.asarray(roi_mask.ravel().astype(np.uint8)) if roi_mask is not None else cp.zeros(1, dtype=cp.uint8)
        has_roi = np.int32(1 if roi_mask is not None else 0)

        cp.cuda.Stream.null.synchronize()
        t_upload = time.perf_counter() - t0_upload

        # Launch kernel
        block_dim = 256
        grid_dim = (n_rays + block_dim - 1) // block_dim

        t0_kernel = time.perf_counter()
        shadow_kernel(
            (grid_dim,), (block_dim,),
            (
                d_origins, d_dir, d_verts, d_tris, d_boxes,
                has_roi, d_roi,
                np.int32(n_rays), np.int32(geom.num_triangles), np.int32(geom.num_buildings),
                np.float64(1e-6), np.float64(1e-10), np.float64(1e-9),
                d_out
            )
        )
        cp.cuda.Stream.null.synchronize()
        t_kernel = time.perf_counter() - t0_kernel

        # Download result
        t0_download = time.perf_counter()
        shadow_mask = cp.asnumpy(d_out).reshape((ny, nx))
        t_download = time.perf_counter() - t0_download

        total_time = t_upload + t_kernel + t_download
        dev = cp.cuda.Device()
        mem_info = dev.mem_info

        self._profile_metrics = BackendProfileMetrics(
            backend_name="gpu",
            scene_upload_time_s=t_upload,
            kernel_runtime_s=t_kernel,
            transfer_to_host_time_s=t_download,
            total_runtime_s=total_time,
            shadow_runtime_s=total_time,
            peak_gpu_memory_bytes=mem_info[1] - mem_info[0],
            shadow_ray_count=n_rays,
            total_ray_count=n_rays,
            num_triangles=geom.num_triangles,
            num_buildings=geom.num_buildings,
            device_name=f"CUDA {dev.id}"
        )

        return shadow_mask

    def compute_sky_view_factor(self, scene: Scene,
                                grid: PedestrianGrid,
                                num_azimuths: int = 32,
                                max_search_dist_m: float = 120.0,
                                roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Computes 2D Sky View Factor on the GPU via mesh rasterization and horizon scan.
        """
        ny, nx = grid.shape
        active_meshes = scene.get_active_meshes()
        active_buildings = scene.get_active_buildings()

        if not active_meshes and not active_buildings:
            return np.ones((ny, nx), dtype=np.float64)

        if not self.is_available():
            if self._fallback_to_cpu:
                return self._cpu_backend.compute_sky_view_factor(
                    scene, grid, num_azimuths, max_search_dist_m, roi_mask
                )
            raise RuntimeError("GPU execution requested but no compatible CUDA device detected.")

        import cupy as cp
        module = self._get_module()
        raster_kernel = module.get_function("rasterize_mesh_height_kernel")
        svf_kernel = module.get_function("compute_svf_horizon_kernel")

        # Flatten geometry
        geom = FlattenedSceneGeometry.from_scene(scene)

        t0_upload = time.perf_counter()
        d_verts = cp.asarray(geom.vertices)
        d_tris = cp.asarray(geom.triangles)
        d_boxes = cp.asarray(geom.bldg_boxes)
        d_height_grid = cp.zeros((ny, nx), dtype=cp.float64)
        d_svf = cp.ones((ny, nx), dtype=cp.float64)
        d_roi = cp.asarray(roi_mask.astype(np.uint8)) if roi_mask is not None else cp.zeros(1, dtype=cp.uint8)
        has_roi = np.int32(1 if roi_mask is not None else 0)

        scene_zmax = float(geom.bounds_3d[5])
        step_dx = max(0.5, grid.dx * 0.5)

        cp.cuda.Stream.null.synchronize()
        t_upload = time.perf_counter() - t0_upload

        block_2d = (16, 16)
        grid_2d = ((nx + block_2d[0] - 1) // block_2d[0], (ny + block_2d[1] - 1) // block_2d[1])

        t0_kernel = time.perf_counter()

        # Step 1: Rasterize meshes to height grid (if meshes present)
        if geom.num_triangles > 0:
            raster_kernel(
                grid_2d, block_2d,
                (
                    d_verts, d_tris, np.int32(geom.num_triangles),
                    np.float64(grid.origin_x), np.float64(grid.origin_y), np.float64(grid.dx),
                    np.int32(nx), np.int32(ny),
                    np.float64(scene_zmax + 1.0),
                    np.float64(1e-6), np.float64(1e-10), np.float64(1e-9),
                    d_height_grid
                )
            )

        # Step 2: Compute SVF horizon elevation scan
        svf_kernel(
            grid_2d, block_2d,
            (
                d_height_grid, d_boxes,
                has_roi, d_roi,
                np.int32(geom.num_buildings),
                np.float64(grid.origin_x), np.float64(grid.origin_y), np.float64(grid.dx),
                np.int32(nx), np.int32(ny),
                np.float64(grid.z_ped),
                np.int32(num_azimuths), np.float64(max_search_dist_m), np.float64(step_dx),
                d_svf
            )
        )
        cp.cuda.Stream.null.synchronize()
        t_kernel = time.perf_counter() - t0_kernel

        t0_download = time.perf_counter()
        svf = cp.asnumpy(d_svf)
        t_download = time.perf_counter() - t0_download

        total_time = t_upload + t_kernel + t_download
        dev = cp.cuda.Device()
        mem_info = dev.mem_info

        eval_pts = int(np.sum(roi_mask)) if roi_mask is not None else (ny * nx)
        svf_rays = eval_pts * num_azimuths

        self._profile_metrics = BackendProfileMetrics(
            backend_name="gpu",
            scene_upload_time_s=t_upload,
            kernel_runtime_s=t_kernel,
            transfer_to_host_time_s=t_download,
            total_runtime_s=total_time,
            svf_runtime_s=total_time,
            peak_gpu_memory_bytes=mem_info[1] - mem_info[0],
            svf_ray_count=svf_rays,
            total_ray_count=svf_rays,
            num_triangles=geom.num_triangles,
            num_buildings=geom.num_buildings,
            device_name=f"CUDA {dev.id}"
        )

        return svf

    def full_simulate(self, scene: Scene,
                      weather: Weather,
                      config: SimulationConfig) -> SimulationResult:
        """
        Executes a deterministic full recomputation using the GPU backend for ray-based steps.
        """
        t_start = time.perf_counter()

        # 1. Parse Datetime and Compute Solar Position
        dt_str = f"{config.date} {config.local_time}"
        from datetime import datetime, timezone
        dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        solar_pos = calculate_solar_position(config.latitude, config.longitude, dt_utc)

        # 2. Pedestrian Grid
        grid = PedestrianGrid(scene.pedestrian_grid)

        # 3. Direct Solar Shadows on GPU
        t0_shadow = time.perf_counter()
        shadow_mask = self.compute_direct_shadow(scene, grid, solar_pos)
        t_shadow = time.perf_counter() - t0_shadow

        # 4. Directional Visibility / SVF on GPU
        t0_svf = time.perf_counter()
        svf = self.compute_sky_view_factor(
            scene, grid,
            num_azimuths=config.sky_patch_configuration,
            max_search_dist_m=config.max_svf_search_dist_m
        )
        t_svf = time.perf_counter() - t0_svf

        # 5. Radiative Exchange (Shortwave + Longwave)
        t0_rad = time.perf_counter()
        wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
        ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)

        sw_fluxes = compute_shortwave_fluxes(
            weather, solar_pos, shadow_mask, svf, ground_mat, wall_mat
        )
        lw_fluxes = compute_longwave_fluxes(
            weather, svf, ground_mat, wall_mat
        )
        radiant_state = compute_tmrt(sw_fluxes.k_total, lw_fluxes.l_total)
        t_rad = time.perf_counter() - t0_rad

        # 6. Thermal Comfort (UTCI)
        t0_utci = time.perf_counter()
        air_temp_c = weather.air_temperature - 273.15
        utci = compute_utci(
            air_temp_c=air_temp_c,
            tmrt_c=radiant_state.tmrt_c,
            wind_speed_ms=weather.wind_speed,
            relative_humidity=weather.relative_humidity
        )
        t_utci = time.perf_counter() - t0_utci

        t_total = time.perf_counter() - t_start

        metadata = {
            "solar_altitude_deg": solar_pos.altitude_deg,
            "solar_azimuth_deg": solar_pos.azimuth_deg,
            "solar_zenith_deg": solar_pos.zenith_deg,
            "sun_vector": solar_pos.sun_vector,
            "is_daylight": solar_pos.is_daylight,
            "timing_shadow_sec": t_shadow,
            "timing_svf_sec": t_svf,
            "timing_radiation_sec": t_rad,
            "timing_utci_sec": t_utci,
            "timing_total_sec": t_total,
            "num_buildings": len(scene.get_active_buildings()),
            "num_meshes": len(scene.get_active_meshes()),
            "total_cells": grid.total_cells,
            "air_temperature_c": air_temp_c,
            "backend": "gpu",
            "gpu_profile": self._profile_metrics.__dict__ if self._profile_metrics else None
        }

        return SimulationResult(
            shadow_mask=shadow_mask,
            direct_irradiance=sw_fluxes.direct_horizontal,
            visibility_fields={"svf": svf},
            shortwave_flux=sw_fluxes.k_total,
            longwave_flux=lw_fluxes.l_total,
            tmrt=radiant_state.tmrt_c,
            utci=utci,
            metadata=metadata
        )
