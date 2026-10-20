"""Tests for evaluation metrics and NASA PHM 2008 scoring function."""

import numpy as np
import pytest

from aircraft_pm.metrics import evaluate_predictions, nasa_phm_score


def test_nasa_phm_score_perfect():
    """Score should be exactly 0 for perfect predictions."""
    y_true = np.array([50, 100, 20, 10])
    y_pred = np.array([50, 100, 20, 10])
    score = nasa_phm_score(y_true, y_pred)
    assert score == pytest.approx(0.0, abs=1e-6)


def test_nasa_phm_score_asymmetry():
    """Late predictions (overestimating RUL) must carry a higher penalty than early ones."""
    y_true = np.array([50.0])
    
    # Early prediction by 10 cycles (d = -10): exp(10/13) - 1 ≈ 1.158
    pred_early = np.array([40.0])
    score_early = nasa_phm_score(y_true, pred_early)
    
    # Late prediction by 10 cycles (d = +10): exp(10/10) - 1 ≈ 1.718
    pred_late = np.array([60.0])
    score_late = nasa_phm_score(y_true, pred_late)

    assert score_late > score_early
    assert score_early == pytest.approx(np.exp(10.0 / 13.0) - 1.0, rel=1e-4)
    assert score_late == pytest.approx(np.exp(10.0 / 10.0) - 1.0, rel=1e-4)


def test_evaluate_predictions_metrics():
    """Verify that evaluate_predictions outputs expected keys and accurate metrics."""
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 30.0])  # errors: +2, -2, 0

    metrics = evaluate_predictions(y_true, y_pred)

    assert "rmse" in metrics
    assert "mae" in metrics
    assert "r2" in metrics
    assert "nasa_score" in metrics
    assert "mean_bias" in metrics
    assert "max_abs_error" in metrics

    # MSE: (4 + 4 + 0) / 3 = 8/3 ≈ 2.6667, RMSE ≈ 1.6330
    assert metrics["rmse"] == pytest.approx(np.sqrt(8.0 / 3.0), rel=1e-3)
    # MAE: (2 + 2 + 0) / 3 = 4/3 ≈ 1.3333
    assert metrics["mae"] == pytest.approx(4.0 / 3.0, rel=1e-3)
    assert metrics["max_abs_error"] == pytest.approx(2.0, abs=1e-4)
    assert metrics["mean_bias"] == pytest.approx(0.0, abs=1e-4)
