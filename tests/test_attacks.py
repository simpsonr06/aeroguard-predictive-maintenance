"""Unit tests for AeroSentinel synthetic telemetry attack simulation."""

import numpy as np
import pandas as pd
import pytest

from aircraft_pm.attacks import (
    calculate_hazardous_prediction_rate,
    compute_baseline_sensor_stats,
    inject_sensor_bias,
    inject_sensor_ramp,
    inject_sensor_replay,
)



@pytest.fixture
def sample_telemetry_df() -> pd.DataFrame:
    """Create a deterministic synthetic two-engine telemetry DataFrame."""
    rows = []
    # Engine 1: 50 cycles
    for c in range(1, 51):
        rows.append({
            "engine_id": 1,
            "cycle": c,
            "setting_1": 0.0,
            "setting_2": 0.0,
            "setting_3": 100.0,
            "sensor_11": 47.0 + c * 0.02,
            "sensor_9": 9000.0 + c * 1.5,
            "sensor_4": 1400.0 + c * 0.5,
        })
    # Engine 2: 100 cycles
    for c in range(1, 101):
        rows.append({
            "engine_id": 2,
            "cycle": c,
            "setting_1": 0.0,
            "setting_2": 0.0,
            "setting_3": 100.0,
            "sensor_11": 46.5 + c * 0.03,
            "sensor_9": 8980.0 + c * 2.0,
            "sensor_4": 1395.0 + c * 0.8,
        })
    return pd.DataFrame(rows)


def test_input_immutability(sample_telemetry_df: pd.DataFrame):
    """Attack functions must never modify the input DataFrame in-place."""
    orig_copy = sample_telemetry_df.copy(deep=True)
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])

    _ = inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": 2.0}, stats, onset_fraction=0.5)
    pd.testing.assert_frame_equal(sample_telemetry_df, orig_copy)

    _ = inject_sensor_ramp(sample_telemetry_df, ["sensor_11"], {"sensor_11": 2.0}, stats, onset_fraction=0.5)
    pd.testing.assert_frame_equal(sample_telemetry_df, orig_copy)

    _ = inject_sensor_replay(sample_telemetry_df, ["sensor_11"], onset_fraction=0.5)
    pd.testing.assert_frame_equal(sample_telemetry_df, orig_copy)


def test_attack_bounds_and_onset(sample_telemetry_df: pd.DataFrame):
    """Prior to onset cycle, data must be identical; after onset, bias is strictly applied."""
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])
    sigma = stats["sensor_11"]["std"]
    k = 1.5

    # Engine 1 has T=50, onset_fraction=0.6 -> onset = floor(30) = cycle 30
    res = inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": k}, stats, onset_fraction=0.6)

    e1_orig = sample_telemetry_df[sample_telemetry_df["engine_id"] == 1]
    e1_res = res[res["engine_id"] == 1]

    # Pre-attack cycles (1 to 29): must be exactly identical
    pd.testing.assert_series_equal(
        e1_orig[e1_orig["cycle"] < 30]["sensor_11"],
        e1_res[e1_res["cycle"] < 30]["sensor_11"],
    )

    # Post-attack cycles (30 to 50): must differ by exactly k * sigma
    diff = e1_res[e1_res["cycle"] >= 30]["sensor_11"] - e1_orig[e1_orig["cycle"] >= 30]["sensor_11"]
    np.testing.assert_allclose(diff.values, k * sigma)


def test_ramp_monotonicity_and_terminal_value(sample_telemetry_df: pd.DataFrame):
    """Ramp starts at 0 delta and reaches full k * sigma at the terminal cycle."""
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])
    sigma = stats["sensor_11"]["std"]
    k = 2.0

    res = inject_sensor_ramp(sample_telemetry_df, ["sensor_11"], {"sensor_11": k}, stats, onset_fraction=0.5)

    e1_orig = sample_telemetry_df[sample_telemetry_df["engine_id"] == 1]
    e1_res = res[res["engine_id"] == 1]

    # At onset (cycle 25 for T=50), delta is 0
    delta_onset = (
        e1_res[e1_res["cycle"] == 25]["sensor_11"].values[0]
        - e1_orig[e1_orig["cycle"] == 25]["sensor_11"].values[0]
    )
    assert abs(delta_onset) < 1e-6

    # At terminal cycle (cycle 50), delta is exactly k * sigma
    delta_final = (
        e1_res[e1_res["cycle"] == 50]["sensor_11"].values[0]
        - e1_orig[e1_orig["cycle"] == 50]["sensor_11"].values[0]
    )
    np.testing.assert_allclose(delta_final, k * sigma)


