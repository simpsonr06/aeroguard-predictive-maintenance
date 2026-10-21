"""Automated verification and security boundary tests for AeroSentinel artifact authentication."""

import json
from pathlib import Path
import shutil
from unittest.mock import patch
import pytest

from aircraft_pm.config import (
    AEROSENTINEL_ED25519_PUBLIC_KEY,
    MODELS_DIR,
)
from aircraft_pm.crypto import (
    ArtifactSecurityError,
    generate_ed25519_keypair,
    get_canonical_manifest_bytes,
    load_verified_model_pipeline,
    sign_manifest_dict,
    verify_artifact_hashes,
    verify_manifest_signature,
)


@pytest.fixture
def mock_models_dir(tmp_path: Path) -> Path:
    """Fixture that copies genuine production artifacts into an isolated disposable test directory."""
    test_models = tmp_path / "models"
    test_models.mkdir(parents=True, exist_ok=True)

    for item in [
        "best_model.joblib",
        "preprocessor.joblib",
        "histgradientboosting.joblib",
        "random_forest.joblib",
        "model_registry.json",
        "model_manifest.json",
    ]:
        src = MODELS_DIR / item
        if src.exists():
            shutil.copy2(src, test_models / item)

    return test_models


def test_valid_artifact_verification_and_loading(mock_models_dir: Path):
    """Production artifacts must verify and load with zero security exceptions."""
    prep, model, manifest = load_verified_model_pipeline(
        models_dir=mock_models_dir,
        public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
        require_signature=True,
    )
    assert prep is not None
    assert model is not None
    assert manifest["signature"]["algorithm"] == "Ed25519"
    assert manifest["model_id"] == "histgradientboosting-fd001-v2.1"


def test_modified_model_bytes_rejected_before_deserialization(mock_models_dir: Path):
    """Mutating model bytes must trigger ArtifactSecurityError without deserialization."""
    model_path = mock_models_dir / "best_model.joblib"
    data = bytearray(model_path.read_bytes())
    # Flip a single byte in the middle of the serialized payload
    data[len(data) // 2] ^= 0xFF
    model_path.write_bytes(bytes(data))

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Artifact hash mismatch for best_model.joblib"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        # CRITICAL SECURITY CHECK: joblib.load MUST NEVER be called on tampered file
        mock_load.assert_not_called()


def test_modified_preprocessor_bytes_rejected_before_deserialization(mock_models_dir: Path):
    """Mutating preprocessor bytes must trigger ArtifactSecurityError without deserialization."""
    prep_path = mock_models_dir / "preprocessor.joblib"
    data = bytearray(prep_path.read_bytes())
    data[len(data) // 2] ^= 0xAA
    prep_path.write_bytes(bytes(data))

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Artifact hash mismatch for preprocessor.joblib"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_altered_manifest_field_rejected(mock_models_dir: Path):
    """Tampering with signed manifest fields invalidates the Ed25519 signature."""
    manifest_path = mock_models_dir / "model_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Malicious actor changes reported unclipped RMSE to a fake number
    manifest["evaluation_protocols"]["raw_unclipped_official_test"]["rmse"] = 5.0000

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="signature invalid for canonical manifest content"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_invalid_signature_hex_rejected(mock_models_dir: Path):
    """Corrupting the signature bytes causes signature verification failure."""
    manifest_path = mock_models_dir / "model_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    sig_hex = manifest["signature"]["signature_hex"]
    # Corrupt last 4 hex characters
    corrupted_hex = sig_hex[:-4] + "dead"
    manifest["signature"]["signature_hex"] = corrupted_hex

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="signature invalid for canonical manifest content"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_missing_signature_rejected_in_secure_mode(mock_models_dir: Path):
    """An unsigned manifest is rejected when require_signature is True."""
    manifest_path = mock_models_dir / "model_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    del manifest["signature"]

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Manifest has no 'signature' block"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_missing_artifact_file_rejected(mock_models_dir: Path):
    """Absence of a required on-disk artifact triggers fail-closed error."""
    model_path = mock_models_dir / "best_model.joblib"
    model_path.unlink()

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Required artifact file missing on disk"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_manifest_rewrite_attack_defeated(mock_models_dir: Path):
    """Attacker modifies model AND updates SHA-256 in manifest without a valid private key.
    
    Hash verification passes against the modified manifest, BUT Ed25519 signature
    verification fails, defeating the rewrite attack.
    """
    model_path = mock_models_dir / "best_model.joblib"
    manifest_path = mock_models_dir / "model_manifest.json"

    # 1. Attacker tampers with model
    data = bytearray(model_path.read_bytes())
    data[100] ^= 0x42
    model_path.write_bytes(bytes(data))

    # 2. Attacker updates the SHA-256 inside manifest to match the tampered model
    import hashlib
    new_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["artifacts_sha256"]["best_model_joblib"] = new_sha

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 3. Verification must fail because signature was computed on original manifest
    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="signature invalid for canonical manifest content"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_dev_mode_fallback_behavior(mock_models_dir: Path):
    """In explicit development mode (require_signature=False), unsigned manifest is tolerated if hashes match."""
    manifest_path = mock_models_dir / "model_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    del manifest["signature"]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # In dev mode, unsigned manifest loads safely because on-disk SHA-256 matches
    prep, model, _ = load_verified_model_pipeline(
        models_dir=mock_models_dir,
        public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
        require_signature=False,
    )
    assert prep is not None
    assert model is not None

    # But if an artifact is tampered even in dev mode, hash checking STILL fails closed!
    model_path = mock_models_dir / "best_model.joblib"
    data = bytearray(model_path.read_bytes())
    data[50] ^= 0x01
    model_path.write_bytes(bytes(data))

    with pytest.raises(ArtifactSecurityError, match="Artifact hash mismatch for best_model.joblib"):
        load_verified_model_pipeline(
            models_dir=mock_models_dir,
            public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
            require_signature=False,
        )


def test_malformed_manifest_json_rejected(mock_models_dir: Path):
    """Corrupted/non-JSON manifest files trigger fail-closed rejection without loading."""
    manifest_path = mock_models_dir / "model_manifest.json"
    manifest_path.write_text("{this is corrupted: invalid json syntax", encoding="utf-8")

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Malformed model manifest JSON"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_trust_key_mismatch_rejected(mock_models_dir: Path):
    """Validly signed manifest verified against an untrusted/different public key fails closed."""
    _, untrusted_pub = generate_ed25519_keypair()

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="signature invalid for canonical manifest content"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=untrusted_pub,
                require_signature=True,
            )
        mock_load.assert_not_called()


def test_unsupported_signature_algorithm_rejected(mock_models_dir: Path):
    """Manifest specifying unsupported algorithm (e.g. RSA or DSA) is rejected."""
    manifest_path = mock_models_dir / "model_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["signature"]["algorithm"] = "RSA-PSS-SHA256"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    with patch("joblib.load") as mock_load:
        with pytest.raises(ArtifactSecurityError, match="Unsupported signature algorithm: RSA-PSS-SHA256"):
            load_verified_model_pipeline(
                models_dir=mock_models_dir,
                public_key_hex=AEROSENTINEL_ED25519_PUBLIC_KEY,
                require_signature=True,
            )
        mock_load.assert_not_called()

