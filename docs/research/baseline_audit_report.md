# AeroSentinel Phase A — Baseline Audit and State Reconciliation Report

**Date of Audit**: October 21, 2026  
**Auditor Role**: Senior ML Security Researcher & Scientific Systems Auditor  
**Repository**: `D:\Simpson\Antigravity\aircraft-predictive-maintenance`  
**Current Git Branch**: `feature/aeroguard-2.1-engineering-upgrade`  
**HEAD Commit**: `bf3a858` (`feat(research): implement AeroSentinel Phase 2 offline telemetry attack simulation harness`)  
**Working Tree Status**: Clean (0 uncommitted changes, 0 staged changes)  

---

## 1. Executive Summary & Objective

This baseline audit reconciles the actual code, data, models, test suites, and documentation against previous milestone claims (Engineering Upgrade, Ed25519 Artifact Authentication, Offline Telemetry Attack Simulation). Every component is treated as a claim requiring independent code and execution verification.

---

## 2. Comprehensive Reconciliation & Verification Matrix

| Feature / Subsystem | Source Files | Implementation Status | Verification Performed | Defect or Limitation | Required Action |
|---|---|---|---|---|---|
| **NASA C-MAPSS Preprocessing & Features** | `src/aircraft_pm/features.py`, `src/aircraft_pm/data.py` | Complete & functional | Verified unit tests (`test_features.py`, `test_data.py`); 122 causal temporal rolling features; strictly isolated by `GroupBy(engine_id)` | None. Clean causal lookback design verified. | Preserve exact implementation. |
| **Prognostic Regression Models** | `src/aircraft_pm/models/train.py`, `models/best_model.joblib` | Trained & frozen | 4 candidate models in registry; champion is `HistGradientBoostingRegressor` | Model was trained on clipped target (125 cycles). Unclipped vs clipped protocols must remain strictly separated. | Maintain dual-protocol separation across all reports. |
| **Model Manifest & Cryptographic Lineage** | `src/aircraft_pm/lineage.py`, `models/model_manifest.json` | Complete with Ed25519 signature | Verified SHA-256 hashes against all on-disk artifacts; Ed25519 signature verified with production public key | Calling `generate_lineage_manifest()` without arguments overwrites `model_manifest.json` with an unsigned version. | Add guard preventing accidental clobbering of the signed manifest. |
| **Artifact Authentication Loader** | `src/aircraft_pm/crypto.py`, `tests/test_artifact_authentication.py` | Functional & tested | 9 security tests passing; rejects modified model bytes, modified preprocessor, modified metadata, missing signature, rewrite attacks | Missing explicit tests for: malformed JSON, trust-key mismatch, key-id mismatch. | Add tests for malformed JSON, key mismatch, and key-id mismatch in Phase E1. |
| **Telemetry Attack Simulation** | `src/aircraft_pm/attacks.py`, `scripts/simulate_attacks.py` | Functional | 7 unit tests passing in `tests/test_attacks.py`; 6 attack scenarios simulated on 100 test engines | **Defect 1**: `scripts/simulate_attacks.py` queried `r.get("psi_status")` which doesn't exist in `drift.py` (key is `status`), causing PSI alert channel count to always report 0. <br>**Defect 2**: HPR used ad-hoc `delta_rul > 15.0 & critical_mask` instead of the canonical definition `pred_atk > 25 & y_true <= 25`. | Fix drift feature status extraction and implement canonical HPR definition in Phase D/E. |
| **Statistical Drift Detection (KS / PSI)** | `src/aircraft_pm/drift.py`, `tests/test_drift.py` | Functional | Non-parametric KS 2-sample test and 10-bin quantile PSI | C-MAPSS test engines are run-to-cutoff, whereas train engines are run-to-failure; natural censoring causes false warnings when comparing test to train. | Systematically evaluate both reference baselines (`train_FD001` and clean `test_FD001`) and document FPR. |
| **FastAPI REST Backend** | `src/aircraft_pm/api.py`, `tests/test_api.py` | Functional | 15 API unit tests passing; observability middleware; health, fleet, predict, drift, and lineage endpoints | Lacks dedicated security hardening tests (payload bounds, NaN/inf rejection, path traversal, injection, rate-limiting behavior). Security status endpoints not exposed to UI. | Add API security test suite and dedicated security endpoints in Phase E4/G. |
| **Nuxt 3 Dashboard Frontend** | `frontend/app/pages/*.vue`, `frontend/package.json` | Functional | Production build succeeds; Yafa-UI design tokens implemented; connects to backend | Security status, artifact authentication verification, and attack simulation findings are not surfaced on the dashboard. | Surface verified security state and attack simulation findings in Phase G with synthetic disclaimers. |
| **Docker & Compose Environment** | `backend.Dockerfile`, `frontend.Dockerfile`, `compose.yaml` | Defined but unverified | Inspected dockerfiles; syntax is valid | Docker daemon is not active in this host environment; containers cannot be tested live. | Clearly document Docker execution status as "defined, unverified in current local host" per instructions. |
| **Experimental Documentation & Reports** | `reports/research/*` | Partially populated | 4 research artifacts generated in Phase 2 | Historical benchmark latency numbers showed arithmetic discrepancies (21.4ms vs 22.6ms vs 13.8ms claimed overhead). Figures directory missing. | Conduct rigorously controlled latency profiling and generate publication-quality figures in Phase E5/F. |

