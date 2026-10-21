"""Synthetic telemetry manipulation and attack simulation module for AeroSentinel.

Provides reproducible, offline research functions to simulate sensor step bias,
gradual creeping ramps, and frozen/replay attacks on copies of C-MAPSS telemetry.
Designed strictly for defensive resilience benchmarking and threat modeling.

Scientific Guardrails:
- All manipulations operate strictly on deep copies of DataFrames (source data is immutable).
- Attack parameters (e.g. sensor standard deviations) are calibrated strictly on training data.
- Feature engineering respects temporal causality and engine isolation.
- Both unclipped (Protocol A) and clipped @ 125 (Protocol B) metrics are evaluated separately.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from aircraft_pm.config import INFORMATIVE_SENSOR_COLS


def compute_baseline_sensor_stats(
    train_df: pd.DataFrame,
    sensor_cols: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """Compute distribution statistics per sensor strictly from training baseline data.

    Args:
        train_df: Training DataFrame (e.g. train_FD001.txt).
        sensor_cols: Sensors to analyze. Defaults to INFORMATIVE_SENSOR_COLS.

    Returns:
        Dict mapping sensor_name -> {'mean': float, 'std': float, 'iqr': float, 'min': float, 'max': float}.
    """
    if sensor_cols is None:
        sensor_cols = [c for c in INFORMATIVE_SENSOR_COLS if c in train_df.columns]

    stats: Dict[str, Dict[str, float]] = {}
    for col in sensor_cols:
        series = train_df[col].dropna()
        q75, q25 = np.percentile(series, [75, 25])
        stats[col] = {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "iqr": float(q75 - q25),
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return stats


def inject_sensor_bias(
    df: pd.DataFrame,
    target_sensors: List[str],
    bias_sigmas: Dict[str, float],
    sensor_stats: Dict[str, Dict[str, float]],
    onset_fraction: float = 0.50,
) -> pd.DataFrame:
    """Inject synthetic step bias (additive offset) starting at an operational fraction of life.

    For each engine i with terminal cycle T_i, the attack onset is:
        t_onset = max(1, floor(onset_fraction * T_i))
    For all cycles t >= t_onset:
        x_{i, j, t}' = x_{i, j, t} + k_j * sigma_j

    Args:
        df: Input telemetry DataFrame.
        target_sensors: List of sensor columns to perturb.
        bias_sigmas: Dict mapping sensor_name -> perturbation multiplier k (e.g. {'sensor_11': 1.5}).
        sensor_stats: Baseline statistics computed from training data.
        onset_fraction: Fraction of trajectory before attack begins (e.g. 0.50 = midpoint).

    Returns:
        New DataFrame with synthetic bias injected. Input df is completely unmodified.
    """
    if not (0.0 <= onset_fraction <= 1.0):
        raise ValueError(f"onset_fraction must be in [0.0, 1.0], got {onset_fraction}")

    df_out = df.copy()

    # Determine per-engine max cycle
    max_cycles = df_out.groupby("engine_id")["cycle"].transform("max")
    onset_cycle = np.floor(max_cycles * onset_fraction).astype(int)

    mask_active = df_out["cycle"] >= onset_cycle

    for col in target_sensors:
        if col not in df_out.columns:
            continue
        k = bias_sigmas.get(col, 0.0)
        sigma = sensor_stats.get(col, {}).get("std", 1.0)
        delta = k * sigma
        df_out.loc[mask_active, col] = df_out.loc[mask_active, col] + delta

    return df_out


def inject_sensor_ramp(
    df: pd.DataFrame,
    target_sensors: List[str],
    max_drift_sigmas: Dict[str, float],
    sensor_stats: Dict[str, Dict[str, float]],
    onset_fraction: float = 0.50,
) -> pd.DataFrame:
    """Inject a gradual creeping linear ramp perturbation starting at t_onset and peaking at T_i.

    For cycles t >= t_onset:
        ramp_factor = (t - t_onset) / max(1, T_i - t_onset)
        x_{i, j, t}' = x_{i, j, t} + ramp_factor * (k_j * sigma_j)

    Args:
        df: Input telemetry DataFrame.
        target_sensors: List of sensor columns to perturb.
        max_drift_sigmas: Dict mapping sensor_name -> max drift at terminal cycle.
        sensor_stats: Baseline statistics from training data.
        onset_fraction: Trajectory fraction at which ramp begins.

    Returns:
        New DataFrame with synthetic ramp injected.
    """
    if not (0.0 <= onset_fraction < 1.0):
        raise ValueError(f"onset_fraction must be in [0.0, 1.0), got {onset_fraction}")

    df_out = df.copy()

    max_cycles = df_out.groupby("engine_id")["cycle"].transform("max")
    onset_cycle = np.floor(max_cycles * onset_fraction).astype(int)

    mask_active = df_out["cycle"] >= onset_cycle

    # Denominator: total cycles remaining from onset to T_i
    remaining = np.maximum(1, max_cycles - onset_cycle)
    ramp_weight = np.clip((df_out["cycle"] - onset_cycle) / remaining, 0.0, 1.0)

    for col in target_sensors:
        if col not in df_out.columns:
            continue
        k = max_drift_sigmas.get(col, 0.0)
        sigma = sensor_stats.get(col, {}).get("std", 1.0)
        total_delta = k * sigma
        df_out.loc[mask_active, col] = (
            df_out.loc[mask_active, col] + ramp_weight[mask_active] * total_delta
        )

    return df_out


def inject_sensor_replay(
    df: pd.DataFrame,
    target_sensors: Optional[List[str]] = None,
    onset_fraction: float = 0.40,
) -> pd.DataFrame:
    """Inject a frozen telemetry / replay attack holding sensor values constant past t_onset.

    Simulates a stuck sensor or an adversary replaying earlier nominal cruise values
    to mask active degradation and fool the maintenance model into late prediction.

    Args:
        df: Input telemetry DataFrame.
        target_sensors: Sensors to freeze. Defaults to INFORMATIVE_SENSOR_COLS.
        onset_fraction: Trajectory fraction after which telemetry is frozen.

    Returns:
        New DataFrame with frozen sensor values past t_onset.
    """
    if not (0.0 <= onset_fraction < 1.0):
        raise ValueError(f"onset_fraction must be in [0.0, 1.0), got {onset_fraction}")

    if target_sensors is None:
        target_sensors = [c for c in INFORMATIVE_SENSOR_COLS if c in df.columns]

    df_out = df.copy()

    # Process each engine independently to preserve engine isolation
    for engine_id, group in df_out.groupby("engine_id"):
        t_max = group["cycle"].max()
        t_onset = max(1, int(np.floor(onset_fraction * t_max)))

        # Find row corresponding to t_onset (or nearest prior)
        onset_row = group[group["cycle"] == t_onset]
        if onset_row.empty:
            onset_row = group[group["cycle"] <= t_onset].iloc[-1:]

        if onset_row.empty:
            continue

        frozen_values = onset_row[target_sensors].iloc[0]

        # Apply frozen values to all cycles >= t_onset for this engine
        mask = (df_out["engine_id"] == engine_id) & (df_out["cycle"] >= t_onset)
        for col in target_sensors:
            df_out.loc[mask, col] = frozen_values[col]

    return df_out
