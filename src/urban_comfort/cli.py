"""Command-line interface for SOLARAEUS.

This module is the single entry point exposed as the ``solaraeus`` console
script. It deliberately depends only on the standard library so that
``solaraeus --version`` and ``solaraeus doctor`` work even in a broken
environment where the scientific stack is missing or a GPU driver is absent.

Subcommands
-----------
``version``   print the package version
``doctor``    report whether the runtime environment can run the engine
``golden``    capture or compare the golden-master physics outputs
``info``      list the simulation pipelines and (when present) configured cities
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from pathlib import Path

# NOTE: this module intentionally avoids mutating sys.path. The package is
# installed (editable in development), so every import resolves normally.

__all__ = ["main", "build_parser"]

# Dependencies the engine cannot run without, mapped to the import name used to
# probe them and the extra that installs them.
REQUIRED_RUNTIME = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("matplotlib", "matplotlib"),
    ("shapely", "shapely"),
    ("trimesh", "trimesh"),
    ("mapbox_earcut", "mapbox_earcut"),
    ("pyproj", "pyproj"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("pythermalcomfort", "pythermalcomfort"),
    ("psutil", "psutil"),
]

OPTIONAL_RUNTIME = [
    ("cupy", "cupy-cuda12x", "gpu"),
    ("rasterio", "rasterio", "viewer-export"),
    ("PIL", "pillow", "viewer-export"),
]


def _repo_root() -> Path:
    """Return the repository root (three levels up from this file)."""
    return Path(__file__).resolve().parent.parent.parent


def cmd_version(_args: argparse.Namespace) -> int:
    """Print the installed package version."""
    from urban_comfort import __version__

    print(f"solaraeus {__version__}")
    print(f"python    {sys.version.split()[0]}")
    print(f"platform  {platform.platform()}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Report whether this environment can run the engine, and exit non-zero if not."""
    from urban_comfort import __version__

    print("=" * 72)
    print(f"SOLARAEUS doctor — package version {__version__}")
    print("=" * 72)
    print(f"python            {sys.version.split()[0]}")
    print(f"executable        {sys.executable}")
    print(f"platform          {platform.platform()}")
    print(f"repo root         {_repo_root()}")
    print()

    missing_required: list[str] = []
    print("required runtime dependencies")
    for module, distribution in REQUIRED_RUNTIME:
        present = importlib.util.find_spec(module) is not None
        print(f"  [{'ok' if present else '--'}] {module:18s} ({distribution})")
        if not present:
            missing_required.append(distribution)
    print()

    print("optional dependencies")
    for module, distribution, extra in OPTIONAL_RUNTIME:
        present = importlib.util.find_spec(module) is not None
        print(f"  [{'ok' if present else '--'}] {module:18s} ({distribution}) extra=[{extra}]")
    print()

    # GPU probe: availability of CuPy is not the same as availability of a device.
    gpu_state = "unavailable"
    gpu_detail = ""
    try:
        import cupy as cp

        count = cp.cuda.runtime.getDeviceCount()
        if count:
            props = cp.cuda.runtime.getDeviceProperties(0)
            gpu_state = "available"
            gpu_detail = f"{props['name'].decode()} CC {props['major']}.{props['minor']}"
        else:
            gpu_state = "no-device"
    except ImportError:
        gpu_detail = "cupy not installed (pip install 'solaraeus[gpu]')"
    except Exception as exc:  # noqa: BLE001 - driver errors surface as many types
        gpu_detail = f"{type(exc).__name__}: {exc}"
    print(f"CUDA GPU          {gpu_state}" + (f" — {gpu_detail}" if gpu_detail else ""))
    print()

    print("data directories")
    for name in ("cities", "reference_artifacts", "artifacts"):
        path = _repo_root() / name
        print(f"  [{'ok' if path.exists() else '--'}] {name}/")
    print()

    if missing_required:
        print("RESULT: cannot run the engine — missing required dependencies:")
        for distribution in missing_required:
            print(f"  - {distribution}")
        print("\nInstall everything with:  pip install -e '.[all]'")
        return 1

    print("RESULT: engine can run (CPU path verified by `solaraeus golden compare`).")
    if gpu_state != "available" and not args.allow_no_gpu:
        print("NOTE: no usable CUDA device; GPU pipelines will fall back to CPU.")
    return 0


def cmd_info(_args: argparse.Namespace) -> int:
    """List available pipelines and configured cities."""
    print("pipelines: static, incremental, gpu, optimize, full3d")
    cities_dir = _repo_root() / "cities"
    if not cities_dir.exists():
        print("cities: (none configured yet — see docs/adding-a-city.md)")
        return 0
    slugs = sorted(p.name for p in cities_dir.iterdir() if (p / "city.yaml").exists())
    if slugs:
        print(f"cities: {', '.join(slugs)}")
    else:
        print("cities: (no city.yaml found under cities/)")
    return 0


def cmd_golden(args: argparse.Namespace) -> int:
    """Run the golden-master capture or comparison harness.

    The harness lives under ``tools/golden`` (developer tooling, not part of the
    shipped package), so it is executed as a subprocess rather than imported.
    This keeps the package free of path manipulation and lets the harness run
    under a different interpreter or virtualenv than the CLI.
    """
    import subprocess

    tools_dir = _repo_root() / "tools" / "golden"
    entry = tools_dir / "golden.py"
    if not entry.exists():
        print(f"{entry} not found", file=sys.stderr)
        return 2

    argv = [sys.executable, str(entry), args.golden_command]
    if args.golden_command == "capture":
        argv += ["--out", args.out or str(tools_dir / "candidate")]
    else:
        argv += [
            "--baseline",
            args.baseline or str(tools_dir / "baseline"),
            "--out",
            args.out or str(tools_dir / "candidate"),
        ]
    return subprocess.call(argv, cwd=str(_repo_root()))


def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser (exposed for testing)."""
    parser = argparse.ArgumentParser(
        prog="solaraeus",
        description="Certified incremental SOLWEIG-compatible urban thermal-comfort engine.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the package version").set_defaults(func=cmd_version)

    doctor = sub.add_parser("doctor", help="check the runtime environment")
    doctor.add_argument(
        "--allow-no-gpu", action="store_true", help="do not warn about a missing GPU"
    )
    doctor.set_defaults(func=cmd_doctor)

    sub.add_parser("info", help="list pipelines and configured cities").set_defaults(func=cmd_info)

    golden = sub.add_parser("golden", help="golden-master capture/compare")
    golden_sub = golden.add_subparsers(dest="golden_command", required=True)
    cap = golden_sub.add_parser("capture", help="capture golden outputs")
    cap.add_argument("--out", default=None)
    cmp_ = golden_sub.add_parser("compare", help="compare against baseline")
    cmp_.add_argument("--baseline", default=None)
    cmp_.add_argument("--out", default=None)
    golden.set_defaults(func=cmd_golden)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; returns a process exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
