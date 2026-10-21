# AeroGuard 2.1 — Engineering Upgrade Gap Analysis & Technical Specification

**Date:** October 2026  
**Baseline:** AeroGuard 2.0 (`commit e99b497`)  
**Branch:** `feature/aeroguard-2.1-engineering-upgrade`  
**Dataset Scope:** NASA C-MAPSS Turbofan Run-to-Failure Simulation (FD001 Benchmark)

---

## 1. Executive Summary

AeroGuard 2.0 established a validated, high-performance predictive maintenance dashboard combining a FastAPI backend, trained HistGradientBoosting regression pipeline, and Nuxt 4/Yafa-UI frontend. This gap analysis evaluates specific engineering deficiencies identified in the benchmark research prototype and outlines the evidence-driven upgrades for AeroGuard 2.1 across four core dimensions:
1. **Containerized Deployment & Runtime Orchestration**
2. **Feature Distribution Drift Monitoring**
3. **Structured Observability & Metrics Instrumentation**
4. **Cryptographic Model Lineage & Reproducibility Manifest**

---

## 2. Detailed Gap Analysis Matrix

| Engineering Area | Current State (AeroGuard 2.0) | Actual Deficiency | Upgrade Strategy (AeroGuard 2.1) |
| :--- | :--- | :--- | :--- |
| **Containerization** | Requires local Python virtualenv + Bun dev server running concurrently. | Non-portable; requires manual dependency installation; no service health synchronization or container restart policies. | Add multi-stage `Dockerfile` for FastAPI (`backend.Dockerfile`), optimized production `Dockerfile` for Nuxt (`frontend.Dockerfile`), and root `compose.yaml` with health checks and network bridging. |
| **Drift Monitoring** | Model evaluation is static on FD001 train vs test. No runtime or batch drift detection. | Operators cannot identify when sensor distributions deviate from nominal baseline, risking silent prognostic decay. | Implement `src/aircraft_pm/drift.py` computing Kolmogorov-Smirnov (KS) statistics and Population Stability Index (PSI) per feature. Expose via `/api/drift` and visualize in dashboard. |
| **Observability** | Standard Python `print` and Uvicorn log statements. No request timing or error rate tracking. | Lack of visibility into API latency distributions, prediction volume, failure rates, or graceful frontend handling of backend outages. | Implement FastAPI logging & metrics middleware tracking latency (mean/p95), throughput, and error rates. Expose `/api/metrics`. Add frontend connectivity banner. |
| **Model Lineage** | `models/model_registry.json` tracks model scores but lacks provenance details. | Missing artifact hashes, dataset checksums, training environment details, and explicit causal window policy verification. | Implement tamper-evident `models/model_manifest.json` recording SHA-256 hashes of all artifacts, exact training hyperparameters, feature definitions, and lineage API endpoint `/api/models/lineage`. Note: SHA-256 checksums provide integrity verification; unsigned manifests do not provide cryptographic authentication against local filesystem modification. |

---

## 3. Scope Boundaries & Constraints

1. **Benchmark Integrity:** Strictly maintain NASA C-MAPSS FD001 data provenance. Do not introduce synthetic streaming data masked as live telemetry.
2. **Stack Preservation:** Retain FastAPI, Nuxt 4, Scikit-Learn/Joblib, and Streamlit fallback.
3. **No Unwarranted Heavy Infrastructure:** Avoid Kafka, Redis, or cloud-specific services that do not solve a concrete problem for an offline/batch-predictive architecture.
4. **Zero Test-Label Leakage:** Maintain strict temporal separation; never compute drift metrics or predictions using future test labels.
