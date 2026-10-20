"""Reproducible statistical drift monitoring for AeroGuard 2.1.

Evaluates covariate distribution shifts between baseline training features
and operational/evaluation datasets using non-parametric Kolmogorov-Smirnov (KS)
tests and the Population Stability Index (PSI).

Operational Caution:
Covariate shift (data drift) quantifies P(X_eval) != P(X_train). It does NOT
constitute ground-truth model degradation unless validated against verified
terminal failure labels Y.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from aircraft_pm.config import INFORMATIVE_SENSOR_COLS


def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """Calculate Population Stability Index (PSI) between two continuous samples.

    PSI = sum((P_i - Q_i) * ln(P_i / Q_i))
    where P_i is the proportion of reference points in bin i and Q_i is the
    proportion of current points in bin i.

    Thresholds:
    - PSI < 0.10: Stable (insignificant change)
    - 0.10 <= PSI < 0.25: Moderate shift (advisory monitoring)
    - PSI >= 0.25: Significant distribution shift (drift alert)

    Args:
        reference: 1D array of baseline reference values.
        current: 1D array of comparison values.
        num_bins: Number of quantiles/bins to partition the reference.
        epsilon: Smoothing factor to avoid division by zero or ln(0).

    Returns:
        PSI score as float.
    """
    ref_clean = reference[~np.isnan(reference)]
    cur_clean = current[~np.isnan(current)]

    if len(ref_clean) == 0 or len(cur_clean) == 0:
        return 0.0

    # Handle invariant array edge case
    if np.all(ref_clean == ref_clean[0]):
        if np.all(cur_clean == ref_clean[0]):
            return 0.0
        return 1.0

    # Determine bin edges from reference quantiles
    quantiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(ref_clean, quantiles)
    # Ensure strictly increasing edges to prevent duplicate bin errors
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    # Compute frequency counts
    ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
    cur_counts, _ = np.histogram(cur_clean, bins=bin_edges)

    # Convert to proportions with smoothing
    ref_props = ref_counts / len(ref_clean)
    cur_props = cur_counts / len(cur_clean)

    ref_props = np.where(ref_props == 0, epsilon, ref_props)
    cur_props = np.where(cur_props == 0, epsilon, cur_props)

    psi_value = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))
    return float(max(0.0, psi_value))


def compute_ks_test(
    reference: np.ndarray,
    current: np.ndarray,
) -> Tuple[float, float]:
    """Execute two-sample Kolmogorov-Smirnov test.

    Tests whether two independent samples are drawn from the same continuous
    distribution.

    Limitations:
    - Highly sensitive to sample size: with N > 5,000, even tiny operational
      shifts may yield p-values < 0.001.
    - Sensitive only to the maximum vertical distance between eCDFs.
    - Assumes continuous i.i.d. observations; in turbofan cycles, time-series
      autocorrelation may inflate significance.

    Args:
        reference: Baseline reference sample.
        current: Evaluation comparison sample.

    Returns:
        Tuple of (ks_statistic, p_value).
    """
    ref_clean = reference[~np.isnan(reference)]
    cur_clean = current[~np.isnan(current)]

    if len(ref_clean) == 0 or len(cur_clean) == 0:
        return (0.0, 1.0)

    res = ks_2samp(ref_clean, cur_clean)
    return (float(res.statistic), float(res.pvalue))


def evaluate_feature_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    reference_name: str = "NASA C-MAPSS FD001 Train",
    comparison_name: str = "NASA C-MAPSS FD001 Test",
    ks_alpha: float = 0.01,
    psi_warning_thresh: float = 0.10,
    psi_drift_thresh: float = 0.25,
    min_sample_size: int = 15,
) -> Dict[str, Any]:
    """Evaluate distribution drift across sensor features between two datasets.

    Args:
        reference_df: Baseline training DataFrame.
        current_df: Evaluation or in-service DataFrame.
        feature_cols: Features to compare. Defaults to INFORMATIVE_SENSOR_COLS.
        reference_name: Label describing the reference source.
        comparison_name: Label describing the comparison source.
        ks_alpha: Significance level for KS test rejection.
        psi_warning_thresh: Threshold for moderate distribution shift.
        psi_drift_thresh: Threshold for significant distribution shift.
        min_sample_size: Minimum observations required to perform testing.

    Returns:
        Structured drift report dictionary.
    """
    if feature_cols is None:
        feature_cols = [c for c in INFORMATIVE_SENSOR_COLS if c in reference_df.columns and c in current_df.columns]

    n_ref = len(reference_df)
    n_cur = len(current_df)

    timestamp_iso = datetime.now(timezone.utc).isoformat()

    # Guard: Insufficient sample size
    if n_ref < min_sample_size or n_cur < min_sample_size:
        return {
            "status": "insufficient_samples",
            "drift_detected": False,
            "overall_status": "insufficient_data",
            "message": (
                f"Sample size too small for reliable non-parametric inference. "
                f"Required: >= {min_sample_size}, got reference: {n_ref}, comparison: {n_cur}."
            ),
            "measurement_time": timestamp_iso,
            "reference_dataset": reference_name,
            "comparison_dataset": comparison_name,
            "sample_size_reference": n_ref,
            "sample_size_comparison": n_cur,
            "features_evaluated": 0,
            "features": {},
            "statistical_methods": {
                "kolmogorov_smirnov": f"alpha={ks_alpha}",
                "population_stability_index": f"warning={psi_warning_thresh}, drift={psi_drift_thresh}",
            },
        }

    features_report: Dict[str, Any] = {}
    drift_alert_features: List[str] = []
    warning_features: List[str] = []

    for col in feature_cols:
        ref_vals = reference_df[col].to_numpy(dtype=float)
        cur_vals = current_df[col].to_numpy(dtype=float)

        # Basic summaries
        ref_mean = float(np.nanmean(ref_vals))
        cur_mean = float(np.nanmean(cur_vals))
        ref_std = float(np.nanstd(ref_vals))
        cur_std = float(np.nanstd(cur_vals))

        std_denom = ref_std if ref_std > 1e-6 else 1.0
        norm_mean_shift = (cur_mean - ref_mean) / std_denom

        ks_stat, ks_pval = compute_ks_test(ref_vals, cur_vals)
        psi_val = compute_psi(ref_vals, cur_vals)

        # Categorize drift status
        if psi_val >= psi_drift_thresh:
            status = "drift_alert"
            drift_alert_features.append(col)
        elif psi_val >= psi_warning_thresh or (ks_pval < ks_alpha and ks_stat > 0.15):
            status = "warning"
            warning_features.append(col)
        else:
            status = "stable"

        features_report[col] = {
            "status": status,
            "psi": round(psi_val, 4),
            "ks_statistic": round(ks_stat, 4),
            "ks_pvalue": float(f"{ks_pval:.2e}") if ks_pval < 1e-4 else round(ks_pval, 4),
            "ref_mean": round(ref_mean, 2),
            "cur_mean": round(cur_mean, 2),
            "norm_mean_shift": round(norm_mean_shift, 3),
            "ref_std": round(ref_std, 2),
            "cur_std": round(cur_std, 2),
        }

    # Aggregate status
    if len(drift_alert_features) >= 2 or len(drift_alert_features) + len(warning_features) >= 5:
        overall_status = "drift_alert"
        drift_detected = True
        summary_msg = (
            f"Significant covariate drift detected across {len(drift_alert_features)} primary channels. "
            f"Distributions diverge from baseline training regime."
        )
    elif len(drift_alert_features) >= 1 or len(warning_features) >= 2:
        overall_status = "warning"
        drift_detected = False
        summary_msg = (
            f"Moderate distribution shift detected across {len(warning_features) + len(drift_alert_features)} channels. "
            f"Sensor readings should be actively monitored."
        )
    else:
        overall_status = "stable"
        drift_detected = False
        summary_msg = (
            f"All {len(feature_cols)} monitored informative channels are stable. "
            f"Distributions align with the reference training baseline."
        )

    return {
        "status": "success",
        "drift_detected": drift_detected,
        "overall_status": overall_status,
        "summary": summary_msg,
        "measurement_time": timestamp_iso,
        "reference_dataset": reference_name,
        "comparison_dataset": comparison_name,
        "sample_size_reference": n_ref,
        "sample_size_comparison": n_cur,
        "features_evaluated": len(feature_cols),
        "alert_features_count": len(drift_alert_features),
        "warning_features_count": len(warning_features),
        "alert_features": drift_alert_features,
        "warning_features": warning_features,
        "features": features_report,
        "caveat": (
            "Statistical covariate shift reflects sensor distribution change P(X). "
            "It does NOT verify degraded physical prognostic accuracy without ground-truth teardown inspection labels."
        ),
        "statistical_methods": {
            "kolmogorov_smirnov": f"alpha={ks_alpha}",
            "population_stability_index": f"warning={psi_warning_thresh}, drift={psi_drift_thresh}",
        },
    }
