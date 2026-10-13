"""Minimal Synthetic Scene Baseline Runner for SOLARAEUS (Stage 1).

Constructs a minimal synthetic scene (single cube on flat ground, fixed sun)
and executes both CPU and GPU backends. Compares numerical parity and saves
arrays, logs, profiling metrics, and static matplotlib figures.

Strictly adheres to GLOBAL RULES:
- No real legacy sites (Church Street / Bengaluru never referenced or used).
- Static figures only (matplotlib PNG).
- Honest recording of hardware, git commit, software versions, and numerical deltas.
"""

from __future__ import annotations
import json
import math
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# SOLARAEUS imports
from solaraeus.core.geometry.mesh import create_box_mesh
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig
from solaraeus.core.pedestrian_grid import PedestrianGrid
from solaraeus.core.config import (
    Weather, SimulationConfig, DEFAULT_WALL_MATERIAL, DEFAULT_GROUND_MATERIAL
)
from solaraeus.physics.solar_position import SolarPosition
from solaraeus.physics.shortwave import compute_shortwave_fluxes
from solaraeus.physics.longwave import compute_longwave_fluxes
from solaraeus.physics.mean_radiant_temperature import mean_radiant_temperature
from solaraeus.physics.utci import compute_utci
from solaraeus.backends.cpu import CPUBackend
from solaraeus.backends.gpu import GPUBackend, is_cupy_available

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(ROOT, "results", "raw", "stage_1", "baseline_synthetic")


def get_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def get_gpu_info() -> Dict[str, Any]:
    gpu_info = {
        "cupy_available": is_cupy_available(),
        "device_count": 0,
        "device_name": "None",
        "driver_version": "None",
    }
    if is_cupy_available():
        try:
            import cupy as cp
            gpu_info["device_count"] = cp.cuda.runtime.getDeviceCount()
            dev = cp.cuda.Device(0)
            dev_props = cp.cuda.runtime.getDeviceProperties(0)
            gpu_info["device_name"] = dev_props["name"].decode("utf-8") if isinstance(dev_props["name"], bytes) else str(dev_props["name"])
            gpu_info["compute_capability"] = f"{dev_props.get('major', 0)}.{dev_props.get('minor', 0)}"
            gpu_info["total_memory_bytes"] = dev.mem_info[1]
        except Exception as e:
            gpu_info["gpu_query_error"] = str(e)
    try:
        smi_out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        parts = [p.strip() for p in smi_out.split(",")]
        if len(parts) >= 3:
            gpu_info["driver_version"] = parts[0]
            gpu_info["nvidia_smi_name"] = parts[1]
            gpu_info["total_vram_mib"] = float(parts[2])
    except Exception:
        pass
    return gpu_info


def build_synthetic_scene() -> Tuple[Scene, PedestrianGrid]:
    """
    Creates a minimal synthetic scene:
    - Domain: 50m x 50m centred at origin (x, y in [-25, 25])
    - Grid resolution: 0.5m -> 100 x 100 = 10,000 evaluation cells
    - Single 10m x 10m x 10m cube at centre: x in [-5, 5], y in [-5, 5], z in [0, 10]
    """
    extent = 50.0
    res = 0.5
    origin = -extent / 2.0  # -25.0
    grid_cfg = PedestrianGridConfig(
        extent_x=extent,
        extent_y=extent,
        origin_x=origin,
        origin_y=origin,
        resolution=res,
        pedestrian_height=1.1,
    )
    grid = PedestrianGrid(grid_cfg)

    scene = Scene(pedestrian_grid=grid_cfg)
    cube_mesh = create_box_mesh(
        box_id="synthetic_cube_10m",
        xmin=-5.0,
        xmax=5.0,
        ymin=-5.0,
        ymax=5.0,
        zmin=0.0,
        zmax=10.0,
        material_id="default_wall",
    )
    scene.add_mesh(cube_mesh)
    return scene, grid


