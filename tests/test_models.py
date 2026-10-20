"""Unit tests for model instantiation, training, and inference."""

import numpy as np
import pytest

from aircraft_pm.models.train import get_candidate_models


def test_candidate_models_presence():
    """Verify all required model families are present: baseline, linear, tree-based."""
    models = get_candidate_models(random_state=42)

    assert "Dummy (Mean Baseline)" in models
    assert "Ridge Regression" in models
    assert "Random Forest" in models
    assert "HistGradientBoosting" in models


def test_candidate_models_fit_predict():
    """Verify each candidate model fits and produces valid 1D prediction output."""
    models = get_candidate_models(random_state=42)

    X_synthetic = np.random.RandomState(42).randn(50, 10)
    y_synthetic = np.random.RandomState(42).uniform(10, 120, size=50)

    for name, model in models.items():
        model.fit(X_synthetic, y_synthetic)
        preds = model.predict(X_synthetic)

        assert preds.shape == (50,), f"{name} output shape mismatch"
        assert not np.isnan(preds).any(), f"{name} produced NaN predictions"
