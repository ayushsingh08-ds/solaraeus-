#!/usr/bin/env bash
# ==============================================================================
# SOLARAEUS CPU Benchmark Runner (Stage 5)
# Usage:
#   ./benchmarks/benchmark_cpu.sh [scene] [mode] [repeats] [output_path]
# Example:
#   ./benchmarks/benchmark_cpu.sh scene_b all 5
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

SCENE="${1:-all}"
MODE="${2:-all}"
REPEATS="${3:-5}"
OUTPUT="${4:-${ROOT_DIR}/results/raw/stage_5/benchmark_cpu_results.json}"

echo "================================================================================"
echo "SOLARAEUS Stage 5: Running CPU Performance Benchmark"
echo "Scene:   ${SCENE}"
echo "Mode:    ${MODE}"
echo "Repeats: ${REPEATS}"
echo "Output:  ${OUTPUT}"
echo "================================================================================"

python "${ROOT_DIR}/benchmarks/benchmark_cpu.py" \
    --scene "${SCENE}" \
    --mode "${MODE}" \
    --repeats "${REPEATS}" \
    --output "${OUTPUT}"
