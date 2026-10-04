"""
Certificate Conservatism and Tightness Quantifier.

Computes fine-grained distributional metrics on certificate slack and bound-to-error ratios:
- actual_error = abs(incremental_tmrt - full_tmrt)
- slack = predicted_bound - actual_error
- ratio = predicted_bound / max(actual_error, 1e-12)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import numpy as np

from urban_comfort.incremental.certificate import ErrorCertificate


@dataclass
class CertificateTightnessMetrics:
    """Detailed distributional metrics for certificate evaluation."""
    scenario_id: str
    total_cells: int
    reused_cells: int
    recomputed_cells: int
    reused_fraction: float
    min_slack_k: float
    percentile_1_slack_k: float
    median_slack_k: float
    percentile_99_slack_k: float
    negative_slack_count: int
    mean_bound_to_error_ratio: float
    median_bound_to_error_ratio: float
    percentile_95_bound_to_error_ratio: float
    percentile_99_bound_to_error_ratio: float
    fraction_error_below_precision: float
    fraction_bound_below_tolerance: float
    max_actual_error_k: float
    mean_actual_error_k: float
    max_predicted_bound_k: float
    tolerance_k: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_certificate_tightness(cert: ErrorCertificate,
                                   incremental_tmrt: np.ndarray,
                                   full_tmrt: np.ndarray,
                                   scenario_id: str = "default",
                                   numerical_precision_k: float = 1e-6) -> CertificateTightnessMetrics:
    """
    Computes exact cell-by-cell slack, ratios, and percentile distributions across the domain.
    """
    actual_error = np.abs(incremental_tmrt - full_tmrt)
    predicted_bound = cert.predicted_error_bound
    slack = predicted_bound - actual_error

    # Avoid division by zero: clamp denominator to 1e-12
    ratios = predicted_bound / np.maximum(actual_error, 1e-12)

    total_cells = int(slack.size)
    reused_cells = cert.reused_cells
    recomputed_cells = cert.affected_cells
    reused_fraction = float(cert.reused_fraction)

    min_slack = float(np.min(slack))
    p1_slack = float(np.percentile(slack, 1.0))
    med_slack = float(np.median(slack))
    p99_slack = float(np.percentile(slack, 99.0))
    neg_slack_cnt = int(np.sum(slack < -numerical_precision_k))

    mean_ratio = float(np.mean(ratios))
    med_ratio = float(np.median(ratios))
    p95_ratio = float(np.percentile(ratios, 95.0))
    p99_ratio = float(np.percentile(ratios, 99.0))

    frac_below_prec = float(np.mean(actual_error < numerical_precision_k))
    frac_bound_below_tol = float(np.mean(predicted_bound <= cert.tolerance))

    max_actual_err = float(np.max(actual_error))
    mean_actual_err = float(np.mean(actual_error))
    max_bound = float(cert.max_predicted_bound)

    return CertificateTightnessMetrics(
        scenario_id=scenario_id,
        total_cells=total_cells,
        reused_cells=reused_cells,
        recomputed_cells=recomputed_cells,
        reused_fraction=reused_fraction,
        min_slack_k=min_slack,
        percentile_1_slack_k=p1_slack,
        median_slack_k=med_slack,
        percentile_99_slack_k=p99_slack,
        negative_slack_count=neg_slack_cnt,
        mean_bound_to_error_ratio=mean_ratio,
        median_bound_to_error_ratio=med_ratio,
        percentile_95_bound_to_error_ratio=p95_ratio,
        percentile_99_bound_to_error_ratio=p99_ratio,
        fraction_error_below_precision=frac_below_prec,
        fraction_bound_below_tolerance=frac_bound_below_tol,
        max_actual_error_k=max_actual_err,
        mean_actual_error_k=mean_actual_err,
        max_predicted_bound_k=max_bound,
        tolerance_k=float(cert.tolerance)
    )
