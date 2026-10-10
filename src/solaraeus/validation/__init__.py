"""
Validation subpackage: comparisons, error norms, and verification metrics, plus
the benchmark/audit suite (reproducibility, certificate tightness, independent
audits, baseline comparisons) and the mesh-geometry benchmarks.
"""

from solaraeus.validation.comparisons import (
    ComparisonMetrics, compare_arrays, compare_results, format_comparison_summary
)
from solaraeus.validation.metrics import (
    compute_shadow_iou, compute_utci_category_agreement, compute_error_percentiles
)

from solaraeus.validation.harness import (
    BenchmarkRecord,
    ReproducibilityRecord,
    TimingBreakdownRecord,
    run_benchmark_trial,
    run_repeated_benchmark_trials,
)
from solaraeus.validation.baseline_comparison import compare_all_baselines
from solaraeus.validation.repeated_edits import run_repeated_edit_sequence
from solaraeus.validation.tightness import evaluate_certificate_tightness
from solaraeus.validation.independent_audit import (
    audit_certificate_independently,
    build_dependency_coverage_audit,
    run_mutation_tests,
    run_detailed_timing_audit,
)

from solaraeus.validation.mesh.mesh_certificate_audit import run_mesh_certificate_audit
from solaraeus.validation.mesh.aabb_vs_mesh_benchmark import (
    run_aabb_vs_mesh_benchmark,
    get_canonical_benchmark_scenes,
    run_single_comparison,
)
from solaraeus.validation.mesh.mesh_scaling_benchmark import (
    run_mesh_scaling_benchmark,
    create_mesh_scaling_scene,
)

__all__ = [
    "ComparisonMetrics",
    "compare_arrays",
    "compare_results",
    "format_comparison_summary",
    "compute_shadow_iou",
    "compute_utci_category_agreement",
    "compute_error_percentiles",
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
