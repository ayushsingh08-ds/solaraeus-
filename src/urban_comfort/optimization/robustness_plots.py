"""
Publication-Quality Visualization Suite for Two-Panel Robustness & Sensitivity Study.

Generates the 13 required scientific figures:
1. best objective versus random seed
2. best objective versus evaluation budget
3. candidate ranking across weather scenarios
4. candidate ranking across solar timestamps
5. objective-weight sensitivity
6. panel-separation sensitivity
7. building-setback sensitivity
8. comfort improvement versus total area
9. comfort improvement versus estimated cost
10. improved-cell coverage comparison
11. CPU/GPU/incremental parity errors
12. reused versus recomputed cells
13. Pareto fronts for each major scenario
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


def setup_style():
    """Sets clean publication styling."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 13,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def plot_best_objective_vs_random_seed(
    seed_results: Dict[int, Dict[str, Any]],
    output_path: Path,
):
    """Plot 1: Best objective value achieved across independent random seeds."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    seeds = sorted(seed_results.keys())
    scores = [seed_results[s]["best_objective"] for s in seeds]
    labels = [f"Seed {s}" for s in seeds]
    areas = [seed_results[s].get("best_area", 0.0) for s in seeds]

    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#1b9e77"][:len(seeds)]
    bars = ax.bar(labels, scores, color=colors, width=0.45, edgecolor="black", linewidth=1.2, zorder=3)

    min_val = min(scores)
    max_val = max(scores)
    margin = (max_val - min_val) * 1.5 if (max_val - min_val) > 0.01 else 0.5
    ax.set_ylim(min_val - margin, max_val + margin)

    for bar, score, area in zip(bars, scores, areas):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01 * margin,
            f"{score:.4f}\n({area:.1f} m²)",
            ha="center", va="bottom", fontsize=9, fontweight="bold"
        )

    mean_score = float(np.mean(scores))
    std_score = float(np.std(scores))
    ax.axhline(mean_score, color="crimson", linestyle="--", linewidth=1.5, label=f"Mean: {mean_score:.4f} ± {std_score:.4f}")

    ax.set_title("Robustness: Best Composite Objective Across Random Seeds")
    ax.set_xlabel("Random Seed")
    ax.set_ylabel("Composite Objective Score (Lower is Better)")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_best_objective_vs_evaluation_budget(
    budget_results: Dict[int, Dict[str, Any]],
    output_path: Path,
):
    """Plot 2: Best objective value vs search budget (25, 50, 100 evaluations)."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    budgets = sorted(budget_results.keys())
    scores = [budget_results[b]["best_objective"] for b in budgets]
    deltas = [budget_results[b].get("peak_tmrt_drop", 0.0) for b in budgets]

    ax.plot(budgets, scores, marker="o", color="#2b5c8f", linewidth=2.2, markersize=8, label="Best Objective Score", zorder=4)

    for b, s, d in zip(budgets, scores, deltas):
        ax.annotate(
            f"{s:.4f}\n(Peak ΔTmrt: {d:.2f} K)",
            (b, s), textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=9, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#2b5c8f", alpha=0.9)
        )

    ax.set_title("Budget Sensitivity: Best Objective vs Evaluation Budget")
    ax.set_xlabel("Physical Evaluation Budget (GPU Incremental Evaluations)")
    ax.set_ylabel("Composite Objective Score (Lower is Better)")
    ax.set_xticks(budgets)
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_candidate_ranking_across_weather_scenarios(
    weather_results: Dict[str, Dict[str, float]],
    output_path: Path,
):
    """Plot 3: Thermal comfort performance across weather perturbation scenarios."""
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    scenarios = list(weather_results.keys())
    nice_names = [s.replace("_", " ").title() for s in scenarios]
    mean_utci = [weather_results[s]["mean_utci_c"] for s in scenarios]
    peak_tmrt = [weather_results[s]["peak_tmrt_drop_k"] for s in scenarios]

    x = np.arange(len(scenarios))
    ax1.bar(x, mean_utci, color="#386cb0", width=0.5, edgecolor="black", linewidth=1.0)
    ax1.set_xticks(x)
    ax1.set_xticklabels(nice_names, rotation=30, ha="right")
    ax1.set_title("Corridor Mean UTCI Across Weather Scenarios")
    ax1.set_ylabel("Mean UTCI (°C)")
    y_min = min(mean_utci) - 1.0
    y_max = max(mean_utci) + 1.0
    ax1.set_ylim(y_min, y_max)
    for i, v in enumerate(mean_utci):
        ax1.text(i, v + 0.1, f"{v:.2f}°C", ha="center", va="bottom", fontsize=8)

    ax2.bar(x, peak_tmrt, color="#e7298a", width=0.5, edgecolor="black", linewidth=1.0)
    ax2.set_xticks(x)
    ax2.set_xticklabels(nice_names, rotation=30, ha="right")
    ax2.set_title("Peak Local Tmrt Cooling Across Weather Scenarios")
    ax2.set_ylabel("Peak Local Tmrt Drop (K)")
    ax2.set_ylim(0, max(peak_tmrt) * 1.25)
    for i, v in enumerate(peak_tmrt):
        ax2.text(i, v + 0.2, f"{v:.2f} K", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_candidate_ranking_across_solar_timestamps(
    timestamp_results: Dict[str, Dict[str, float]],
    output_path: Path,
):
    """Plot 4: Candidate performance across diurnal solar timestamps (09:00, 11:00, 13:00, 15:00)."""
    setup_style()
    fig, ax1 = plt.subplots(figsize=(8, 4.5))

    times = list(timestamp_results.keys())
    utci_drops = [timestamp_results[t]["delta_mean_utci_c"] for t in times]
    tmrt_drops = [timestamp_results[t]["delta_mean_tmrt_c"] for t in times]
    peak_tmrt = [timestamp_results[t]["peak_tmrt_drop_k"] for t in times]

    x = np.arange(len(times))
    w = 0.25

    rects1 = ax1.bar(x - w, utci_drops, w, label="Δ Corridor Mean UTCI (°C)", color="#2ca25f", edgecolor="black")
    rects2 = ax1.bar(x, tmrt_drops, w, label="Δ Corridor Mean Tmrt (K)", color="#3182bd", edgecolor="black")
    rects3 = ax1.bar(x + w, peak_tmrt, w, label="Peak Local Tmrt Relief (K)", color="#fd8d3c", edgecolor="black")

    ax1.set_xticks(x)
    ax1.set_xticklabels(times)
    ax1.set_title("Solar Path Sensitivity: Thermal Relief Across Timestamps")
    ax1.set_xlabel("Local Sun Time (2024-04-15)")
    ax1.set_ylabel("Thermal Improvement Magnitude")
    ax1.legend(loc="upper right")

    for rects in [rects1, rects2, rects3]:
        for r in rects:
            h = r.get_height()
            if h > 0:
                ax1.text(r.get_x() + r.get_width() / 2, h + 0.1, f"{h:.2f}", ha="center", va="bottom", fontsize=7)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_objective_weight_sensitivity(
    weight_sensitivity: Dict[str, List[Tuple[str, float]]],
    output_path: Path,
):
    """Plot 5: Candidate ranking shift across alternative objective weight formulations."""
    setup_style()
    fig, ax = plt.subplots(figsize=(9, 5))

    scenarios = list(weight_sensitivity.keys())
    nice_scenarios = [s.replace("_", " ").title() for s in scenarios]

    # Trace top 4 candidates across scenarios
    all_cands = set()
    for sc in scenarios:
        for cid, _ in weight_sensitivity[sc][:4]:
            all_cands.add(cid)

    sorted_cands = sorted(all_cands)
    colors = plt.cm.tab10(np.linspace(0, 1, len(sorted_cands)))

    x = np.arange(len(scenarios))
    for c_idx, cid in enumerate(sorted_cands):
        ranks = []
        for sc in scenarios:
            ranked_list = [c for c, _ in weight_sensitivity[sc]]
            if cid in ranked_list:
                ranks.append(ranked_list.index(cid) + 1)
            else:
                ranks.append(len(ranked_list) + 1)
        ax.plot(x, ranks, marker="o", linewidth=2.0, markersize=7, label=cid, color=colors[c_idx])

    ax.set_xticks(x)
    ax.set_xticklabels(nice_scenarios)
    ax.set_yticks(range(1, 8))
    ax.invert_yaxis()
    ax.set_title("Objective Formulation Sensitivity: Candidate Rank Shift")
    ax.set_xlabel("Objective Formulation Scenario")
    ax.set_ylabel("Candidate Rank (1 = Top Ranked)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_panel_separation_sensitivity(
    sep_data: Dict[float, Dict[str, Any]],
    output_path: Path,
):
    """Plot 6: Feasible candidate yield vs minimum panel separation requirement."""
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    seps = sorted(sep_data.keys())
    feas_pct = [sep_data[s]["feasible_pct"] for s in seps]
    rej_sep = [sep_data[s]["separation_rejections"] for s in seps]

    ax1.plot(seps, feas_pct, marker="s", color="#1f78b4", linewidth=2.0, markersize=8)
    ax1.set_title("Feasibility Acceptance vs Min Separation")
    ax1.set_xlabel("Minimum Panel Separation (m)")
    ax1.set_ylabel("Feasible Proposal Rate (%)")
    for s, p in zip(seps, feas_pct):
        ax1.annotate(f"{p:.1f}%", (s, p), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)

    ax2.bar([str(s) + " m" for s in seps], rej_sep, color="#e31a1c", width=0.45, edgecolor="black")
    ax2.set_title("Separation Constraint Rejection Count")
    ax2.set_xlabel("Minimum Separation Constraint")
    ax2.set_ylabel("Rejections (out of 500 proposals)")
    for i, count in enumerate(rej_sep):
        ax2.text(i, count + 5, f"{count}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_building_setback_sensitivity(
    setback_data: Dict[float, Dict[str, Any]],
    output_path: Path,
):
    """Plot 7: Feasible candidate yield vs building setback requirement."""
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    setbacks = sorted(setback_data.keys())
    feas_pct = [setback_data[s]["feasible_pct"] for s in setbacks]
    rej_setback = [setback_data[s]["setback_rejections"] for s in setbacks]

    ax1.plot(setbacks, feas_pct, marker="^", color="#33a02c", linewidth=2.0, markersize=8)
    ax1.set_title("Feasibility Acceptance vs Building Setback")
    ax1.set_xlabel("Minimum Building Setback (m)")
    ax1.set_ylabel("Feasible Proposal Rate (%)")
    for s, p in zip(setbacks, feas_pct):
        ax1.annotate(f"{p:.1f}%", (s, p), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)

    ax2.bar([str(s) + " m" for s in setbacks], rej_setback, color="#ff7f00", width=0.45, edgecolor="black")
    ax2.set_title("Setback Constraint Rejection Count")
    ax2.set_xlabel("Building Setback Constraint")
    ax2.set_ylabel("Rejections (out of 500 proposals)")
    for i, count in enumerate(rej_setback):
        ax2.text(i, count + 2, f"{count}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_comfort_improvement_vs_total_area(
    candidates_data: List[Dict[str, Any]],
    output_path: Path,
):
    """Plot 8: Thermal comfort improvement (peak Tmrt & delta UTCI) vs total shade area."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7.5, 5))

    areas = [c["total_area_m2"] for c in candidates_data]
    peak_tmrt = [c["peak_tmrt_drop_k"] for c in candidates_data]
    utci_drop = [c["delta_mean_utci_c"] * 10.0 for c in candidates_data]  # scaled for visibility
    labels = [c["candidate_id"] for c in candidates_data]

    scatter = ax.scatter(areas, peak_tmrt, s=80, c=utci_drop, cmap="plasma", edgecolor="black", zorder=3)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("10 × Δ Corridor Mean UTCI (Scaled °C)")

    for a, p, cid in zip(areas, peak_tmrt, labels):
        if "BEST" in cid or "SURR" in cid or "STAGE" in cid:
            ax.annotate(cid, (a, p), textcoords="offset points", xytext=(5, 5), fontsize=8, fontweight="bold")

    ax.set_title("Intervention Scaling: Comfort Relief vs Canopy Area")
    ax.set_xlabel("Total Canopy Area (m²)")
    ax.set_ylabel("Peak Local Tmrt Relief (K)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_comfort_improvement_vs_estimated_cost(
    candidates_data: List[Dict[str, Any]],
    output_path: Path,
):
    """Plot 9: Thermal comfort improvement vs estimated construction cost."""
    setup_style()
    fig, ax = plt.subplots(figsize=(7.5, 5))

    costs = [c["cost_usd"] for c in candidates_data]
    peak_tmrt = [c["peak_tmrt_drop_k"] for c in candidates_data]
    labels = [c["candidate_id"] for c in candidates_data]

    ax.scatter(costs, peak_tmrt, s=90, color="#2b5c8f", edgecolor="black", zorder=3)

    for cost, p, cid in zip(costs, peak_tmrt, labels):
        if "BEST" in cid or "SURR" in cid or "STAGE" in cid:
            ax.annotate(f"{cid}\n(${cost:,.0f})", (cost, p), textcoords="offset points", xytext=(5, -10), fontsize=8)

    ax.set_title("Cost Efficiency: Peak Tmrt Cooling vs Capital Cost")
    ax.set_xlabel("Estimated Construction Cost (USD)")
    ax.set_ylabel("Peak Local Tmrt Relief (K)")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_improved_cell_coverage_comparison(
    candidates_data: List[Dict[str, Any]],
    output_path: Path,
):
    """Plot 10: Percentage of corridor pedestrian cells cooled across interventions."""
    setup_style()
    fig, ax = plt.subplots(figsize=(9, 4.5))

    labels = [c["name"] for c in candidates_data]
    coverages = [c["pct_cells_improved"] for c in candidates_data]
    colors = ["#999999", "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c"][:len(labels)]

    bars = ax.barh(labels, coverages, color=colors, edgecolor="black", height=0.55, zorder=3)
    ax.set_xlim(0, max(coverages) * 1.25 if coverages else 50)
    ax.set_title("Spatial Cooling Footprint: Pedestrian Cells Improved")
    ax.set_xlabel("Percentage of Corridor Receptors Improved (%)")

    for bar, cov in zip(bars, coverages):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2, f"{cov:.2f}%", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_cpu_gpu_incremental_parity_errors(
    parity_reports: List[Dict[str, Any]],
    output_path: Path,
):
    """Plot 11: Machine-precision parity audit errors across all audited candidates."""
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    cids = [r["candidate_id"] for r in parity_reports]
    cpu_vs_gpu_tmrt = [r["cpu_full_vs_gpu_full"]["max_tmrt_diff_k"] for r in parity_reports]
    gpu_full_vs_inc_tmrt = [r["gpu_full_vs_gpu_inc"]["max_tmrt_diff_k"] for r in parity_reports]

    x = np.arange(len(cids))
    ax1.bar(x, cpu_vs_gpu_tmrt, color="#2b5c8f", width=0.5, edgecolor="black", label="Max |CPU Full - GPU Full|")
    ax1.axhline(0.05, color="red", linestyle="--", label="Tolerance (0.05 K)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(cids, rotation=45, ha="right", fontsize=8)
    ax1.set_title("CPU Full vs GPU Full Parity")
    ax1.set_ylabel("Max Tmrt Difference (K)")
    ax1.set_ylim(0, 0.06)
    ax1.legend(loc="upper right")

    ax2.bar(x, gpu_full_vs_inc_tmrt, color="#41b6c4", width=0.5, edgecolor="black", label="Max |GPU Full - GPU Inc|")
    ax2.axhline(0.05, color="red", linestyle="--", label="Tolerance (0.05 K)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(cids, rotation=45, ha="right", fontsize=8)
    ax2.set_title("GPU Full vs GPU Incremental Parity")
    ax2.set_ylabel("Max Tmrt Difference (K)")
    ax2.set_ylim(0, 0.06)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_reused_vs_recomputed_cells(
    eval_records: List[Dict[str, Any]],
    output_path: Path,
):
    """Plot 12: Incremental execution efficiency: Reused vs recomputed cells."""
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    indices = list(range(1, len(eval_records) + 1))
    reused = [r["reused_cells_count"] for r in eval_records]
    recomputed = [r["recomputed_cells_count"] for r in eval_records]
    pct_reuse = [r["reused_fraction_pct"] for r in eval_records]

    ax.plot(indices, pct_reuse, marker="o", color="#238b45", linewidth=2.0, markersize=5, label="Cell Reuse Percentage")
    ax.axhline(float(np.mean(pct_reuse)), color="crimson", linestyle="--", label=f"Mean Reuse: {np.mean(pct_reuse):.2f}%")

    ax.set_title("GPU Incremental Solver: Pedestrian Grid Cell Reuse Ratio")
    ax.set_xlabel("Evaluation Index")
    ax.set_ylabel("Grid Cells Reused Without Ray Tracing (%)")
    ax.set_ylim(98.5, 100.0)
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)


def plot_pareto_fronts_across_scenarios(
    pareto_scenarios: Dict[str, List[Dict[str, Any]]],
    output_path: Path,
):
    """Plot 13: Non-dominated Pareto fronts for major optimization scenarios."""
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 5))

    colors = {"nominal": "#1f78b4", "seed_7": "#33a02c", "seed_12345": "#e31a1c", "budget_50": "#ff7f00"}
    for sc_name, cands in pareto_scenarios.items():
        if not cands:
            continue
        costs = [c["cost_usd"] for c in cands]
        drops = [c["peak_tmrt_drop_k"] for c in cands]
        color = colors.get(sc_name, "#984ea3")
        # Sort for connected line
        sorted_pairs = sorted(zip(costs, drops))
        c_sorted, d_sorted = zip(*sorted_pairs)
        ax.plot(c_sorted, d_sorted, marker="o", label=f"Pareto: {sc_name.title()}", color=color, linewidth=1.8, markersize=6)

    ax.set_title("Multi-Objective Pareto Frontiers Across Scenarios")
    ax.set_xlabel("Estimated Construction Cost (USD)")
    ax.set_ylabel("Peak Local Tmrt Relief (K)")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)
