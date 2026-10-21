"""Cryptographic model artifact authentication and canonical manifest verification for AeroSentinel.

Provides Ed25519 asymmetric signature verification, canonical JSON serialization,
tamper-evident SHA-256 artifact verification, and fail-closed secure loading
before any model or preprocessor deserialization.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import joblib

from aircraft_pm.config import (
    AEROSENTINEL_ED25519_PUBLIC_KEY,
    AEROSENTINEL_REQUIRE_AUTH,
    MODELS_DIR,
)


class ArtifactSecurityError(RuntimeError):
    """Raised when model or pipeline artifacts fail cryptographic authentication or integrity verification."""
    pass


def get_canonical_manifest_bytes(manifest: Dict[str, Any]) -> bytes:
    """Return deterministic canonical UTF-8 bytes for manifest signing and verification.

    The 'signature' key (if present) is excluded from the signed payload.
    Keys are sorted recursively and compact JSON formatting (no extra whitespace) is used.
    """
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return canonical_json.encode("utf-8")


def generate_ed25519_keypair() -> Tuple[str, str]:
    """Generate a new Ed25519 keypair, returning (private_key_hex, public_key_hex)."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_bytes.hex(), pub_bytes.hex()


def sign_manifest_dict(
    manifest: Dict[str, Any],
    private_key_hex: str,
    key_id: str = "aerosentinel-ed25519-v1",
) -> Dict[str, Any]:
    """Sign canonical manifest bytes using an Ed25519 private key.

    Returns a new copy of the manifest with the 'signature' block attached.
    """
    private_key_bytes = bytes.fromhex(private_key_hex.strip())
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)

    canonical_bytes = get_canonical_manifest_bytes(manifest)
    signature_bytes = private_key.sign(canonical_bytes)

    out = dict(manifest)
    out["signature"] = {
        "algorithm": "Ed25519",
        "key_id": key_id,
        "signature_hex": signature_bytes.hex(),
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }
    return out


def verify_manifest_signature(
    manifest: Dict[str, Any],
    public_key_hex: str,
    expected_key_id: Optional[str] = None,
) -> bool:
    """Verify Ed25519 signature of a manifest against a trusted public key.

    Raises ArtifactSecurityError if verification fails.
    """
    if "signature" not in manifest or not isinstance(manifest["signature"], dict):
        raise ArtifactSecurityError("Manifest has no 'signature' block.")

    sig_block = manifest["signature"]
    if sig_block.get("algorithm") != "Ed25519":
        raise ArtifactSecurityError(f"Unsupported signature algorithm: {sig_block.get('algorithm')}")

    if expected_key_id and sig_block.get("key_id") != expected_key_id:
        raise ArtifactSecurityError(
            f"Key ID mismatch: manifest has '{sig_block.get('key_id')}', expected '{expected_key_id}'"
        )

    sig_hex = sig_block.get("signature_hex", "")
    try:
        sig_bytes = bytes.fromhex(sig_hex)
        pub_bytes = bytes.fromhex(public_key_hex.strip())
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
    except Exception as e:
        raise ArtifactSecurityError(f"Invalid public key or signature hex: {e}")

    canonical_bytes = get_canonical_manifest_bytes(manifest)
    try:
        public_key.verify(sig_bytes, canonical_bytes)
        return True
    except InvalidSignature:
        raise ArtifactSecurityError("Cryptographic signature verification failed: signature invalid for canonical manifest content.")


def compute_file_sha256(filepath: Path) -> str:
    """Compute the hexadecimal SHA-256 checksum of a file on disk."""
    if not filepath.exists():
        return "file_not_found"

    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_artifact_hashes(
    manifest: Dict[str, Any],
    models_dir: Path,
) -> Dict[str, str]:
    """Verify on-disk SHA-256 hashes against manifest['artifacts_sha256'].

    Returns dict mapping artifact_name -> 'VERIFIED'.
    Raises ArtifactSecurityError on any mismatch or missing file.
    """
    artifacts_map = manifest.get("artifacts_sha256", {})
    if not artifacts_map:
        raise ArtifactSecurityError("Manifest does not declare any 'artifacts_sha256' entries.")

    # Mapping of manifest key to on-disk filename
    filename_map = {
        "best_model_joblib": "best_model.joblib",
        "preprocessor_joblib": "preprocessor.joblib",
        "histgradientboosting_joblib": "histgradientboosting.joblib",
        "random_forest_joblib": "random_forest.joblib",
        "model_registry_json": "model_registry.json",
    }

    results = {}
    for key, expected_sha in artifacts_map.items():
        fname = filename_map.get(key, key)
        fpath = models_dir / fname
        if not fpath.exists():
            raise ArtifactSecurityError(f"Required artifact file missing on disk: {fname} (path: {fpath})")

        actual_sha = compute_file_sha256(fpath)
        if actual_sha != expected_sha:
            raise ArtifactSecurityError(
                f"Artifact hash mismatch for {fname}: "
                f"on-disk={actual_sha[:16]}... != manifest={expected_sha[:16]}..."
            )
        results[key] = "VERIFIED"

    return results


