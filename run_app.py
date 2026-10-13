#!/usr/bin/env python3
"""
SOLARAEUS Digital Twin Engine & Interface Launcher.

Runs the segregated microclimate engine API server and hosts
the interactive 3D WebGL digital twin web interface.
"""

import sys
import argparse
from pathlib import Path

# Add src to sys.path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))

from solaraeus.server.app import run_server


def main():
    parser = argparse.ArgumentParser(description="Launch SOLARAEUS Digital Twin Engine & UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    print("\n" + "=" * 75)
    print("      SOLARAEUS 3D URBAN MICROCLIMATE DIGITAL TWIN & AI SOLVER")
    print("=" * 75)
    print(f"  Unified Input Data:     data/input/<case_area>/")
    print(f"  Segregated Processed:   data/processed/<case_area>/<timestamp>/")
    print(f"  Segregated Optimized:   data/optimized/<case_area>/<timestamp>/")
    print(f"  Web Interface URL:      http://{args.host}:{args.port}")
    print("=" * 75 + "\n")

    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
