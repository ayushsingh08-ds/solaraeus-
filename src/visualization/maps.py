"""
Publication-Quality Cartographic & Microclimate Visualization Module.
Renders high-resolution raster maps for DSM elevation, shadow masks, SVF, Tmrt, and UTCI.
Includes standardized scale bars, north arrows, statistical annotations, and colormaps.
"""

import logging
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")  # Headless, non-interactive backend preventing Tkinter errors
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
import numpy as np

from src.config import ProjectConfig, StudyArea

logger = logging.getLogger(__name__)


def _add_north_arrow(ax: plt.Axes, x: float = 0.92, y: float = 0.90, length: float = 0.07) -> None:
    """Draws a crisp cartographic North arrow on the given Matplotlib axis."""
    ax.annotate(
        "N",
        xy=(x, y),
        xytext=(x, y - length),
        arrowprops=dict(facecolor="white", edgecolor="black", width=2.5, headwidth=8.0),
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="white",
        xycoords="axes fraction",
        zorder=10,
    )


def _add_scale_bar(
    ax: plt.Axes,
    width_m: float = 100.0,
    resolution_m: float = 1.0,
    x_frac: float = 0.03,
    y_frac: float = 0.04,
) -> None:
    """
    Draws a clean, accurate metric scale bar (e.g. 100m) in the bottom-left corner
    using axes fraction coordinates for absolute positioning without element overlap.
    """
    xlim = ax.get_xlim()
    W_data = abs(xlim[1] - xlim[0])
    # Fraction of axis width corresponding to width_m
    bar_w_frac = (width_m / resolution_m) / W_data
    bar_h_frac = 0.016

    # Background padding box
    bg_box = mpatches.FancyBboxPatch(
        (x_frac - 0.012, y_frac - 0.010),
        bar_w_frac + 0.024,
        bar_h_frac + 0.038,
        transform=ax.transAxes,
        boxstyle="round,pad=0.008",
        facecolor="#1e1e1e",
        edgecolor="#444444",
        alpha=0.88,
        zorder=9,
    )
    ax.add_patch(bg_box)

    # Scale bar divided into two segments (white & gold)
    half_w = bar_w_frac / 2.0
    rect1 = mpatches.Rectangle(
        (x_frac, y_frac),
        half_w,
        bar_h_frac,
        transform=ax.transAxes,
        facecolor="white",
        edgecolor="black",
        linewidth=0.8,
        zorder=10,
    )
    rect2 = mpatches.Rectangle(
        (x_frac + half_w, y_frac),
        half_w,
        bar_h_frac,
        transform=ax.transAxes,
        facecolor="#ffcc00",
        edgecolor="black",
        linewidth=0.8,
        zorder=10,
    )
    ax.add_patch(rect1)
    ax.add_patch(rect2)

    # Centered label above the bar
    label_text = f"{int(width_m)} m" if width_m >= 1.0 else f"{width_m:.1f} m"
    ax.text(
        x_frac + half_w,
        y_frac + bar_h_frac + 0.008,
        label_text,
        transform=ax.transAxes,
        color="white",
        fontsize=8.5,
        fontweight="bold",
        ha="center",
        va="bottom",
        family="sans-serif",
        zorder=10,
    )


def _add_stats_box(ax: plt.Axes, data_arr: np.ndarray, unit: str = "") -> None:
    """Adds a statistics summary box (min, mean, max, std) to the plot above the scale bar."""
    finite_data = data_arr[np.isfinite(data_arr)]
    if len(finite_data) == 0:
        return
    min_v = float(np.min(finite_data))
    mean_v = float(np.mean(finite_data))
    max_v = float(np.max(finite_data))
    std_v = float(np.std(finite_data))

    text = (
        f"Min:  {min_v:5.1f}{unit}\n"
        f"Mean: {mean_v:5.1f}{unit}\n"
        f"Max:  {max_v:5.1f}{unit}\n"
        f"Std:  {std_v:5.1f}{unit}"
    )
    props = dict(boxstyle="round,pad=0.5", facecolor="#1e1e1e", alpha=0.88, edgecolor="#555555")
    ax.text(
        0.03,
        0.12,
        text,
        transform=ax.transAxes,
        fontsize=8.5,
        verticalalignment="bottom",
        bbox=props,
        color="white",
        family="monospace",
        zorder=10,
    )


