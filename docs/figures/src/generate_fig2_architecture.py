#!/usr/bin/env python3
"""
Figure 2: System Architecture & Module Hierarchy
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

def create_fig2():
    # Width: double-column (175 mm = 6.89 in), height: 4.4 in
    fig, ax = plt.subplots(figsize=(6.89, 4.4), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis('off')

    # Okabe-Ito Palette
    c_blue = '#0072B2'
    c_orange = '#E69F00'
    c_green = '#009E73'
    c_sky = '#56B4E9'
    c_purple = '#CC79A7'
    c_grey = '#4D4D4D'
    c_border = '#333333'

    def draw_module(x, y, w, h, title, subtitle, color, items=None):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.0",
                                      facecolor='#FCFCFC', edgecolor=color, linewidth=1.3)
        ax.add_patch(rect)
        hdr = patches.FancyBboxPatch((x, y + h - 3.8), w, 3.8, boxstyle="round,pad=0.1,rounding_size=0.8",
                                     facecolor=color, edgecolor=color, linewidth=0.8)
        ax.add_patch(hdr)
        ax.text(x + w/2, y + h - 1.9, title, color='white', ha='center', va='center', fontsize=8.0, fontweight='bold')
        ax.text(x + w/2, y + h - 5.4, subtitle, color=c_grey, ha='center', va='center', fontsize=6.5, fontstyle='italic')
        if items:
            yp = y + h - 8.2
            for it in items:
                ax.text(x + 1.2, yp, f"• {it}", color='#1A1A1A', ha='left', va='center', fontsize=6.8)
                yp -= 3.2

    # Layer 1: Data & Config Layer (Top)
    draw_module(2.0, 52.0, 28.0, 15.0, "Data Ingestion & Contracts", "data/raw/ & data/processed/", c_blue,
                ["LoD2 CityGML & OSM (GeoJSON)", "DWD / NOAA 24h Diurnal (CSV)", "Baumbestand Tree Cadaster", "CRS Datum: EPSG:25833/32616"])

    draw_module(36.0, 52.0, 28.0, 15.0, "Geometry & Scene Models", "src/solaraeus/extensions/ & core/", c_sky,
                ["PedestrianGrid (1.0m, z=1.1m)", "TriangleMesh (Vertices/Faces)", "TreeModel (Crown r, height h, τ)", "MaterialProperties (α, ε)"])

    draw_module(70.0, 52.0, 28.0, 15.0, "Incremental Marking & Bounds", "src/solaraeus/incremental/", c_orange,
                ["AffectedRegionFinder (Dilated Cone)", "ErrorBounds (Stefan–Boltzmann B_T)", "MutationAudit (Mesh Hash)", "StateCache (NumPy Arrays)"])

    # Data arrows between top modules
    ax.annotate('', xy=(36.0, 59.5), xytext=(30.0, 59.5),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(33.0, 61.2, "GeoDataFrame\n& Weather CSV", color='#222222', ha='center', va='bottom', fontsize=5.8)

    ax.annotate('', xy=(70.0, 59.5), xytext=(64.0, 59.5),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(67.0, 61.2, "Mesh Delta\nΔM (verts)", color='#222222', ha='center', va='bottom', fontsize=5.8)

    # Layer 2: Core Physics & Dual Computational Backends (Middle)
    draw_module(2.0, 28.0, 44.0, 18.0, "Biometeorological Physics Engine", "src/solaraeus/physics/", c_green,
                ["NOAA Astronomical Solar Vector (Alt θ_alt, Az φ_az)",
                 "Steyn (1980) Sky View Factor (36-Azimuth Horizon March)",
                 "Möller–Trumbore Ray-Triangle Shadow Occlusion",
                 "6-Flux Shortwave & Longwave Radiation Cylinder",
                 "Stefan–Boltzmann Tmrt & 6th-Order UTCI Polynomial"])

    draw_module(52.0, 28.0, 46.0, 18.0, "Dual-Backend Acceleration Engines", "src/solaraeus/reference/ & backends/", c_purple,
                ["CPU Reference Backend (Vectorized NumPy/SciPy FP64)",
                 "CUDA GPU Engine (CuPy Custom Raw Kernels in VRAM)",
                 "FP64 Shadow Mask Kernel (rtx_shadow_mask_kernel)",
                 "FP64 Horizon SVF Kernel (rtx_svf_horizon_kernel)",
                 "Numerical Parity Assertion (max |ΔTmrt| < 0.05 K)"])

    # Connections between layers
    ax.annotate('', xy=(24.0, 46.0), xytext=(24.0, 52.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(25.0, 49.0, "Grid & Solar Vectors", color='#222222', ha='left', va='center', fontsize=6.0)

    ax.annotate('', xy=(75.0, 46.0), xytext=(75.0, 52.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(76.0, 49.0, "Affected Mask\nA(u,v) $\\in$ {0,1}", color='#222222', ha='left', va='center', fontsize=6.0)

    ax.annotate('', xy=(52.0, 37.0), xytext=(46.0, 37.0),
                arrowprops=dict(arrowstyle="<|-|>", color=c_border, lw=1.1))
    ax.text(49.0, 39.0, "Parity\nOracle", color='#222222', ha='center', va='bottom', fontsize=6.0)

    # Layer 3: Optimization & Results Layer (Bottom)
    draw_module(2.0, 3.0, 46.0, 19.0, "Active Learning & Placement Optimizer", "src/solaraeus/optimizer/", '#D55E00',
                ["Canopy Feasibility Screening (Non-overlap, Setbacks, Budget ≤ 50m²)",
                 "Random Search (Uniform parameter exploration)",
                 "Genetic Algorithm (Tournament selection, Gaussian mutation)",
                 "Gaussian Process Surrogate (Matérn-5/2 Covariance Kernel)",
                 "GP-LCB Active Learning Acquisition & Truth Verification"])

    draw_module(54.0, 3.0, 44.0, 19.0, "Benchmark & Evaluation Pipeline", "benchmarks/ & results/raw/", '#333333',
                ["Stage 7 Master Pipeline (run_stage_7_pipeline.py)",
                 "Multi-City Morphological Replication (Berlin, Chicago, London)",
                 "7-Scenario Sensitivity Analysis (Trees, Wind, DNI, Height)",
                 "Geometric Shadow Consistency Verification (Analytic vs Ray)",
                 "Output Arrays (*.npy, 48,000 cells) & Publication Maps"])

    # Connections between middle and bottom
    ax.annotate('', xy=(25.0, 22.0), xytext=(25.0, 28.0),
                arrowprops=dict(arrowstyle="<|-|>", color='#D55E00', lw=1.2, linestyle="--"))
    ax.text(26.0, 25.0, "Physics Function Eval f(θ) = Mean Tmrt (11.4 ms)",
            color='#D55E00', ha='left', va='center', fontsize=6.2, fontweight='bold')

    ax.annotate('', xy=(75.0, 22.0), xytext=(75.0, 28.0),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(76.0, 25.0, "Tmrt, UTCI, SVF Arrays\n(shape: 200x240)", color='#222222', ha='left', va='center', fontsize=6.0)

    ax.annotate('', xy=(54.0, 12.5), xytext=(48.0, 12.5),
                arrowprops=dict(arrowstyle="-|>", color=c_border, lw=1.1))
    ax.text(51.0, 14.5, "Best Design\nθ* = [x,y,w,L,h]", color='#222222', ha='center', va='bottom', fontsize=6.0)

    plt.tight_layout(pad=0.4)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig2_system_architecture.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig2_system_architecture.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig2_system_architecture.svg", bbox_inches='tight')
    plt.close()
    print("Figure 2 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig2()
