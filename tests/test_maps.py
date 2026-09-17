"""
Unit tests for visualization map generation (src/visualization/maps.py).
"""

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pytest
from pathlib import Path

from src.config import ProjectConfig, WASHINGTON_SQUARE_PARK
from src.visualization.maps import (
    plot_dsm,
    plot_shadows,
    plot_svf,
    plot_tmrt,
    plot_utci,
)


@pytest.fixture
def sample_data(tmp_path):
    cfg = ProjectConfig(study_area=WASHINGTON_SQUARE_PARK)
    # Use temporary directory for test figure generation
    cfg.data.figure_dir.mkdir(parents=True, exist_ok=True)

    H, W = 40, 40
    dsm = np.full((H, W), 10.0, dtype=np.float32)
    dsm[15:25, 15:25] = 30.0

    shadow_mask = np.ones((H, W), dtype=bool)
    shadow_mask[10:15, 15:25] = False  # Shaded north of building

    svf = np.full((H, W), 0.90, dtype=np.float32)
    svf[15:25, 15:25] = 0.40

    tmrt = np.full((H, W), 58.0, dtype=np.float32)
    tmrt[~shadow_mask] = 36.0

    utci = np.full((H, W), 40.0, dtype=np.float32)
    utci[~shadow_mask] = 34.0

    return {
        "cfg": cfg,
        "tmp_path": tmp_path,
        "dsm": dsm,
        "shadow_mask": shadow_mask,
        "svf": svf,
        "tmrt": tmrt,
        "utci": utci,
    }


def test_plot_dsm(sample_data):
    out_path = sample_data["tmp_path"] / "test_dsm.png"
    p = plot_dsm(sample_data["dsm"], sample_data["cfg"], output_path=out_path)
    assert p.exists()
    assert p.stat().st_size > 1000


def test_plot_shadows(sample_data):
    out_path = sample_data["tmp_path"] / "test_shadows.png"
    p = plot_shadows(
        sample_data["dsm"],
        sample_data["shadow_mask"],
        alt_rad=1.17,
        az_rad=2.49,
        cfg=sample_data["cfg"],
        output_path=out_path,
    )
    assert p.exists()
    assert p.stat().st_size > 1000


def test_plot_svf(sample_data):
    out_path = sample_data["tmp_path"] / "test_svf.png"
    p = plot_svf(sample_data["svf"], sample_data["cfg"], output_path=out_path)
    assert p.exists()
    assert p.stat().st_size > 1000


def test_plot_tmrt(sample_data):
    out_path = sample_data["tmp_path"] / "test_tmrt.png"
    p = plot_tmrt(sample_data["tmrt"], sample_data["cfg"], output_path=out_path)
    assert p.exists()
    assert p.stat().st_size > 1000


def test_plot_utci(sample_data):
    out_path = sample_data["tmp_path"] / "test_utci.png"
    p = plot_utci(sample_data["utci"], sample_data["cfg"], output_path=out_path)
    assert p.exists()
    assert p.stat().st_size > 1000