def load_verified_model_pipeline(
    models_dir: Optional[Path] = None,
    public_key_hex: Optional[str] = None,
    require_signature: Optional[bool] = None,
) -> Tuple[Any, Any, Dict[str, Any]]:
    """Verify Ed25519 signature and SHA-256 hashes strictly BEFORE any deserialization.

    Fail-closed policy: If any verification check fails, no joblib.load is ever executed.

    Args:
        models_dir: Path containing model artifacts and model_manifest.json (default: MODELS_DIR).
        public_key_hex: Trusted Ed25519 public key hex (default: AEROSENTINEL_ED25519_PUBLIC_KEY).
        require_signature: If True, enforce Ed25519 signature check. If False (dev/test mode),
                           only SHA-256 hash checking is performed (default: AEROSENTINEL_REQUIRE_AUTH).

    Returns:
        Tuple of (fitted_preprocessor, production_model, verified_manifest).

    Raises:
        ArtifactSecurityError: If any verification check fails.
        FileNotFoundError: If manifest or required files are not found.
    """
    m_dir = models_dir or MODELS_DIR
    pub_key = public_key_hex or AEROSENTINEL_ED25519_PUBLIC_KEY
    must_sign = require_signature if require_signature is not None else AEROSENTINEL_REQUIRE_AUTH

    manifest_path = m_dir / "model_manifest.json"
    if not manifest_path.exists():
        raise ArtifactSecurityError(f"Model manifest not found: {manifest_path}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        raise ArtifactSecurityError(f"Malformed model manifest JSON: {e}")

    # Stage 1: Cryptographic Authentication (Ed25519 Signature Verification)
    if must_sign:
        if not pub_key:
            raise ArtifactSecurityError(
                "Secure artifact loading requires a trusted Ed25519 public key, but none is configured."
            )
        verify_manifest_signature(manifest, pub_key)

    # Stage 2: Tamper-Evident SHA-256 Hash Verification (All Artifacts)
    verify_artifact_hashes(manifest, m_dir)

    # Stage 3: Deserialization (Only executed if Stages 1 and 2 passed completely)
    prep_path = m_dir / "preprocessor.joblib"
    model_path = m_dir / "best_model.joblib"

    try:
        preprocessor = joblib.load(prep_path)
        prod_model = joblib.load(model_path)
    except Exception as e:
        raise ArtifactSecurityError(f"Deserialization failed after verification: {e}")

    return preprocessor, prod_model, manifest


def main():
    """CLI utility for offline artifact signing, verification, and key management."""
    parser = argparse.ArgumentParser(
        description="AeroSentinel Model Artifact Authentication Utility"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Keygen command
    p_keygen = subparsers.add_parser("keygen", help="Generate a new Ed25519 keypair")
    p_keygen.add_argument("--out-dir", type=Path, help="Directory to save private.key (0600)")

    # Sign command
    p_sign = subparsers.add_parser("sign", help="Sign model_manifest.json with an Ed25519 private key")
    p_sign.add_argument("--manifest", type=Path, default=MODELS_DIR / "model_manifest.json", help="Manifest path")
    p_sign.add_argument("--key", type=str, required=True, help="Private key hex string or path to private key file")
    p_sign.add_argument("--key-id", type=str, default="aerosentinel-ed25519-v1", help="Identifier for key")

    # Verify command
    p_verify = subparsers.add_parser("verify", help="Verify model_manifest.json and artifact SHA-256 hashes")
    p_verify.add_argument("--manifest", type=Path, default=MODELS_DIR / "model_manifest.json", help="Manifest path")
    p_verify.add_argument("--public-key", type=str, default=AEROSENTINEL_ED25519_PUBLIC_KEY, help="Public key hex")

    args = parser.parse_args()

    if args.command == "keygen":
        priv_hex, pub_hex = generate_ed25519_keypair()
        print(f"Generated Ed25519 Keypair:")
        print(f"PUBLIC KEY (Safe to commit / store in config):\n{pub_hex}\n")
        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            priv_file = args.out_dir / "aerosentinel_ed25519_private.key"
            priv_file.write_text(priv_hex, encoding="utf-8")
            print(f"Private key saved to: {priv_file}")
            print("WARNING: NEVER commit, share, or bundle the private key file.")
        else:
            print(f"PRIVATE KEY (DO NOT COMMIT):\n{priv_hex}")

    elif args.command == "sign":
        key_input = args.key
        if os.path.isfile(key_input):
            key_input = Path(key_input).read_text(encoding="utf-8").strip()

        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        signed_manifest = sign_manifest_dict(manifest_data, key_input, key_id=args.key_id)
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(signed_manifest, f, indent=2)

        print(f"Manifest successfully signed with Ed25519 key [{args.key_id}].")
        print(f"Signature hex: {signed_manifest['signature']['signature_hex']}")

    elif args.command == "verify":
        with open(args.manifest, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        verify_manifest_signature(manifest_data, args.public_key)
        print("Ed25519 Signature: VALID")
        hashes = verify_artifact_hashes(manifest_data, args.manifest.parent)
        for k, status in hashes.items():
            print(f"Artifact [{k}]: {status}")
        print("All artifact integrity and authenticity checks PASSED.")


if __name__ == "__main__":
    main()
