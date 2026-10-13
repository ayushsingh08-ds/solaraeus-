#!/usr/bin/env python3
"""
Figure 10: Before/After Microclimatic Spatial Distribution Maps (Berlin Friedrichstraße)
Generated for Earth Science Informatics (Springer)
Conforms to: Times New Roman, Okabe-Ito colourblind-safe palette, vector PDF/SVG + 300 DPI PNG
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

# Publication typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif', 'Liberation Serif']
plt.rcParams['mathtext.fontset'] = 'stix'
plt.rcParams['font.size'] = 9

def create_fig10():
    # Load actual Stage 7 computed arrays (shape: 200, 240, 1m resolution)
    b_tmrt = np.load("results/raw/stage_7/berlin_baseline_tmrt.npy")
    o_tmrt = np.load("results/raw/stage_7/berlin_optimised_tmrt.npy")
    d_tmrt = np.load("results/raw/stage_7/berlin_delta_tmrt.npy")

    # Zoom in to the street canyon corridor for maximum visual clarity:
    # Full domain is x in [-120, 120] (indices 0 to 239), y in [-100, 100] (indices 0 to 199)
    # Street corridor is centered at x=120 (+/- 35m -> indices 85 to 155), y in [-60, 60] (indices 40 to 160)
    x_slice = slice(85, 155)
    y_slice = slice(40, 160)
    extent = [-35, 35, -60, 60]

    b_sub = b_tmrt[y_slice, x_slice]
    o_sub = o_tmrt[y_slice, x_slice]
    d_sub = d_tmrt[y_slice, x_slice]

    from mpl_toolkits.axes_grid1 import make_axes_locatable

    # Width: double-column (175 mm = 6.89 in), height: 3.2 in
    fig, axes = plt.subplots(1, 3, figsize=(6.89, 3.2), dpi=300)

    # Panels 1 & 2 share thermal colormap (inferno, 32 to 47 °C)
    vmin_t, vmax_t = 32.0, 47.0
    cmap_t = 'inferno'

    # (a) Baseline Tmrt
    im0 = axes[0].imshow(b_sub, origin='lower', extent=extent, cmap=cmap_t, vmin=vmin_t, vmax=vmax_t)
    axes[0].set_title(r"(a) Baseline $T_{\mathrm{mrt}}$" + "\n(No Canopies)", fontsize=8.2, fontweight='bold', pad=4)
    axes[0].set_ylabel("Local Y (m)", fontsize=7.8)

    # (b) Optimised Tmrt
    im1 = axes[1].imshow(o_sub, origin='lower', extent=extent, cmap=cmap_t, vmin=vmin_t, vmax=vmax_t)
    axes[1].set_title(r"(b) Optimised $T_{\mathrm{mrt}}$" + "\n(Dual Canopies: 48.2 m²)", fontsize=8.2, fontweight='bold', pad=4)

    # Overlay canopy outlines on panel (b)
    c1 = patches.Rectangle((-1.73 - 1.95, 34.06 - 3.43), 3.90, 6.87, fill=False, edgecolor='#00FFCC', lw=1.2, linestyle='-')
    c2 = patches.Rectangle((1.92 - 1.68, -26.47 - 3.17), 3.37, 6.35, fill=False, edgecolor='#00FFCC', lw=1.2, linestyle='-')
    axes[1].add_patch(c1)
    axes[1].add_patch(c2)

    # (c) Cooling Delta Tmrt
    im2 = axes[2].imshow(d_sub, origin='lower', extent=extent, cmap='viridis', vmin=0.0, vmax=14.0)
    axes[2].set_title(r"(c) Cooling Delta $\Delta T_{\mathrm{mrt}}$" + "\n" + r"($T_{\mathrm{mrt}}^{\mathrm{base}} - T_{\mathrm{mrt}}^{\mathrm{opt}}$)",
                      fontsize=8.2, fontweight='bold', pad=4)

    # Overlay canopy outlines on panel (c)
    c1_d = patches.Rectangle((-1.73 - 1.95, 34.06 - 3.43), 3.90, 6.87, fill=False, edgecolor='white', lw=1.2, linestyle='--')
    c2_d = patches.Rectangle((1.92 - 1.68, -26.47 - 3.17), 3.37, 6.35, fill=False, edgecolor='white', lw=1.2, linestyle='--')
    axes[2].add_patch(c1_d)
    axes[2].add_patch(c2_d)

    # Annotation on Panel (c)
    axes[2].text(0.05, 0.95, "Peak Shading Relief:\n" + r"$\mathbf{+13.14\,\mathrm{K}}$",
                 transform=axes[2].transAxes, fontsize=6.5, va='top', ha='left',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.90, lw=0.4))

    for ax in axes:
        ax.set_xlabel("Local X (m)", fontsize=7.8)
        ax.tick_params(labelsize=6.8)
        ax.set_xlim(-35, 35)
        ax.set_ylim(-60, 60)

    # Equalize axis widths and attach vertical colorbars to eliminate collision with x-axis labels
    divider0 = make_axes_locatable(axes[0])
    cax0 = divider0.append_axes('right', size='5%', pad=0.08)
    cax0.axis('off')

    divider1 = make_axes_locatable(axes[1])
    cax1 = divider1.append_axes('right', size='5%', pad=0.08)
    cb_t = fig.colorbar(im1, cax=cax1)
    cb_t.set_label(r'$T_{\mathrm{mrt}}$ [°C]', fontsize=7.5)
    cb_t.ax.tick_params(labelsize=6.5)

    divider2 = make_axes_locatable(axes[2])
    cax2 = divider2.append_axes('right', size='5%', pad=0.08)
    cb_d = fig.colorbar(im2, cax=cax2)
    cb_d.set_label(r'$\Delta T_{\mathrm{mrt}}$ [K]', fontsize=7.5)
    cb_d.ax.tick_params(labelsize=6.5)

    plt.tight_layout(pad=0.4)
    out_dir = Path("docs/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_dir / "fig10_before_after_maps.png", dpi=300, bbox_inches='tight')
    plt.savefig(out_dir / "fig10_before_after_maps.pdf", bbox_inches='tight')
    plt.savefig(out_dir / "fig10_before_after_maps.svg", bbox_inches='tight')
    plt.close()
    print("Figure 10 generated successfully in PNG, PDF, and SVG.")

if __name__ == '__main__':
    create_fig10()