def get_fixed_sun() -> SolarPosition:
    """
    Fixed solar position:
    Altitude: 45.0 degrees above horizon
    Azimuth: 180.0 degrees (due south)
    Zenith: 45.0 degrees
    Sun vector: points towards sun (0.0, -cos(45), sin(45))
    """
    alt_deg = 45.0
    az_deg = 180.0
    zenith_deg = 45.0
    alt_rad = math.radians(alt_deg)
    az_rad = math.radians(az_deg)
    sun_vec = (
        math.sin(az_rad) * math.cos(alt_rad),
        math.cos(az_rad) * math.cos(alt_rad),
        math.sin(alt_rad),
    )
    return SolarPosition(
        altitude_deg=alt_deg,
        azimuth_deg=az_deg,
        zenith_deg=zenith_deg,
        sun_vector=sun_vec,
        is_daylight=True,
    )


def run_full_pipeline_with_backend(backend, scene: Scene, grid: PedestrianGrid,
                                   sun: SolarPosition, weather: Weather,
                                   azimuth_count: int = 32, max_dist_m: float = 40.0) -> Dict[str, Any]:
    t0_all = time.perf_counter()

    # 1. Direct Shadow
    t0_shadow = time.perf_counter()
    shadow = backend.compute_direct_shadow(scene, grid, sun)
    t_shadow = time.perf_counter() - t0_shadow

    # 2. SVF
    t0_svf = time.perf_counter()
    svf = backend.compute_sky_view_factor(
        scene, grid, azimuth_count=azimuth_count, max_search_dist_m=max_dist_m
    )
    t_svf = time.perf_counter() - t0_svf

    # 3. Radiative fluxes
    t0_rad = time.perf_counter()
    wall_mat = scene.materials.get("default_wall", DEFAULT_WALL_MATERIAL)
    ground_mat = scene.materials.get("default_ground", DEFAULT_GROUND_MATERIAL)
    sw = compute_shortwave_fluxes(weather, sun, shadow, svf, ground_mat, wall_mat)
    lw = compute_longwave_fluxes(weather, svf, ground_mat, wall_mat)
    rad_state = mean_radiant_temperature(sw.k_total, lw.l_total)
    t_rad = time.perf_counter() - t0_rad

    # 4. UTCI
    t0_utci = time.perf_counter()
    air_temp_c = weather.air_temperature - 273.15
    utci = compute_utci(
        air_temp_c=air_temp_c,
        tmrt_c=rad_state.tmrt_c,
        wind_speed_ms=weather.wind_speed,
        relative_humidity=weather.relative_humidity,
    )
    t_utci = time.perf_counter() - t0_utci
    t_total = time.perf_counter() - t0_all

    return {
        "shadow": shadow,
        "svf": svf,
        "tmrt": rad_state.tmrt_c,
        "utci": utci,
        "sw_flux": sw.k_total,
        "lw_flux": lw.l_total,
        "timing": {
            "shadow_s": t_shadow,
            "svf_s": t_svf,
            "radiation_s": t_rad,
            "utci_s": t_utci,
            "total_s": t_total,
        },
    }


