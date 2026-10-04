"""
End-to-End Comparative Benchmark: Full Recomputation vs. Certified Incremental SOLWEIG.

Demonstrates:
1. Baseline scene simulation.
2. Building edit application.
3. Ground-truth full recomputation on edited scene.
4. Certified incremental update with rigorous computable bounds.
5. Pointwise verification of mathematical soundness (|Delta T_mrt(x)| <= B_T(x)).
6. Evaluation of speedup and reused cell fraction.
7. Generation of all benchmark artifacts in results/:
   - results/baseline_result.npz
   - results/edited_full_result.npz
   - results/edited_incremental_result.npz
   - results/error_map.png
   - results/affected_region.png
   - results/performance.json
   - results/certificate.json
"""

from __future__ import annotations
import os
import sys
import time
import json
import numpy as np

# Use Agg backend for headless matplotlib rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as patches

# Ensure src is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from urban_comfort.config import Weather, SimulationConfig
from urban_comfort.geometry.primitives import Building, BoundingBox2D
from urban_comfort.geometry.scene import Scene, PedestrianGridConfig
from urban_comfort.reference.full_recompute import full_recompute
from urban_comfort.incremental.update import (
    AddBuildingEdit, incremental_update_certified
)
from urban_comfort.incremental.certificate import verify_certificate


