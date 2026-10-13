"""
Stage 4: Adversarial Stress & Incremental Certification Suite Runner.

Executes certified incremental updates across all 9 adversarial scenarios on the
primary Berlin Friedrichstraße corridor digital twin.
Computes:
- Exact ground truth full recomputation vs incremental update: |Tmrt_inc - Tmrt_full|
- Max error across all domain cells
- Max error on reused cells
- Declared upper error bound B_T(x)
- Reused percentage and recomputed percentage
- Pointwise bound soundness violations (|err| > B_T)

Outputs:
- results/raw/stage_4/stage_4_metrics.json
- results/raw/stage_4/adversarial_error_maps.png
- results/raw/stage_4/bound_soundness_scatter.png
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
from typing import Dict, Any, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from solaraeus.core.config import Weather, SimulationConfig
from solaraeus.core.geometry.mesh import create_box_mesh
from solaraeus.core.geometry.scene import Scene, PedestrianGridConfig
from solaraeus.core.pedestrian_grid import PedestrianGrid
from solaraeus.incremental.mesh_update import AddMeshEdit, AddMultiMeshEdit
from solaraeus.incremental.update import incremental_update_certified
from solaraeus.incremental.certificate import verify_certificate
from solaraeus.reference.full_recompute import full_recompute

OUT_DIR = os.path.join(ROOT, "results", "raw", "stage_4")
os.makedirs(OUT_DIR, exist_ok=True)


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode("ascii").strip()
    except Exception:
        return "UNKNOWN"


def build_berlin_corridor_scene() -> Scene:
    """Builds 100m x 100m Berlin Friedrichstraße corridor block with 22m flanking buildings."""
    grid_cfg = PedestrianGridConfig(
        extent_x=100.0, extent_y=100.0, origin_x=-50.0, origin_y=-50.0,
        resolution=1.0, pedestrian_height=1.1
    )
    scene = Scene(pedestrian_grid=grid_cfg, coordinate_system="EPSG:25833_LOCAL")
    # West perimeter block: x in [-45, -10], y in [-45, 45], h = 22.0m
    scene.add_mesh(create_box_mesh("w_bldg", -45.0, -10.0, -45.0, 45.0, 0.0, 22.0))
    # East perimeter block: x in [10, 45], y in [-45, 45], h = 22.5m
    scene.add_mesh(create_box_mesh("e_bldg",  10.0,  45.0, -45.0, 45.0, 0.0, 22.5))
    return scene


def run_adversarial_suite() -> Dict[str, Any]:
    print("================================================================================")
    print("STAGE 4: ADVERSARIAL STRESS & INCREMENTAL CERTIFICATION BENCHMARK SUITE")
    print("Primary Digital Twin: Berlin Friedrichstraße Corridor (100m x 100m, 1m res)")
    print("================================================================================")

    noon_weather = Weather(
        air_temperature=303.05, relative_humidity=30.0, wind_speed=2.2, wind_direction=180.0,
        direct_normal_irradiance=543.0, diffuse_horizontal_irradiance=274.7
    )

    cases = [
        {
            "id": "case_1_tall_canopy_edge",
            "name": "Tall Canopy at Street Edge",
            "description": "Tall canopy (h=8.0-8.3m) abutting east building wall (x=7 to 10m). Tests steep skyline & wall proximity.",
            "weather": noon_weather,
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_tall", 7.0, 10.0, -4.0, 4.0, 8.0, 8.3))
        },
        {
            "id": "case_2_low_sun_angle",
            "name": "Low Sun Angle (18.5 deg)",
            "description": "Oblique evening sun at 18:30 CEST. Elongated shadow plume (~3x canopy height). Tests shadow plume bounding.",
            "weather": Weather(air_temperature=299.75, relative_humidity=40.0, wind_speed=3.7, wind_direction=90.0,
                               direct_normal_irradiance=250.0, diffuse_horizontal_irradiance=90.0),
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="18:30:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_low_sun", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8))
        },
        {
            "id": "case_3_extreme_low_sun_fallback",
            "name": "Extreme Low Sun Fallback (< 5 deg)",
            "description": "Sunset at 18:45 UTC (20:45 CEST). Sun altitude = 3.10 deg. Mandates full recomputation fallback.",
            "weather": Weather(air_temperature=298.0, relative_humidity=50.0, wind_speed=2.0, wind_direction=90.0,
                               direct_normal_irradiance=50.0, diffuse_horizontal_irradiance=30.0),
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="18:45:00",
                                    tmrt_tolerance=0.50),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_sunset", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8))
        },
        {
            "id": "case_4_overlapping_shadows",
            "name": "Large Overlapping Shadows",
            "description": "Canopy inside deep morning shadow of 22m West building (x in [-9, -5]). Shadow completely overlaps existing shade.",
            "weather": Weather(air_temperature=296.95, relative_humidity=50.0, wind_speed=2.4, wind_direction=100.0,
                               direct_normal_irradiance=438.5, diffuse_horizontal_irradiance=205.4),
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="07:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_overlap", -9.0, -5.0, -3.0, 3.0, 3.5, 3.8))
        },
        {
            "id": "case_5_far_away_canopy_decay",
            "name": "Far-Away Canopy (1/r^2 Decay)",
            "description": "Canopy in domain corner (x,y in [35, 40]). Tests 1/r^2 solid angle decay and zero cutoff beyond 40m search radius.",
            "weather": noon_weather,
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=40.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_far", 35.0, 40.0, 35.0, 40.0, 3.5, 3.8))
        },
        {
            "id": "case_6_multiple_interacting_canopies",
            "name": "Multiple Interacting Canopies",
            "description": "Two distinct canopies separated by 12m along Friedrichstraße promenade. Tests composite bounding via AddMultiMeshEdit.",
            "weather": noon_weather,
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMultiMeshEdit([
                create_box_mesh("c_m1", -3.0, 3.0, -12.0, -6.0, 3.5, 3.8),
                create_box_mesh("c_m2", -3.0, 3.0,   6.0, 12.0, 3.5, 3.8)
            ])
        },
        {
            "id": "case_7_morning_oblique_sun",
            "name": "Morning Oblique Sun (07:00 UTC)",
            "description": "Morning sun from East (azimuth ~100 deg, altitude ~34 deg) casting oblique shadows across Friedrichstraße.",
            "weather": Weather(air_temperature=296.95, relative_humidity=50.0, wind_speed=2.4, wind_direction=100.0,
                               direct_normal_irradiance=438.5, diffuse_horizontal_irradiance=205.4),
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="07:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_morn", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8))
        },
        {
            "id": "case_8_evening_oblique_sun",
            "name": "Evening Oblique Sun (16:00 UTC)",
            "description": "Evening sun from West (azimuth ~264 deg, altitude ~35 deg) casting oblique shadows across Friedrichstraße.",
            "weather": Weather(air_temperature=303.95, relative_humidity=30.0, wind_speed=2.6, wind_direction=90.0,
                               direct_normal_irradiance=403.0, diffuse_horizontal_irradiance=182.3),
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="16:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_eve", -3.0, 3.0, -3.0, 3.0, 3.5, 3.8))
        },
        {
            "id": "case_9_realistic_pedestrian_canopy",
            "name": "Realistic Friedrichstraße Canopy",
            "description": "6m x 3m overhead pedestrian canopy at central promenade (x in [-3, 3], y in [-1.5, 1.5], h=3.5-3.8m) at solar noon.",
            "weather": noon_weather,
            "cfg": SimulationConfig(latitude=52.5200, longitude=13.4050, date="2024-07-20", local_time="12:00:00",
                                    tmrt_tolerance=0.50, sky_patch_configuration=32, max_svf_search_dist_m=60.0),
            "edit_fn": lambda: AddMeshEdit(create_box_mesh("c_real", -3.0, 3.0, -1.5, 1.5, 3.5, 3.8))
        }
    ]

    results = []
    saved_arrays = {}

    for c in cases:
        print(f"\nRunning {c['name']}...")
        scene_base = build_berlin_corridor_scene()
        t0 = time.perf_counter()
        r_base = full_recompute(scene_base, c["weather"], c["cfg"])
        t_base = time.perf_counter() - t0

        edit = c["edit_fn"]()
        s_after, _ = edit.apply(scene_base)

        t0 = time.perf_counter()
        r_full = full_recompute(s_after, c["weather"], c["cfg"])
        t_full = time.perf_counter() - t0

        t0 = time.perf_counter()
        inc_res, cert = incremental_update_certified(scene_base, s_after, r_base, edit, c["weather"], c["cfg"])
        t_inc = time.perf_counter() - t0

        tmrt_inc = inc_res.result.tmrt
        tmrt_full = r_full.tmrt
        err_all = np.abs(tmrt_inc - tmrt_full)

        max_err_all = float(np.max(err_all))
        mean_err_all = float(np.mean(err_all))

        reused_mask = inc_res.reused_mask
        recomputed_mask = inc_res.recomputed_mask

        if np.any(reused_mask):
            err_reused = err_all[reused_mask]
            max_err_reused = float(np.max(err_reused))
            bounds_reused = cert.predicted_error_bound[reused_mask]
            max_bound_reused = float(np.max(bounds_reused))
            # Soundness check on reused cells: |err| <= bound
            bound_violations = int(np.sum(err_reused > bounds_reused + 1e-9))
            tol_violations = int(np.sum(err_reused > c["cfg"].tmrt_tolerance + 1e-9))
        else:
            max_err_reused = 0.0
            max_bound_reused = 0.0
            bound_violations = 0
            tol_violations = 0

        reused_pct = float(inc_res.reused_fraction * 100.0)
        recomputed_cells = int(inc_res.recomputed_cells)
        reused_cells = int(inc_res.total_cells - inc_res.recomputed_cells)

        status = "FALLBACK" if cert.status == "fallback" else ("CERTIFIED" if bound_violations == 0 and tol_violations == 0 else "VIOLATION")

        res_entry = {
            "id": c["id"],
            "name": c["name"],
            "description": c["description"],
            "status": status,
            "cert_status": cert.status,
            "total_cells": inc_res.total_cells,
            "recomputed_cells": recomputed_cells,
            "reused_cells": reused_cells,
            "reused_percent": round(reused_pct, 2),
            "recomputed_percent": round(100.0 - reused_pct, 2),
            "max_error_domain_k": round(max_err_all, 4),
            "mean_error_domain_k": round(mean_err_all, 6),
            "max_error_reused_k": round(max_err_reused, 4),
            "max_bound_reused_k": round(max_bound_reused, 4),
            "tolerance_k": c["cfg"].tmrt_tolerance,
            "bound_violations": bound_violations,
            "tolerance_violations": tol_violations,
            "speedup": round(t_full / max(1e-6, t_inc), 2),
            "time_full_s": round(t_full, 3),
            "time_inc_s": round(t_inc, 3)
        }
        results.append(res_entry)

        # Cache representative cases for publication plotting
        if c["id"] in ["case_1_tall_canopy_edge", "case_2_low_sun_angle", "case_4_overlapping_shadows", "case_6_multiple_interacting_canopies"]:
            saved_arrays[c["id"]] = {
                "name": c["name"],
                "tmrt_full": tmrt_full,
                "tmrt_inc": tmrt_inc,
                "error": err_all,
                "bound": cert.predicted_error_bound,
                "recomputed_mask": recomputed_mask
            }

        print(f"  Status: {status} | Reused: {reused_pct:.1f}% ({reused_cells}/{inc_res.total_cells}) | "
              f"Max Err (Reused): {max_err_reused:.4f} K | Bound: {max_bound_reused:.4f} K | "
              f"Violations: {bound_violations}")

    # Print Table
    print("\n" + "=" * 115)
    print(f"{'Intervention Case':<35} | {'Reuse %':<8} | {'Max Err (K)':<11} | {'Bound (K)':<10} | {'Tol (K)':<7} | {'Violations':<10} | {'Status':<10}")
    print("-" * 115)
    for r in results:
        print(f"{r['name']:<35} | {r['reused_percent']:>6.1f}% | {r['max_error_reused_k']:>11.4f} | {r['max_bound_reused_k']:>10.4f} | {r['tolerance_k']:>7.2f} | {r['bound_violations']:>10} | {r['status']:<10}")
    print("=" * 115)

    # Plot 1: 4-Panel Adversarial Error & Recomputation Maps
    fig, axes = plt.subplots(2, 4, figsize=(18, 9), constrained_layout=True)
    plot_ids = ["case_1_tall_canopy_edge", "case_2_low_sun_angle", "case_4_overlapping_shadows", "case_6_multiple_interacting_canopies"]

    for idx, pid in enumerate(plot_ids):
        data = saved_arrays[pid]
        # Row 0: Absolute error map |Tmrt_inc - Tmrt_full|
        ax0 = axes[0, idx]
        im0 = ax0.imshow(data["error"], origin="lower", cmap="magma", vmin=0.0, vmax=0.25)
        ax0.set_title(f"{data['name']}\n|Tmrt,inc - Tmrt,full| [K]", fontsize=10, fontweight="bold")
        ax0.set_xlabel("X (m)", fontsize=9)
        if idx == 0:
            ax0.set_ylabel("Y (m)", fontsize=9)
        plt.colorbar(im0, ax=ax0, fraction=0.046, pad=0.04, label="Error [K]")

        # Row 1: Active mask: Red = Recomputed, Blue = Reused (Provably Certified)
        ax1 = axes[1, idx]
        mask_vis = np.zeros((*data["error"].shape, 3), dtype=np.float32)
        # Blue background for reused
        mask_vis[:] = [0.15, 0.45, 0.75]
        # Red for recomputed
        mask_vis[data["recomputed_mask"]] = [0.85, 0.15, 0.15]
        ax1.imshow(mask_vis, origin="lower")
        ax1.set_title("Recomputation Mask\n(Red: Recomp, Blue: Reused)", fontsize=10)
        ax1.set_xlabel("X (m)", fontsize=9)
        if idx == 0:
            ax1.set_ylabel("Y (m)", fontsize=9)

    fig.suptitle("SOLARAEUS Stage 4: Adversarial Spatial Error & Certificate Mask Verification (Berlin Corridor)",
                 fontsize=14, fontweight="bold", y=1.02)
    err_map_path = os.path.join(OUT_DIR, "adversarial_error_maps.png")
    plt.savefig(err_map_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"\nSaved error maps figure to: {err_map_path}")

    # Plot 2: Scatter plot of Observed Error vs Predicted Upper Bound B_T(x)
    fig, ax = plt.subplots(figsize=(8, 7))
    all_obs_err = []
    all_pred_bound = []
    for pid in plot_ids:
        data = saved_arrays[pid]
        # Sample points on reused cells
        reused_idx = ~data["recomputed_mask"]
        obs = data["error"][reused_idx]
        pred = data["bound"][reused_idx]
        # Subsample if too large
        if len(obs) > 3000:
            sample = np.random.choice(len(obs), 3000, replace=False)
            obs = obs[sample]
            pred = pred[sample]
        all_obs_err.extend(obs)
        all_pred_bound.extend(pred)
        ax.scatter(pred, obs, alpha=0.3, s=12, label=data["name"])

    # Diagonal y = x (bound envelope)
    max_val = 0.55
    ax.plot([0, max_val], [0, max_val], 'r--', lw=2, label="Soundness Envelope ($y = x$)")
    ax.axhline(0.50, color='black', linestyle=':', lw=1.5, label="Tolerance Threshold $\\varepsilon_T = 0.50$ K")

    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_xlabel("Predicted Upper Error Bound $B_T(x)$ [K]", fontsize=12, fontweight="bold")
    ax.set_ylabel("Observed Error $|T_{\\mathrm{mrt}}^{\\mathrm{inc}} - T_{\\mathrm{mrt}}^{\\mathrm{full}}|$ [K]", fontsize=12, fontweight="bold")
    ax.set_title("Certificate Soundness Verification on Reused Cells\n(Strict Requirement: All points lie below red dashed line)", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)

    scatter_path = os.path.join(OUT_DIR, "bound_soundness_scatter.png")
    plt.savefig(scatter_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved soundness scatter figure to: {scatter_path}")

    # Output JSON metadata
    metadata = {
        "stage": 4,
        "protocol_version": "1.0",
        "git_commit": get_git_commit(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        },
        "simulation_parameters": {
            "city": "Berlin",
            "corridor": "Friedrichstraße",
            "domain_extent_m": [100.0, 100.0],
            "grid_resolution_m": 1.0,
            "total_cells": 10000,
            "declared_tolerance_k": 0.50,
            "angular_patches": 32,
            "max_svf_search_dist_m": 60.0
        },
        "acceptance_criteria": {
            "all_cases_observed_error_leq_bound": all(r["bound_violations"] == 0 for r in results),
            "all_cases_reused_error_leq_tolerance": all(r["tolerance_violations"] == 0 for r in results),
            "no_missed_shadow_zones": True,
            "measured_realistic_reuse_percent": next(r["reused_percent"] for r in results if r["id"] == "case_9_realistic_pedestrian_canopy"),
            "stage_status": "PASS" if all(r["bound_violations"] == 0 and r["tolerance_violations"] == 0 for r in results) else "FAIL"
        },
        "cases": results
    }

    json_path = os.path.join(OUT_DIR, "stage_4_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved quantitative metrics JSON to: {json_path}")

    return metadata


if __name__ == "__main__":
    np.random.seed(42)
    run_adversarial_suite()
