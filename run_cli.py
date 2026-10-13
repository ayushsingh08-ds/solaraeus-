#!/usr/bin/env python3
"""
SOLARAEUS Presentation CLI: Interactive Terminal Demonstration Tool.

Designed for live academic panel defenses and presentations:
1. Baseline Microclimate Calculation for any location (Berlin, London, Chicago, or custom).
2. AI-Assisted Intervention Solver with budget / canopy allocation.
3. Automated high-resolution spatial heatmap PNG generation (Baseline, Optimized, Delta Cooling).
"""

import sys
import argparse
import json
import math
import time
from pathlib import Path

# Add src to sys.path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from mpl_toolkits.axes_grid1 import make_axes_locatable

from solaraeus.pipeline.engine import (
    get_available_case_areas,
    process_case_data,
    optimize_canopies,
)


def render_spatial_map(
    area: str,
    target_proc_dir: Path,
    opt_dir: Path,
    output_png: Path,
) -> Path:
    """Renders high-resolution 3-panel microclimate map PNG with true spatial geometry."""
    output_png.parent.mkdir(parents=True, exist_ok=True)

    grid_path = target_proc_dir / "01_data_ingestion" / "pedestrian_grid.json"
    grid_info = json.loads(grid_path.read_text(encoding="utf-8"))
    
    b_tmrt = np.load(target_proc_dir / "02_calculation" / "baseline_tmrt.npz")["tmrt"]
    o_tmrt = np.load(opt_dir / "optimized_tmrt.npz")["tmrt"]
    d_tmrt = np.load(opt_dir / "cooling_delta_tmrt.npz")["delta_tmrt_k"]
    canopies = json.loads((opt_dir / "optimal_canopies.json").read_text(encoding="utf-8"))

    # Load building footprints from scene_mesh.json
    scene_path = target_proc_dir / "01_data_ingestion" / "scene_mesh.json"
    scene_data = json.loads(scene_path.read_text(encoding="utf-8")) if scene_path.exists() else {}
    local_bldgs = scene_data.get("metadata", {}).get("building_polygons_local", [])

    # Load simulation timestamp metadata
    summary_path = target_proc_dir / "02_calculation" / "baseline_summary.json"
    sim_date = "2026-10-13"
    sim_time = "12:00:00"
    tz_label = "IST"
    if summary_path.exists():
        try:
            s_sum = json.loads(summary_path.read_text(encoding="utf-8"))
            st = s_sum.get("simulation_timestamp", {})
            sim_date = st.get("date", sim_date)
            sim_time = st.get("local_time", sim_time)
            tz_str = st.get("timezone", "")
            if "Kolkata" in tz_str or area.lower().startswith("bengaluru"):
                tz_label = "IST"
            elif tz_str:
                tz_label = tz_str
            else:
                tz_label = "Local"
        except Exception:
            pass

    ox = grid_info["origin_x_m"]
    oy = grid_info["origin_y_m"]
    ex = grid_info["extent_x_m"]
    ey = grid_info["extent_y_m"]
    res = grid_info["resolution_m"]
    nx = grid_info["nx"]
    ny = grid_info["ny"]
    extent = [ox, ox + nx * res, oy, oy + ny * res]

    fig, axes = plt.subplots(1, 3, figsize=(21, 7.0), dpi=300)
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Common temperature scale for panels (a) and (b)
    valid_tmrt = b_tmrt[~np.isnan(b_tmrt)]
    if len(valid_tmrt) > 0:
        vmin_t = float(np.percentile(valid_tmrt, 2))
        vmax_t = float(np.percentile(valid_tmrt, 98))
    else:
        vmin_t = 25.0
        vmax_t = 55.0
    if vmax_t - vmin_t < 5.0:
        vmax_t = vmin_t + 15.0

    cmap_t = matplotlib.colormaps.get_cmap('inferno').copy()
    cmap_t.set_bad(color='#1E1E28')  # Dark charcoal for building interior / masked cells

    city_title = area.replace('_', ' ').title()

    # Helper function to render building footprints
    def draw_buildings(ax):
        if local_bldgs:
            for b in local_bldgs:
                coords = b.get("coordinates", [])
                if len(coords) >= 3:
                    poly = patches.Polygon(
                        coords, closed=True, facecolor='#2B2D42', edgecolor='#8D99AE',
                        linewidth=0.8, alpha=0.92, zorder=3
                    )
                    ax.add_patch(poly)
        elif scene_data.get("meshes"):
            for m_id, m in scene_data["meshes"].items():
                if "bldg" in m_id.lower() or "building" in m_id.lower():
                    verts = np.array(m.get("vertices", []))
                    if len(verts) > 0:
                        min_x, max_x = float(np.min(verts[:, 0])), float(np.max(verts[:, 0]))
                        min_y, max_y = float(np.min(verts[:, 1])), float(np.max(verts[:, 1]))
                        rect = patches.Rectangle(
                            (min_x, min_y), max_x - min_x, max_y - min_y,
                            facecolor='#2B2D42', edgecolor='#8D99AE', linewidth=0.8, alpha=0.92, zorder=3
                        )
                        ax.add_patch(rect)

    # -------------------------------------------------------------
    # (a) Baseline Tmrt Map
    # -------------------------------------------------------------
    axes[0].set_aspect('equal')
    axes[0].set_facecolor('#1E1E28')
    im0 = axes[0].imshow(b_tmrt, origin='lower', extent=extent, cmap=cmap_t, vmin=vmin_t, vmax=vmax_t, zorder=1)
    draw_buildings(axes[0])
    axes[0].set_title(f"(a) Baseline Mean Radiant Temperature\n{city_title} (No Intervention)", fontsize=11, fontweight='bold', pad=8)
    axes[0].set_xlabel("East-West Distance X (m)", fontsize=9)
    axes[0].set_ylabel("North-South Distance Y (m)", fontsize=9)
    axes[0].set_xlim(extent[0], extent[1])
    axes[0].set_ylim(extent[2], extent[3])
    axes[0].grid(True, color='white', alpha=0.12, linestyle=':', lw=0.6, zorder=2)

    divider0 = make_axes_locatable(axes[0])
    cax0 = divider0.append_axes('right', size='4.5%', pad=0.08)
    cb0 = fig.colorbar(im0, cax=cax0)
    cb0.set_label("Tmrt [°C]", fontsize=9)

    # -------------------------------------------------------------
    # (b) Optimized Tmrt with canopies
    # -------------------------------------------------------------
    axes[1].set_aspect('equal')
    axes[1].set_facecolor('#1E1E28')
    im1 = axes[1].imshow(o_tmrt, origin='lower', extent=extent, cmap=cmap_t, vmin=vmin_t, vmax=vmax_t, zorder=1)
    draw_buildings(axes[1])
    axes[1].set_title(f"(b) AI-Optimized Tmrt Map\n({len(canopies)} Tensile Shade Canopies)", fontsize=11, fontweight='bold', pad=8)
    axes[1].set_xlabel("East-West Distance X (m)", fontsize=9)
    axes[1].set_xlim(extent[0], extent[1])
    axes[1].set_ylim(extent[2], extent[3])
    axes[1].grid(True, color='white', alpha=0.12, linestyle=':', lw=0.6, zorder=2)

    for c in canopies:
        # Draw physical canopy roof (solid cyan outline)
        roof_corners = c.get("roof_corners")
        if roof_corners:
            poly_roof = patches.Polygon(roof_corners, closed=True, fill=False, edgecolor="#00FFFF", lw=1.6, zorder=5)
            axes[1].add_patch(poly_roof)
        else:
            cx, cy = c["x"], c["y"]
            w, h = c["length_m"], c["width_m"]
            rect = patches.Rectangle((cx - w / 2.0, cy - h / 2.0), w, h, fill=False, edgecolor="#00FFFF", lw=1.6, zorder=5)
            axes[1].add_patch(rect)

        # Draw ground shadow outline (dashed yellow footprint)
        shadow_corners = c.get("shadow_corners")
        if shadow_corners:
            poly_shadow = patches.Polygon(shadow_corners, closed=True, fill=False, edgecolor="#FFD166", lw=1.1, linestyle="--", zorder=4)
            axes[1].add_patch(poly_shadow)

        axes[1].text(
            c["x"], c["y"], c["id"], color="#00FFFF", fontsize=7.0, ha='center', va='center',
            fontweight='bold', zorder=6,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='#0B0C10', edgecolor='#00FFFF', lw=0.5, alpha=0.85)
        )

    divider1 = make_axes_locatable(axes[1])
    cax1 = divider1.append_axes('right', size='4.5%', pad=0.08)
    cb1 = fig.colorbar(im1, cax=cax1)
    cb1.set_label("Tmrt [°C]", fontsize=9)

    # -------------------------------------------------------------
    # (c) Cooling Delta Heatmap (Tmrt baseline - Tmrt opt)
    # -------------------------------------------------------------
    valid_delta = d_tmrt[~np.isnan(d_tmrt)]
    max_cooling = float(np.nanmax(valid_delta)) if len(valid_delta) > 0 else 0.0
    min_cooling = float(np.nanmin(valid_delta)) if len(valid_delta) > 0 else 0.0

    axes[2].set_aspect('equal')
    axes[2].set_facecolor('#1E1E28')

    # Sequential cooling scale unless meaningful warming occurs
    if min_cooling < -0.5:
        cmap_d = matplotlib.colormaps.get_cmap('coolwarm').copy()
        cmap_d.set_bad(color='#1E1E28')
        v_lim = max(abs(min_cooling), max_cooling, 5.0)
        im2 = axes[2].imshow(d_tmrt, origin='lower', extent=extent, cmap=cmap_d, vmin=-v_lim, vmax=v_lim, zorder=1)
    else:
        cmap_d = matplotlib.colormaps.get_cmap('viridis').copy()
        cmap_d.set_bad(color='#1E1E28')
        vmax_d = max(8.0, max_cooling + 1.0)
        im2 = axes[2].imshow(d_tmrt, origin='lower', extent=extent, cmap=cmap_d, vmin=0.0, vmax=vmax_d, zorder=1)

    draw_buildings(axes[2])
    axes[2].set_title(f"(c) Cooling Delta Heatmap (Tmrt_base − Tmrt_opt)\nPeak Pedestrian Relief: +{max_cooling:.2f} K", fontsize=11, fontweight='bold', pad=8)
    axes[2].set_xlabel("East-West Distance X (m)", fontsize=9)
    axes[2].set_xlim(extent[0], extent[1])
    axes[2].set_ylim(extent[2], extent[3])
    axes[2].grid(True, color='white', alpha=0.12, linestyle=':', lw=0.6, zorder=2)

    # Overlay ground shadow footprint outline directly from solver geometry
    for c in canopies:
        shadow_corners = c.get("shadow_corners")
        if shadow_corners:
            poly_shadow_c = patches.Polygon(
                shadow_corners, closed=True, fill=False, edgecolor="white", lw=1.5, linestyle="--", zorder=4
            )
            axes[2].add_patch(poly_shadow_c)
            sx = c.get("shadow_x", c["x"])
            sy = c.get("shadow_y", c["y"])
            axes[2].text(sx, sy, c["id"], color="white", fontsize=6.8, ha='center', va='center', fontweight='bold', zorder=6)
        else:
            cx, cy = c["x"], c["y"]
            w, h = c["length_m"], c["width_m"]
            rect = patches.Rectangle((cx - w / 2.0, cy - h / 2.0), w, h, fill=False, edgecolor="white", lw=1.5, linestyle="--", zorder=4)
            axes[2].add_patch(rect)

    # Positive peak thermal relief callout
    axes[2].text(
        0.04, 0.94, f"Peak Thermal Relief:\n+{max_cooling:.2f} K (ΔTmrt)",
        transform=axes[2].transAxes, fontsize=8.5, fontweight='bold', va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.35', facecolor='white', alpha=0.94, lw=0.6), zorder=7
    )

    divider2 = make_axes_locatable(axes[2])
    cax2 = divider2.append_axes('right', size='4.5%', pad=0.08)
    cb2 = fig.colorbar(im2, cax=cax2)
    cb2.set_label("Cooling Delta ΔTmrt [K]", fontsize=9)

    # Super Title with exact date/time
    fig.suptitle(
        f"SOLARAEUS Urban Microclimate Intervention Map — {city_title}\n"
        f"Simulation Timestamp: {sim_date} at {sim_time} ({tz_label}) | Domain Extent: {ex:.0f} × {ey:.0f} m | Grid Resolution: {res:.1f} m",
        fontsize=12.5, fontweight='bold', y=0.98
    )

    # Mandatory Scientific Limitations Footer
    fig.text(
        0.5, 0.02,
        "Scientific Limitations: All building heights are OSM estimates; terrain is synthetic flat z=0; "
        "trees.geojson is empty (unmapped in OSM). Model is uncalibrated.",
        ha='center', fontsize=8.5, fontstyle='italic', color='#555555'
    )

    plt.tight_layout(rect=[0.0, 0.05, 1.0, 0.94])
    plt.savefig(output_png, bbox_inches="tight")
    plt.close()
    return output_png


