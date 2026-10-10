"""
Validation subpackage for comparisons, error norms, and verification metrics.
"""

from solaraeus.validation.comparisons import (
    ComparisonMetrics, compare_arrays, compare_results, format_comparison_summary
)
from solaraeus.validation.metrics import (
    compute_shadow_iou, compute_utci_category_agreement, compute_error_percentiles
)

__all__ = [
    "ComparisonMetrics",
    "compare_arrays",
    "compare_results",
    "format_comparison_summary",
    "compute_shadow_iou",
    "compute_utci_category_agreement",
    "compute_error_percentiles",
]