def _to_2d_raster(
    values: np.ndarray,
    cfg: ProjectConfig,
    pedestrian_points: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Converts 1D or 2D values into a 2D (H, W) raster using study area grid bounds.
    """
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim == 2:
        return arr

    # Target grid dimensions
    bounds = cfg.study_area.utm_bounds
    res = cfg.study_area.resolution_m
    W = int(round((bounds[2] - bounds[0]) / res))
    H = int(round((bounds[3] - bounds[1]) / res))

    if len(arr) == H * W:
        return arr.reshape((H, W))

    # If length doesn't match total grid, map coordinates if pedestrian_points is given
    out = np.full((H, W), np.nan, dtype=np.float32)
    if pedestrian_points is not None and len(pedestrian_points) == len(arr):
        xs = pedestrian_points[:, 0]
        ys = pedestrian_points[:, 1]
        cols = np.clip(np.round((xs - bounds[0]) / res).astype(int), 0, W - 1)
        rows = np.clip(np.round((bounds[3] - ys) / res).astype(int), 0, H - 1)
        out[rows, cols] = arr
        return out

    # Fallback padding/truncation
    out.ravel()[: len(arr)] = arr
    return out


def plot_dsm(
    dsm: np.ndarray,
    cfg: Optional[ProjectConfig] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Renders 2.5D Digital Surface Model (DSM) elevation map with topography, buildings,
    scale bar, north arrow, colorbar, and statistics box.
    """
    if cfg is None:
        cfg = ProjectConfig()
    if output_path is None:
        output_path = cfg.data.figure_dir / "dsm_wsp.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dsm_2d = np.asarray(dsm, dtype=np.float32)

    fig, ax = plt.subplots(figsize=(10, 9), constrained_layout=True)

    im = ax.imshow(dsm_2d, cmap="viridis", origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.03)
    cbar.set_label("Surface Elevation (m ASL)", fontsize=10, fontweight="bold")

    _add_north_arrow(ax)
    _add_scale_bar(ax, width_m=100.0, resolution_m=cfg.study_area.resolution_m)
    _add_stats_box(ax, dsm_2d, unit="m")

    title = f"Solaraeus — 2.5D Digital Surface Model (DSM)\n{cfg.study_area.name} (1.0m Resolution)"
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("UTM Easting (m relative)", fontsize=10)
    ax.set_ylabel("UTM Northing (m relative)", fontsize=10)

    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info(f"DSM plot saved to {output_path}")
    return output_path


def plot_shadows(
    dsm: np.ndarray,
    shadow_mask: np.ndarray,
    alt_rad: float,
    az_rad: float,
    cfg: Optional[ProjectConfig] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Renders direct solar shadow mask overlay on the DSM with sun direction arrow,
    scale bar, north arrow, illumination statistics, and legend.
    """
    if cfg is None:
        cfg = ProjectConfig()
    if output_path is None:
        output_path = cfg.data.figure_dir / "shadow_mask_wsp.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dsm_2d = np.asarray(dsm, dtype=np.float32)
    sunlit_2d = _to_2d_raster(shadow_mask, cfg).astype(bool)

    fig, ax = plt.subplots(figsize=(10, 9), constrained_layout=True)

    # Grayscale DSM terrain base
    ax.imshow(dsm_2d, cmap="gray", origin="upper", alpha=0.7)

    # High-contrast overlay: Navy Blue = Shaded, Warm Amber/Gold = Sunlit
    cmap_shadow = plt.cm.colors.ListedColormap(["#1a2a3a", "#ffcc00"])
    norm_shadow = Normalize(vmin=0, vmax=1)
    ax.imshow(sunlit_2d.astype(int), cmap=cmap_shadow, norm=norm_shadow, alpha=0.55, origin="upper")

    sunlit_pct = (np.count_nonzero(sunlit_2d) / sunlit_2d.size) * 100.0
    shaded_pct = 100.0 - sunlit_pct

    # Legend patches
    patch_sun = mpatches.Patch(color="#ffcc00", label=f"Sunlit: {sunlit_pct:.1f}%")
    patch_shade = mpatches.Patch(color="#1a2a3a", label=f"Shaded: {shaded_pct:.1f}%")
    ax.legend(
        handles=[patch_sun, patch_shade],
        loc="lower right",
        facecolor="#1e1e1e",
        labelcolor="white",
        fontsize=10,
        framealpha=0.9,
    )

    alt_deg = math.degrees(alt_rad)
    az_deg = math.degrees(az_rad)

    # Sun direction indicator
    ax.annotate(
        f"Sun: {az_deg:.0f}° az, {alt_deg:.0f}° alt",
        xy=(0.06, 0.92),
        xytext=(0.06, 0.84),
        arrowprops=dict(facecolor="#ffaa00", edgecolor="black", width=2.5, headwidth=7.5),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#ffaa00",
        xycoords="axes fraction",
        zorder=10,
    )

    _add_north_arrow(ax)
    _add_scale_bar(ax, width_m=100.0, resolution_m=cfg.study_area.resolution_m)

    title = (
        f"Solaraeus — Direct Solar Shadow Occlusion\n"
        f"{cfg.study_area.name} — {cfg.simulation.date} 14:00 EDT (18:00 UTC)"
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("UTM Easting (m relative)", fontsize=10)
    ax.set_ylabel("UTM Northing (m relative)", fontsize=10)

    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info(f"Shadow mask plot saved to {output_path}")
    return output_path


def plot_svf(
    svf_values: np.ndarray,
    cfg: Optional[ProjectConfig] = None,
    pedestrian_points: Optional[np.ndarray] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Renders Sky View Factor (SVF) heat map with colorbar, scale bar, north arrow, and stats box.
    """
    if cfg is None:
        cfg = ProjectConfig()
    if output_path is None:
        output_path = cfg.data.figure_dir / "svf_wsp.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    svf_2d = _to_2d_raster(svf_values, cfg, pedestrian_points)

    fig, ax = plt.subplots(figsize=(10, 9), constrained_layout=True)

    im = ax.imshow(svf_2d, cmap="cividis", vmin=0.0, vmax=1.0, origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.03)
    cbar.set_label("Sky View Factor (SVF, 0 = Obstructed, 1 = Open Sky)", fontsize=10, fontweight="bold")

    _add_north_arrow(ax)
    _add_scale_bar(ax, width_m=100.0, resolution_m=cfg.study_area.resolution_m)
    _add_stats_box(ax, svf_2d)

    title = (
        f"Solaraeus — Sky View Factor (SVF)\n"
        f"{cfg.study_area.name} — Steyn (1980) 360° Ray-Marching (1m Resolution)"
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("UTM Easting (m relative)", fontsize=10)
    ax.set_ylabel("UTM Northing (m relative)", fontsize=10)

    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info(f"SVF plot saved to {output_path}")
    return output_path


def plot_tmrt(
    tmrt_values: np.ndarray,
    cfg: Optional[ProjectConfig] = None,
    pedestrian_points: Optional[np.ndarray] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Renders Mean Radiant Temperature (Tmrt) heat map with colorbar, scale bar, north arrow, and stats box.
    """
    if cfg is None:
        cfg = ProjectConfig()
    if output_path is None:
        output_path = cfg.data.figure_dir / "tmrt_wsp.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmrt_2d = _to_2d_raster(tmrt_values, cfg, pedestrian_points)

    fig, ax = plt.subplots(figsize=(10, 9), constrained_layout=True)

    # Formatted dynamic color range
    valid_tmrt = tmrt_2d[np.isfinite(tmrt_2d)]
    vmin = float(max(20.0, np.floor(np.percentile(valid_tmrt, 1)))) if len(valid_tmrt) > 0 else 25.0
    vmax = float(min(75.0, np.ceil(np.percentile(valid_tmrt, 99)))) if len(valid_tmrt) > 0 else 65.0

    im = ax.imshow(tmrt_2d, cmap="magma", vmin=vmin, vmax=vmax, origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.03)
    cbar.set_label("Mean Radiant Temperature Tmrt (°C)", fontsize=10, fontweight="bold")

    _add_north_arrow(ax)
    _add_scale_bar(ax, width_m=100.0, resolution_m=cfg.study_area.resolution_m)
    _add_stats_box(ax, tmrt_2d, unit="°C")

    title = (
        f"Solaraeus — Mean Radiant Temperature (Tmrt)\n"
        f"{cfg.study_area.name} — {cfg.simulation.date} 14:00 EDT (18:00 UTC)"
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("UTM Easting (m relative)", fontsize=10)
    ax.set_ylabel("UTM Northing (m relative)", fontsize=10)

    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info(f"Tmrt plot saved to {output_path}")
    return output_path


def plot_utci(
    utci_values: np.ndarray,
    cfg: Optional[ProjectConfig] = None,
    pedestrian_points: Optional[np.ndarray] = None,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Renders Universal Thermal Climate Index (UTCI) heat map with thermal stress thresholds,
    colorbar, scale bar, north arrow, and stats box.
    """
    if cfg is None:
        cfg = ProjectConfig()
    if output_path is None:
        output_path = cfg.data.figure_dir / "utci_wsp.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    utci_2d = _to_2d_raster(utci_values, cfg, pedestrian_points)

    fig, ax = plt.subplots(figsize=(10, 9), constrained_layout=True)

    im = ax.imshow(utci_2d, cmap="Spectral_r", vmin=26.0, vmax=46.0, origin="upper")
    cbar = plt.colorbar(im, ax=ax, shrink=0.75, pad=0.03)
    cbar.set_label("Universal Thermal Climate Index (°C)", fontsize=10, fontweight="bold")

    # Standard UTCI stress category annotations
    cbar.set_ticks([26, 32, 38, 46])
    cbar.set_ticklabels(["26 (Moderate)", "32 (Strong)", "38 (Very Strong)", "46 (Extreme)"])

    _add_north_arrow(ax)
    _add_scale_bar(ax, width_m=100.0, resolution_m=cfg.study_area.resolution_m)
    _add_stats_box(ax, utci_2d, unit="°C")

    title = (
        f"Solaraeus — Universal Thermal Climate Index (UTCI)\n"
        f"{cfg.study_area.name} — {cfg.simulation.date} 14:00 EDT (18:00 UTC)"
    )
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("UTM Easting (m relative)", fontsize=10)
    ax.set_ylabel("UTM Northing (m relative)", fontsize=10)

    plt.savefig(output_path, dpi=200)
    plt.close()
    logger.info(f"UTCI plot saved to {output_path}")
    return output_path
