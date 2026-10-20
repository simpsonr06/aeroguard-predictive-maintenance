"""End-to-end integration tests verifying artifacts, model registry, and prediction pipeline."""

import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from aircraft_pm.config import FIGURES_DIR, MODELS_DIR, REPORTS_DIR
from aircraft_pm.data import load_test_data


def test_model_artifacts_and_registry_exist():
    """Ensure all required model artifacts and registry files are generated."""
    preprocessor_path = MODELS_DIR / "preprocessor.joblib"
    best_model_path = MODELS_DIR / "best_model.joblib"
    registry_path = MODELS_DIR / "model_registry.json"

    assert preprocessor_path.exists(), "preprocessor.joblib not found"
    assert best_model_path.exists(), "best_model.joblib not found"
    assert registry_path.exists(), "model_registry.json not found"

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    assert "cross_validation" in registry
    assert "official_test" in registry
    assert "best_model" in registry


def test_reports_and_figures_generated():
    """Ensure all required EDA and evaluation figures are present."""
    expected_figures = [
        "engine_lifetime_distribution.png",
        "sensor_variance_profile.png",
        "sensor_degradation_trajectories.png",
        "sensor_correlations.png",
        "model_test_predictions.png",
        "model_residuals.png",
        "feature_importances.png",
    ]

    for fig_name in expected_figures:
        fig_path = FIGURES_DIR / fig_name
        assert fig_path.exists(), f"Expected figure not found: {fig_name}"
        assert fig_path.stat().st_size > 1000, f"Figure is suspiciously small: {fig_name}"

    assert (REPORTS_DIR / "eda_summary.md").exists()
    assert (REPORTS_DIR / "model_evaluation_report.md").exists()


def test_production_model_inference():
    """Verify loading production model and generating RUL predictions on real test data."""
    preprocessor = joblib.load(MODELS_DIR / "preprocessor.joblib")
    model = joblib.load(MODELS_DIR / "best_model.joblib")

    test_df, test_last, _ = load_test_data()

    # Score sample sequence from test engine 1
    sample = test_df[test_df["engine_id"] == 1].copy()
    X_scaled, _ = preprocessor.transform(sample)
    preds = model.predict(X_scaled)

    assert len(preds) == len(sample)
    assert not np.isnan(preds).any()
    # At the final cycle, predicted RUL should be within reasonable bounds (> 0 and < 200)
    final_pred = preds[-1]
    assert 0 <= final_pred <= 200
