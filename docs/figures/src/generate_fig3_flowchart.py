#!/usr/bin/env python3
"""
Figure 3: Incremental Update Flowchart (Proved vs Empirical Parts)
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

def create_fig3():
    # Width: double-column (175 mm = 6.89 in), height: 4.8 in
    fig, ax = plt.subplots(figsize=(6.89, 4.8), dpi=300)
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

    # Legend at top: Proved vs Empirical
    leg_x = 18.0
    leg_y = 70.0
    # Proved patch
    rect_pr = patches.Rectangle((leg_x, leg_y), 3.5, 2.2, facecolor='#E6F2FF', edgecolor=c_blue, linewidth=1.2)
    ax.add_patch(rect_pr)
    ax.text(leg_x + 4.5, leg_y + 1.1, "Mathematically Proved Stage (Stefan–Boltzmann Error Certificate)",
            color='#111111', ha='left', va='center', fontsize=7.2, fontweight='bold')

    # Empirical patch
    rect_em = patches.Rectangle((leg_x + 42.0, leg_y), 3.5, 2.2, facecolor='#FFF5E6', edgecolor=c_orange, linewidth=1.2, linestyle='--')
    ax.add_patch(rect_em)
    ax.text(leg_x + 46.5, leg_y + 1.1, "Empirically Calibrated Stage (Ray Discretization & Morphology)",
            color='#111111', ha='left', va='center', fontsize=7.2, fontweight='bold')

    # Step 1: Intervention Added (Top Center)
    step1 = patches.FancyBboxPatch((32.0, 58.0), 36.0, 8.5, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#FFF5E6', edgecolor=c_orange, linewidth=1.3, linestyle='--')
    ax.add_patch(step1)
    ax.text(50.0, 63.8, "1. Localized Intervention Introduced", ha='center', va='center', fontsize=8.2, fontweight='bold')
    ax.text(50.0, 60.2, "Canopy mesh $\\Delta\\mathcal{M}$: position $(x,y)$, dimensions $(L,W)$, height $h$, heading $\\theta$",
            ha='center', va='center', fontsize=7.0, color=c_grey)

    # Arrow 1 -> 2
    ax.annotate('', xy=(50.0, 52.0), xytext=(50.0, 58.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))

    # Step 2: Affected-Cell Identification (Marked Zone)
    step2 = patches.FancyBboxPatch((15.0, 41.5), 70.0, 10.5, boxstyle="round,pad=0.2,rounding_size=1.0",
                                   facecolor='#E6F2FF', edgecolor=c_blue, linewidth=1.3)
    ax.add_patch(step2)
    ax.text(50.0, 49.3, "2. Conservative Affected-Region Identification (Proved Soundness)",
            ha='center', va='center', fontsize=8.2, fontweight='bold', color=c_blue)
    ax.text(50.0, 46.0, "Dilated Solar Projection Cone: $C_{\\mathrm{cone}} = \\mathrm{Footprint} + \\{ -\\frac{h - z_{\\mathrm{ped}}}{\\tan \\theta_{\\mathrm{alt}}} \\vec{s}_{xy} \\} + B(r_{\\mathrm{tol}})$",
            ha='center', va='center', fontsize=7.1)
    ax.text(50.0, 43.2, "Solid-Angle Horizon Radius: $R_{\\mathrm{svf}} = \\sqrt{ \\frac{H_{\\mathrm{canopy}} \\cdot W_{\\mathrm{canopy}}}{2\\pi \\Delta\\Psi_{\\max}} }$; Marked set $A = C_{\\mathrm{cone}} \\cup B(R_{\\mathrm{svf}})$",
            ha='center', va='center', fontsize=6.8, color=c_grey)

    # Arrows 2 -> 3A & 3B
    ax.annotate('', xy=(30.0, 35.0), xytext=(38.0, 41.5),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.annotate('', xy=(70.0, 35.0), xytext=(62.0, 41.5),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))

    # Step 3A: Recompute Affected Cells
    step3a = patches.FancyBboxPatch((10.0, 26.0), 38.0, 9.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                    facecolor='#FFF5E6', edgecolor=c_orange, linewidth=1.2, linestyle='--')
    ax.add_patch(step3a)
    ax.text(29.0, 32.5, "3a. Recompute Affected Cells ($x \\in A$)", ha='center', va='center', fontsize=7.8, fontweight='bold')
    ax.text(29.0, 29.5, "Möller–Trumbore shadow ray-tracing\nSteyn SVF horizon updates on $< 2.0\\%$ of cells",
            ha='center', va='center', fontsize=6.8, color='#222222')

    # Step 3B: Reuse Remaining Cells
    step3b = patches.FancyBboxPatch((52.0, 26.0), 38.0, 9.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                    facecolor='#E6F2FF', edgecolor=c_blue, linewidth=1.2)
    ax.add_patch(step3b)
    ax.text(71.0, 32.5, "3b. Reuse Unaffected Cells ($x \\notin A$)", ha='center', va='center', fontsize=7.8, fontweight='bold', color=c_blue)
    ax.text(71.0, 29.5, "Direct memory reuse from baseline arrays\n$> 98.0\\%$ static cell state preserved directly",
            ha='center', va='center', fontsize=6.8, color='#222222')

    # Arrows 3A & 3B -> 4
    ax.annotate('', xy=(45.0, 20.0), xytext=(35.0, 26.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))
    ax.annotate('', xy=(55.0, 20.0), xytext=(65.0, 26.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.2))

    # Step 4: Decision Diamond / Check
    # Diamond centered at (50, 15)
    diamond = patches.Polygon([[50.0, 20.0], [66.0, 15.0], [50.0, 10.0], [34.0, 15.0]],
                              facecolor='#E6F2FF', edgecolor=c_blue, linewidth=1.4)
    ax.add_patch(diamond)
    ax.text(50.0, 16.2, "Error Certificate Check", ha='center', va='center', fontsize=7.8, fontweight='bold', color=c_blue)
    ax.text(50.0, 13.8, "$B_T(x) \\leq \\varepsilon_T = 0.50\\,\\mathrm{K}$ ?", ha='center', va='center', fontsize=7.4)

    # Pass branch -> Step 5 (Left/Bottom)
    ax.annotate('', xy=(28.0, 7.5), xytext=(37.0, 12.5),
                arrowprops=dict(arrowstyle="-|>", color=c_green, lw=1.3))
    ax.text(28.0, 11.5, "PASS (Sound)", color=c_green, ha='center', va='center', fontsize=7.5, fontweight='bold')

    step5_pass = patches.FancyBboxPatch((8.0, 2.0), 38.0, 7.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        facecolor='#E6F9F0', edgecolor=c_green, linewidth=1.3)
    ax.add_patch(step5_pass)
    ax.text(27.0, 6.5, "5a. Emit Certified Incremental State", ha='center', va='center', fontsize=7.8, fontweight='bold', color=c_green)
    ax.text(27.0, 3.8, "Combine reused + updated fields; latency $11.4\\text{--}18.2\\,\\mathrm{ms}$",
            ha='center', va='center', fontsize=6.8, color='#222222')

    # Fail branch -> Step 5 Fallback (Right/Bottom)
    ax.annotate('', xy=(72.0, 7.5), xytext=(63.0, 12.5),
                arrowprops=dict(arrowstyle="-|>", color=c_vermil, lw=1.3))
    ax.text(72.0, 11.5, "FAIL (Low Sun / Bound Exceeded)", color=c_vermil, ha='center', va='center', fontsize=7.5, fontweight='bold')

    step5_fail = patches.FancyBboxPatch((54.0, 2.0), 38.0, 7.0, boxstyle="round,pad=0.2,rounding_size=1.0",
                                        facecolor='#FFF0F0', edgecolor=c_vermil, linewidth=1.3)
    ax.add_patch(step5_fail)
    ax.text(73.0, 6.5, "5b. Fallback to Full Recomputation", ha='center', va='center', fontsize=7.8, fontweight='bold', color=c_vermil)
    ax.text(73.0, 3.8, "Full domain ray-tracing ($0.08\\text{--}2.03\\,\\mathrm{s}$); zero certificate failure",
            ha='center', va='center', fontsize=6.8, color='#222222')

    plt.tight_layout(pad=0.3)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig3_incremental_flowchart.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig3_incremental_flowchart.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig3_incremental_flowchart.svg", bbox_inches='tight')
    plt.close()
    print("Figure 3 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig3()
