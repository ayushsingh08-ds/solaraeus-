#!/usr/bin/env python3
"""
Figure 4: Active Learning & Multi-Method Optimization Loop
Generated for Earth Science Informatics (Springer)
Conforms to: Times New Roman, Okabe-Ito colourblind-safe palette, vector PDF/SVG + 300 DPI PNG
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Configure publication typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.size'] = 10

def create_fig4():
    # Width: double-column (175 mm = 6.89 in), height: 4.6 in
    fig, ax = plt.subplots(figsize=(6.89, 4.6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 75)
    ax.axis('off')

    # Okabe-Ito Palette
    c_blue = '#0072B2'
    c_orange = '#E69F00'
    c_green = '#009E73'
    c_vermil = '#D55E00'
    c_purple = '#CC79A7'
    c_grey = '#4D4D4D'
    c_border = '#222222'

    # Step 1: Initial Sample (Top Left)
    step1 = patches.FancyBboxPatch((4.0, 56.0), 42.0, 14.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FCFCFC', edgecolor=c_blue, linewidth=1.3)
    ax.add_patch(step1)
    hdr1 = patches.FancyBboxPatch((4.0, 66.5), 42.0, 3.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                  facecolor=c_blue, edgecolor=c_blue)
    ax.add_patch(hdr1)
    ax.text(25.0, 68.2, "1. Initial Design Sampling (LHS)", color='white', ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(25.0, 63.5, "Latin Hypercube Sampling ($N_{\\mathrm{init}} = 15$ points in $D=12$ dimensions)\nGeometric filter: Area $\\leq 50\\,\\mathrm{m}^2$, non-overlap, $1\\,\\mathrm{m}$ facade setback",
            ha='center', va='center', fontsize=6.8, color='#1A1A1A')

    # Arrow 1 -> 2
    ax.annotate('', xy=(54.0, 63.0), xytext=(46.0, 63.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.text(50.0, 64.5, "15 Vectors", color=c_grey, ha='center', va='bottom', fontsize=6.2)

    # Step 2: Initial Physics Eval (Top Right)
    step2 = patches.FancyBboxPatch((54.0, 56.0), 42.0, 14.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FCFCFC', edgecolor=c_green, linewidth=1.3)
    ax.add_patch(step2)
    hdr2 = patches.FancyBboxPatch((54.0, 66.5), 42.0, 3.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                  facecolor=c_green, edgecolor=c_green)
    ax.add_patch(hdr2)
    ax.text(75.0, 68.2, "2. Initial Physics Simulation", color='white', ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(75.0, 63.5, "Parallel GPU ray-tracing & Stefan–Boltzmann balance\nEvaluate objective: $y_i = f(\\theta_i) = \\mathrm{Mean}\\; T_{\\mathrm{mrt}}$ ($25\\,\\mathrm{ms}$/eval)",
            ha='center', va='center', fontsize=6.8, color='#1A1A1A')

    # Arrow 2 -> 3
    ax.annotate('', xy=(75.0, 48.0), xytext=(75.0, 56.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.text(76.5, 52.0, "Dataset $D_{15} = \\{(\\theta_i, y_i)\\}$", color=c_grey, ha='left', va='center', fontsize=6.2)

    # Step 3: Train Surrogate (Middle Right)
    step3 = patches.FancyBboxPatch((54.0, 34.0), 42.0, 14.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FCFCFC', edgecolor=c_purple, linewidth=1.3)
    ax.add_patch(step3)
    hdr3 = patches.FancyBboxPatch((54.0, 44.5), 42.0, 3.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                  facecolor=c_purple, edgecolor=c_purple)
    ax.add_patch(hdr3)
    ax.text(75.0, 46.2, "3. Gaussian Process Surrogate Training", color='white', ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(75.0, 41.0, "Fit Gaussian Process Regressor with Matérn-5/2 kernel:\n$k(x, x') = \\sigma_f^2 (1 + \\sqrt{5}d + \\frac{5}{3}d^2) \\exp(-\\sqrt{5}d)$\nYields posterior mean $\\mu(\\theta)$ and uncertainty $\\sigma(\\theta)$",
            ha='center', va='center', fontsize=6.6, color='#1A1A1A')

    # Arrow 3 -> 4
    ax.annotate('', xy=(46.0, 41.0), xytext=(54.0, 41.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.text(50.0, 42.5, "$\\mu(\\theta), \\sigma(\\theta)$", color=c_grey, ha='center', va='bottom', fontsize=6.5)

    # Step 4: Propose Next Design via Acquisition (Middle Left)
    step4 = patches.FancyBboxPatch((4.0, 34.0), 42.0, 14.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FCFCFC', edgecolor=c_orange, linewidth=1.3)
    ax.add_patch(step4)
    hdr4 = patches.FancyBboxPatch((4.0, 44.5), 42.0, 3.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                  facecolor=c_orange, edgecolor=c_orange)
    ax.add_patch(hdr4)
    ax.text(25.0, 46.2, "4. Active Learning Acquisition (GP-LCB)", color='white', ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(25.0, 41.0, "Maximize Lower Confidence Bound over feasible candidates:\n$\\alpha_{\\mathrm{LCB}}(\\theta) = \\mu(\\theta) - \\kappa \\sigma(\\theta)$  with $\\kappa = 1.96$\nSelect $\\theta_{\\mathrm{next}} = \\arg\\min \\alpha_{\\mathrm{LCB}}(\\theta)$",
            ha='center', va='center', fontsize=6.6, color='#1A1A1A')

    # Arrow 4 -> 5
    ax.annotate('', xy=(25.0, 26.0), xytext=(25.0, 34.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.text(26.5, 30.0, "Proposed $\\theta_{\\mathrm{next}}$", color=c_grey, ha='left', va='center', fontsize=6.5)

    # Step 5: GPU Incremental Simulation (Bottom Left)
    step5 = patches.FancyBboxPatch((4.0, 12.0), 42.0, 14.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FCFCFC', edgecolor=c_green, linewidth=1.3)
    ax.add_patch(step5)
    hdr5 = patches.FancyBboxPatch((4.0, 22.5), 42.0, 3.5, boxstyle="round,pad=0.1,rounding_size=0.8",
                                  facecolor=c_green, edgecolor=c_green)
    ax.add_patch(hdr5)
    ax.text(25.0, 24.2, "5. GPU Incremental Truth Evaluation", color='white', ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(25.0, 19.0, "Execute certified incremental GPU kernel ($11.4\\text{--}18.2\\,\\mathrm{ms}$)\nCompute actual microclimatic performance $y_{\\mathrm{next}} = f(\\theta_{\\mathrm{next}})$\nAugment dataset: $D_{t+1} \\leftarrow D_t \\cup \\{(\\theta_{\\mathrm{next}}, y_{\\mathrm{next}})\\}$",
            ha='center', va='center', fontsize=6.6, color='#1A1A1A')

    # Feedback Arrow from Step 5 -> Step 3
    ax.annotate('', xy=(54.0, 38.0), xytext=(46.0, 19.0),
                arrowprops=dict(arrowstyle="-|>", color=c_purple, lw=1.2,
                                connectionstyle="arc3,rad=-0.15", linestyle="--"))
    ax.text(54.0, 24.0, "Refit GP on $D_{t+1}$", color=c_purple, ha='left', va='center', fontsize=6.5, fontstyle='italic')

    # Step 6: Budget Check Diamond
    diamond = patches.Polygon([[75.0, 26.0], [86.0, 19.0], [75.0, 12.0], [64.0, 19.0]],
                              facecolor='#E6F2FF', edgecolor=c_blue, linewidth=1.3)
    ax.add_patch(diamond)
    ax.text(75.0, 20.2, "Budget Reached?", ha='center', va='center', fontsize=7.2, fontweight='bold', color=c_blue)
    ax.text(75.0, 17.5, "$N \\geq 50$ Evals?", ha='center', va='center', fontsize=6.8)

    # Arrow 5 -> Diamond
    ax.annotate('', xy=(64.0, 19.0), xytext=(46.0, 19.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))

    # Diamond "No" branch back to Step 4
    ax.annotate('', xy=(25.0, 34.0), xytext=(75.0, 26.0),
                arrowprops=dict(arrowstyle="-|>", color=c_orange, lw=1.1,
                                connectionstyle="arc3,rad=0.25", linestyle=":"))
    ax.text(50.0, 29.5, "No: Continue Loop ($t \\leftarrow t + 1$)", color=c_orange, ha='center', va='center', fontsize=6.5)

    # Diamond "Yes" branch -> Step 7
    ax.annotate('', xy=(75.0, 7.5), xytext=(75.0, 12.0),
                arrowprops=dict(arrowstyle="-|>", color=c_green, lw=1.3))
    ax.text(76.5, 9.8, "Yes", color=c_green, ha='left', va='center', fontsize=7.2, fontweight='bold')

    # Step 7: Final Verification Box (Bottom Right)
    step7 = patches.FancyBboxPatch((52.0, 0.8), 46.0, 6.7, boxstyle="round,pad=0.2,rounding_size=0.8",
                                   facecolor='#E6F9F0', edgecolor=c_green, linewidth=1.3)
    ax.add_patch(step7)
    ax.text(75.0, 5.2, "6. Full-Physics Verification of Best Design", ha='center', va='center', fontsize=7.6, fontweight='bold', color=c_green)
    ax.text(75.0, 2.5, "Golden CPU FP64 re-evaluation of optimal candidate $\\theta^*$; Zero surrogate bias in reporting",
            ha='center', va='center', fontsize=6.5, color='#1A1A1A')

    plt.tight_layout(pad=0.3)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig4_optimization_loop.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig4_optimization_loop.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig4_optimization_loop.svg", bbox_inches='tight')
    plt.close()
    print("Figure 4 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig4()
