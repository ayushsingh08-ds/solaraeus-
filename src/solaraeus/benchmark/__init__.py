"""Benchmark suite for urban comfort simulation."""

from solaraeus.benchmark.harness import (
    BenchmarkRecord,
    ReproducibilityRecord,
    TimingBreakdownRecord,
    run_benchmark_trial,
    run_repeated_benchmark_trials,
)
from solaraeus.benchmark.baseline_comparison import compare_all_baselines
from solaraeus.benchmark.repeated_edits import run_repeated_edit_sequence
from solaraeus.benchmark.tightness import evaluate_certificate_tightness
from solaraeus.benchmark.independent_audit import (
    audit_certificate_independently,
    build_dependency_coverage_audit,
    run_mutation_tests,
    run_detailed_timing_audit,
)

from solaraeus.benchmark.mesh_certificate_audit import run_mesh_certificate_audit
from solaraeus.benchmark.aabb_vs_mesh_benchmark import (
    run_aabb_vs_mesh_benchmark,
    get_canonical_benchmark_scenes,
    run_single_comparison,
)

from solaraeus.benchmark.mesh_scaling_benchmark import (
    run_mesh_scaling_benchmark,
    create_mesh_scaling_scene,
)

__all__ = [
    "BenchmarkRecord",
    "ReproducibilityRecord",
    "TimingBreakdownRecord",
    "run_benchmark_trial",
    "run_repeated_benchmark_trials",
    "compare_all_baselines",
    "run_repeated_edit_sequence",
    "evaluate_certificate_tightness",
    "audit_certificate_independently",
    "build_dependency_coverage_audit",
    "run_mutation_tests",
    "run_detailed_timing_audit",
    "run_mesh_certificate_audit",
    "run_aabb_vs_mesh_benchmark",
    "get_canonical_benchmark_scenes",
    "run_single_comparison",
    "run_mesh_scaling_benchmark",
    "create_mesh_scaling_scene",
]
