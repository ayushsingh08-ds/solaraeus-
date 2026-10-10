"""Compare current engine output against the frozen golden-master baseline.

Re-runs every captured scenario and asserts the refactored tree reproduces the
baseline:
  * float arrays -> allclose(rtol, atol)   (default rtol=1e-9, atol=1e-12)
  * int/bool arrays (masks) -> exact
  * scalars -> numeric rtol / exact for bool|str|int

GPU scenarios are only checked when (a) the baseline captured them and (b) a GPU
is present now; otherwise they are reported UNVERIFIED and never fail the run.

Exit code 0 = GREEN (behaviour preserved), 1 = DRIFT, 2 = baseline missing.

Usage:  python tools/golden_master/compare.py [--rtol 1e-9] [--atol 1e-12]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

import scenarios as S  # noqa: E402

BASE_DIR = os.path.join(os.path.dirname(__file__), "baseline")


def _load_manifest() -> dict:
    with open(os.path.join(BASE_DIR, "manifest.json")) as f:
        return json.load(f)


def _gpu_available() -> bool:
    try:
        from urban_comfort.backend import is_gpu_available
        return bool(is_gpu_available())
    except Exception:
        return False


def _cmp_arrays(cur: dict, ref, rtol: float, atol: float):
    problems = []
    worst = 0.0
    ref_keys = set(ref.files)
    if set(cur) != ref_keys:
        problems.append(f"array set differs: +{sorted(set(cur) - ref_keys)} "
                        f"-{sorted(ref_keys - set(cur))}")
    for k in sorted(set(cur) & ref_keys):
        a, b = np.asarray(cur[k]), np.asarray(ref[k])
        if a.shape != b.shape:
            problems.append(f"{k}: shape {a.shape} vs {b.shape}")
            continue
        if np.issubdtype(b.dtype, np.floating):
            d = float(np.max(np.abs(a - b))) if a.size else 0.0
            worst = max(worst, d)
            if not np.allclose(a, b, rtol=rtol, atol=atol):
                problems.append(f"{k}: max|diff|={d:.3e} exceeds rtol={rtol}/atol={atol}")
        else:
            if not np.array_equal(a, b):
                problems.append(f"{k}: {int(np.sum(a != b))} discrete cells differ")
    return problems, worst


def _cmp_scalars(cur: dict, ref: dict, rtol: float):
    problems = []
    for k in sorted(set(cur) | set(ref)):
        if k not in cur or k not in ref:
            problems.append(f"scalar {k}: present in only one side")
            continue
        a, b = cur[k], ref[k]
        if isinstance(b, bool) or isinstance(b, str):
            if a != b:
                problems.append(f"scalar {k}: {a!r} != {b!r}")
        elif isinstance(b, (int, float)):
            if not np.isclose(float(a), float(b), rtol=rtol, atol=1e-12):
                problems.append(f"scalar {k}: {a} != {b}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rtol", type=float, default=1e-9)
    ap.add_argument("--atol", type=float, default=1e-12)
    args = ap.parse_args()

    if not os.path.exists(os.path.join(BASE_DIR, "manifest.json")):
        print("NO BASELINE: run tools/golden_master/capture.py first", file=sys.stderr)
        return 2

    manifest = _load_manifest()
    gpu = _gpu_available()
    captured = {n: m for n, m in manifest["scenarios"].items() if m.get("status") == "CAPTURED"}

    any_fail = False
    rows = []
    for name, (builder, needs_gpu) in S.SCENARIOS.items():
        if name not in captured:
            rows.append((name, "UNVERIFIED", manifest["scenarios"].get(name, {}).get("status", "absent")))
            continue
        if needs_gpu and not gpu:
            rows.append((name, "UNVERIFIED", "GPU absent now; baseline exists"))
            continue
        try:
            cur_arrays, cur_scalars = builder()
            ref = np.load(os.path.join(BASE_DIR, f"{name}.npz"), allow_pickle=False)
            with open(os.path.join(BASE_DIR, f"{name}.scalars.json")) as f:
                ref_scalars = json.load(f)
            parr, worst = _cmp_arrays(cur_arrays, ref, args.rtol, args.atol)
            # scalars.json stringifies via default=str; coerce ref types to cur types
            psc = _cmp_scalars(cur_scalars, {k: _coerce(ref_scalars[k], cur_scalars.get(k))
                                             for k in ref_scalars}, args.rtol)
            probs = parr + psc
            if probs:
                any_fail = True
                rows.append((name, "DRIFT", f"max|diff|={worst:.3e}; " + " | ".join(probs[:4])))
            else:
                rows.append((name, "PASS", f"max|diff|={worst:.3e}"))
        except Exception as e:  # noqa: BLE001
            any_fail = True
            rows.append((name, "ERROR", f"{type(e).__name__}: {e}"))

    width = max(len(r[0]) for r in rows)
    print("\nGOLDEN-MASTER COMPARE  (rtol=%g atol=%g, gpu=%s)" % (args.rtol, args.atol, gpu))
    print("-" * 72)
    for name, verdict, detail in rows:
        print(f"  {name:<{width}}  {verdict:<10}  {detail}")
    print("-" * 72)
    print("RESULT:", "DRIFT DETECTED" if any_fail else "GREEN (behaviour preserved)")
    return 1 if any_fail else 0


def _coerce(ref_val, cur_val):
    """scalars.json stored everything JSON-native; re-type to match current."""
    if isinstance(cur_val, bool):
        return bool(ref_val) if not isinstance(ref_val, str) else ref_val == "True"
    if isinstance(cur_val, (int, float)):
        try:
            return type(cur_val)(ref_val)
        except (TypeError, ValueError):
            return ref_val
    return ref_val


if __name__ == "__main__":
    raise SystemExit(main())
