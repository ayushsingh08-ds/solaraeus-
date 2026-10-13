#!/usr/bin/env python3
"""
Figure 5: Empirical Study Areas (Berlin, Chicago, London)
Generated for Earth Science Informatics (Springer)
Conforms to: Times New Roman, Okabe-Ito colourblind-safe palette, vector PDF/SVG + 300 DPI PNG
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

# Configure publication typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.size'] = 9

def draw_north_arrow(ax, x, y, size=14.0):
    """Draws a clean, publication-grade cartographic North arrow."""
    ax.annotate('N', xy=(x, y + size), xytext=(x, y),
                ha='center', va='bottom', fontsize=8.5, fontweight='bold',
                arrowprops=dict(facecolor='black', edgecolor='black', width=1.5, headwidth=5.5))

def draw_scale_bar(ax, x, y, length_m=50.0):
    """Draws a cartographic 50 m scale bar with tick marks and label."""
    ax.plot([x, x + length_m], [y, y], color='black', lw=1.8)
    ax.plot([x, x], [y - 2.5, y + 2.5], color='black', lw=1.2)
    ax.plot([x + length_m, x + length_m], [y - 2.5, y + 2.5], color='black', lw=1.2)
    ax.plot([x + length_m/2, x + length_m/2], [y - 1.5, y + 1.5], color='black', lw=1.0)
    ax.text(x + length_m/2, y + 3.5, f"{int(length_m)} m", ha='center', va='bottom', fontsize=7.2, fontweight='bold')

def create_fig5():
    # Width: double-column (175 mm = 6.89 in), height: 3.4 in
    fig, axes = plt.subplots(1, 3, figsize=(6.89, 3.4), dpi=300)

    # Palette
    c_street = '#F5F5F5'
    c_bldg_edge = '#222222'
    c_tree = '#009E73'
    c_canopy = '#E69F00'
    c_core = '#56B4E9'

    # (a) BERLIN
    ax = axes[0]
    ax.set_title("(a) Berlin (Primary Site)\nFriedrichstraße Corridor", fontsize=8.5, fontweight='bold', pad=4)
    ax.set_xlim(-120, 120)
    ax.set_ylim(-100, 100)
    ax.set_facecolor('#EAEAEA')

    # Street corridor polygon
    ax.fill_between([-12, 12], -100, 100, color=c_street, ec='#CCCCCC', lw=0.6)
    # Core pedestrian evaluation box
    core_rect = patches.Rectangle((-10, -40), 20, 80, fill=True, facecolor=c_core, alpha=0.25,
                                  edgecolor=c_core, lw=1.0, linestyle='--')
    ax.add_patch(core_rect)

    # Berlin Buildings (8 perimeter blocks, heights 21.5m to 24.0m)
    blocks = [
        (-110, -12, -90, -45, 22.0), (-110, -12, -35, 10, 23.5),
        (-110, -12, 20, 55, 21.5), (-110, -12, 65, 95, 24.0),
        (12, 110, -90, -45, 22.5), (12, 110, -35, 10, 24.0),
        (12, 110, 20, 55, 22.0), (12, 110, 65, 95, 23.0)
    ]
    for xmin, xmax, ymin, ymax, h in blocks:
        rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                 facecolor='#D0D0D0', edgecolor=c_bldg_edge, lw=0.9)
        ax.add_patch(rect)
        ax.text((xmin + xmax)/2, (ymin + ymax)/2, f"{h:.1f}m", ha='center', va='center', fontsize=6.2, color='#444444')

    # 16 Tilia cordata trees
    y_trees = [-75, -55, -25, -5, 25, 45, 75, 90]
    for y in y_trees:
        for x in [-10.5, 10.5]:
            circ = patches.Circle((x, y), 3.5, facecolor=c_tree, alpha=0.65, edgecolor='#006644', lw=0.7)
            ax.add_patch(circ)

    # 2 Discovered Canopies
    canopy1 = patches.Rectangle((-1.73 - 1.95, 34.06 - 3.43), 3.90, 6.87, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    canopy2 = patches.Rectangle((1.92 - 1.68, -26.47 - 3.17), 3.37, 6.35, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    ax.add_patch(canopy1)
    ax.add_patch(canopy2)

    # Labels & Cartography
    draw_north_arrow(ax, 95, 65, 16)
    draw_scale_bar(ax, -100, -88, 50)
    ax.text(0, -96, "EPSG:25833 (UTM 33N)\nDatum: DHHN2016 (z=34.2m)", ha='center', va='bottom', fontsize=5.8,
            bbox=dict(boxstyle="square,pad=0.2", facecolor='white', alpha=0.85, lw=0.4))

    # (b) CHICAGO
    ax = axes[1]
    ax.set_title("(b) Chicago (Replication Site)\nS LaSalle Financial Canyon", fontsize=8.5, fontweight='bold', pad=4)
    ax.set_xlim(-120, 120)
    ax.set_ylim(-100, 100)
    ax.set_facecolor('#EAEAEA')

    # Street corridor
    ax.fill_between([-14, 14], -100, 100, color=c_street, ec='#CCCCCC', lw=0.6)
    core_rect = patches.Rectangle((-10, -40), 20, 80, fill=True, facecolor=c_core, alpha=0.25,
                                  edgecolor=c_core, lw=1.0, linestyle='--')
    ax.add_patch(core_rect)

    # Chicago Towers (heights 48m to 110m)
    towers = [
        (-115, -14, -90, -30, 55.0), (-115, -14, -20, 35, 110.0), (-115, -14, 45, 95, 68.0),
        (14, 115, -90, -30, 48.0), (14, 115, -20, 35, 85.0), (14, 115, 45, 95, 62.0)
    ]
    for xmin, xmax, ymin, ymax, h in towers:
        rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                 facecolor='#B8B8B8', edgecolor=c_bldg_edge, lw=0.9)
        ax.add_patch(rect)
        ax.text((xmin + xmax)/2, (ymin + ymax)/2, f"{int(h)}m", ha='center', va='center', fontsize=6.2, color='#222222', fontweight='bold')

    # 8 Gleditsia triacanthos trees
    for y in [-60, -10, 20, 70]:
        for x in [-12.5, 12.5]:
            circ = patches.Circle((x, y), 2.0, facecolor=c_tree, alpha=0.65, edgecolor='#006644', lw=0.7)
            ax.add_patch(circ)

    # Canopies
    canopy1_c = patches.Rectangle((-1.73 - 1.95, 34.06 - 3.43), 3.90, 6.87, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    canopy2_c = patches.Rectangle((1.92 - 1.68, -26.47 - 3.17), 3.37, 6.35, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    ax.add_patch(canopy1_c)
    ax.add_patch(canopy2_c)

    draw_north_arrow(ax, 95, 65, 16)
    draw_scale_bar(ax, -100, -88, 50)
    ax.text(0, -96, "EPSG:32616 (UTM 16N)\nDatum: NAVD88 (z=181.5m)", ha='center', va='bottom', fontsize=5.8,
            bbox=dict(boxstyle="square,pad=0.2", facecolor='white', alpha=0.85, lw=0.4))

    # (c) LONDON
    ax = axes[2]
    ax.set_title("(c) London (Replication Site)\nExhibition Road Boulevard", fontsize=8.5, fontweight='bold', pad=4)
    ax.set_xlim(-120, 120)
    ax.set_ylim(-100, 100)
    ax.set_facecolor('#EAEAEA')

    # Boulevard
    ax.fill_between([-16, 16], -100, 100, color=c_street, ec='#CCCCCC', lw=0.6)
    core_rect = patches.Rectangle((-10, -40), 20, 80, fill=True, facecolor=c_core, alpha=0.25,
                                  edgecolor=c_core, lw=1.0, linestyle='--')
    ax.add_patch(core_rect)

    # London Victorian Blocks (heights 22m to 32m)
    blocks_lon = [
        (-110, -16, -90, -35, 26.0), (-110, -16, -25, 35, 32.0), (-110, -16, 45, 95, 24.0),
        (16, 110, -90, -35, 28.0), (16, 110, -25, 35, 30.0), (16, 110, 45, 95, 22.0)
    ]
    for xmin, xmax, ymin, ymax, h in blocks_lon:
        rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                                 facecolor='#C8C8C8', edgecolor=c_bldg_edge, lw=0.9)
        ax.add_patch(rect)
        ax.text((xmin + xmax)/2, (ymin + ymax)/2, f"{int(h)}m", ha='center', va='center', fontsize=6.2, color='#444444')

    # 14 Platanus x hispanica trees
    for y in [-70, -45, -20, 5, 30, 55, 80]:
        for x in [-13.0, 13.0]:
            circ = patches.Circle((x, y), 4.0, facecolor=c_tree, alpha=0.65, edgecolor='#006644', lw=0.7)
            ax.add_patch(circ)

    # Canopies
    canopy1_l = patches.Rectangle((-1.73 - 1.95, 34.06 - 3.43), 3.90, 6.87, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    canopy2_l = patches.Rectangle((1.92 - 1.68, -26.47 - 3.17), 3.37, 6.35, facecolor=c_canopy, edgecolor='#995500', lw=1.1)
    ax.add_patch(canopy1_l)
    ax.add_patch(canopy2_l)

    draw_north_arrow(ax, 95, 65, 16)
    draw_scale_bar(ax, -100, -88, 50)
    ax.text(0, -96, "EPSG:27700 (BNG)\nDatum: ODN (z=21.0m)", ha='center', va='bottom', fontsize=5.8,
            bbox=dict(boxstyle="square,pad=0.2", facecolor='white', alpha=0.85, lw=0.4))

    for ax in axes:
        ax.set_aspect('equal')
        ax.set_xticks([-100, -50, 0, 50, 100])
        ax.set_yticks([-100, -50, 0, 50, 100])
        ax.tick_params(labelsize=6.5)
        ax.set_xlabel("Local X (m)", fontsize=7.2)
    axes[0].set_ylabel("Local Y (m)", fontsize=7.2)

    plt.tight_layout(pad=0.4)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig5_study_areas.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig5_study_areas.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig5_study_areas.svg", bbox_inches='tight')
    plt.close()
    print("Figure 5 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig5()