def run_comparative_experiment():
    print("=" * 80)
    print("SOLARAEUS: CERTIFIED INCREMENTAL SOLWEIG vs FULL RECOMPUTATION BENCHMARK")
    print("=" * 80)

    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(results_dir, exist_ok=True)

    # 1. Environment & Simulation Configuration
    weather = Weather(
        air_temperature=301.15,           # 28.0 C
        relative_humidity=50.0,           # 50%
        wind_speed=2.0,                   # 2 m/s
        wind_direction=180.0,
        direct_normal_irradiance=800.0,   # 800 W/m^2
        diffuse_horizontal_irradiance=160.0
    )

    config = SimulationConfig(
        latitude=40.7128,
        longitude=-74.0060,
        date="2024-07-15",
        local_time="12:00:00",
        grid_resolution=1.0,
        sky_patch_configuration=16,
        max_svf_search_dist_m=30.0,
        tmrt_tolerance=0.5               # 0.5 K tolerance contract
    )

    # 2. Build Baseline Urban Scene
    grid_cfg = PedestrianGridConfig(extent_x=80.0, extent_y=80.0, resolution=1.0, pedestrian_height=1.1)
    scene_baseline = Scene(pedestrian_grid=grid_cfg)

    # Central existing building (16x16x18m)
    bldg_center = Building("bldg_center", BoundingBox2D(32.0, 48.0, 32.0, 48.0), height=18.0)
    scene_baseline.add_building(bldg_center)

    print(f"Domain Extent: {grid_cfg.extent_x:.0f}m x {grid_cfg.extent_y:.0f}m ({int(grid_cfg.extent_x * grid_cfg.extent_y)} cells)")
    print(f"Tolerance Threshold: epsilon_T = {config.tmrt_tolerance:.2f} K")
    print("Running Baseline Full Recomputation...")

    t0 = time.perf_counter()
    baseline_res = full_recompute(scene_baseline, weather, config)
    time_baseline_sec = time.perf_counter() - t0
    print(f"Baseline Solved in {time_baseline_sec:.3f} s")

    # 3. Apply Local Geometric Edit: Add a second building (Infill project)
    # A 14x14x15m building located at (14..28, 46..60)
    bldg_infill = Building("bldg_infill", BoundingBox2D(14.0, 28.0, 46.0, 60.0), height=15.0)
    edit = AddBuildingEdit(bldg_infill)
    scene_edited, _ = edit.apply(scene_baseline)

    print(f"\nApplied Geometric Edit: Add Building 'bldg_infill' (14x14x15m)")

    # 4. Ground Truth Full Recomputation on Edited Scene
    print("Running Ground-Truth Full Recomputation on Edited Scene...")
    t0 = time.perf_counter()
    edited_full_res = full_recompute(scene_edited, weather, config)
    time_full_recompute_sec = time.perf_counter() - t0
    print(f"Ground-Truth Full Recomputation Solved in {time_full_recompute_sec:.3f} s")

    # 5. Certified Incremental SOLWEIG Update
    print("Running Certified Incremental SOLWEIG Update...")
    t0 = time.perf_counter()
    inc_update_res, cert = incremental_update_certified(
        scene_baseline, scene_edited, baseline_res, edit, weather, config
    )
    time_incremental_sec = time.perf_counter() - t0
    edited_inc_res = inc_update_res.result
    print(f"Certified Incremental Solved in {time_incremental_sec:.3f} s")

    speedup = time_full_recompute_sec / time_incremental_sec if time_incremental_sec > 0 else 1.0
    print(f"Speedup Factor: {speedup:.2f}x")

    # 6. Verify Mathematical Soundness
    verif = verify_certificate(cert, edited_inc_res.tmrt, edited_full_res.tmrt)
    print("\n" + "-" * 40)
    print("CERTIFICATE AUDIT & VERIFICATION RESULTS")
    print("-" * 40)
    print(f"Certificate Status:           {cert.status}")
    print(f"Mathematical Validity:        {verif.is_valid} (Violations: {verif.num_violations})")
    print(f"Within User Tolerance:        {verif.is_within_tolerance}")
    print(f"Total Grid Cells:             {cert.total_cells}")
    print(f"Reused Cells (Safe):          {cert.reused_cells} ({cert.reused_fraction * 100:.1f}%)")
    print(f"Recomputed Cells (Dirty):     {cert.affected_cells} ({(1.0 - cert.reused_fraction) * 100:.1f}%)")
    print(f"Max Actual Error on Reused:   {verif.reused_max_error:.4e} K (Threshold: {config.tmrt_tolerance} K)")
    print(f"Max Theoretical Upper Bound:  {cert.max_predicted_bound:.2f} K")
    print(f"Min Verification Slack:       {np.min(verif.slack_map):.4e} K (>= 0 guarantees soundness)")

    reused_mask = (cert.predicted_error_bound <= cert.tolerance)
    dirty_mask = (cert.predicted_error_bound > cert.tolerance)
    actual_error_map = np.abs(edited_inc_res.tmrt - edited_full_res.tmrt)

    # 7. Save Array Outputs (.npz)
    baseline_npz_path = os.path.join(results_dir, "baseline_result.npz")
    np.savez_compressed(
        baseline_npz_path,
        shadow_mask=baseline_res.shadow_mask,
        svf=baseline_res.svf,
        shortwave_flux=baseline_res.shortwave_flux,
        longwave_flux=baseline_res.longwave_flux,
        tmrt=baseline_res.tmrt,
        utci=baseline_res.utci
    )
    print(f"\n[Saved] Baseline results -> {baseline_npz_path}")

    edited_full_npz_path = os.path.join(results_dir, "edited_full_result.npz")
    np.savez_compressed(
        edited_full_npz_path,
        shadow_mask=edited_full_res.shadow_mask,
        svf=edited_full_res.svf,
        shortwave_flux=edited_full_res.shortwave_flux,
        longwave_flux=edited_full_res.longwave_flux,
        tmrt=edited_full_res.tmrt,
        utci=edited_full_res.utci
    )
    print(f"[Saved] Ground-truth edited results -> {edited_full_npz_path}")

    edited_inc_npz_path = os.path.join(results_dir, "edited_incremental_result.npz")
    np.savez_compressed(
        edited_inc_npz_path,
        shadow_mask=edited_inc_res.shadow_mask,
        svf=edited_inc_res.svf,
        shortwave_flux=edited_inc_res.shortwave_flux,
        longwave_flux=edited_inc_res.longwave_flux,
        tmrt=edited_inc_res.tmrt,
        utci=edited_inc_res.utci,
        certificate_bound=cert.predicted_error_bound,
        reused_mask=reused_mask,
        dirty_mask=dirty_mask
    )
    print(f"[Saved] Certified incremental results -> {edited_inc_npz_path}")

    # 8. Generate Visualizations (.png)
    # Figure 1: Error Map & Certificate Bound (2x2 publication layout)
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), dpi=150)
    
    # 1. Full Recomputed Tmrt
    im0 = axes[0, 0].imshow(edited_full_res.tmrt, origin="lower", cmap="inferno")
    axes[0, 0].set_title(r"Full Ground Truth $T_{\mathrm{mrt}}^{\mathrm{full}}$ ($^\circ$C)", fontsize=13, fontweight="bold")
    plt.colorbar(im0, ax=axes[0, 0], fraction=0.046, pad=0.04, label=r"$T_{\mathrm{mrt}}$ ($^\circ$C)")

    # 2. Incremental Tmrt
    im1 = axes[0, 1].imshow(edited_inc_res.tmrt, origin="lower", cmap="inferno")
    axes[0, 1].set_title(r"Certified Incremental $\widetilde{T}_{\mathrm{mrt}}$ ($^\circ$C)", fontsize=13, fontweight="bold")
    plt.colorbar(im1, ax=axes[0, 1], fraction=0.046, pad=0.04, label=r"$T_{\mathrm{mrt}}$ ($^\circ$C)")

    # 3. Actual Error Map
    im2 = axes[1, 0].imshow(actual_error_map, origin="lower", cmap="magma")
    axes[1, 0].set_title(r"Actual Error $|\widetilde{T}_{\mathrm{mrt}} - T_{\mathrm{mrt}}^{\mathrm{full}}|$ (K)", fontsize=13, fontweight="bold")
    plt.colorbar(im2, ax=axes[1, 0], fraction=0.046, pad=0.04, label="Error (K)")

    # 4. Certificate Upper Bound B_T(x) with Tolerance Contour
    im3 = axes[1, 1].imshow(cert.predicted_error_bound, origin="lower", cmap="viridis", vmax=max(2.0, config.tmrt_tolerance * 2))
    axes[1, 1].contour(cert.predicted_error_bound, levels=[config.tmrt_tolerance], colors=["red"], linewidths=[2.0], linestyles=["--"])
    axes[1, 1].set_title(r"Computable Certificate Bound $B_T(x)$ (K)" f"\n(Red dashed = $\\varepsilon_T = {config.tmrt_tolerance}$ K contour)", fontsize=13, fontweight="bold")
    plt.colorbar(im3, ax=axes[1, 1], fraction=0.046, pad=0.04, label=r"Bound $B_T(x)$ (K)")

    for ax in axes.flat:
        ax.set_xlabel("X (m)", fontsize=11)
        ax.set_ylabel("Y (m)", fontsize=11)

    plt.tight_layout()
    error_map_path = os.path.join(results_dir, "error_map.png")
    plt.savefig(error_map_path)
    plt.close(fig)
    print(f"[Saved] Error map visualization -> {error_map_path}")

    # Figure 2: Affected Region & Reuse Partition (1x3 layout)
    fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5.5), dpi=150)

    # Panel A: Direct Shadow Mask
    axes2[0].imshow(edited_full_res.shadow_mask, origin="lower", cmap="gray", vmin=0, vmax=1)
    axes2[0].set_title("Direct Solar Shadow Mask\n(0 = Shadow, 1 = Lit)", fontsize=12, fontweight="bold")
    # Draw building footprints
    rect_c = patches.Rectangle((32, 32), 16, 16, linewidth=1.5, edgecolor="cyan", facecolor="none", label="Baseline Bldg")
    rect_i = patches.Rectangle((14, 46), 14, 14, linewidth=1.5, edgecolor="yellow", facecolor="none", label="Infill Edit")
    axes2[0].add_patch(rect_c)
    axes2[0].add_patch(rect_i)
    axes2[0].legend(loc="upper right", fontsize=9)

    # Panel B: Sky View Factor (SVF)
    im_svf = axes2[1].imshow(edited_full_res.svf, origin="lower", cmap="Blues_r", vmin=0.0, vmax=1.0)
    axes2[1].set_title("Sky View Factor (SVF) Field", fontsize=12, fontweight="bold")
    plt.colorbar(im_svf, ax=axes2[1], fraction=0.046, pad=0.04, label="SVF [0..1]")

    # Panel C: Reused vs Dirty Recomputed Cells
    partition_map = np.zeros_like(reused_mask, dtype=int)
    partition_map[dirty_mask] = 1   # Dirty = 1 (Red)
    partition_map[reused_mask] = 2  # Reused = 2 (Green)
    cmap_partition = ListedColormap(["#2b2b2b", "#d9534f", "#5cb85c"])
    im_part = axes2[2].imshow(partition_map, origin="lower", cmap=cmap_partition, vmin=0, vmax=2)
    axes2[2].set_title(f"Selective Domain Partition\n(Green = Reused {cert.reused_fraction*100:.1f}%, Red = Dirty)", fontsize=12, fontweight="bold")

    for ax in axes2:
        ax.set_xlabel("X (m)", fontsize=11)
        ax.set_ylabel("Y (m)", fontsize=11)

    plt.tight_layout()
    affected_region_path = os.path.join(results_dir, "affected_region.png")
    plt.savefig(affected_region_path)
    plt.close(fig2)
    print(f"[Saved] Affected region visualization -> {affected_region_path}")

    # 9. Save Performance Telemetry (JSON)
    perf_data = {
        "benchmark_metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "domain_extent_x_m": grid_cfg.extent_x,
            "domain_extent_y_m": grid_cfg.extent_y,
            "grid_resolution_m": grid_cfg.resolution,
            "total_cells": cert.total_cells,
            "tolerance_k": config.tmrt_tolerance
        },
        "timings_sec": {
            "baseline_full_recompute": time_baseline_sec,
            "edited_full_recompute": time_full_recompute_sec,
            "certified_incremental": time_incremental_sec,
            "speedup_ratio": round(speedup, 3)
        },
        "domain_partition": {
            "reused_cells": cert.reused_cells,
            "recomputed_dirty_cells": cert.affected_cells,
            "reused_fraction": round(cert.reused_fraction, 4),
            "dirty_fraction": round(1.0 - cert.reused_fraction, 4)
        },
        "error_metrics_k": {
            "max_actual_error_overall": float(np.max(actual_error_map)),
            "mean_actual_error_overall": float(np.mean(actual_error_map)),
            "max_actual_error_reused": float(verif.reused_max_error),
            "max_predicted_bound": float(cert.max_predicted_bound),
            "mean_slack": float(np.mean(verif.slack_map)),
            "min_slack": float(np.min(verif.slack_map))
        },
        "soundness_audit": {
            "is_valid": verif.is_valid,
            "num_violations": verif.num_violations,
            "violation_rate": 0.0 if verif.is_valid else float(verif.num_violations) / cert.total_cells,
            "is_within_tolerance": verif.is_within_tolerance
        }
    }

    perf_json_path = os.path.join(results_dir, "performance.json")
    with open(perf_json_path, "w") as f:
        json.dump(perf_data, f, indent=2)
    print(f"[Saved] Performance telemetry -> {perf_json_path}")

    # 10. Save Certificate Audit Record (JSON)
    cert_data = {
        "certificate_id": f"CERT-{int(time.time())}",
        "status": cert.status,
        "tolerance_k": cert.tolerance,
        "total_cells": cert.total_cells,
        "reused_cells": cert.reused_cells,
        "affected_cells": cert.affected_cells,
        "reused_fraction": round(cert.reused_fraction, 4),
        "max_predicted_bound_k": round(cert.max_predicted_bound, 4),
        "mathematical_assumptions": cert.assumptions,
        "verification": {
            "verified": verif.is_valid,
            "num_violations": verif.num_violations,
            "max_violation_k": float(verif.max_violation),
            "reused_cells_max_error_k": float(verif.reused_max_error),
            "is_strictly_within_tolerance": verif.is_within_tolerance
        }
    }

    cert_json_path = os.path.join(results_dir, "certificate.json")
    with open(cert_json_path, "w") as f:
        json.dump(cert_data, f, indent=2)
    print(f"[Saved] Certificate contract record -> {cert_json_path}")

    print("=" * 80)
    print("ALL 7 SECTION 15 BENCHMARK ARTIFACTS GENERATED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_comparative_experiment()
