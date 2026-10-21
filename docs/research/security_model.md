# AeroSentinel: Threat Model & Security Engineering Specification

**Document Identifier:** `DOC-RES-003`  
**Version:** `1.0.0`  
**Classification:** Security Architecture & Cryptographic Integrity  
**Key Reference Public Key:** `2fc1416b5634cf20e6b403fafc572160b27615adbdf5352458a492d52251e45b`  

---

## 1. Threat Classification (STRIDE)

We map threats against aircraft predictive maintenance analytics using the Microsoft STRIDE framework:

| STRIDE Category | Threat Description | Attack Vector in Maintenance Analytics | AeroSentinel Control |
|---|---|---|---|
| **Spoofing** | Telemetry source impersonation | Ground gateway injecting false aircraft tail numbers | Request metadata validation & tail registry matching |
| **Tampering** | Model artifact corruption or telemetry modification | Modifying `model.joblib` weights; altering $s_{11}$ pressure readings in transit | **Ed25519 signature verification** on startup; **Dual-baseline KS/PSI drift screening** |
| **Repudiation** | Denying dispatch of corrupted model or telemetry | Dispatching unvetted model to maintenance hangars without audit trail | Cryptographic signature binding author, timestamp, git commit, and dataset hash |
| **Information Disclosure** | Leakage of proprietary engine parameters or credentials | Stack traces exposing server internals; logging raw credentials | Fail-closed Pydantic error handlers; sanitized structured JSON logs |
| **Denial of Service** | Exhaustion of inference endpoints with malformed requests | Sending NaN/Inf floats, oversized payloads, or recursive JSON | Strict Pydantic float validation (`math.isnan`, `math.isinf` rejection); payload caps |
| **Elevation of Privilege** | Bypassing verification to execute arbitrary pickle bytecode | Exploiting `joblib.load` Python object deserialization gadget chains | Pre-deserialization SHA-256 verification against cryptographically authenticated manifest |

---

## 2. Cryptographic Authentication Specification

### 2.1 Algorithm Selection & Rationale
* **Algorithm:** Edwards-curve Digital Signature Algorithm over Curve25519 (**Ed25519**, RFC 8032).
* **Security Level:** 128-bit security level, resistant to side-channel timing attacks, branch-prediction attacks, and small-subgroup attacks.
* **Key Representation:** 32-byte public key (hex-encoded string of 64 characters), 64-byte signature (hex-encoded string of 128 characters).
* **Rationale over RSA:** RSA-2048/4096 requires significantly larger key and signature sizes, exhibits order-of-magnitude slower verification latencies, and is vulnerable to padding oracle attacks.

### 2.2 Canonical Serialization (RFC 8785)
Cryptographic signatures must sign a deterministic byte representation. Standard JSON serializers introduce non-deterministic whitespace, dict key ordering, and floating-point representations. AeroSentinel implements canonical formatting:
$$\text{bytes}_{\text{canonical}} = \text{json.dumps}(M_{\text{payload}}, \text{sort\_keys}=\text{True}, \text{separators}=(',', ':'), \text{ensure\_ascii}=\text{False}).\text{encode}('utf-8')$$
Where $M_{\text{payload}}$ contains all manifest fields *except* the `signature` object itself.

### 2.3 Fail-Closed Deserialization Protocol
In Python applications, `joblib.load()` or `pickle.loads()` deserializes arbitrary object state, representing a critical Remote Code Execution (RCE) vector if corrupted artifacts are read. AeroSentinel enforces an inviolable pre-execution check:

```
[Startup / Model Load Request]
          │
          ▼
   Read Manifest JSON
          │
          ├──> 1. Check Public Key matches Pinned Key? ──[NO]──> RAISE VerificationError (Abort)
          │
          ├──> 2. Check Signature Scheme == "ed25519"? ──[NO]──> RAISE VerificationError (Abort)
          │
          ├──> 3. Verify Ed25519 Signature over RFC 8785 JSON ──[FAIL]──> RAISE VerificationError (Abort)
          │
          ├──> 4. Compute SHA-256 of all 5 physical artifacts on disk
          │       Compare with hashes declared in Signed Manifest ──[MISMATCH]──> RAISE IntegrityError (Abort)
          │
          ▼ [100% MATCH]
   Invoke joblib.load(model_path)
```
No artifact file is ever passed to `joblib.load` unless both cryptographic verification and byte-level SHA-256 digest checks succeed.

---

## 3. API Security & Input Hardening

The FastAPI prediction interface (`/api/v1/predict`, `/api/v1/predict/fleet`) is hardened according to OWASP API Security Top 10 recommendations:

1. **Non-Finite Value Rejection:**  
   Pydantic validators screen every sensor float field. Any value satisfying $\text{isnan}(x)$ or $\text{isinf}(x)$ triggers HTTP 422 with a structured error payload. Python `float('nan')` deserialization exploits are eliminated.
2. **Dimension & Range Enforcement:**  
   Every payload must provide all 14 active degradation channels. Missing channels or extra unknown channels are rejected.
3. **Structured Audit Endpoints:**  
   The API exposes dedicated audit endpoints:
   - `GET /api/security/status`: Reports Ed25519 verification state, manifest timestamp, pinned public key, artifact file digests, and security mode (`verified` vs `permissive`).
   - `GET /api/security/attack-simulation`: Provides real-time resilience benchmark metrics across all 6 evaluated attack scenarios.
4. **Information Leakage Prevention:**  
   FastAPI exception handlers catch unhandled server errors, logging detailed exceptions to internal files while returning sanitized, generic messages (`"Internal processing error"`) to external clients.
