"""Capture the golden-master baseline (run ONCE, at the pre-cleanup state).

Writes, under ``tools/golden_master/baseline/``:
  * ``<scenario>.npz``          -- all arrays for the scenario
  * ``<scenario>.scalars.json`` -- all scalars for the scenario
  * ``manifest.json``           -- provenance + env + determinism self-check

GPU scenarios are captured when a GPU is present; otherwise they are recorded as
UNVERIFIED and skipped (never fabricated).

Usage:  python tools/golden_master/capture.py
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time

import numpy as np

import scenarios as S  # noqa: E402  (same-dir import; run as a script)

BASE_DIR = os.path.join(os.path.dirname(__file__), "baseline")


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=os.path.dirname(__file__),
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def _versions() -> dict:
    out = {"python": platform.python_version(), "numpy": np.__version__}
    for mod in ("scipy", "sklearn", "trimesh", "pyproj", "pythermalcomfort", "cupy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:
            out[mod] = "absent"
    return out


def _max_abs_diff(a: dict, b: dict) -> float:
    worst = 0.0
    for k in a:
        da, db = np.asarray(a[k]), np.asarray(b[k])
        if da.shape != db.shape:
            return float("inf")
        if np.issubdtype(da.dtype, np.floating):
            worst = max(worst, float(np.max(np.abs(da - db))) if da.size else 0.0)
        else:
            worst = max(worst, 0.0 if np.array_equal(da, db) else float("inf"))
    return worst


def _gpu_available() -> bool:
    try:
        from solaraeus.backend import is_gpu_available
        return bool(is_gpu_available())
    except Exception:
        return False


def main() -> int:
    os.makedirs(BASE_DIR, exist_ok=True)
    gpu = _gpu_available()
    manifest = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "git_sha": _git("rev-parse", "HEAD"),
        "git_describe": _git("describe", "--tags", "--always"),
        "env": _versions(),
        "gpu_available": gpu,
        "scenarios": {},
    }

    for name, (builder, needs_gpu) in S.SCENARIOS.items():
        if needs_gpu and not gpu:
            manifest["scenarios"][name] = {"status": "UNVERIFIED_NO_GPU"}
            print(f"[skip] {name}: UNVERIFIED (no GPU)")
            continue
        try:
            arrays, scalars = builder()
            arrays2, _ = builder()  # determinism self-check
            drift = _max_abs_diff(arrays, arrays2)
            np.savez_compressed(os.path.join(BASE_DIR, f"{name}.npz"), **arrays)
            with open(os.path.join(BASE_DIR, f"{name}.scalars.json"), "w") as f:
                json.dump(scalars, f, indent=2, sort_keys=True, default=str)
            manifest["scenarios"][name] = {
                "status": "CAPTURED",
                "n_arrays": len(arrays),
                "n_scalars": len(scalars),
                "run_to_run_max_abs_diff": drift,
            }
            print(f"[ok]   {name}: {len(arrays)} arrays, {len(scalars)} scalars, "
                  f"run-to-run max|diff|={drift:.3e}")
        except Exception as e:  # noqa: BLE001 - record, never fabricate
            manifest["scenarios"][name] = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
            print(f"[err]  {name}: {type(e).__name__}: {e}")

    with open(os.path.join(BASE_DIR, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"\nmanifest -> {os.path.join(BASE_DIR, 'manifest.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
