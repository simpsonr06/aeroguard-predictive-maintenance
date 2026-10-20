"""Unit tests for leakage safety and feature engineering."""

import numpy as np
import pandas as pd
import pytest

from aircraft_pm.config import RAW_COLUMNS
from aircraft_pm.features import CMAPSSPreprocessor, compute_leakage_safe_features


def test_no_cross_engine_leakage_in_rolling_windows():
    """Verify rolling statistics NEVER leak data across engine boundaries.

    Engine 1 values should not affect Engine 2's rolling mean or std.
    """
    # Create two engines with distinct values
    df = pd.DataFrame(
        {
            "engine_id": [1, 1, 1, 2, 2, 2],
            "cycle": [1, 2, 3, 1, 2, 3],
            "sensor_2": [10.0, 10.0, 10.0, 500.0, 500.0, 500.0],
            "sensor_3": [1.0, 2.0, 3.0, 100.0, 200.0, 300.0],
        }
    )
    for c in RAW_COLUMNS:
        if c not in df.columns:
            df[c] = 0.0

    features = compute_leakage_safe_features(df, sensor_cols=["sensor_2", "sensor_3"], windows=[2], lags=[1])

    # Check Engine 2 at cycle 1:
    # Its rolling mean for sensor_2 with window 2 should be 500.0 (only its own cycle 1), NOT (10 + 500)/2 = 255.0
    eng2_cycle1 = features[(features["engine_id"] == 2) & (features["cycle"] == 1)].iloc[0]
    assert eng2_cycle1["sensor_2_roll_mean_2"] == pytest.approx(500.0)

    # Check lag difference for Engine 2 at cycle 1:
    # Should be 0.0 (no previous cycle in Engine 2), NOT 500 - 10 = 490
    assert eng2_cycle1["sensor_2_diff_1"] == pytest.approx(0.0)


def test_temporal_causality():
    """Verify that feature engineering at cycle t does not depend on cycle t + 1."""
    df1 = pd.DataFrame(
        {
            "engine_id": [1, 1],
            "cycle": [1, 2],
            "sensor_2": [10.0, 20.0],
        }
    )
    # Identical cycle 1, but different future cycle 2
    df2 = pd.DataFrame(
        {
            "engine_id": [1, 1],
            "cycle": [1, 2],
            "sensor_2": [10.0, 999.0],
        }
    )
    for c in RAW_COLUMNS:
        if c not in df1.columns:
            df1[c] = 0.0
            df2[c] = 0.0

    feat1 = compute_leakage_safe_features(df1, sensor_cols=["sensor_2"], windows=[2], lags=[1])
    feat2 = compute_leakage_safe_features(df2, sensor_cols=["sensor_2"], windows=[2], lags=[1])

    # The computed features at cycle 1 must be strictly identical regardless of future cycle 2
    c1_1 = feat1[feat1["cycle"] == 1].drop(columns=["engine_id", "cycle"]).values
    c1_2 = feat2[feat2["cycle"] == 1].drop(columns=["engine_id", "cycle"]).values

    assert np.allclose(c1_1, c1_2)


def test_preprocessor_fit_transform():
    """Verify CMAPSSPreprocessor scales and transforms without producing NaNs."""
    df = pd.DataFrame(
        {
            "engine_id": [1, 1, 1, 1, 2, 2, 2, 2],
            "cycle": [1, 2, 3, 4, 1, 2, 3, 4],
            "sensor_2": [10.0, 11.0, 12.0, 13.0, 20.0, 21.0, 22.0, 23.0],
            "sensor_3": [100.0, 105.0, 110.0, 115.0, 200.0, 205.0, 210.0, 215.0],
        }
    )
    for c in RAW_COLUMNS:
        if c not in df.columns:
            df[c] = 0.0

    pre = CMAPSSPreprocessor(sensor_cols=["sensor_2", "sensor_3"], windows=[2], lags=[1])
    X_scaled, X_raw = pre.fit(df).transform(df)

    assert not np.isnan(X_scaled).any()
    assert X_scaled.shape[0] == len(df)
    assert len(pre.feature_names_) > 0
