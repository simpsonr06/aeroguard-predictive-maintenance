"""Leakage-safe feature engineering and preprocessing for C-MAPSS FD001."""

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

from aircraft_pm.config import (
    CONSTANT_OR_LOW_VARIANCE_COLS,
    INFORMATIVE_SENSOR_COLS,
    SETTING_COLUMNS,
)


def compute_leakage_safe_features(
    df: pd.DataFrame,
    sensor_cols: Optional[List[str]] = None,
    windows: Optional[List[int]] = None,
    lags: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Engineer temporal and degradation features without lookahead or cross-engine leakage.

    Guarantees:
    - Grouped strictly by engine_id: Rolling windows and lag differences never cross engine boundaries.
    - Strictly historical: Uses only current and past cycles (<= cycle t).
    - Preserves engine_id and cycle for downstream indexing.

    Args:
        df: Input DataFrame containing engine_id, cycle, settings, and sensors.
        sensor_cols: List of sensor columns to compute rolling/lag features for.
                     Defaults to INFORMATIVE_SENSOR_COLS.
        windows: Rolling window sizes in cycles. Defaults to [5, 15].
        lags: Difference step lags in cycles. Defaults to [1, 5].

    Returns:
        DataFrame with original informative features plus engineered rolling and lag columns.
    """
    if sensor_cols is None:
        sensor_cols = [c for c in INFORMATIVE_SENSOR_COLS if c in df.columns]
    if windows is None:
        windows = [5, 15]
    if lags is None:
        lags = [1, 5]

    # Start with base informative features
    keep_settings = [c for c in SETTING_COLUMNS if c not in CONSTANT_OR_LOW_VARIANCE_COLS and c in df.columns]
    base_cols = ["engine_id", "cycle"] + keep_settings + sensor_cols
    
    # Check if target columns exist in df, keep them if present
    target_cols = [c for c in ["rul", "rul_clipped"] if c in df.columns]

    df_out = df[base_cols + target_cols].copy()

    # Sort strictly by engine_id and cycle to ensure proper temporal ordering
    df_out = df_out.sort_values(by=["engine_id", "cycle"]).reset_index(drop=True)

    grouped = df_out.groupby("engine_id")

    # 1. Rolling statistics per engine
    for w in windows:
        # Rolling Mean
        rolling_mean = (
            grouped[sensor_cols]
            .rolling(window=w, min_periods=1)
            .mean()
            .reset_index(level=0, drop=True)
        )
        rolling_mean.columns = [f"{c}_roll_mean_{w}" for c in sensor_cols]

        # Rolling Standard Deviation
        rolling_std = (
            grouped[sensor_cols]
            .rolling(window=w, min_periods=1)
            .std()
            .reset_index(level=0, drop=True)
            .fillna(0.0)
        )
        rolling_std.columns = [f"{c}_roll_std_{w}" for c in sensor_cols]

        df_out = pd.concat([df_out, rolling_mean, rolling_std], axis=1)

    # 2. Lag differences (rate of change) per engine
    for lag in lags:
        lag_diff = grouped[sensor_cols].diff(periods=lag).fillna(0.0)
        lag_diff.columns = [f"{c}_diff_{lag}" for c in sensor_cols]
        df_out = pd.concat([df_out, lag_diff], axis=1)

    # 3. Drift from initial baseline cycle (cycle 1) per engine
    # Safe from future leakage: uses only the first recorded observation of that engine
    initial_values = grouped[sensor_cols].transform("first")
    drift = df_out[sensor_cols] - initial_values
    drift.columns = [f"{c}_drift" for c in sensor_cols]
    df_out = pd.concat([df_out, drift], axis=1)

    return df_out


class CMAPSSPreprocessor(BaseEstimator, TransformerMixin):
    """Preprocessor that extracts features and fits a scaler only on training data."""

    def __init__(
        self,
        sensor_cols: Optional[List[str]] = None,
        windows: Optional[List[int]] = None,
        lags: Optional[List[int]] = None,
    ):
        self.sensor_cols = sensor_cols
        self.windows = windows
        self.lags = lags
        self.scaler = StandardScaler()
        self.feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y=None):
        """Fit scaler on engineered features of training data."""
        X_feat = compute_leakage_safe_features(
            X,
            sensor_cols=self.sensor_cols,
            windows=self.windows,
            lags=self.lags,
        )

        non_feature_cols = {"engine_id", "cycle", "rul", "rul_clipped"}
        self.feature_names_ = [
            c for c in X_feat.columns if c not in non_feature_cols
        ]

        self.scaler.fit(X_feat[self.feature_names_])
        return self

    def transform(self, X: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """Compute features and scale using fitted scaler.

        Returns:
            Tuple of (scaled numpy array, raw engineered feature DataFrame).
        """
        X_feat = compute_leakage_safe_features(
            X,
            sensor_cols=self.sensor_cols,
            windows=self.windows,
            lags=self.lags,
        )

        X_selected = X_feat[self.feature_names_].fillna(0.0)
        X_scaled = self.scaler.transform(X_selected)
        return X_scaled, X_feat
