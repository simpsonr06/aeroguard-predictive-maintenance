"""Evaluation metrics for Remaining Useful Life (RUL) prediction, including the NASA PHM score."""

from typing import Dict, Union

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def nasa_phm_score(
    y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]
) -> float:
    """Calculate the official NASA PHM 2008 Prognostics asymmetric score.

    In predictive maintenance, predicting failure late (d > 0) carries
    a much higher operational penalty than predicting early (d < 0).

    The error is defined as d = y_pred - y_true:
        s_i = exp(-d / 13) - 1   if d < 0 (early prediction)
        s_i = exp(d / 10) - 1    if d >= 0 (late prediction)
        Total Score = sum(s_i)

    Args:
        y_true: True RUL values.
        y_pred: Predicted RUL values.

    Returns:
        Total NASA PHM score (lower is better, 0 is perfect).
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    diff = y_p - y_t
    early_mask = diff < 0
    late_mask = ~early_mask

    scores = np.zeros_like(diff, dtype=np.float64)
    scores[early_mask] = np.exp(-diff[early_mask] / 13.0) - 1.0
    scores[late_mask] = np.exp(diff[late_mask] / 10.0) - 1.0

    return float(np.sum(scores))


def evaluate_predictions(
    y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]
) -> Dict[str, float]:
    """Calculate comprehensive evaluation metrics for RUL regression.

    Returns:
        Dictionary containing RMSE, MAE, R2, NASA PHM Score, Mean Error (bias),
        and Max Absolute Error.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)

    # In case predictions have negative values, practical RUL is non-negative
    # However, raw model predictions are evaluated as produced
    mse = mean_squared_error(y_t, y_p)
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_t, y_p))
    r2 = float(r2_score(y_t, y_p))
    score = nasa_phm_score(y_t, y_p)

    errors = y_p - y_t
    bias = float(np.mean(errors))
    max_err = float(np.max(np.abs(errors)))

    return {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r2": round(r2, 4),
        "nasa_score": round(score, 2),
        "mean_bias": round(bias, 4),
        "max_abs_error": round(max_err, 4),
        "n_samples": int(len(y_t)),
    }
