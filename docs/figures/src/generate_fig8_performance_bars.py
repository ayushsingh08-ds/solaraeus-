#!/usr/bin/env python3
"""
Figure 8: Dual-Backend Performance & Scalability Benchmarks
Generated for Earth Science Informatics (Springer)
Conforms to: Times New Roman, Okabe-Ito colourblind-safe palette, vector PDF/SVG + 300 DPI PNG
"""

import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path

# Publication typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.size'] = 9

def create_fig8():
    # Load Stage 5 performance metrics
    json_path = Path("results/raw/stage_5/stage_5_performance_metrics.json")
    with open(json_path) as f:
        benchmarks = json.load(f)["benchmarks"]

    # Scenes: Scene A (Warmup), Scene B (Berlin Corridor), Scene C (Large Extent)
    scene_labels = [
        "Scene A: Warmup\n(1,600 cells)",
        "Scene B: Berlin Corridor\n(10,000 cells)",
        "Scene C: Dense Extent\n(48,000 cells)"
    ]

    modes = ["cpu_full", "cpu_inc", "gpu_full", "gpu_inc"]
    mode_labels = ["CPU Full Recompute", "CPU Incremental", "CUDA GPU Full", "CUDA GPU Incremental"]
    # Okabe-Ito colors: Charcoal, Sky Blue, Orange, Deep Blue
    colors = ["#4D4D4D", "#56B4E9", "#E69F00", "#0072B2"]

    medians = {m: [] for m in modes}
    stds = {m: [] for m in modes}

    for b in benchmarks:
        for m in modes:
            # Convert to milliseconds
            med_ms = b["modes"][m]["total_time_median_s"] * 1000.0
            std_ms = b["modes"][m]["total_time_std_s"] * 1000.0
            medians[m].append(med_ms)
            stds[m].append(std_ms)

    # Width: single-column (~85 mm = 3.35 in) or double-column (175 mm = 6.89 in)
    # Double-column looks spectacular: 6.89 in x 3.2 in
    fig, ax = plt.subplots(figsize=(6.89, 3.2), dpi=300)

    x = np.arange(len(scene_labels))
    width = 0.18

    rects = []
    for i, (m, lbl, col) in enumerate(zip(modes, mode_labels, colors)):
        pos = x + (i - 1.5) * width
        rect = ax.bar(pos, medians[m], width, yerr=stds[m], label=lbl,
                      color=col, edgecolor='#222222', lw=0.6,
                      capsize=3.0, error_kw=dict(lw=0.8, capthick=0.8, ecolor='#222222'))
        rects.append(rect)

    # Speedup annotations on Scene B (Berlin primary)
    cpu_full_b = medians["cpu_full"][1]
    gpu_inc_b = medians["gpu_inc"][1]
    speedup_b = cpu_full_b / gpu_inc_b
    ax.annotate(f"{speedup_b:.1f}× Speedup", xy=(x[1] + 1.5*width, gpu_inc_b),
                xytext=(x[1] + 1.5*width + 0.15, gpu_inc_b * 3.5),
                arrowprops=dict(arrowstyle="->", color='#0072B2', lw=1.1),
                fontsize=7.2, fontweight='bold', color='#0072B2')

    # Logarithmic scale for wide dynamic range
    ax.set_yscale('log')
    ax.set_ylim(1.0, 10000.0)
    ax.set_ylabel('Total Latency per Step [ms] (Log Scale)', fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(scene_labels, fontsize=8.0)
    ax.set_title('Dual-Backend Latency Across Computational Modes (5 Repeats, NVIDIA RTX 4050)',
                 fontsize=9.2, fontweight='bold', pad=6)

    ax.legend(loc='upper left', fontsize=7.2, framealpha=0.92, ncol=2)
    ax.grid(True, which="both", linestyle=':', alpha=0.5, axis='y')

    plt.tight_layout(pad=0.3)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig8_performance_grouped_bars.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig8_performance_grouped_bars.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig8_performance_grouped_bars.svg", bbox_inches='tight')
    plt.close()
    print("Figure 8 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig8()