---

## 3. Discrepancy & Anomaly Reconciliation

### 3.1 Reconciliation of Zero PSI Alert Channels vs `drift_alert` Status
- **Root Cause Identified**: In `scripts/simulate_attacks.py` line 276:
  ```python
  psi_drift_clean = [f for f, r in drift_report_clean_test.get("features", {}).items() if r.get("psi_status") == "drift"]
  ```
  In `src/aircraft_pm/drift.py`, the per-feature dictionary key is `"status"` (with values `"drift_alert"`, `"warning"`, or `"stable"`), NOT `"psi_status"`.
- Consequently, `len(psi_drift_clean)` always evaluated to `0`, even when individual features were classified as `"drift_alert"`.
- The overall status (`warning` or `drift_alert`) was computed correctly in `drift.py` using internal lists `drift_alert_features` and `warning_features`, creating the apparent contradiction in the summary table where `PSI Alert Channels = 0` coincided with `Status = warning` or `Status = drift_alert`.

### 3.2 Reconciliation of Hazardous Prediction Rate (HPR) Semantics
- In `scripts/simulate_attacks.py`, HPR was computed as:
  ```python
  hazardous_count = int(np.sum((delta_rul > 15.0) & critical_mask))
  ```
  where `critical_mask = y_clipped <= 25`.
- **Intended Canonical Definition**:
  $$\text{HPR} = \frac{\sum_{i \in \text{Critical}} \mathbb{I}(\hat{y}_i^{\text{attack}} > 25)}{|\text{Critical}|} \times 100\%$$
  where $\text{Critical} = \{i : y_i \le 25\}$.
- An engine with true RUL of 18 whose prediction is shifted from 20 to 28 ($\Delta = +8 \le 15$) was previously omitted from the numerator despite presenting a hazardous condition (maintenance deferred past the critical 25-cycle threshold).
- This will be corrected to the canonical definition in Phase D/E.

### 3.3 Reconciliation of Latency Overhead Claims
- Historical documentation claimed an artifact verification overhead of ~13.87 ms, while reported deserialization mean was 21.407 ms and verified pipeline mean was 22.621 ms (a delta of only 1.214 ms).
- **Audit Diagnosis**: The 13.87 ms figure conflated full cold-start verification (including parsing JSON and verifying Ed25519 signature) with warm/cached runtime verification, or was measured across different machine architectures.
- Controlled microbenchmarking with explicit separation of cryptographic verification, SHA-256 hashing, deserialization, and inference will be conducted in Phase E5.

---

## 4. Quality Gate Status
Phase A is **PASSED**. Key defects and discrepancies have been identified with precise code-level root causes, establishing a verified foundation for Phases B through J.
