"""Deterministic tests for statistical drift monitoring in AeroGuard 2.1."""

import numpy as np
import pandas as pd
import pytest

from aircraft_pm.data import load_train_data, load_test_data
from aircraft_pm.drift import compute_psi, compute_ks_test, evaluate_feature_drift


def test_psi_unchanged_distribution():
    """Identical or near-identical distributions must produce negligible PSI (< 0.05)."""
    np.random.seed(42)
    ref = np.random.normal(loc=100.0, scale=15.0, size=2000)
    cur = np.random.normal(loc=100.1, scale=15.0, size=2000)

    psi = compute_psi(ref, cur, num_bins=10)
    assert psi < 0.05, f"Expected negligible PSI for unchanged distribution, got {psi}"


def test_psi_shifted_distribution():
    """Significant mean and variance shift must trigger high PSI (>= 0.25)."""
    np.random.seed(42)
    ref = np.random.normal(loc=100.0, scale=10.0, size=2000)
    cur = np.random.normal(loc=125.0, scale=20.0, size=2000)

    psi = compute_psi(ref, cur, num_bins=10)
    assert psi >= 0.25, f"Expected drift alert PSI >= 0.25 for shifted distribution, got {psi}"


def test_ks_test_identical_and_shifted_samples():
    """KS test must distinguish identical samples from heavily shifted samples."""
    np.random.seed(42)
    ref = np.random.uniform(low=0.0, high=50.0, size=1500)
    cur_same = np.random.uniform(low=0.0, high=50.0, size=1500)
    cur_shifted = np.random.uniform(low=30.0, high=80.0, size=1500)

    stat_same, pval_same = compute_ks_test(ref, cur_same)
    assert stat_same < 0.08
    assert pval_same > 0.01

    stat_shift, pval_shift = compute_ks_test(ref, cur_shifted)
    assert stat_shift > 0.40
    assert pval_shift < 1e-10


def test_evaluate_feature_drift_insufficient_samples():
    """Sample sizes below threshold must return explicit insufficient_samples status."""
    ref_df = pd.DataFrame({"sensor_2": [1.0, 2.0, 3.0]})
    cur_df = pd.DataFrame({"sensor_2": [1.0, 2.0, 3.0]})

    report = evaluate_feature_drift(ref_df, cur_df, feature_cols=["sensor_2"], min_sample_size=15)
    assert report["status"] == "insufficient_samples"
    assert report["drift_detected"] is False
    assert "sample size too small" in report["message"].lower()


def test_evaluate_feature_drift_with_missing_values():
    """Missing/NaN values must be safely filtered without exceptions."""
    np.random.seed(42)
    ref_vals = np.random.normal(50, 5, 200)
    cur_vals = np.random.normal(50, 5, 200)
    # Inject NaNs
    ref_vals[::10] = np.nan
    cur_vals[::8] = np.nan

    ref_df = pd.DataFrame({"sensor_2": ref_vals})
    cur_df = pd.DataFrame({"sensor_2": cur_vals})

    report = evaluate_feature_drift(ref_df, cur_df, feature_cols=["sensor_2"])
    assert report["status"] == "success"
    assert "sensor_2" in report["features"]
    assert report["features"]["sensor_2"]["status"] in ["stable", "warning", "drift_alert"]


def test_evaluate_feature_drift_real_cmapss_benchmark():
    """Evaluate drift on real NASA C-MAPSS FD001 benchmark train vs test partitions."""
    train_df, _ = load_train_data()
    test_df, _, _ = load_test_data()

    report = evaluate_feature_drift(
        reference_df=train_df,
        current_df=test_df,
        reference_name="NASA C-MAPSS FD001 Train (100 Engines)",
        comparison_name="NASA C-MAPSS FD001 Test (100 Engines)",
    )

    assert report["status"] == "success"
    assert report["sample_size_reference"] == len(train_df)
    assert report["sample_size_comparison"] == len(test_df)
    assert report["features_evaluated"] > 10
    assert "caveat" in report
    assert "P(X)" in report["caveat"]