def test_engine_grouping_isolation(sample_telemetry_df: pd.DataFrame):
    """Onset cycle is computed per-engine based on each engine's own lifetime."""
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])

    # onset_fraction=0.5 -> Engine 1 onset = 25 (T=50), Engine 2 onset = 50 (T=100)
    res = inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": 1.0}, stats, onset_fraction=0.5)

    e1 = res[res["engine_id"] == 1]
    e2 = res[res["engine_id"] == 2]

    # Engine 1 cycle 25 is perturbed
    orig_e1 = sample_telemetry_df[sample_telemetry_df["engine_id"] == 1]
    assert e1[e1["cycle"] == 25]["sensor_11"].values[0] != orig_e1[orig_e1["cycle"] == 25]["sensor_11"].values[0]

    # Engine 2 cycle 25 is UNPERTURBED (onset is cycle 50)
    orig_e2 = sample_telemetry_df[sample_telemetry_df["engine_id"] == 2]
    assert e2[e2["cycle"] == 25]["sensor_11"].values[0] == orig_e2[orig_e2["cycle"] == 25]["sensor_11"].values[0]


def test_frozen_replay_behavior(sample_telemetry_df: pd.DataFrame):
    """Replay attack freezes sensor values at the exact reading of the onset cycle."""
    res = inject_sensor_replay(sample_telemetry_df, ["sensor_11"], onset_fraction=0.4)

    e1_res = res[res["engine_id"] == 1]
    # T=50, onset = floor(20) = 20
    val_at_20 = e1_res[e1_res["cycle"] == 20]["sensor_11"].values[0]

    # All cycles from 20 to 50 must have this exact value
    post_vals = e1_res[e1_res["cycle"] >= 20]["sensor_11"].values
    assert np.all(post_vals == val_at_20)


def test_reproducibility(sample_telemetry_df: pd.DataFrame):
    """Deterministic attacks must produce bit-identical DataFrames on repeated runs."""
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])

    run1 = inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": 1.23}, stats, onset_fraction=0.5)
    run2 = inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": 1.23}, stats, onset_fraction=0.5)
    pd.testing.assert_frame_equal(run1, run2)


def test_invalid_fraction_validation(sample_telemetry_df: pd.DataFrame):
    """Invalid onset fractions must raise ValueError."""
    stats = compute_baseline_sensor_stats(sample_telemetry_df, ["sensor_11"])

    with pytest.raises(ValueError, match="onset_fraction"):
        inject_sensor_bias(sample_telemetry_df, ["sensor_11"], {"sensor_11": 1.0}, stats, onset_fraction=-0.1)

    with pytest.raises(ValueError, match="onset_fraction"):
        inject_sensor_ramp(sample_telemetry_df, ["sensor_11"], {"sensor_11": 1.0}, stats, onset_fraction=1.5)


def test_hazardous_prediction_rate_canonical_calculation():
    """Verify HPR calculation on mixed critical and non-critical sets."""
    # 4 engines:
    # Engine 1: true=10 (crit), pred=30 (falsely healthy -> hazardous!)
    # Engine 2: true=20 (crit), pred=15 (crit -> safe)
    # Engine 3: true=25 (crit boundary), pred=25 (crit boundary -> safe)
    # Engine 4: true=60 (non-crit), pred=80 (safe non-crit)
    y_true = [10.0, 20.0, 25.0, 60.0]
    y_pred = [30.0, 15.0, 25.0, 80.0]

    res = calculate_hazardous_prediction_rate(y_true, y_pred, critical_threshold=25.0)
    assert res["critical_count"] == 3
    assert res["hazardous_count"] == 1
    assert res["hpr_pct"] == pytest.approx(33.33, rel=1e-2)


def test_hazardous_prediction_rate_boundary_conditions():
    """Verify HPR handling of boundary conditions: exactly 25.0 vs 25.01."""
    # true RUL = 25.0
    y_true = [25.0, 25.0]
    # pred 25.0 is NOT hazardous; pred 25.01 IS hazardous
    y_pred = [25.0, 25.01]

    res = calculate_hazardous_prediction_rate(y_true, y_pred, critical_threshold=25.0)
    assert res["critical_count"] == 2
    assert res["hazardous_count"] == 1
    assert res["hpr_pct"] == 50.0


def test_hazardous_prediction_rate_zero_critical_denominator():
    """When no engines are critical (e.g. early cruise flight), HPR must safely return 0.0%."""
    y_true = [80.0, 90.0, 100.0]
    y_pred = [70.0, 85.0, 95.0]

    res = calculate_hazardous_prediction_rate(y_true, y_pred, critical_threshold=25.0)
    assert res["critical_count"] == 0
    assert res["hazardous_count"] == 0
    assert res["hpr_pct"] == 0.0

