"""Benchmark suite for urban comfort simulation."""

from urban_comfort.benchmark.harness import (
    BenchmarkHarness,
    BenchmarkRecord,
    ReproducibilityRecord,
    TimingBreakdownRecord,
    run_repeated_benchmark_trials,
)
from urban_comfort.benchmark.baseline_comparison import run_baseline_comparison
from urban_comfort.benchmark.repeated_edits import run_repeated_edits_benchmark
from urban_comfort.benchmark.tightness import compute_certificate_tightness

__all__ = [
    "BenchmarkHarness",
    "BenchmarkRecord",
    "ReproducibilityRecord",
    "TimingBreakdownRecord",
    "run_repeated_benchmark_trials",
    "run_baseline_comparison",
    "run_repeated_edits_benchmark",
    "compute_certificate_tightness",
]
