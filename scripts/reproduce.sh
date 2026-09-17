#!/usr/bin/env bash
# =========================================================================
# Solaraeus — Master Reproduction Script (Unix / Linux / macOS)
# =========================================================================

set -e

echo "[Solaraeus] Starting full project reproduction..."

# 1. Activate Python virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    echo "[Solaraeus] Activating virtual environment in .venv..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "[Solaraeus] Activating virtual environment in venv..."
    source venv/bin/activate
fi

# 2. Run master reproduction script
python3 scripts/reproduce_all.py "$@"

echo "[Solaraeus] Reproduction completed successfully!"
