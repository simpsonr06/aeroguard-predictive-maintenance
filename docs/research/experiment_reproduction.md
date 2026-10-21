# AeroSentinel: Experiment Reproduction Guide

**Document Identifier:** `DOC-RES-005`  
**Version:** `1.0.0`  
**Classification:** Research Reproducibility & Verification Guide  

---

## 1. System Requirements & Environment Setup

### 1.1 Python Virtual Environment
* **Python Version:** Python 3.10 to 3.14 (tested under Python 3.14.3 on Windows AMD64).
* **Package Management:** Run inside a dedicated virtual environment (`.venv`).

```powershell
# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt
pip install python-docx
```

### 1.2 Mandatory Security Environment Variables
The application enforces signature verification on model loading by default when the public key is configured:

```powershell
$env:AEROSENTINEL_REQUIRE_SIGNATURE = "true"
$env:AEROSENTINEL_ED25519_PUBLIC_KEY = "2fc1416b5634cf20e6b403fafc572160b27615adbdf5352458a492d52251e45b"
$env:PYTHONPATH = "src"
```

---

## 2. Automated Test Suite Execution

Run the complete test suite covering cryptographic verification, API input security, unit tests, and attack simulations:

```powershell
pytest tests/ -v
```

Expected Output:
```
tests/test_api.py ..................                         [ 24%]
tests/test_api_security.py ...........                      [ 39%]
tests/test_artifact_authentication.py ............          [ 55%]
tests/test_attacks.py ...                                   [ 59%]
...
======================== 75 passed in ~8.5s ========================
```

---

## 3. Reproducing Experimental Benchmarks & Data Suite

### Step 1: Run Latency Microbenchmarks ($N=100$ repetitions)
Executes 100 iterations of Ed25519 verification, SHA-256 multi-file hashing, model deserialization, batch inference, and drift calculation:

```powershell
python scripts/benchmark_latency.py
```
*Outputs:*  
`reports/research/performance_benchmarks.csv`  
`reports/research/performance_benchmarks.json`

### Step 2: Run Sensor Manipulation Simulation Suite
Executes the 6 synthetic attack scenarios against all 100 test engines, recording per-engine predictions, RMSE, MAE, NASA asymmetric penalties, HPR, and drift metrics:

```powershell
python scripts/simulate_attacks.py
```
*Outputs:*  
`reports/research/attack_simulation_summary.csv`  
`reports/research/attack_simulation_summary.json`  
`reports/research/attack_simulation_report.md`

### Step 3: Export Complete Research Suite & High-Resolution Figures
Regenerates all publication tables, verifies Protocol A vs. Protocol B baseline reproduction, and renders 300 DPI publication figures:

```powershell
python scripts/export_research_suite.py
```

Generated Research Artifacts in `reports/research/`:
* `baseline_metrics.csv` — Official Protocol A and Protocol B comparison.
* `artifact_integrity_results.csv` — Matrix of 10 cryptographic tampering test vectors.
* `api_security_results.csv` — Input validation and sanitization test outcomes.
* `sensor_attack_results.csv` — Fleet metrics across all attack scenarios.
* `engine_level_results.csv` — Granular per-engine predictions and error deltas.
* `experiment_configuration.json` — Software versions, environment hashes, and seeds.
* `figures/fig1_baseline_protocols.png` — Dual-protocol comparison chart.
* `figures/fig2_attack_rul_shifts.png` — Attack RUL degradation and error distributions.
* `figures/fig3_asymmetric_nasa_surge.png` — Exponential NASA risk penalty escalation.
* `figures/fig4_drift_psi_heatmap.png` — Multi-channel drift detection evasion heatmap.
* `figures/fig5_latency_breakdown.png` — Sub-millisecond verification overhead profile.

---

## 4. Frontend Dashboard Build & Launch

### Step 1: Build & Launch FastAPI Backend
```powershell
uvicorn aircraft_pm.api:app --host 127.0.0.1 --port 8000
```

### Step 2: Launch Nuxt 3 Client
```powershell
cd frontend
bun install
bun run dev --port 3000
```
Navigate to `http://localhost:3000/models` to inspect the live Ed25519 cryptographic authentication banner and the interactive Attack Resilience Matrix.
