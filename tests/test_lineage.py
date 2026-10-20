"""Deterministic tests for cryptographic model lineage in AeroGuard 2.1."""

from pathlib import Path
import pytest

from aircraft_pm.lineage import (
    compute_file_sha256,
    generate_lineage_manifest,
    get_model_lineage_manifest,
)


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
    """Manifest must contain version, algorithm, SHA-256 checksums, and MLflow evaluation."""
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
    assert manifest_out.exists()


def test_get_model_lineage_manifest_cached():
    """Retrieve production manifest from disk or memory."""
    manifest = get_model_lineage_manifest()
    assert manifest["manifest_version"] == "2.1.0"
    assert "evaluation_regimes" in manifest
    assert manifest["evaluation_regimes"]["official_test_rmse"] == 13.01
