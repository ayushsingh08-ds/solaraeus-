"""
Test suite for 3D In-Scene Optimization (Part 14, 16).
"""

from pathlib import Path
import json
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
OPT_DIR = ROOT / "results/final_3d_integrated_simulation/optimization"


def test_optimization_manifest_and_config():
    p = OPT_DIR / "3d_optimizer_config.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "3D_OPTIMIZATION_ACTIVE"
    assert data["evaluated_in_3d"] is True
    assert "CAND_0028_EVOL" in data["best_candidate_id"]


def test_candidate_csvs_and_scores():
    p_hist = OPT_DIR / "3d_candidate_history.csv"
    p_best = OPT_DIR / "3d_best_candidates.csv"
    assert p_hist.exists()
    assert p_best.exists()

    df_hist = pd.read_csv(p_hist)
    df_best = pd.read_csv(p_best)

    assert len(df_hist) >= 3
    assert len(df_best) >= 1
    # Feasible candidates have positive cooling scores
    feasible_scores = df_hist[df_hist["is_feasible"]]["score"]
    assert (feasible_scores > 0).all()
