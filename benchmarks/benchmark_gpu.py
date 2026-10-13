#!/usr/bin/env python3
"""
SOLARAEUS GPU Benchmark Script (benchmark_gpu.py).
Protocol Stage 5: High-Performance GPU Benchmarking.

Usage:
    python benchmarks/benchmark_gpu.py --scene [scene_a|scene_b|scene_c|all] --mode [full|inc|all] --repeats 5 --output /path/to/results.json
"""

from __future__ import annotations
import argparse
import gc
import json
import os
import platform
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from benchmarks.run_stage_5_performance_suite import (
    build_scene_a_small,
    build_scene_b_berlin,
    build_scene_c_large_extent,
    run_benchmark_trial,
    get_system_info,
    get_git_commit,
    HAS_CUPY
)
from solaraeus.backends.gpu import is_cupy_available
from solaraeus.reference.full_recompute import full_recompute


def run_gpu_benchmarks(scenes: List[str], modes: List[str], repeats: int, out_path: Optional[str] = None) -> Dict[str, Any]:
    if not HAS_CUPY or not is_cupy_available():
        raise RuntimeError("CUDA / CuPy is not available on this host. Cannot execute GPU benchmarks.")

    scene_map = {
        "scene_a": ("Scene A: Small Warmup Scene", build_scene_a_small),
        "scene_b": ("Scene B: Berlin Friedrichstraße Corridor", build_scene_b_berlin),
        "scene_c": ("Scene C: Dense Large-Scale Extent", build_scene_c_large_extent),
    }

    results = []
    sys_info = get_system_info()
    git_hash = get_git_commit()

    print("=" * 80)
    print("SOLARAEUS GPU BENCHMARK (benchmark_gpu.py)")
    print(f"Device: {sys_info['gpu_model']} (Driver: {sys_info['gpu_driver']}, VRAM: {sys_info['vram_mb']} MB)")
    print("=" * 80)

    for sc_id in scenes:
        sc_name, builder_fn = scene_map[sc_id]
        scene_base, edit, weather, cfg = builder_fn()
        grid = scene_base.pedestrian_grid
        n_cells = int(grid.extent_x * grid.extent_y / (cfg.grid_resolution ** 2))
        n_rays = n_cells * (1 + cfg.sky_patch_configuration)

        print(f"\n--- Scene: {sc_name} ({n_cells:,} cells, {n_rays:,} rays) ---")
        base_res = full_recompute(scene_base, weather, cfg, backend="gpu")

        scene_out = {
            "scene_id": sc_id,
            "scene_name": sc_name,
            "domain_cells": n_cells,
            "ray_count": n_rays,
            "modes": {}
        }

        # Run full recompute on CPU as numerical reference
        cpu_ref = full_recompute(edit.apply(scene_base)[0], weather, cfg, backend="cpu")

        for m in modes:
            gpu_mode = f"gpu_{m}"
            print(f"  Mode: {gpu_mode.upper()} ({repeats} repeats + 1 warmup)...")
            # Warmup
            _ = run_benchmark_trial(scene_base, edit, weather, cfg, gpu_mode, base_result=base_res)

            trials = []
            for _ in range(repeats):
                t = run_benchmark_trial(scene_base, edit, weather, cfg, gpu_mode, base_result=base_res)
                trials.append(t)

            totals = [t["total_time_s"] for t in trials]
            inits = [t["init_time_s"] for t in trials]
            rts = [t["raytrace_time_s"] for t in trials]
            transfers = [t["transfer_time_s"] for t in trials]
            rads = [t["rad_comfort_time_s"] for t in trials]
            mems = [t["peak_gpu_mem_mb"] for t in trials]

            med_total = float(np.median(totals))
            last = trials[-1]
            diff_vs_ref = float(np.max(np.abs(last["tmrt"] - cpu_ref.tmrt)))

            mode_metric = {
                "mode": gpu_mode,
                "initialisation_s": {
                    "median": round(float(np.median(inits)), 5),
                    "std": round(float(np.std(inits)), 5)
                },
                "ray_tracing_s": {
                    "median": round(float(np.median(rts)), 5),
                    "std": round(float(np.std(rts)), 5)
                },
                "data_transfer_s": {
                    "median": round(float(np.median(transfers)), 6),
                    "std": round(float(np.std(transfers)), 6)
                },
                "radiation_comfort_s": {
                    "median": round(float(np.median(rads)), 5),
                    "std": round(float(np.std(rads)), 5)
                },
                "total_end_to_end_s": {
                    "median": round(med_total, 5),
                    "std": round(float(np.std(totals)), 5)
                },
                "peak_gpu_memory_mb": round(float(np.max(mems)), 2),
                "cells_per_second": round(n_cells / max(1e-6, med_total), 1),
                "rays_per_second": round(n_rays / max(1e-6, med_total), 1),
                "reused_percent": round(last["reused_fraction"] * 100.0, 2),
                "recomputed_cells": last["recomputed_cells"],
                "reused_cells": last["reused_cells"],
                "max_tmrt_diff_vs_full_k": round(diff_vs_ref, 6)
            }
            scene_out["modes"][m] = mode_metric

            print(f"    Total: {med_total*1000:>6.2f} ms (std: {mode_metric['total_end_to_end_s']['std']*1000:.2f} ms) | "
                  f"RT: {mode_metric['ray_tracing_s']['median']*1000:>6.2f} ms | "
                  f"Transfer: {mode_metric['data_transfer_s']['median']*1000:>5.2f} ms | "
                  f"Peak VRAM: {mode_metric['peak_gpu_memory_mb']} MB | "
                  f"Parity: {diff_vs_ref:.4f} K")

        results.append(scene_out)

    output_payload = {
        "backend": "gpu",
        "git_commit": git_hash,
        "hardware": sys_info,
        "benchmarks": results
    }

    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"\nSaved GPU benchmark results to: {out_path}")

    return output_payload


def main():
    parser = argparse.ArgumentParser(description="SOLARAEUS GPU Performance Benchmark (Stage 5)")
    parser.add_argument("--scene", choices=["scene_a", "scene_b", "scene_c", "all"], default="all")
    parser.add_argument("--mode", choices=["full", "inc", "all"], default="all")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    scenes = ["scene_a", "scene_b", "scene_c"] if args.scene == "all" else [args.scene]
    modes = ["full", "inc"] if args.mode == "all" else [args.mode]

    out_file = args.output
    if not out_file:
        out_file = os.path.join(ROOT, "results", "raw", "stage_5", "benchmark_gpu_results.json")

    run_gpu_benchmarks(scenes, modes, args.repeats, out_file)


if __name__ == "__main__":
    main()
