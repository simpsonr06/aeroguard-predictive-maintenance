# AeroGuard 2.0 — Architecture & ML Baseline Audit Report

**Date:** October 20, 2026  
**Auditor:** Senior Full-Stack & ML Systems Architect  
**Project:** AeroGuard Aircraft Predictive Maintenance (NASA C-MAPSS FD001)

---

## 1. Executive Summary & Objective

This audit establishes the baseline for the **AeroGuard 2.0** full-stack migration. AeroGuard is transitioning from a standalone Streamlit prototype to a decoupled enterprise architecture:
1. **Frontend:** Nuxt 3 + Vue 3 + TypeScript based on the official Nuxt UI Dashboard template (`frontend/`).
2. **Backend:** FastAPI high-performance ASGI service (`src/aircraft_pm/api.py`).
3. **ML Core:** Direct reuse of existing trained models (`models/best_model.joblib`), preprocessing pipelines (`models/preprocessor.joblib`), and benchmark registry (`models/model_registry.json`).
4. **Preservation:** The existing Streamlit dashboard (`src/aircraft_pm/app.py`) is preserved intact and remains fully runnable on port 8501.

---

## 2. ML & Data Pipeline Audit

### 2.1 Dataset Ingestion & Schema Integrity (`src/aircraft_pm/data.py`)
- **Dataset:** NASA C-MAPSS FD001 (Sea-Level single-condition, High-Pressure Compressor degradation).
- **Training Fleet (`train_FD001.txt`):** 100 run-to-failure engines, 20,631 total cycles ($T_i \in [128, 362]$).
- **Test Fleet (`test_FD001.txt`):** 100 in-service truncated engines, 13,096 cycles ($t_{\text{cutoff}} \in [31, 303]$).
- **Ground Truth Targets (`RUL_FD001.txt`):** 100 true remaining cycles strictly for held-out evaluation.
- **Data Validation:** Enforces zero missing values, cycle monotonicity ($c_{t} = c_{t-1} + 1$), and column schema adherence.

### 2.2 Causal Feature Engineering (`src/aircraft_pm/features.py`)
- **Physics Variance Pruning:** 7 invariant channels (`setting_3`, `sensor_1`, `sensor_5`, `sensor_10`, `sensor_16`, `sensor_18`, `sensor_19`) with $\sigma < 10^{-4}$ pruned. 14 informative degradation channels retained.
- **Engine-Level Isolation:** Rolling aggregations (windows $w \in \{5, 10, 20\}$) and lag differences ($k \in \{1, 5\}$) grouped strictly by `engine_id`.
- **Zero Future Leakage:** For any cycle $t$, features use observations strictly in $[1, t]$.
- **Baseline Drift:** Causal drift $x(t) - x(1)$ computed without knowledge of terminal cycle $T_i$.
- **Feature Vector:** 122 total scaled numerical features.

### 2.3 Production Model & Artifact Registry (`models/`)
- **Production Classifier/Regressor:** `HistGradientBoostingRegressor` serialized as `models/best_model.joblib`.
- **Preprocessor:** Fitted `CMAPSSPreprocessor` pipeline serialized as `models/preprocessor.joblib`.
- **Target Policy:** Training targets clipped at $RUL = 125$ cycles.
- **Evaluation Regimes (`models/model_registry.json`):**
  1. *Official Test Set (Held-Out Final Cycle):* RMSE = 13.90 cycles (Clipped RMSE = 13.01), MAE = 10.40 cycles, $R^2 = 0.888$, NASA Score = 302.0.
  2. *In-Service Cutoff 5-Fold CV:* RMSE = 19.52 ± 2.84, MAE = 16.09 ± 2.54 cycles.
  3. *Full-Trajectory 5-Fold CV:* RMSE = 13.76 ± 1.57, MAE = 9.68 ± 1.10 cycles.
  4. *Terminal Failure-Point 5-Fold CV:* RMSE = 3.35 ± 0.27 cycles.

### 2.4 Maintenance Operations Logic (`src/aircraft_pm/operations.py`)
- `classify_health_status(pred_rul, critical_thresh, warning_thresh)`
- `get_maintenance_priority(pred_rul, critical_thresh, warning_thresh)`
- `get_alert_rationale(pred_rul, cycle, critical_thresh, warning_thresh)`
- `get_recommended_action(pred_rul, critical_thresh, warning_thresh)`
- `build_maintenance_queue(fleet_summary, critical_thresh, warning_thresh, filter_status)`
- `export_queue_to_csv(queue_df)`

---

## 3. Existing Function Mapping for FastAPI Backend

| Capability | Existing Function / Source | Target FastAPI Endpoint |
|---|---|---|
| Health & Model Status | Inspect `preprocessor.joblib`, `best_model.joblib` | `GET /api/health` |
| Fleet Summary & Coverage | `load_test_data()`, preprocessor transform, `prod_model.predict` | `GET /api/fleet/summary` |
| Engine Listing | `test_df["engine_id"].unique()` | `GET /api/engines` |
| Engine Observations & History | `test_df[test_df["engine_id"] == id]` | `GET /api/engines/{engine_id}` |
| Causal RUL Inference | `preprocessor.transform(sub_seq)`, `prod_model.predict` | `POST /api/predict` |
| Sensor Catalog & Diagnostics | `SENSOR_DESCRIPTIONS`, `CONSTANT_OR_LOW_VARIANCE_COLS` | `GET /api/sensors/summary` |
| Benchmark Model Metrics | `models/model_registry.json` | `GET /api/models/metrics` |
| Maintenance Review Queue | `operations.build_maintenance_queue()` | `GET /api/maintenance/queue` |
| CSV Maintenance Export | `operations.export_queue_to_csv()` | `GET /api/maintenance/export` |

---

## 4. Nuxt UI Frontend Architecture Plan

- **Framework:** Nuxt 3 + Vue 3 + TypeScript + Tailwind CSS.
- **Template:** Official `nuxt-ui-templates/dashboard` adapted into AeroGuard.
- **Design Tokens:** Dark midnight navy theme (`#080d1a`, `#0f172a`, `#1e293b`), crisp borders (`#334155`), multi-color KPI strips, 6px semantic dots (anti-capsule invariant).
- **Routes:**
  1. `/` (Fleet Command Center)
  2. `/engines` (Engine Digital Twin)
  3. `/sensors` (Sensor Intelligence)
  4. `/models` (Model Intelligence)
  5. `/maintenance` (Maintenance Operations)
  6. `/inference` (RUL Inference Lab)
- **API Client:** Nuxt `$fetch` client configured via `runtimeConfig.public.apiBase` (`http://localhost:8000`).
