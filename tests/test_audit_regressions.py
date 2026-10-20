"""Regression and audit verification tests for AeroGuard."""

from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
import pytest

from aircraft_pm.config import DEFAULT_CLIP_RUL, MODELS_DIR
from aircraft_pm.data import load_test_data, load_train_data
from aircraft_pm.features import CMAPSSPreprocessor, compute_leakage_safe_features
from aircraft_pm.metrics import nasa_phm_score
from aircraft_pm.models.train import create_in_service_cutoffs, get_candidate_models


def test_styler_compatibility_pandas():
    """Verify that Styler highlighting works with pandas 3.0+ (no applymap AttributeError)."""
    df = pd.DataFrame({"Health Category": ["Critical", "Advisory", "Healthy"]})

    def highlight_status(val):
        if val == "Critical":
            return "background-color: #fee2e2;"
        elif val == "Advisory":
            return "background-color: #fef9c3;"
        return "background-color: #dcfce7;"

    styler = df.style
    if hasattr(styler, "map"):
        styler = styler.map(highlight_status, subset=["Health Category"])
    else:
        styler = styler.applymap(highlight_status, subset=["Health Category"])

    html = styler.to_html()
    assert "Critical" in html
    assert "#fee2e2" in html


def test_normalized_nasa_phm_score_linearity():
    """Verify that normalized NASA score (score / N) properly normalizes across different fleet sizes."""
    errors = np.array([-5.0, 5.0, 0.0, -10.0, 10.0])
    y_true_small = np.zeros(5)
    y_pred_small = errors.copy()

    y_true_large = np.zeros(50)
    y_pred_large = np.tile(errors, 10)

    score_small = nasa_phm_score(y_true_small, y_pred_small)
    score_large = nasa_phm_score(y_true_large, y_pred_large)

    assert score_large == pytest.approx(10 * score_small, rel=1e-5)
    assert (score_small / 5) == pytest.approx(score_large / 50, rel=1e-5)


def test_reproducible_reloading_and_inference():
    """Ensure persisted preprocessor and model reproduce identical predictions upon reload."""
    prep_path = MODELS_DIR / "preprocessor.joblib"
    model_path = MODELS_DIR / "best_model.joblib"

    if not prep_path.exists() or not model_path.exists():
        pytest.skip("Models not yet generated")

    preprocessor = joblib.load(prep_path)
    model = joblib.load(model_path)

    test_df, test_last, _ = load_test_data()
    sample = test_df[test_df["engine_id"] == 1].copy()

    X_scaled1, _ = preprocessor.transform(sample)
    preds1 = model.predict(X_scaled1)

    X_scaled2, _ = preprocessor.transform(sample)
    preds2 = model.predict(X_scaled2)

    assert np.allclose(preds1, preds2)
    assert np.allclose(X_scaled1, X_scaled2)


def test_validation_cutoff_does_not_access_official_test_labels():
    """Verify that in-service cutoff creation runs completely isolated from official test files."""
    train_df, _ = load_train_data()
    val_sample = train_df[train_df["engine_id"].isin([1, 2, 3])].copy()

    # Intercept open calls to ensure test_FD001.txt or RUL_FD001.txt are NOT accessed
    original_open = open

    def guarded_open(file, *args, **kwargs):
        file_str = str(file)
        if "RUL_FD001" in file_str or "test_FD001" in file_str:
            raise AssertionError(f"LEAKAGE DETECTED: Cutoff validation tried to access {file_str}")
        return original_open(file, *args, **kwargs)

    with patch("builtins.open", side_effect=guarded_open):
        trunc_df, gt_df = create_in_service_cutoffs(val_sample, random_state=42)

    assert len(gt_df) == 3
    for _, row in gt_df.iterrows():
        eid = row["engine_id"]
        t_max = val_sample[val_sample["engine_id"] == eid]["cycle"].max()
        cutoff_c = row["cutoff_cycle"]
        # Ground truth must be actual remaining cycles: t_max - cutoff_cycle
        assert row["actual_rul"] == (t_max - cutoff_c)
        assert 1 <= cutoff_c < t_max
        # Truncated data must contain strictly cycles <= cutoff_cycle
        eng_trunc = trunc_df[trunc_df["engine_id"] == eid]
        assert eng_trunc["cycle"].max() == cutoff_c


def test_clipping_policy_consistency():
    """Verify that predictions capped at 125 have an expected residual gap against unclipped targets > 125."""
    # When true RUL is 140, a model predicting 125 has an error of exactly 15
    y_true_unclipped = np.array([140.0, 50.0])
    y_pred = np.array([125.0, 50.0])
    y_true_clipped = np.minimum(y_true_unclipped, 125.0)

    # Clipped target error: |125 - 125| = 0, |50 - 50| = 0 -> RMSE = 0.0
    err_clipped = np.sqrt(np.mean((y_pred - y_true_clipped) ** 2))
    assert err_clipped == pytest.approx(0.0)

    # Unclipped target error: |125 - 140| = 15, |50 - 50| = 0 -> RMSE = sqrt(225/2) ≈ 10.6066
    err_unclipped = np.sqrt(np.mean((y_pred - y_true_unclipped) ** 2))
    assert err_unclipped == pytest.approx(np.sqrt(225.0 / 2.0))
