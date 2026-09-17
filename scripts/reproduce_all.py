#!/usr/bin/env python3
"""
Solaraeus — Master End-to-End Reproduction Script.
Executes the full pipeline from raw data ingest, physics modeling,
scientific validation, and 3D mesh synthesis to frontend data contract export and web app build.

Usage:
    python scripts/reproduce_all.py
    python scripts/reproduce_all.py --skip-frontend
    python scripts/reproduce_all.py --run-dev
"""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def log_header(title: str):
    width = 75
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def check_python_environment():
    log_header("STEP 1: Checking Python Environment & Dependencies")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version   : {sys.version.split()[0]}")

    if sys.version_info < (3, 10):
        print("[-] WARNING: Python 3.10 or higher is recommended.")

    required_packages = [
        ("numpy", "numpy"),
        ("rasterio", "rasterio"),
        ("geopandas", "geopandas"),
        ("shapely", "shapely"),
        ("xarray", "xarray"),
        ("matplotlib", "matplotlib"),
        ("trimesh", "trimesh"),
        ("pythermalcomfort", "pythermalcomfort"),
        ("pytest", "pytest"),
    ]

    missing = []
    for pkg_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  [+] {pkg_name:20s}: available")
        except ImportError:
            print(f"  [-] {pkg_name:20s}: MISSING")
            missing.append(pkg_name)

    if missing:
        print(f"\n[-] ERROR: Missing required packages: {', '.join(missing)}")
        print("[-] Please install them with: pip install -r requirements.txt")
        sys.exit(1)

    print("[+] All core scientific dependencies verified.")


def run_stage1_backend():
    log_header("STEP 2: Executing Stage 1 Microclimate Backend Pipeline")
    script_path = PROJECT_ROOT / "scripts" / "run_stage1.py"
    cmd = [sys.executable, str(script_path)]
    print(f"Running command: {' '.join(cmd)}")
    start = time.time()
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(f"[-] ERROR: Stage 1 pipeline failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[+] Stage 1 backend completed successfully in {time.time() - start:.1f}s.")


def export_frontend_data_contracts():
    log_header("STEP 3: Exporting React/Three.js JSON Data Contracts")
    script_path = PROJECT_ROOT / "scripts" / "export_frontend_data.py"
    cmd = [sys.executable, str(script_path)]
    print(f"Running command: {' '.join(cmd)}")
    start = time.time()
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(f"[-] ERROR: Frontend data export failed with exit code {res.returncode}")
        sys.exit(res.returncode)
    print(f"[+] Frontend data contracts exported successfully in {time.time() - start:.1f}s.")


def run_unit_tests():
    log_header("STEP 4: Running Scientific Physics & Unit Tests")
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(f"[-] WARNING: Some unit tests failed with code {res.returncode}.")
    else:
        print("[+] All physics and pipeline unit tests PASSED.")


def build_frontend():
    log_header("STEP 5: Building React + Three.js 3D Digital Twin Client")
    frontend_dir = PROJECT_ROOT / "frontend"
    if not frontend_dir.exists():
        print(f"[-] Frontend directory not found at: {frontend_dir}")
        return

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("[-] WARNING: 'npm' not found in PATH. Skipping frontend build.")
        print("[-] Please install Node.js (v18+) to run the web frontend.")
        return

    # Check node_modules
    if not (frontend_dir / "node_modules").exists():
        print("Installing frontend npm dependencies...")
        res_install = subprocess.run([npm_cmd, "install"], cwd=str(frontend_dir))
        if res_install.returncode != 0:
            print(f"[-] ERROR: npm install failed with code {res_install.returncode}")
            return

    # Build production bundle
    print("Building production client bundle...")
    res_build = subprocess.run([npm_cmd, "run", "build"], cwd=str(frontend_dir))
    if res_build.returncode != 0:
        print(f"[-] ERROR: npm run build failed with code {res_build.returncode}")
        return
    print("[+] Frontend client built successfully (dist/ created).")


def print_artifact_summary():
    log_header("REPRODUCTION COMPLETE — SUMMARY OF GENERATED ARTIFACTS")

    # Find dynamically named NetCDF file
    nc_files = list((PROJECT_ROOT / "outputs" / "netcdf").glob("*.nc"))
    nc_path = nc_files[0] if nc_files else PROJECT_ROOT / "outputs" / "netcdf" / "microclimate_washington_square_park_2024-07-15_18utc.nc"

    artifacts = [
        ("Scientific NetCDF Grid", nc_path),
        ("Validation Report", PROJECT_ROOT / "outputs" / "reports" / "stage1_validation.md"),
        ("3D Extruded Buildings (OBJ)", PROJECT_ROOT / "outputs" / "meshes" / "buildings_3d.obj"),
        ("3D Building Mesh (JSON)", PROJECT_ROOT / "outputs" / "meshes" / "buildings_3d.json"),
        ("Simulation Config Contract", PROJECT_ROOT / "outputs" / "data" / "simulation_config.json"),
        ("Available Times Contract", PROJECT_ROOT / "outputs" / "data" / "available_times.json"),
        ("Walkable Grid Contract", PROJECT_ROOT / "outputs" / "data" / "walkable_grid.json"),
        ("Cartographic Figures", PROJECT_ROOT / "outputs" / "figures"),
        ("Production Web Bundle", PROJECT_ROOT / "frontend" / "dist" / "index.html"),
    ]


    for label, path in artifacts:
        status = "[EXISTS]" if path.exists() else "[MISSING]"
        size_str = ""
        if path.exists():
            if path.is_file():
                size_mb = path.stat().st_size / (1024 * 1024)
                size_str = f"({size_mb:.2f} MB)" if size_mb >= 0.1 else f"({path.stat().st_size / 1024:.1f} KB)"
            elif path.is_dir():
                count = len(list(path.glob("*")))
                size_str = f"({count} files)"
        print(f"  {status:9s} {label:32s} -> {path.relative_to(PROJECT_ROOT)} {size_str}")

    print("\n" + "=" * 75)
    print("  HOW TO RUN THE INTERACTIVE 3D DIGITAL TWIN:")
    print("=" * 75)
    print("  1. cd frontend")
    print("  2. npm run dev")
    print("  3. Open your browser at http://localhost:5173/\n")


def main():
    parser = argparse.ArgumentParser(description="Solaraeus Full Pipeline Reproduction Script")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip npm install and build")
    parser.add_argument("--skip-tests", action="store_true", help="Skip pytest test suite")
    parser.add_argument("--run-dev", action="store_true", help="Launch Vite dev server after reproduction")
    args = parser.parse_args()

    start_total = time.time()
    log_header("SOLARAEUS — 3D URBAN MICROCLIMATE DIGITAL TWIN REPRODUCER")

    check_python_environment()
    run_stage1_backend()
    export_frontend_data_contracts()

    if not args.skip_tests:
        run_unit_tests()

    if not args.skip_frontend:
        build_frontend()

    print_artifact_summary()
    print(f"[+] Total reproduction pipeline finished in {time.time() - start_total:.1f}s.")

    if args.run_dev:
        npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
        frontend_dir = PROJECT_ROOT / "frontend"
        if npm_cmd and frontend_dir.exists():
            print("\nLaunching Vite dev server at http://localhost:5173/ ...")
            subprocess.run([npm_cmd, "run", "dev"], cwd=str(frontend_dir))


if __name__ == "__main__":
    main()
