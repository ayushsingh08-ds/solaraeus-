"""Golden-master capture and comparison driver.

Usage
-----
    python tools/golden/golden.py capture [--out DIR] [--only NAME ...]
    python tools/golden/golden.py compare [--baseline DIR] [--out DIR]

Storage layout (one directory per case):
    <dir>/<case_name>/fields.npz     field arrays, float64
    <dir>/<case_name>/metrics.json   scalars + exact-match counts

Comparison contract
-------------------
field arrays        allclose(rtol=1e-9, atol=1e-12)
integer metrics     exactly equal
other scalars       allclose(rtol=1e-9, atol=1e-12)
string metrics      exactly equal
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
import traceback
from pathlib import Path

import numpy as np


def _load_cases():
    """Load the sibling ``cases`` module by file path, without touching sys.path.

    The module must be registered in ``sys.modules`` *before* execution: module
    code (``@dataclass`` on annotated classes, forward references) looks itself
    up by ``__module__`` and raises ``AttributeError`` if the entry is missing.
    """
    spec = importlib.util.spec_from_file_location(
        "golden_cases", Path(__file__).resolve().parent / "cases.py"
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError("cannot locate tools/golden/cases.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(spec.name, None)
        raise
    return module


golden_cases = _load_cases()

DEFAULT_DIR = Path(__file__).resolve().parent / "baseline"
RTOL = 1e-9
ATOL = 1e-12


def gpu_available() -> bool:
    """True if a CUDA device is usable through CuPy."""
    try:
        import cupy as cp

        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False


def capture(out_dir: Path, only: list[str] | None, force: bool = False) -> dict:
    """Run every case and persist its fields and metrics; return a summary.

    The frozen baseline is the project's regression evidence, so writing into
    it requires an explicit ``force=True``.  Capture into a scratch directory
    and compare against the baseline to check a change (that is `make golden`).
    """
    resolved = out_dir.resolve()
    if resolved == DEFAULT_DIR.resolve() and (DEFAULT_DIR / "summary.json").exists():
        if not force:
            raise SystemExit(
                f"refusing to overwrite the frozen golden baseline at {DEFAULT_DIR}\n"
                "Capture to a scratch directory and compare instead:\n"
                "    make golden\n"
                "Re-capture the baseline only when behaviour intentionally changes:\n"
                "    make golden-capture   (passes --force)"
            )
        print("!! --force: overwriting the frozen golden baseline")

    out_dir.mkdir(parents=True, exist_ok=True)
    has_gpu = gpu_available()
    selected = [c for c in golden_cases.CASES if not only or c.name in only]

    summary = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "gpu_available": has_gpu,
        "cases": {},
    }

    for case in selected:
        case_dir = out_dir / case.name
        try:
            fields, metrics = case.fn()
        except Exception as exc:  # noqa: BLE001 - report, never swallow
            summary["cases"][case.name] = {
                "status": "ERROR",
                "area": case.area,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc().splitlines()[-6:],
            }
            print(f"  [ERROR] {case.name}: {type(exc).__name__}: {exc}")
            continue

        shutil.rmtree(case_dir, ignore_errors=True)
        case_dir.mkdir(parents=True, exist_ok=True)
        arrays = {k: np.asarray(v, dtype=np.float64) for k, v in fields.items()}
        np.savez_compressed(case_dir / "fields.npz", **arrays)
        with open(case_dir / "metrics.json", "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=1, sort_keys=True, default=str)

        summary["cases"][case.name] = {
            "status": "OK",
            "area": case.area,
            "n_arrays": len(arrays),
            "n_metrics": len(metrics),
            "note": case.note,
        }
        print(f"  [ok] {case.name}  ({len(arrays)} arrays, {len(metrics)} metrics)")

    with open(out_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1, sort_keys=True)
    return summary


def _compare_values(path: str, base, cand, mismatches: list[str]) -> None:
    """Compare one scalar/string metric and record any mismatch."""
    if isinstance(base, bool) or isinstance(base, int):
        if base != cand:
            mismatches.append(f"{path}: baseline={base!r} candidate={cand!r} (must match exactly)")
    elif isinstance(base, float):
        if not np.allclose(base, cand, rtol=RTOL, atol=ATOL, equal_nan=True):
            mismatches.append(f"{path}: baseline={base!r} candidate={cand!r}")
    elif isinstance(base, str):
        if base != cand:
            mismatches.append(f"{path}: baseline={base!r} candidate={cand!r}")
    elif isinstance(base, list):
        if len(base) != len(cand):
            mismatches.append(f"{path}: length {len(base)} != {len(cand)}")
            return
        for idx, (b, c) in enumerate(zip(base, cand)):
            _compare_values(f"{path}[{idx}]", b, c, mismatches)
    elif isinstance(base, dict):
        for key in sorted(set(base) | set(cand)):
            if key not in base or key not in cand:
                mismatches.append(f"{path}.{key}: present in only one side")
                continue
            _compare_values(f"{path}.{key}", base[key], cand[key], mismatches)


def compare(baseline_dir: Path, candidate_dir: Path) -> tuple[list[str], dict]:
    """Compare a candidate capture against the baseline; return (mismatches, report)."""
    with open(baseline_dir / "summary.json", encoding="utf-8") as handle:
        base_summary = json.load(handle)
    with open(candidate_dir / "summary.json", encoding="utf-8") as handle:
        cand_summary = json.load(handle)

    report: dict = {
        "baseline_python": base_summary.get("python"),
        "candidate_python": cand_summary.get("python"),
        "gpu_available": cand_summary.get("gpu_available"),
        "cases": {},
    }
    mismatches: list[str] = []

    all_cases = sorted(set(base_summary["cases"]) | set(cand_summary["cases"]))
    for name in all_cases:
        base_case = base_summary["cases"].get(name)
        cand_case = cand_summary["cases"].get(name)

        if base_case is None or cand_case is None:
            mismatches.append(f"{name}: missing on one side")
            report["cases"][name] = {"status": "MISSING"}
            continue
        if base_case["status"] != "OK" or cand_case["status"] != "OK":
            # A case that errored at baseline cannot be regression-checked.
            report["cases"][name] = {
                "status": "BASELINE_OR_CANDIDATE_ERROR",
                "baseline": base_case.get("error", base_case["status"]),
                "candidate": cand_case.get("error", cand_case["status"]),
            }
            if base_case["status"] == "OK" and cand_case["status"] != "OK":
                mismatches.append(f"{name}: regressed to ERROR: {cand_case.get('error')}")
            continue

        case_mismatches: list[str] = []

        # --- field arrays ---
        base_npz = np.load(baseline_dir / name / "fields.npz")
        cand_npz = np.load(candidate_dir / name / "fields.npz")
        base_keys, cand_keys = set(base_npz.files), set(cand_npz.files)
        for key in sorted(base_keys - cand_keys):
            case_mismatches.append(f"fields.{key}: missing in candidate")
        for key in sorted(cand_keys - base_keys):
            case_mismatches.append(f"fields.{key}: new in candidate")
        for key in sorted(base_keys & cand_keys):
            a, b = base_npz[key], cand_npz[key]
            if a.shape != b.shape:
                case_mismatches.append(f"fields.{key}: shape {a.shape} != {b.shape}")
                continue
            if not np.allclose(a, b, rtol=RTOL, atol=ATOL, equal_nan=True):
                delta = np.nanmax(np.abs(a - b))
                case_mismatches.append(
                    f"fields.{key}: max|delta|={delta:.3e} exceeds rtol={RTOL} atol={ATOL}"
                )

        # --- metrics ---
        with open(baseline_dir / name / "metrics.json", encoding="utf-8") as handle:
            base_metrics = json.load(handle)
        with open(candidate_dir / name / "metrics.json", encoding="utf-8") as handle:
            cand_metrics = json.load(handle)
        _compare_values("metrics", base_metrics, cand_metrics, case_mismatches)

        report["cases"][name] = {
            "status": "MATCH" if not case_mismatches else "MISMATCH",
            "n_arrays": len(base_keys),
            "mismatches": case_mismatches[:40],
        }
        mismatches.extend(f"{name} -> {m}" for m in case_mismatches)

    report["total_mismatches"] = len(mismatches)
    report["verdict"] = "PASS" if not mismatches else "FAIL"
    return mismatches, report


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["capture", "compare"])
    parser.add_argument("--out", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument(
        "--force",
        action="store_true",
        help="capture: allow overwriting the frozen baseline directory",
    )
    args = parser.parse_args()

    if args.command == "capture":
        print(f"capturing golden master -> {args.out}")
        summary = capture(args.out, args.only, force=args.force)
        ok = sum(1 for c in summary["cases"].values() if c["status"] == "OK")
        print(
            f"captured {ok}/{len(summary['cases'])} cases; gpu_available={summary['gpu_available']}"
        )
        return 0

    candidate_dir = (
        args.out if args.out != DEFAULT_DIR else Path(__file__).resolve().parent / "candidate"
    )
    print(f"comparing {candidate_dir} vs baseline {args.baseline}")
    mismatches, report = compare(args.baseline, candidate_dir)
    (candidate_dir / "comparison.json").write_text(
        json.dumps(report, indent=1, sort_keys=True), encoding="utf-8"
    )
    for name, case in report["cases"].items():
        print(f"  {case['status']:>10}  {name}")
        for line in case.get("mismatches", []):
            print(f"              {line}")
    print(f"verdict: {report['verdict']}  ({report['total_mismatches']} mismatches)")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
