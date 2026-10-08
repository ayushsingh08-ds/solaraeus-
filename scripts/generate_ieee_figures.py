"""
Generate 4 Modular, Publication-Grade IEEE Figures for Solaraeus (300 DPI)
Divides the tasks cleanly into 4 focused, compact diagrams:
  - Fig 1: End-to-End System Architecture & Dataflow
  - Fig 2: Certified Incremental Radiative Transfer & Error Bounding
  - Fig 3: CUDA GPU Acceleration Engine & Resident-Memory Pipeline
  - Fig 4: Active Surrogate Multi-Intervention Optimization Loop
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Configure Matplotlib for Publication Typography
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['font.size'] = 8.5

out_dir = Path("research_paper_sol")
out_dir.mkdir(parents=True, exist_ok=True)

# Helper: Draw Process Rectangle
def draw_rect(ax, x, y, w, h, text_lines, is_dashed=False, fill_color='#F3F4F6', border_color='#374151', font_size=7.5, bold_title=True, zorder=3):
    ls = (0, (4, 3)) if is_dashed else '-'
    lw = 0.95
    rect = patches.Rectangle(
        (x, y), w, h,
        facecolor=fill_color,
        edgecolor=border_color,
        linestyle=ls,
        linewidth=lw,
        zorder=zorder
    )
    ax.add_patch(rect)
    
    n_lines = len(text_lines)
    line_spacing = h / (n_lines + 1.1)
    for i, line in enumerate(text_lines):
        fw = 'bold' if (i == 0 and bold_title) else 'normal'
        ax.text(x + w / 2.0, y + h - (i + 1.0) * line_spacing, line,
                ha='center', va='center',
                fontsize=font_size, fontweight=fw,
                color='#111827', zorder=zorder+1)

# Helper: Draw Data Product Parallelogram
def draw_parallelogram(ax, x, y, w, h, text_lines, is_dashed=False, fill_color='#E5E7EB', border_color='#1F2937', font_size=7.5, bold_title=True, zorder=3):
    ls = (0, (4, 3)) if is_dashed else '-'
    lw = 0.95
    skew = h * 0.26
    points = [
        [x + skew, y],
        [x + w, y],
        [x + w - skew, y + h],
        [x, y + h]
    ]
    poly = patches.Polygon(
        points, closed=True,
        facecolor=fill_color,
        edgecolor=border_color,
        linestyle=ls,
        linewidth=lw,
        zorder=zorder
    )
    ax.add_patch(poly)
    
    n_lines = len(text_lines)
    line_spacing = h / (n_lines + 1.1)
    for i, line in enumerate(text_lines):
        fw = 'bold' if (i == 0 and bold_title) else 'normal'
        ax.text(x + w / 2.0, y + h - (i + 1.0) * line_spacing, line,
                ha='center', va='center',
                fontsize=font_size, fontweight=fw,
                color='#111827', zorder=zorder+1)

# Helper: Draw Orthogonal Arrow
def draw_arrow(ax, p1, p2, label=None, label_side='above', is_dashed=False, label_fontsize=6.5, label_dx=0.0, label_dy=0.0, zorder=5):
    ls = (0, (4, 3)) if is_dashed else '-'
    col = '#374151' if not is_dashed else '#6B7280'
    ax.annotate(
        '', xy=p2, xytext=p1,
        arrowprops=dict(
            arrowstyle="-|>",
            color=col,
            linestyle=ls,
            lw=0.9,
            mutation_scale=10,
            shrinkA=0,
            shrinkB=0
        ),
        zorder=zorder
    )
    if label:
        lx = (p1[0] + p2[0]) / 2.0 + label_dx
        ly = (p1[1] + p2[1]) / 2.0 + label_dy
        dy = 1.1 if label_side == 'above' else -1.1
        ax.text(lx, ly + dy, label,
                ha='center', va='center',
                fontsize=label_fontsize, fontstyle='italic',
                color='#1F2937',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFFFFF', edgecolor='#D1D5DB', lw=0.6, alpha=0.95),
                zorder=zorder+1)

# =========================================================================
# FIGURE 1: END-TO-END MODULAR SYSTEM ARCHITECTURE
# =========================================================================
def generate_figure_1():
    print("Generating Figure 1: System Architecture...")
    fig_w, fig_h = 7.6, 3.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')
    
    col_w = 21.5
    gap_x = 3.0
    layer_names = [
        "1. Geospatial Ingestion",
        "2. Physics Preprocessing",
        "3. Dual-Backend Physics",
        "4. WebGL Digital Twin"
    ]
    
    xs = [2.0 + i * (col_w + gap_x) for i in range(4)]
    
    # Background Columns
    for i in range(4):
        bg = patches.Rectangle(
            (xs[i], 1.5), col_w, 48.5,
            facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1
        )
        ax.add_patch(bg)
        header = patches.Rectangle(
            (xs[i], 46.0), col_w, 4.0,
            facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2
        )
        ax.add_patch(header)
        ax.text(xs[i] + col_w / 2.0, 48.0, layer_names[i],
                ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)

    box_w = 18.5
    bx = [x + (col_w - box_w) / 2.0 for x in xs]
    
    # Layer 1: Inputs
    draw_parallelogram(ax, bx[0], 34.0, box_w, 9.5, ["Overture Buildings", "& Open Buildings ML", "123 structures, heights"], font_size=6.8)
    draw_parallelogram(ax, bx[0], 19.5, box_w, 9.5, ["NOAA & NASA POWER", "Atmospheric Vectors", "Ta=35C, GHI=756 W/m2"], font_size=6.8)
    draw_parallelogram(ax, bx[0], 5.0, box_w, 9.5, ["Topography & Trees", "FABDEM & BBMP Data", "14 census trees (LOD-1)"], font_size=6.8)
    
    # Layer 2: Preprocessing
    draw_rect(ax, bx[1], 31.0, box_w, 11.5, ["CRS Harmonization", "UTM Zone 43N metric grid", "gamma = +0.5854 deg"], font_size=7.0)
    draw_rect(ax, bx[1], 11.0, box_w, 12.0, ["3D Triangular Mesh", "2,136 watertight triangles", "37 core + 86 context"], font_size=7.0)
    
    # Connections: Layer 1 -> Layer 2
    draw_arrow(ax, (bx[0] + box_w, 38.75), (bx[1], 36.75))
    draw_arrow(ax, (bx[0] + box_w, 24.25), (bx[1] - 1.2, 24.25))
    ax.plot([bx[0] + box_w, bx[1] - 1.2], [24.25, 24.25], color='#374151', lw=0.9)
    ax.plot([bx[1] - 1.2, bx[1] - 1.2], [24.25, 17.0], color='#374151', lw=0.9)
    draw_arrow(ax, (bx[1] - 1.2, 17.0), (bx[1], 17.0))
    draw_arrow(ax, (bx[0] + box_w, 9.75), (bx[1], 14.0))

    # Layer 3: Physics Engine
    draw_rect(ax, bx[2], 34.5, box_w, 8.5, ["Steyn 36-Radial SVF", "& Moller-Trumbore Ray", "Directional cast shadows"], font_size=6.8)
    draw_rect(ax, bx[2], 20.0, box_w, 9.5, ["Stefan-Boltzmann 6-Flux", "Radiant balance: T_mrt", "UTCI pythermalcomfort"], font_size=6.8)
    draw_rect(ax, bx[2], 5.0, box_w, 10.0, ["Certified Incremental", "& CUDA GPU Kernels", "99.74% cell reuse, 11.4 ms"], font_size=6.8)
    
    # Connections: Layer 2 -> Layer 3
    draw_arrow(ax, (bx[1] + box_w, 36.75), (bx[2], 38.75))
    draw_arrow(ax, (bx[1] + box_w, 17.0), (bx[2], 10.0))
    draw_arrow(ax, (bx[2] + box_w / 2.0, 34.5), (bx[2] + box_w / 2.0, 29.5))
    draw_arrow(ax, (bx[2] + box_w / 2.0, 20.0), (bx[2] + box_w / 2.0, 15.0))
    
    # Layer 4: Visualization & Contracts
    draw_parallelogram(ax, bx[3], 32.0, box_w, 10.5, ["Typed JSON Contracts", "& NetCDF Rasters", "Direct API schema"], font_size=6.8)
    draw_rect(ax, bx[3], 15.0, box_w, 12.0, ["3D WebGL Digital Twin", "Three.js r128 browser runtime", "GLSL Thermal Heatmap Shader"], font_size=7.0)
    draw_rect(ax, bx[3], 4.5, box_w, 6.5, ["Pedestrian Avatar HUD", "Interactive comfort timeline"], font_size=6.6)
    
    # Connections: Layer 3 -> Layer 4
    draw_arrow(ax, (bx[2] + box_w, 24.75), (bx[3], 37.25))
    draw_arrow(ax, (bx[3] + box_w / 2.0, 32.0), (bx[3] + box_w / 2.0, 27.0))
    draw_arrow(ax, (bx[3] + box_w / 2.0, 15.0), (bx[3] + box_w / 2.0, 11.0))
    
    plt.tight_layout()
    f1_path = out_dir / "fig1_architecture.png"
    plt.savefig(f1_path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print(f"Saved: {f1_path} ({f1_path.stat().st_size} bytes)")

# =========================================================================
# FIGURE 2: CERTIFIED INCREMENTAL RADIATIVE TRANSFER & ERROR BOUNDING
# =========================================================================
def generate_figure_2():
    print("Generating Figure 2: Certified Incremental Framework...")
    fig_w, fig_h = 7.6, 3.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')
    
    # Column 1: Scene & Intervention Input (X=3 to 26)
    bg1 = patches.Rectangle((2.0, 1.5), 24.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg1)
    h1 = patches.Rectangle((2.0, 46.0), 24.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h1)
    ax.text(14.0, 48.0, "1. Urban Domain & Edit", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 4.0, 27.5, 20.0, 14.0, ["Static Baseline Scene", "Church Street: 28,120 cells", "123 context buildings", "Precomputed T_mrt & SVF"], font_size=6.8)
    draw_parallelogram(ax, 4.0, 6.0, 20.0, 15.0, ["Shade Canopy Intervention", "BLR_SHADE_001 (6m x 3m)", "Underside clearance: 3.5m", "Local coordinate anchor"], font_size=6.8)
    
    # Column 2: Mathematical Error Certificate (X=29 to 68)
    bg2 = patches.Rectangle((28.0, 1.5), 40.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg2)
    h2 = patches.Rectangle((28.0, 46.0), 40.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h2)
    ax.text(48.0, 48.0, "2. Closed-Form Error Certificate & Spatial Bounds", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 30.5, 30.5, 35.0, 11.5, ["Shadow Frustum & SVF Horizon Decay", "Delta_Psi_svf <= min(1.0, W*H / (2*pi*r^2))", "Casts beam cone along sun vector s(alpha, phi)"], font_size=6.8)
    draw_rect(ax, 30.5, 7.0, 35.0, 18.5, ["Concave Stefan-Boltzmann Bound (Theorem 1)", "|T_mrt_inc(x) - T_mrt_full(x)| <= B_T(x) <= eps_T", "B_T(x) = Delta_Phi_max(x) / (4 * sigma * T_min^3)", "Target tolerance: eps_T = 0.50 K"], font_size=6.8)
    
    # Column 3: Domain Partitioning & Parity Verification (X=71 to 98)
    bg3 = patches.Rectangle((70.5, 1.5), 27.5, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg3)
    h3 = patches.Rectangle((70.5, 46.0), 27.5, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h3)
    ax.text(84.25, 48.0, "3. Certified Execution", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 72.5, 31.0, 23.5, 11.0, ["Dirty Cells Omega_dirty", "Recomputed: 72 cells (0.26%)", "2,376 rays evaluated"], font_size=6.8, fill_color='#FEE2E2', border_color='#B91C1C')
    draw_rect(ax, 72.5, 17.5, 23.5, 10.5, ["Clean Cells Omega_clean", "Reused: 28,048 cells (99.74%)", "925,584 rays avoided"], font_size=6.8, fill_color='#ECFDF5', border_color='#047857')
    draw_rect(ax, 72.5, 4.0, 23.5, 10.5, ["Verified Parity", "Max Error: 0.0289 K << 0.5 K", "0 Violations (18 Audited)"], font_size=6.8, fill_color='#FFFFFF')
    
    # Connections
    draw_arrow(ax, (24.0, 34.5), (30.5, 36.25))
    draw_arrow(ax, (24.0, 13.5), (30.5, 16.25))
    draw_arrow(ax, (48.0, 30.5), (48.0, 25.5), label="Flux decay", label_side='above', label_fontsize=6.2)
    draw_arrow(ax, (65.5, 36.25), (72.5, 36.5), label="B_T > eps_T", label_side='above', label_fontsize=6.0)
    draw_arrow(ax, (65.5, 16.25), (72.5, 22.75), label="B_T <= eps_T", label_side='above', label_fontsize=6.0)
    
    plt.tight_layout()
    f2_path = out_dir / "fig2_incremental.png"
    plt.savefig(f2_path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print(f"Saved: {f2_path} ({f2_path.stat().st_size} bytes)")

# =========================================================================
# FIGURE 3: CUDA GPU ACCELERATION ARCHITECTURE & PIPELINE
# =========================================================================
def generate_figure_3():
    print("Generating Figure 3: CUDA GPU Acceleration Pipeline...")
    fig_w, fig_h = 7.6, 3.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')
    
    # Left: Host CPU Side (X=2 to 28)
    bg1 = patches.Rectangle((2.0, 1.5), 26.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg1)
    h1 = patches.Rectangle((2.0, 46.0), 26.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h1)
    ax.text(15.0, 48.0, "Host (Intel CPU / RAM)", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 4.5, 31.0, 21.0, 11.0, ["Simulation Orchestrator", "Candidate geometry parsing", "Dirty mask determination"], font_size=6.8)
    draw_parallelogram(ax, 4.5, 10.0, 21.0, 14.0, ["Candidate Geometry Stream", "Intervention triangle buffer", "Transferred once on update (<1 ms)"], font_size=6.8)

    # Middle: Resident Device VRAM (X=31 to 65)
    bg2 = patches.Rectangle((31.0, 1.5), 35.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg2)
    h2 = patches.Rectangle((31.0, 46.0), 35.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h2)
    ax.text(48.5, 48.0, "Resident VRAM (NVIDIA RTX 4050)", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 33.5, 32.5, 30.0, 10.5, ["Persistent Domain Tensors", "Watertight mesh: 2,136 triangles", "Sensor grid: 28,120 pedestrian points", "Zero CPU-GPU memory ping-pong"], font_size=6.8)
    draw_rect(ax, 33.5, 19.0, 30.0, 10.5, ["moller_trumbore_shadow_kernel", "Parallel ray-triangle intersection", "Evaluates Omega_dirty active blocks", "Bit-identical shadow mask (0.000000)"], font_size=6.8)
    draw_rect(ax, 33.5, 5.5, 30.0, 10.5, ["compute_svf_horizon_kernel", "Warp-level 36-radial horizon reduction", "Double-precision parity (1.05e-14)"], font_size=6.8)
    
    # Right: Benchmark Speedup & Profiling (X=68 to 98)
    bg3 = patches.Rectangle((68.0, 1.5), 30.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg3)
    h3 = patches.Rectangle((68.0, 46.0), 30.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h3)
    ax.text(83.0, 48.0, "Performance & Speedup", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 70.0, 32.5, 26.0, 10.5, ["Full Recomputation", "CPU: 5.71 s | GPU: 133 ms", "Speedup: 69.1x vs CPU"], font_size=6.8)
    draw_rect(ax, 70.0, 19.0, 26.0, 10.5, ["Incremental Recomputation", "CPU Inc: 420 ms", "GPU Kernel: 11.40 ms", "Speedup: 500.87x vs CPU Full"], font_size=6.8, fill_color='#FEF3C7', border_color='#B45309')
    draw_rect(ax, 70.0, 5.5, 26.0, 10.5, ["Memory Footprint", "Peak VRAM: 1,089 MB", "Bound well within 6 GB VRAM"], font_size=6.8)
    
    # Connections
    draw_arrow(ax, (25.5, 17.0), (33.5, 24.25), label="Stream delta", label_side='above', label_fontsize=6.2)
    draw_arrow(ax, (48.5, 32.5), (48.5, 29.5))
    draw_arrow(ax, (48.5, 19.0), (48.5, 16.0))
    draw_arrow(ax, (63.5, 37.75), (70.0, 37.75))
    draw_arrow(ax, (63.5, 24.25), (70.0, 24.25))
    
    plt.tight_layout()
    f3_path = out_dir / "fig3_gpu_engine.png"
    plt.savefig(f3_path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print(f"Saved: {f3_path} ({f3_path.stat().st_size} bytes)")

# =========================================================================
# FIGURE 4: ACTIVE SURROGATE MULTI-INTERVENTION OPTIMIZATION
# =========================================================================
def generate_figure_4():
    print("Generating Figure 4: Active Surrogate Optimization Loop...")
    fig_w, fig_h = 7.6, 3.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis('off')
    
    # Step 1: Proposal Generator (X=2 to 24)
    bg1 = patches.Rectangle((2.0, 1.5), 22.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg1)
    h1 = patches.Rectangle((2.0, 46.0), 22.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h1)
    ax.text(13.0, 48.0, "1. Proposal Generator", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 3.5, 25.0, 19.0, 17.5, ["Parameter Search Space", "Panel 1: (x1, y1, L1, W1, H1)", "Panel 2: (x2, y2, L2, W2, H2)", "Headings: theta in [0, 180]", "Albedo: alpha in [0.2, 0.8]"], font_size=6.6)
    draw_rect(ax, 3.5, 5.5, 19.0, 15.5, ["Acquisition Strategy", "Upper Confidence Bound:", "alpha_ucb = J_hat + kappa*sigma", "Balancing explore/exploit"], font_size=6.6)
    
    # Step 2: 4-Stage Feasibility Screening (X=26 to 48)
    bg2 = patches.Rectangle((26.0, 1.5), 22.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg2)
    h2 = patches.Rectangle((26.0, 46.0), 22.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h2)
    ax.text(37.0, 48.0, "2. Feasibility Filter", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 27.5, 30.5, 19.0, 12.0, ["Corridor & Setback", "Walkway containment", "Facade setback > 1.0 m"], font_size=6.8)
    draw_rect(ax, 27.5, 17.0, 19.0, 11.0, ["Clearance & Area", "Clearway H >= 3.5 m", "Total Area <= 30 m2"], font_size=6.8)
    draw_rect(ax, 27.5, 4.5, 19.0, 10.0, ["Screening Ledger", "129 candidates screened", "55 feasible | 74 rejected"], font_size=6.8, fill_color='#FFFFFF')
    
    # Step 3: Fast Incremental Objective Evaluation (X=50 to 74)
    bg3 = patches.Rectangle((50.0, 1.5), 24.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg3)
    h3 = patches.Rectangle((50.0, 46.0), 24.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h3)
    ax.text(62.0, 48.0, "3. Physics Evaluation", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 51.5, 27.0, 21.0, 15.5, ["Incremental Simulation", "GPU 11.4 ms per candidate", "99.74% ray work avoidance", "Direct T_mrt field update"], font_size=6.8)
    draw_rect(ax, 51.5, 5.5, 21.0, 17.5, ["Multi-Panel Objective", "J = sum(Delta_T_mrt)", "  - lambda_area*(A1+A2)", "  - lambda_cost*Cost", "  - lambda_overlap*|S1 cap S2|"], font_size=6.6)
    
    # Step 4: Pareto Optimal Discovery (X=76 to 98)
    bg4 = patches.Rectangle((76.0, 1.5), 22.0, 48.5, facecolor='#F9FAFB', edgecolor='#D1D5DB', lw=0.8, zorder=1)
    ax.add_patch(bg4)
    h4 = patches.Rectangle((76.0, 46.0), 22.0, 4.0, facecolor='#E5E7EB', edgecolor='#D1D5DB', lw=0.8, zorder=2)
    ax.add_patch(h4)
    ax.text(87.0, 48.0, "4. Optimal Layout", ha='center', va='center', fontsize=7.6, fontweight='bold', color='#111827', zorder=3)
    
    draw_rect(ax, 77.5, 26.5, 19.0, 16.0, ["Best Proposal:", "CAND_4196_SURR", "Panel 1: 14.01 m2 (H=3.79m)", "Panel 2: 8.86 m2 (H=4.16m)", "Total Area: 22.87 m2"], font_size=6.8, fill_color='#ECFDF5', border_color='#047857')
    draw_rect(ax, 77.5, 5.5, 19.0, 17.0, ["Physical Impact", "Peak T_mrt: -12.68 K", "Corridor Delta: -0.05 K", "Zero shadow overlap", "Evaluated in 0.33 s"], font_size=6.8, fill_color='#FFFFFF')
    
    # Connections
    draw_arrow(ax, (22.5, 33.75), (27.5, 36.5))
    draw_arrow(ax, (46.5, 22.5), (51.5, 34.75), label="Feasible proposals", label_side='above', label_fontsize=5.8)
    draw_arrow(ax, (62.0, 27.0), (62.0, 23.0))
    draw_arrow(ax, (72.5, 34.75), (77.5, 34.5), label="Surrogate model", label_side='above', label_fontsize=5.8)
    
    # Feedback loop: from Step 3/4 back to Proposal Generator (Acquisition update)
    ax.plot([62.0, 62.0], [5.5, 3.2], color='#374151', lw=0.8)
    ax.plot([62.0, 13.0], [3.2, 3.2], color='#374151', lw=0.8)
    draw_arrow(ax, (13.0, 3.2), (13.0, 5.5), label="Surrogate retraining & active acquisition", label_side='above', label_fontsize=5.6, label_dx=18.0)
    
    plt.tight_layout()
    f4_path = out_dir / "fig4_optimization.png"
    plt.savefig(f4_path, dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close()
    print(f"Saved: {f4_path} ({f4_path.stat().st_size} bytes)")

if __name__ == "__main__":
    generate_figure_1()
    generate_figure_2()
    generate_figure_3()
    generate_figure_4()
    print("All 4 publication figures generated successfully.")
