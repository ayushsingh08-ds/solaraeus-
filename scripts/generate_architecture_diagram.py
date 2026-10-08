"""
Refined Publication-Quality Architectural Block Diagram for SOLARAEUS
Format: IEEE Conference Paper Flowchart (300 DPI PNG)
Font: Times New Roman, size 11pt equivalent
Collision-free layout with clean margins and professional colors.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Configure Matplotlib for Publication Typography
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 11

fig, ax = plt.subplots(figsize=(15.5, 7.8), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Style helper: rounded box with clear readable text
def draw_card(ax, x, y, w, h, bg_color, border_color, title, subtitle=None, title_color='#0F172A'):
    card = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.7,rounding_size=1.4",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=1.8,
        zorder=2
    )
    ax.add_patch(card)
    
    # Title
    ax.text(x + w / 2, y + h - 3.8, title,
            ha='center', va='center',
            fontsize=11.5, fontweight='bold',
            color=title_color, zorder=3)
    
    if subtitle:
        ax.text(x + w / 2, y + h - 7.0, subtitle,
                ha='center', va='center',
                fontsize=9.5, fontstyle='italic',
                color='#475569', zorder=3)

def draw_item_box(ax, x, y, w, h, bg_color, border_color, text_lines, text_color='#1E293B', header_weight='bold'):
    box = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.4,rounding_size=0.7",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=1.2,
        zorder=4
    )
    ax.add_patch(box)
    
    line_h = h / (len(text_lines) + 0.8)
    for i, line in enumerate(text_lines):
        fw = header_weight if i == 0 else 'normal'
        ax.text(x + w / 2, y + h - (i + 0.9) * line_h, line,
                ha='center', va='center',
                fontsize=9.8, fontweight=fw,
                color=text_color, zorder=5)

def draw_arrow(ax, x1, y1, x2, y2, label=None, label_above=True, color='#334155'):
    ax.annotate(
        '', xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=1.8,
            mutation_scale=13,
            shrinkA=1,
            shrinkB=1
        ),
        zorder=6
    )
    if label:
        lx = (x1 + x2) / 2
        ly = (y1 + y2) / 2 + (1.8 if label_above else -1.8)
        ax.text(lx, ly, label, ha='center', va='center',
                fontsize=9.0, fontweight='bold', color=color,
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFFFFF", edgecolor=color, lw=0.8, alpha=0.95),
                zorder=7)

# Background canvas panel
bg_rect = patches.Rectangle((0.5, 0.5), 99, 99, facecolor='#F8FAFC', edgecolor='#CBD5E1', lw=1.2, zorder=0)
ax.add_patch(bg_rect)

# Top Banner: Architecture Title
ax.text(50, 96.5, "SOLARAEUS SYSTEM ARCHITECTURE & CERTIFIED INCREMENTAL WORKFLOW",
        ha='center', va='center', fontsize=12.5, fontweight='bold', color='#0F172A')
ax.text(50, 93.8, "Error-Bounded Urban Microclimate Simulation, GPU Ray-Tracing Avoidance, and Thermal Comfort Optimization",
        ha='center', va='center', fontsize=10.0, fontstyle='italic', color='#475569')

# ==========================================
# COLUMN 1: DOMAIN INPUTS & LOCAL EDIT (X: 2.5 - 21.5, W: 19)
# ==========================================
draw_card(ax, 2.5, 3.5, 19, 87.5, '#EFF6FF', '#3B82F6', "1. INPUT SPECIFICATION", "Urban Scene & Boundary Data", '#1D4ED8')

draw_item_box(ax, 4.0, 71.5, 16, 13, '#FFFFFF', '#93C5FD', [
    "Urban Geometry (G)",
    "• 34 Building LOD1 Meshes",
    "• Church Street Footprints",
    "• Context Heights (OSM)"
])

draw_item_box(ax, 4.0, 56.5, 16, 13, '#FFFFFF', '#93C5FD', [
    "Terrain & Vegetation",
    "• DTM Surface Raster Grid",
    "• 14 BBMP Census Trees",
    "• Canopy Transmittance (tau)"
])

draw_item_box(ax, 4.0, 41.5, 16, 13, '#FFFFFF', '#93C5FD', [
    "Meteorological Forcing",
    "• Solar Angles (theta_s, phi_s)",
    "• Direct Shortwave (I_dir)",
    "• Diffuse Shortwave (I_diff)",
    "• Downward Longwave (L_sky)"
])

draw_item_box(ax, 4.0, 5.5, 16, 33, '#FEF3C7', '#D97706', [
    "Local Urban Mutation",
    "Interactive Geometry Edit:",
    "Delta G in {Add, Delete, Resize}",
    "• Tensile Fabric Shade Panels",
    "• Tree Pruning / Planting",
    "• AI Constrained Optimizer",
    "A_panel <= 120 m^2",
    "Clearance Height >= 4.5 m",
    "Collision Constraints Active"
], text_color='#92400E')


# ==========================================
# COLUMN 2: INVALIDATION & SPATIAL BOUNDING (X: 25.5 - 45.5, W: 20)
# ==========================================
draw_card(ax, 25.5, 3.5, 20, 87.5, '#FEF9C3', '#EAB308', "2. SPATIAL INVALIDATION", "Conservative Bounding Engine", '#854D0E')

draw_item_box(ax, 27.0, 69.5, 17, 15, '#FFFFFF', '#FDE047', [
    "Shadow Cone Tracking",
    "Bounding Box Sweep B(Delta G)",
    "Directional Prism s(theta_s, phi_s):",
    "C_shad = B (x) [0, L_max] s",
    "Captures all altered direct shade",
    "Zero false negatives guaranteed"
], text_color='#713F12')

draw_item_box(ax, 27.0, 49.5, 17, 17.5, '#FFFFFF', '#FDE047', [
    "Sky-View Horizon Bound",
    "Radial Horizon Influence R_svf:",
    "tan(alpha_min) = Delta h_max / R_svf",
    "Omega_dirty = C_shad U B_svf",
    "Conservative Domain Partition:",
    "Omega = Omega_clean U Omega_dirty"
], text_color='#713F12')

draw_item_box(ax, 27.0, 5.5, 17, 41, '#FEF08A', '#CA8A04', [
    "Domain Partitioning Ratio",
    "Empirical Church Street Result:",
    "• Omega_clean (Reused): 99.74%",
    "• Omega_dirty (Active): 0.26%",
    "(28,048 of 28,120 cells reused)",
    "",
    "Formal Invariance Contracts:",
    "1. Zero false negatives",
    "2. Rigorous directional prisms",
    "3. Exact cache bypass",
    "4. Safe analytical bounds"
], text_color='#854D0E')


# ==========================================
# COLUMN 3: RESIDENT GPU EXECUTION ENGINE (X: 49.5 - 72.5, W: 23)
# ==========================================
draw_card(ax, 49.5, 3.5, 23, 87.5, '#F0FDF4', '#22C55E', "3. DUAL-PATH SOLVER PIPELINE", "Resident CUDA Acceleration", '#15803D')

draw_item_box(ax, 51.0, 65.5, 20, 19, '#DCFCE7', '#86EFAC', [
    "Clean Domain Path (Omega_clean)",
    "Zero Ray-Tracing Evaluation",
    "• Direct Radiance: K_dir (Cached)",
    "• Sky View Factor: SVF (Cached)",
    "• Diffuse Flux: K_diff (Cached)",
    "• Longwave Flux: L_net (Cached)",
    "Lookup Latency: < 0.1 ms"
], text_color='#14532D')

draw_item_box(ax, 51.0, 39.5, 20, 23.5, '#FFFFFF', '#86EFAC', [
    "Dirty Domain Path (Omega_dirty)",
    "Localized GPU Recomputation",
    "• Parallel Ray Casts (32x32 Blocks)",
    "• Tree Transmittance Mask M_tree",
    "• Terrain DTM Ground Rays",
    "• SVF Quadrature (153 rays/cell)",
    "CUDA Kernel Latency: 11.40 ms",
    "Speedup: 500.87x vs CPU Full"
], text_color='#14532D')

draw_item_box(ax, 51.0, 5.5, 20, 31, '#BBF7D0', '#4ADE80', [
    "State Harmonization",
    "Phi_tot(x) = Phi_reused (x in Omega_clean)",
    "Phi_tot(x) = Phi_kernel (x in Omega_dirty)",
    "• Bit-identical shadow mask (0.0 error)",
    "• Machine-precision SVF (1e-14 error)",
    "• Resident GPU VRAM: 1,089.45 MB",
    "• Avoids 99.74% of ray workloads"
], text_color='#14532D')


# ==========================================
# COLUMN 4: CERTIFICATION & OUTPUTS (X: 76.5 - 97.5, W: 21)
# ==========================================
draw_card(ax, 76.5, 3.5, 21, 87.5, '#FAF5FF', '#A855F7', "4. CERTIFICATION & COMFORT", "Mathematical Bound & Thermal Fields", '#7E22CE')

draw_item_box(ax, 78.0, 66.5, 18, 18, '#F3E8FF', '#D8B4FE', [
    "Provable Error Bound Engine",
    "|T_mrt_approx - T_mrt_full| <= B_T",
    "Taylor Expansion on Stefan-Boltzmann:",
    "B_T(x) = Delta Phi_max / (4 sigma T_0^3)",
    "Empirical Bound: B_T <= 0.0812 K",
    "Soundness Rate: 100% (0 Violations)"
], text_color='#581C87')

draw_item_box(ax, 78.0, 41.5, 18, 22.5, '#FFFFFF', '#D8B4FE', [
    "Thermal Comfort Fields",
    "Mean Radiant Temperature (Tmrt):",
    "T_mrt = [(F_sw a_p + F_lw)/sigma]^(0.25)",
    "UTCI 6th-Order Polynomial:",
    "Delta T_mrt = -12.62 K",
    "Delta UTCI = -4.3 K",
    "Shifts 'Strong' -> 'Moderate Stress'"
], text_color='#581C87')

draw_item_box(ax, 78.0, 5.5, 18, 33, '#E9D5FF', '#C084FC', [
    "Verification & Delivery",
    "• 4-Way Numerical Parity Verified",
    "• 457 / 457 Regression Tests Passing",
    "• 3D WebGL Observatory Viewer",
    "• WCAG AA Contrast, 14 Trees Rendered",
    "• Unlit GPU Bilinear Discard Heatmap",
    "Certified Fast Interactive Updates"
], text_color='#581C87')


# ==========================================
# CONNECTING FLOW ARROWS WITH CLEAN CLEARANCE
# ==========================================
# Column 1 to Column 2
draw_arrow(ax, 21.5, 77.0, 25.5, 77.0, "Scene", label_above=True, color='#2563EB')
draw_arrow(ax, 21.5, 22.0, 25.5, 22.0, "Delta G", label_above=True, color='#D97706')

# Column 2 to Column 3
draw_arrow(ax, 45.5, 75.0, 49.5, 75.0, "Clean Domain", label_above=True, color='#16A34A')
draw_arrow(ax, 45.5, 51.0, 49.5, 51.0, "Dirty Domain", label_above=True, color='#DC2626')

# Column 3 Internal arrows
draw_arrow(ax, 61.0, 65.5, 61.0, 63.3, color='#15803D')
draw_arrow(ax, 61.0, 39.5, 61.0, 36.8, color='#15803D')

# Column 3 to Column 4
draw_arrow(ax, 72.5, 75.0, 76.5, 75.0, "Flux Bound", label_above=True, color='#7C3AED')
draw_arrow(ax, 72.5, 52.0, 76.5, 52.0, "Total Fluxes", label_above=True, color='#7C3AED')

# Column 4 Internal arrows
draw_arrow(ax, 87.0, 66.5, 87.0, 64.3, color='#7E22CE')
draw_arrow(ax, 87.0, 41.5, 87.0, 38.8, color='#7E22CE')

plt.tight_layout()

out_path = Path("research_paper_sol/solaraeus_workflow.png")
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out_path, dpi=300, bbox_inches='tight', pad_inches=0.08)
plt.close()
print(f"Refined workflow diagram generated successfully at: {out_path} (File size: {out_path.stat().st_size} bytes)")
