"""
Validation subpackage for comparisons, error norms, and verification metrics.
"""

from urban_comfort.validation.comparisons import (
    ComparisonMetrics, compare_arrays, compare_results, format_comparison_summary
)
from urban_comfort.validation.metrics import (
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
