#!/usr/bin/env python3
"""
Figure 9: Optimization Convergence (Best Objective vs Evaluation Budget)
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

def create_fig9():
    json_path = Path("results/raw/stage_6/stage_6_optimization_metrics.json")
    with open(json_path) as f:
        data = json.load(f)["multi_canopy_methods_aggregated"]

    methods = [
        ("random_search", "Random Search", "#4D4D4D", "-"),
        ("direct_search", "Direct Search (GA)", "#009E73", "-"),
        ("surrogate_only", "Static GP Surrogate", "#E69F00", "-."),
        ("active_learning", "Active Learning (GP-LCB)", "#0072B2", "-")
    ]

    budget = np.arange(1, 51)

    # Width: single-column (~85 mm = 3.35 in) or double-column (175 mm = 6.89 in)
    # Let's make single-column (~3.35 in x 3.2 in) or 4.5 in x 3.2 in
    fig, ax = plt.subplots(figsize=(3.35, 3.2), dpi=300)

    # Baseline no-intervention line (43.0630 °C)
    ax.axhline(43.0630, color='#CC79A7', linestyle=':', lw=1.3, label='Baseline (No Intervention, 43.06°C)')

    for m_id, label, color, lstyle in methods:
        mean_curve = np.array(data[m_id]["convergence_mean"])
        std_curve = np.array(data[m_id]["convergence_std"])
        
        # Plot mean trajectory
        ax.plot(budget, mean_curve, color=color, linestyle=lstyle, lw=1.3, label=label)
        # Shaded min/max band (+/- 1 std)
        ax.fill_between(budget, mean_curve - std_curve, mean_curve + std_curve,
                        color=color, alpha=0.15, edgecolor='none')

    ax.set_xlim(1, 50)
    ax.set_ylim(42.56, 43.22)
    ax.set_xlabel('Simulation Evaluation Budget ($N$)', fontsize=8.5)
    ax.set_ylabel('Core Corridor Mean $T_{\\mathrm{mrt}}$ (°C)', fontsize=8.5)
    ax.set_title('Optimization Convergence (3 Seeds, Budget=50)', fontsize=9.2, fontweight='bold', pad=6)

    # Welch's t-test statistical annotation placed cleanly in open space
    stat_text = (
        "Welch's $t$-test (AL vs Random):\n"
        "$t = 0.760,\\; p = 0.514\\; (p > 0.05)$\n"
        "Direct GA achieves lowest $T_{\\mathrm{mrt}}$ ($42.62^\\circ\\mathrm{C}$)"
    )
    ax.text(0.18, 0.44, stat_text, transform=ax.transAxes, fontsize=6.2, va='center', ha='left',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#AAAAAA', alpha=0.92, lw=0.5))

    ax.legend(loc='upper right', fontsize=6.0, framealpha=0.92)
    ax.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout(pad=0.3)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig9_optimization_convergence.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig9_optimization_convergence.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig9_optimization_convergence.svg", bbox_inches='tight')
    plt.close()
    print("Figure 9 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig9()
