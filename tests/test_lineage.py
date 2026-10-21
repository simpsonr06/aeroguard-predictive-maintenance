"""Deterministic tests for model lineage, artifact verification, and metric consistency in AeroGuard 2.1."""

import json
from pathlib import Path
import joblib
import numpy as np
import pytest

from aircraft_pm.config import MODELS_DIR
from aircraft_pm.data import load_test_data
from aircraft_pm.lineage import (
    BEST_MODEL_PATH,
    PREPROCESSOR_PATH,
    compute_file_sha256,
    generate_lineage_manifest,
    get_model_lineage_manifest,
)
from aircraft_pm.metrics import evaluate_predictions


def test_compute_file_sha256_existing_file(tmp_path: Path):
    """Test SHA-256 calculation on known input."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("AeroGuard 2.1 Prognostics Lineage Test", encoding="utf-8")

    sha = compute_file_sha256(test_file)
    assert len(sha) == 64
    assert isinstance(sha, str)


def test_compute_file_sha256_missing_file(tmp_path: Path):
    """Missing file should return 'file_not_found' string rather than crash."""
    missing_file = tmp_path / "does_not_exist.bin"
    sha = compute_file_sha256(missing_file)
    assert sha == "file_not_found"


def test_generate_lineage_manifest_structure(tmp_path: Path):
    """Manifest must contain version, algorithm, SHA-256 checksums, and evaluation protocols."""
    manifest_out = tmp_path / "model_manifest_test.json"
    manifest = generate_lineage_manifest(output_path=manifest_out)

    assert manifest["manifest_version"] == "2.1.0"
    assert manifest["model_id"] == "histgradientboosting-fd001-v2.1"
    assert manifest["algorithm"] == "HistGradientBoostingRegressor"
    assert "artifacts_sha256" in manifest
    assert "datasets_sha256" in manifest
    assert "best_model_joblib" in manifest["artifacts_sha256"]
    assert "train_FD001" in manifest["datasets_sha256"]
    assert len(manifest["artifacts_sha256"]["best_model_joblib"]) == 64
    assert "mlflow_evaluation" in manifest
    assert "evaluation_protocols" in manifest
    assert manifest_out.exists()


def test_get_model_lineage_manifest_cached():
    """Retrieve production manifest from disk or memory and verify protocol separation."""
    manifest = get_model_lineage_manifest()
    assert manifest["manifest_version"] == "2.1.0"
    assert "evaluation_protocols" in manifest
    assert "evaluation_regimes" in manifest

    raw = manifest["evaluation_protocols"]["raw_unclipped_official_test"]
    clipped = manifest["evaluation_protocols"]["clipped_125_ground_truth"]

    # Verify raw unclipped official metrics
    assert raw["rmse"] == 13.9044
    assert raw["mae"] == 10.4044
    assert round(raw["r2"], 4) == 0.8880
    assert raw["nasa_score_total"] == 301.97
    assert raw["nasa_score_per_engine"] == 3.02
    assert raw["test_engines_count"] == 100

    # Verify clipped @ 125 metrics
    assert clipped["rmse"] == 13.0082
    assert clipped["mae"] == 9.3344
    assert round(clipped["r2"], 4) == 0.8946
    assert clipped["nasa_score_total"] == 280.35
    assert clipped["nasa_score_per_engine"] == 2.80
    assert clipped["test_engines_count"] == 100


def test_manifest_metric_consistency_and_separation():
    """Ensure raw unclipped and clipped metrics are never conflated or mixed."""
    manifest = get_model_lineage_manifest()
    protocols = manifest["evaluation_protocols"]

    raw = protocols["raw_unclipped_official_test"]
    clipped = protocols["clipped_125_ground_truth"]

    # The two evaluation protocols must have distinct values
    assert raw["rmse"] != clipped["rmse"], "Unclipped and clipped RMSE must not be identical"
    assert raw["mae"] != clipped["mae"], "Unclipped and clipped MAE must not be identical"
    assert raw["nasa_score_total"] != clipped["nasa_score_total"], "NASA scores must differ between protocols"

    # Evaluation regimes must also reflect explicit naming
    regimes = manifest["evaluation_regimes"]
    assert regimes["raw_unclipped_official_test_rmse"] == 13.9044
    assert regimes["clipped_125_test_rmse"] == 13.0082


def test_manifest_metrics_match_live_evaluation():
    """Verify that manifest values are not hardcoded fictions and exactly match live model evaluation."""
    manifest = get_model_lineage_manifest()

    model = joblib.load(BEST_MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    test_df, test_last, _ = load_test_data(clip_rul=125)

    X_test_scaled, test_feat_df = preprocessor.transform(test_df)
    test_feat_df = test_feat_df.copy()

    all_preds = model.predict(X_test_scaled)
    all_preds = np.clip(all_preds, 0, 125)
    test_feat_df["pred"] = all_preds
    last_preds = test_feat_df.groupby("engine_id")["pred"].last().values

    y_unclipped = test_last["rul"].values
    y_clipped = test_last["rul_clipped"].values

    live_raw = evaluate_predictions(y_unclipped, last_preds)
    live_clipped = evaluate_predictions(y_clipped, last_preds)

    raw_manifest = manifest["evaluation_protocols"]["raw_unclipped_official_test"]
    clipped_manifest = manifest["evaluation_protocols"]["clipped_125_ground_truth"]

    assert raw_manifest["rmse"] == live_raw["rmse"]
    assert raw_manifest["mae"] == live_raw["mae"]
    assert raw_manifest["nasa_score_total"] == live_raw["nasa_score"]

    assert clipped_manifest["rmse"] == live_clipped["rmse"]
    assert clipped_manifest["mae"] == live_clipped["mae"]
    assert clipped_manifest["nasa_score_total"] == live_clipped["nasa_score"]


def test_manifest_security_disclaimer():
    """Verify security disclaimer accurately defines SHA-256 boundaries and avoids false immutability claims."""
    manifest = get_model_lineage_manifest()
    disclaimer = manifest.get("security_disclaimer", "")

    # Must NOT claim the unsigned manifest is immutable
    assert "not immutable" in disclaimer.lower()

    # Must explicitly state SHA-256 alone does not authenticate against an attacker with filesystem write access
    assert "does not authenticate" in disclaimer.lower() or "not authenticate" in disclaimer.lower()
    assert "write access" in disclaimer.lower()