def cmd_calculate(args):
    area = args.area.lower()
    res = args.resolution
    print("\n" + "=" * 80)
    print(f"  STEP 1: BASELINE MICROCLIMATE SIMULATION — {area.upper()}")
    print("=" * 80)
    print(f"• Study Area Domain:   {area}")
    print(f"• Grid Resolution:     {res} meters")
    print(f"• Acceleration:        {'GPU (CUDA Kernels)' if args.gpu else 'CPU Multithreaded'}")
    print("-" * 80)

    t0 = time.perf_counter()
    summary = process_case_data(area=area, grid_resolution_m=res, use_gpu=args.gpu, verbose=True)
    dt = time.perf_counter() - t0

    print("\n" + "=" * 80)
    print("  CALCULATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"  Execution Time:         {dt:.2f} seconds")
    print(f"  Total Domain Meshes:    {summary['total_buildings']}")
    print(f"  Evaluated Grid Cells:   {summary['grid_cells']} points")
    print(f"  Baseline Mean Tmrt:     {summary['baseline_tmrt_mean_c']:.2f} °C")
    print(f"  Baseline Max Tmrt:      {summary['baseline_tmrt_max_c']:.2f} °C")
    print(f"  Baseline Mean UTCI:     {summary['baseline_utci_mean_c']:.2f} °C")
    print(f"  Pedestrian Sunlit Area: {summary['sunlit_cells_pct']:.1f}%")
    print(f"  Artifacts Folder:       {summary['processed_dir']}")
    print("=" * 80 + "\n")
    return summary


def cmd_optimize(args):
    area = args.area.lower()
    
    # Calculate number of shades based on shades or budget
    unit_cost = 4500.0  # approximate cost per tensile canopy unit in $
    if args.budget and not args.shades:
        num_shades = max(1, min(10, int(args.budget / unit_cost)))
        print(f"• Budget Input:        ${args.budget:,.2f} -> Allocated {num_shades} shade canopies (~${unit_cost:,.0f}/canopy)")
    else:
        num_shades = args.shades or 2
        total_est_cost = num_shades * unit_cost
        print(f"• Canopy Allocation:   {num_shades} units (Est. Structure Budget: ${total_est_cost:,.2f})")

    print("\n" + "=" * 80)
    print(f"  STEP 2: AI INTERVENTION & CANOPY OPTIMIZATION — {area.upper()}")
    print("=" * 80)
    print(f"• Study Area:          {area}")
    print(f"• Number of Canopies:  {num_shades}")
    print(f"• Optimization Goal:   Maximum pedestrian thermal cooling (UTCI + Tmrt)")
    print("-" * 80)

    t0 = time.perf_counter()
    opt_results = optimize_canopies(
        area=area,
        num_shades=num_shades,
        canopy_width=args.width,
        canopy_length=args.length,
        canopy_height=args.height,
        transmissivity=args.transmissivity,
    )
    dt = time.perf_counter() - t0

    cooling = opt_results["summary"]
    canopies = opt_results["canopies"]
    opt_dir = Path(opt_results["opt_dir"])
    target_proc_dir = Path(opt_results.get("proc_dir", ""))
    if not target_proc_dir.exists():
        root = Path(__file__).resolve().parent
        proc_base = root / "data" / "processed" / area
        target_proc_dir = sorted([d for d in proc_base.iterdir() if d.is_dir()])[-1]

    # Generate visual spatial map
    root = Path(__file__).resolve().parent
    png_path = root / "results" / "maps" / f"{area}_intervention_map.png"
    render_spatial_map(area, target_proc_dir, opt_dir, png_path)

    # Print clean results table
    print("\n" + "=" * 80)
    print("  AI OPTIMIZATION RESULTS SUMMARY")
    print("=" * 80)
    print(f"  Solve Time:              {dt:.3f} seconds")
    print(f"  Canopies Deployed:       {cooling['num_canopies']} units")
    print(f"  Total Shaded Area:       {cooling['total_shaded_pedestrian_area_m2']} m²")
    print(f"  Peak Local Cooling:      +{cooling['max_tmrt_reduction_k']:.2f} K (Tmrt) | +{cooling['max_utci_reduction_k']:.2f} K (UTCI)")
    print(f"  Mean Pedestrian Cooling: +{cooling['mean_corridor_cooling_k']:.2f} K")
    print(f"  Thermal Comfort Shift:   {cooling['comfort_category_before']} -> {cooling['comfort_category_after']}")
    print("-" * 80)
    print("  PLACED CANOPY LOCATIONS:")
    for c in canopies:
        print(f"    • {c['id']}: Roof=({c['x']:>6.2f}m, {c['y']:>6.2f}m, z={c['z']}m) | Ground Shadow=({c.get('shadow_x', c['x']):>6.2f}m, {c.get('shadow_y', c['y']):>6.2f}m) | Size={c['length_m']}x{c['width_m']}m | Shaded={c['shaded_area_m2']} m²")
    print("=" * 80)
    print("  RESULT SPATIAL MAP GENERATED:")
    print(f"  >>> File: {png_path.resolve()}")
    print("=" * 80 + "\n")
    return png_path


def cmd_run_all(args):
    print("\n" + "#" * 80)
    print(f"  SOLARAEUS FULL LIVE DEMONSTRATION: {args.area.upper()}")
    print("#" * 80)
    cmd_calculate(args)
    png_path = cmd_optimize(args)
    print("\n" + "*" * 80)
    print(f"  DEMONSTRATION COMPLETE!")
    print(f"  Show the panel members the generated map image at:")
    print(f"  {png_path.resolve()}")
    print("*" * 80 + "\n")


def cmd_list(args):
    areas = get_available_case_areas()
    print("\n" + "=" * 80)
    print("  AVAILABLE STUDY AREAS IN SYSTEM")
    print("=" * 80)
    for a in areas:
        print(f"  • {a['area_id']:<15} | {a['name']:<20} | Files: {a['total_files']} | Path: {a['path']}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="SOLARAEUS Terminal Presentation & Microclimate CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples for Live Defense Presentation:
  1. Full Demo in 1 command (Calculate + AI Optimize + Generate Map):
     python run_cli.py demo --area berlin --shades 2

  2. Baseline Microclimate Calculation only:
     python run_cli.py calculate --area berlin --res 1.0

  3. AI Optimization based on shade count or budget ($):
     python run_cli.py optimize --area berlin --shades 3
     python run_cli.py optimize --area berlin --budget 15000

  4. List all supported study areas:
     python run_cli.py list
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: list
    p_list = subparsers.add_parser("list", help="List all available map areas")

    # Command: calculate
    p_calc = subparsers.add_parser("calculate", help="Run baseline microclimate calculation")
    p_calc.add_argument("--area", default="berlin", help="Target area (e.g., berlin, london, chicago)")
    p_calc.add_argument("--resolution", "--res", type=float, default=2.0, help="Grid resolution in meters (default: 2.0)")
    p_calc.add_argument("--gpu", action="store_true", help="Enable GPU CUDA acceleration")

    # Command: optimize
    p_opt = subparsers.add_parser("optimize", help="Run AI intervention solver with budget/shades")
    p_opt.add_argument("--area", default="berlin", help="Target area (e.g., berlin, london, chicago)")
    p_opt.add_argument("--shades", type=int, default=None, help="Number of shade structures to place (default: 2)")
    p_opt.add_argument("--budget", type=float, help="Total investment budget in dollars (e.g., 12000)")
    p_opt.add_argument("--length", type=float, default=8.0, help="Canopy length in meters (default: 8.0)")
    p_opt.add_argument("--width", type=float, default=4.0, help="Canopy width in meters (default: 4.0)")
    p_opt.add_argument("--height", type=float, default=4.0, help="Canopy height in meters (default: 4.0)")
    p_opt.add_argument("--transmissivity", type=float, default=0.10, help="Fabric transmissivity (default: 0.10)")

    # Command: demo / run-all
    p_demo = subparsers.add_parser("demo", help="All-in-one live presentation demo")
    p_demo.add_argument("--area", default="berlin", help="Target area (e.g., berlin, london, chicago)")
    p_demo.add_argument("--resolution", "--res", type=float, default=2.0, help="Grid resolution in meters (default: 2.0)")
    p_demo.add_argument("--shades", type=int, default=None, help="Number of shade structures (default: 2)")
    p_demo.add_argument("--budget", type=float, help="Budget in dollars")
    p_demo.add_argument("--length", type=float, default=8.0, help="Canopy length (m)")
    p_demo.add_argument("--width", type=float, default=4.0, help="Canopy width (m)")
    p_demo.add_argument("--height", type=float, default=4.0, help="Canopy height (m)")
    p_demo.add_argument("--transmissivity", type=float, default=0.10, help="Fabric transmissivity")
    p_demo.add_argument("--gpu", action="store_true", help="Enable GPU acceleration")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "calculate":
        cmd_calculate(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command in ["demo", "run-all"]:
        cmd_run_all(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