def generate_static_plot(res_cpu: Dict[str, Any], res_gpu: Dict[str, Any],
                         grid: PedestrianGrid, out_path: str):
    """Generates publication-quality static matplotlib figures comparing CPU and GPU."""
    fig, axes = plt.subplots(3, 3, figsize=(16, 15), dpi=300)

    ny, nx = grid.shape
    extent = [grid.origin_x, grid.origin_x + nx * grid.dx,
              grid.origin_y, grid.origin_y + ny * grid.dx]

    diff_shadow = np.abs(res_cpu["shadow"] - res_gpu["shadow"])
    diff_svf = np.abs(res_cpu["svf"] - res_gpu["svf"])
    diff_tmrt = np.abs(res_cpu["tmrt"] - res_gpu["tmrt"])

    # Row 1: Direct Shadow
    im00 = axes[0, 0].imshow(res_cpu["shadow"], origin="lower", extent=extent, cmap="gray", vmin=0, vmax=1)
    axes[0, 0].set_title("CPU Direct Solar Shadow (0=Shaded, 1=Sunlit)", fontsize=11, fontweight="bold")
    plt.colorbar(im00, ax=axes[0, 0], fraction=0.046, pad=0.04)

    im01 = axes[0, 1].imshow(res_gpu["shadow"], origin="lower", extent=extent, cmap="gray", vmin=0, vmax=1)
    axes[0, 1].set_title("GPU Direct Solar Shadow (0=Shaded, 1=Sunlit)", fontsize=11, fontweight="bold")
    plt.colorbar(im01, ax=axes[0, 1], fraction=0.046, pad=0.04)

    im02 = axes[0, 2].imshow(diff_shadow, origin="lower", extent=extent, cmap="inferno", vmin=0, vmax=1)
    axes[0, 2].set_title(f"|CPU - GPU| Shadow Delta (Max: {diff_shadow.max():.4f})", fontsize=11, fontweight="bold")
    plt.colorbar(im02, ax=axes[0, 2], fraction=0.046, pad=0.04)

    # Row 2: Sky View Factor (SVF)
    im10 = axes[1, 0].imshow(res_cpu["svf"], origin="lower", extent=extent, cmap="viridis", vmin=0, vmax=1)
    axes[1, 0].set_title("CPU Sky View Factor (SVF)", fontsize=11, fontweight="bold")
    plt.colorbar(im10, ax=axes[1, 0], fraction=0.046, pad=0.04)

    im11 = axes[1, 1].imshow(res_gpu["svf"], origin="lower", extent=extent, cmap="viridis", vmin=0, vmax=1)
    axes[1, 1].set_title("GPU Sky View Factor (SVF)", fontsize=11, fontweight="bold")
    plt.colorbar(im11, ax=axes[1, 1], fraction=0.046, pad=0.04)

    im12 = axes[1, 2].imshow(diff_svf, origin="lower", extent=extent, cmap="magma")
    axes[1, 2].set_title(f"|CPU - GPU| SVF Delta (Max: {diff_svf.max():.2e})", fontsize=11, fontweight="bold")
    plt.colorbar(im12, ax=axes[1, 2], fraction=0.046, pad=0.04)

    # Row 3: Mean Radiant Temperature (Tmrt)
    vmin_t = min(res_cpu["tmrt"].min(), res_gpu["tmrt"].min())
    vmax_t = max(res_cpu["tmrt"].max(), res_gpu["tmrt"].max())
    im20 = axes[2, 0].imshow(res_cpu["tmrt"], origin="lower", extent=extent, cmap="coolwarm", vmin=vmin_t, vmax=vmax_t)
    axes[2, 0].set_title("CPU $T_{\\mathrm{mrt}}$ [°C]", fontsize=11, fontweight="bold")
    plt.colorbar(im20, ax=axes[2, 0], fraction=0.046, pad=0.04)

    im21 = axes[2, 1].imshow(res_gpu["tmrt"], origin="lower", extent=extent, cmap="coolwarm", vmin=vmin_t, vmax=vmax_t)
    axes[2, 1].set_title("GPU $T_{\\mathrm{mrt}}$ [°C]", fontsize=11, fontweight="bold")
    plt.colorbar(im21, ax=axes[2, 1], fraction=0.046, pad=0.04)

    im22 = axes[2, 2].imshow(diff_tmrt, origin="lower", extent=extent, cmap="magma")
    axes[2, 2].set_title(f"|CPU - GPU| $T_{{\\mathrm{{mrt}}}}$ Delta (Max: {diff_tmrt.max():.2e} K)", fontsize=11, fontweight="bold")
    plt.colorbar(im22, ax=axes[2, 2], fraction=0.046, pad=0.04)

    # Draw cube footprint outline on all plots
    cube_box = [-5, 5, -5, 5]
    for row in axes:
        for ax in row:
            ax.plot([cube_box[0], cube_box[1], cube_box[1], cube_box[0], cube_box[0]],
                    [cube_box[2], cube_box[2], cube_box[3], cube_box[3], cube_box[2]],
                    color="red", linestyle="--", linewidth=1.5, label="10m Cube Footprint")
            ax.set_xlabel("X (m)", fontsize=9)
            ax.set_ylabel("Y (m)", fontsize=9)
            ax.grid(True, linestyle=":", alpha=0.4)

    plt.suptitle("SOLARAEUS Synthetic Baseline: Single Cube on Flat Ground (Fixed Sun: Alt=45°, Az=180°)\nCPU vs GPU Parity Verification",
                 fontsize=14, fontweight="bold", y=0.995)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    git_hash = get_git_commit()
    seed = 42
    np.random.seed(seed)

    print("=====================================================================")
    print("  SOLARAEUS STAGE 1: MINIMAL SYNTHETIC BASELINE RUNNER")
    print("=====================================================================")
    print(f"Git commit:       {git_hash}")
    print(f"Execution time:   {datetime.now(timezone.utc).isoformat()}")
    print(f"Platform:         {platform.platform()} ({platform.processor()})")
    print(f"Python:           {platform.python_version()}")
    gpu_info = get_gpu_info()
    print(f"GPU device:       {gpu_info.get('device_name') or gpu_info.get('nvidia_smi_name', 'None')}")
    print(f"GPU driver:       {gpu_info.get('driver_version', 'None')}")
    print("=====================================================================")

    # 1. Build Scene
    scene, grid = build_synthetic_scene()
    sun = get_fixed_sun()
    weather = Weather(
        air_temperature=303.15,      # 30.0 C
        relative_humidity=50.0,
        wind_speed=1.5,
        wind_direction=180.0,
        direct_normal_irradiance=800.0,
        diffuse_horizontal_irradiance=150.0,
    )

    print(f"\nSynthetic Scene: 10m x 10m x 10m cube, Domain: {grid.extent_x}m x {grid.extent_y}m ({grid.nx} x {grid.ny} = {grid.total_cells} cells)")
    print(f"Sun Position: Altitude={sun.altitude_deg} deg, Azimuth={sun.azimuth_deg} deg")

    # 2. Run CPU backend
    print("\n[1/3] Running CPU reference solver...")
    cpu_backend = CPUBackend()
    res_cpu = run_full_pipeline_with_backend(cpu_backend, scene, grid, sun, weather)
    print(f"  CPU Total time: {res_cpu['timing']['total_s']:.4f} s (Shadow: {res_cpu['timing']['shadow_s']:.4f} s, SVF: {res_cpu['timing']['svf_s']:.4f} s)")

    # 3. Run GPU backend
    print("\n[2/3] Running GPU solver (CUDA / CuPy)...")
    if not is_cupy_available():
        print("  WARNING: GPU (CuPy) is not available. GPU solver run skipped.")
        res_gpu = None
    else:
        gpu_backend = GPUBackend()
        # Warm-up run for JIT compilation
        _ = gpu_backend.compute_direct_shadow(scene, grid, sun)
        res_gpu = run_full_pipeline_with_backend(gpu_backend, scene, grid, sun, weather)
        print(f"  GPU Total time: {res_gpu['timing']['total_s']:.4f} s (Shadow: {res_gpu['timing']['shadow_s']:.4f} s, SVF: {res_gpu['timing']['svf_s']:.4f} s)")

    # 4. Compare CPU vs GPU
    print("\n[3/3] Numerical Parity & Baseline Verification:")
    metrics = {
        "metadata": {
            "git_commit": git_hash,
            "seed": seed,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "os": platform.platform(),
            "cpu": platform.processor(),
            "python": platform.python_version(),
            "gpu_info": gpu_info,
            "numpy": np.__version__,
        },
        "scene": {
            "cube_dimensions_m": [10.0, 10.0, 10.0],
            "domain_extent_m": [grid.extent_x, grid.extent_y],
            "resolution_m": grid.dx,
            "grid_cells": [grid.ny, grid.nx],
            "total_cells": grid.total_cells,
            "pedestrian_height_m": grid.z_ped,
            "sun_altitude_deg": sun.altitude_deg,
            "sun_azimuth_deg": sun.azimuth_deg,
        },
        "cpu_timings_seconds": res_cpu["timing"],
        "cpu_summary": {
            "shadow_sunlit_fraction": float(np.mean(res_cpu["shadow"])),
            "svf_mean": float(np.mean(res_cpu["svf"])),
            "svf_min": float(np.min(res_cpu["svf"])),
            "svf_max": float(np.max(res_cpu["svf"])),
            "tmrt_c_mean": float(np.mean(res_cpu["tmrt"])),
            "tmrt_c_min": float(np.min(res_cpu["tmrt"])),
            "tmrt_c_max": float(np.max(res_cpu["tmrt"])),
            "utci_c_mean": float(np.mean(res_cpu["utci"])),
            "utci_c_min": float(np.min(res_cpu["utci"])),
            "utci_c_max": float(np.max(res_cpu["utci"])),
        },
    }

    if res_gpu is not None:
        shadow_diff = np.abs(res_cpu["shadow"] - res_gpu["shadow"])
        svf_diff = np.abs(res_cpu["svf"] - res_gpu["svf"])
        tmrt_diff = np.abs(res_cpu["tmrt"] - res_gpu["tmrt"])
        utci_diff = np.abs(res_cpu["utci"] - res_gpu["utci"])

        speedup_shadow = res_cpu["timing"]["shadow_s"] / max(res_gpu["timing"]["shadow_s"], 1e-9)
        speedup_svf = res_cpu["timing"]["svf_s"] / max(res_gpu["timing"]["svf_s"], 1e-9)
        speedup_total = res_cpu["timing"]["total_s"] / max(res_gpu["timing"]["total_s"], 1e-9)

        metrics["gpu_timings_seconds"] = res_gpu["timing"]
        metrics["speedups"] = {
            "shadow_speedup": float(speedup_shadow),
            "svf_speedup": float(speedup_svf),
            "total_speedup": float(speedup_total),
        }
        metrics["numerical_parity"] = {
            "shadow_max_abs_diff": float(np.max(shadow_diff)),
            "shadow_mean_abs_diff": float(np.mean(shadow_diff)),
            "shadow_mismatch_cell_count": int(np.sum(shadow_diff > 1e-6)),
            "svf_max_abs_diff": float(np.max(svf_diff)),
            "svf_mean_abs_diff": float(np.mean(svf_diff)),
            "tmrt_max_abs_diff_k": float(np.max(tmrt_diff)),
            "tmrt_mean_abs_diff_k": float(np.mean(tmrt_diff)),
            "utci_max_abs_diff_k": float(np.max(utci_diff)),
            "utci_mean_abs_diff_k": float(np.mean(utci_diff)),
        }

        print(f"  Shadow Max Diff:    {metrics['numerical_parity']['shadow_max_abs_diff']}")
        print(f"  SVF Max Diff:       {metrics['numerical_parity']['svf_max_abs_diff']:.2e}")
        print(f"  Tmrt Max Diff:      {metrics['numerical_parity']['tmrt_max_abs_diff_k']:.2e} K")
        print(f"  UTCI Max Diff:      {metrics['numerical_parity']['utci_max_abs_diff_k']:.2e} K")
        print(f"  Speedup Shadow:     {speedup_shadow:.2f}x")
        print(f"  Speedup SVF:        {speedup_svf:.2f}x")
        print(f"  Speedup Full Total: {speedup_total:.2f}x")

        # Save numpy arrays
        np.save(os.path.join(OUT_DIR, "gpu_shadow.npy"), res_gpu["shadow"])
        np.save(os.path.join(OUT_DIR, "gpu_svf.npy"), res_gpu["svf"])
        np.save(os.path.join(OUT_DIR, "gpu_tmrt.npy"), res_gpu["tmrt"])
        np.save(os.path.join(OUT_DIR, "gpu_utci.npy"), res_gpu["utci"])

    # Save CPU arrays
    np.save(os.path.join(OUT_DIR, "cpu_shadow.npy"), res_cpu["shadow"])
    np.save(os.path.join(OUT_DIR, "cpu_svf.npy"), res_cpu["svf"])
    np.save(os.path.join(OUT_DIR, "cpu_tmrt.npy"), res_cpu["tmrt"])
    np.save(os.path.join(OUT_DIR, "cpu_utci.npy"), res_cpu["utci"])

    # Save metrics JSON
    json_path = os.path.join(OUT_DIR, "baseline_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nSaved metrics: {os.path.relpath(json_path, ROOT)}")

    # Generate static figure
    if res_gpu is not None:
        plot_path = os.path.join(OUT_DIR, "synthetic_cube_baseline_comparison.png")
        generate_static_plot(res_cpu, res_gpu, grid, plot_path)
        print(f"Saved figure:  {os.path.relpath(plot_path, ROOT)}")

    print("\nStage 1 Baseline Run Completed Successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
