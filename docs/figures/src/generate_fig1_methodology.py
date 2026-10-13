#!/usr/bin/env python3
"""
Figure 1: Complete Methodology Workflow Block Diagram
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
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.titlesize'] = 11

def create_fig1():
    # Width: double-column (175 mm = 6.89 in), height: 3.8 in
    fig, ax = plt.subplots(figsize=(6.89, 3.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')

    # Okabe-Ito Palette & neutral backgrounds
    c_blue = '#0072B2'
    c_orange = '#E69F00'
    c_green = '#009E73'
    c_sky = '#56B4E9'
    c_vermil = '#D55E00'
    c_purple = '#CC79A7'
    c_grey = '#4D4D4D'
    box_bg = '#FAFAFA'

    # Six shaded pipeline groups
    groups = [
        {"x": 1.5, "w": 14.5, "title": "(1) Data Acquisition", "color": c_blue,
         "mods": "solaraeus.data\nmanifest.py",
         "items": ["Building LoD2 (Berlin)", "Canyon Heights (Chicago)", "Shared Blvd (London)", "DWD / NOAA / MetOffice", " Baumbestand & DEM"]},
        {"x": 18.0, "w": 14.5, "title": "(2) Preprocessing", "color": c_sky,
         "mods": "solaraeus.geometry\nsite_builder.py",
         "items": ["CRS Alignment (UTM)", "1.0 m Pedestrian Grid", "Albedo (α=0.15–0.20)", "Emissivity (ε=0.90–0.95)", "Terrain & Trees Mask"]},
        {"x": 34.5, "w": 15.5, "title": "(3) Physics Core", "color": c_green,
         "mods": "solaraeus.physics\nsolar_position / svf",
         "items": ["NOAA Solar Tracking", "Möller–Trumbore Rays", "Steyn 36-Azimuth SVF", "6-Flux Stefan–Boltzmann", "UTCI Polynomial"]},
        {"x": 52.0, "w": 15.0, "title": "(4) Acceleration", "color": c_orange,
         "mods": "solaraeus.gpu\ncupy_backend.py",
         "items": ["CPU FP64 Reference", "CUDA/CuPy Kernels", "Incremental Spatial Bound", "B_T(x) ≤ 0.50 K Check", ">98% Static Cell Reuse"]},
        {"x": 69.0, "w": 15.0, "title": "(5) Optimization", "color": c_purple,
         "mods": "solaraeus.optimizer\nalgorithms / problem",
         "items": ["Canopy Feasibility (x,y,θ)", "Random / Genetic Search", "Matérn-5/2 GP Surrogate", "Active Learning GP-LCB", "Full-Physics Verification"]},
        {"x": 86.0, "w": 12.5, "title": "(6) Outputs", "color": c_vermil,
         "mods": "results.raw\nstage_7_pipeline.py",
         "items": ["Baseline Tmrt / UTCI", "Optimized Canopy Field", "Cooling ΔTmrt Maps", "Replication Matrix", "Sensitivity Tornado"]}
    ]

    for g in groups:
        # Shaded group container
        rect = patches.FancyBboxPatch((g['x'], 6), g['w'], 40,
                                      boxstyle="round,pad=0.3,rounding_size=1.2",
                                      facecolor=box_bg, edgecolor=g['color'], linewidth=1.4)
        ax.add_patch(rect)
        
        # Header bar
        header_rect = patches.FancyBboxPatch((g['x'], 41.5), g['w'], 4.5,
                                             boxstyle="round,pad=0.2,rounding_size=1.0",
                                             facecolor=g['color'], edgecolor=g['color'], linewidth=1.0)
        ax.add_patch(header_rect)
        ax.text(g['x'] + g['w']/2, 43.75, g['title'], color='white',
                ha='center', va='center', fontsize=8.5, fontweight='bold')

        # Subtitle: Module name
        ax.text(g['x'] + g['w']/2, 38.5, g['mods'], color=c_grey,
                ha='center', va='center', fontsize=6.8, fontstyle='italic')

        # Line separator
        ax.plot([g['x'] + 1.0, g['x'] + g['w'] - 1.0], [35.5, 35.5], color='#D0D0D0', lw=0.7)

        # Bullet items inside group
        y_pos = 32.5
        for item in g['items']:
            ax.text(g['x'] + 1.2, y_pos, f"• {item}", color='#1A1A1A',
                    ha='left', va='center', fontsize=7.1)
            y_pos -= 5.5

    # Inter-stage arrows
    for i in range(len(groups) - 1):
        x_start = groups[i]['x'] + groups[i]['w']
        x_end = groups[i+1]['x']
        y_mid = 26.0
        ax.annotate('', xy=(x_end, y_mid), xytext=(x_start, y_mid),
                    arrowprops=dict(arrowstyle="-|>", color='#333333', lw=1.2, mutation_scale=10))

    # Optimization -> Physics core feedback arrow
    ax.annotate('', xy=(42.25, 6.0), xytext=(76.5, 6.0),
                arrowprops=dict(arrowstyle="-|>", color=c_purple, lw=1.3,
                                connectionstyle="arc3,rad=-0.22", mutation_scale=11, linestyle="--"))
    ax.text(59.5, 1.2, "Active Learning Proposed Design Feedback (Full-Physics Re-Evaluation)",
            color=c_purple, ha='center', va='center', fontsize=7.2, fontweight='bold')

    # Side Validation Box (Stages 3–4)
    val_rect = patches.FancyBboxPatch((34.5, 47.0), 32.5, 4.5,
                                      boxstyle="round,pad=0.2,rounding_size=0.8",
                                      facecolor='#F0F0F0', edgecolor=c_grey, linewidth=1.0, linestyle=":")
    ax.add_patch(val_rect)
    ax.text(50.75, 49.25, "Physical Validation & Error Bound Oracle (SOLWEIG Parity & Stefan–Boltzmann Bounds)",
            color='#222222', ha='center', va='center', fontsize=7.0, fontweight='bold')
    
    # Validation connections to Physics and Acceleration
    ax.annotate('', xy=(42.25, 46.0), xytext=(42.25, 47.0),
                arrowprops=dict(arrowstyle="->", color=c_grey, lw=0.9, linestyle=":"))
    ax.annotate('', xy=(59.5, 46.0), xytext=(59.5, 47.0),
                arrowprops=dict(arrowstyle="->", color=c_grey, lw=0.9, linestyle=":"))

    plt.tight_layout(pad=0.4)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig1_methodology_workflow.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig1_methodology_workflow.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig1_methodology_workflow.svg", bbox_inches='tight')
    plt.close()
    print("Figure 1 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig1()
