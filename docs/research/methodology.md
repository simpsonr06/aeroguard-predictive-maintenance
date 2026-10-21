# AeroSentinel: Experimental Methodology & Scientific Protocols

**Document Identifier:** `DOC-RES-002`  
**Version:** `1.0.0`  
**Classification:** Research Methodology & Experimental Rigor  
**Associated Artifacts:** `scripts/export_research_suite.py`, `src/aircraft_pm/attacks.py`, `src/aircraft_pm/lineage.py`  

---

## 1. Dataset Provenance & Preprocessing Pipeline

### 1.1 Dataset Characteristics (NASA C-MAPSS FD001)
The Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) turbofan engine degradation dataset (FD001 sub-dataset) is the established benchmark for prognostics research:
* **Operating Conditions:** Sea-level, single operating regime ($1.00$ Mach, $0\text{ ft}$ altitude).
* **Fault Mode:** High-Pressure Compressor (HPC) degradation driven by synthetic thermal and mechanical wear.
* **Training Trajectories (`train_FD001.txt`):** 100 engines ($N_{\text{train}}=100$) simulated from initial nominal conditions to structural failure (total observations: 20,631 cycles; engine lifespan: $128$ to $362$ cycles).
* **Test Trajectories (`test_FD001.txt`):** 100 engines ($N_{\text{test}}=100$) censored at an arbitrary cycle prior to functional breakdown (total observations: 13,096 cycles; terminal operational cycles: $31$ to $303$).
* **True Ground-Truth RUL (`RUL_FD001.txt`):** Exact remaining operational cycles from the terminal censored cycle $T_{\text{last}}$ to structural breakdown for all 100 test engines.

### 1.2 Feature Engineering & Selection
Of the 21 recorded sensor channels and 3 operational settings, 7 sensors exhibit near-zero variance across operating regimes ($s_1, s_5, s_6, s_10, s_16, s_18, s_19$) and are discarded. The pipeline extracts **14 active degradation channels**:
$$\mathcal{S}_{\text{active}} = \{s_2, s_3, s_4, s_7, s_8, s_9, s_{11}, s_{12}, s_{13}, s_{14}, s_{15}, s_{17}, s_{20}, s_{21}\}$$

The feature transformation pipeline constructs temporal features per engine trajectory:
1. **Lag Operators:** 5-cycle backward lag $\Delta_5 s_j(t) = s_j(t) - s_j(t-5)$.
2. **Rolling Statistics:** 10-cycle window rolling mean $\mu_{10}(s_j)$ and standard deviation $\sigma_{10}(s_j)$.
3. **Robust Normalization:** Outlier-resistant median centering and interquartile scaling (`RobustScaler`).
4. **Interaction Terms:** Polynomial cross-features between high-correlation thermodynamic pairs (e.g., $s_4$ LPC exit temperature $\times$ $s_{11}$ HPC static pressure).

---

## 2. Dual Evaluation Protocols

In PHM literature, reported metrics frequently conflate raw regression performance against piecewise-linear clipped ground truth. AeroSentinel strictly separates and tracks two independent evaluation protocols:

### 2.1 Protocol A: Raw, Unclipped Ground-Truth
Evaluates prediction fidelity against the true physical terminal cycle count $y_i^* \in [7, 145]$:
$$y_{i, A}^* = y_i^*$$
* **Primary Utility:** Measures unbounded physical degradation modeling and captures extreme tail-error penalties.
* **Baseline Fidelity:** RMSE $= 13.9044$, MAE $= 10.4044$, $R^2 = 0.8880$, NASA Penalty $= 301.97$.

### 2.2 Protocol B: Piecewise-Linear Clipped Ground-Truth ($RUL_{\max} = 125$)
Truncates ground truth at a ceiling of 125 cycles during initial flight phases where degradation is negligible:
$$y_{i, B}^* = \min(125, y_i^*)$$
* **Primary Utility:** Aligns with standard literature benchmarks (Heimes 2008, Saxena et al. 2008) reflecting industrial practice where maintenance scheduling is irrelevant beyond $125$ cycles.
* **Baseline Fidelity:** RMSE $= 13.0082$, MAE $= 9.3344$, $R^2 = 0.8946$, NASA Penalty $= 280.35$.

---

## 3. Mathematical Evaluation Metrics

### 3.1 Standard Error Metrics
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i^*)^2}, \quad \text{MAE} = \frac{1}{N} \sum_{i=1}^N |\hat{y}_i - y_i^*|, \quad R^2 = 1 - \frac{\sum_{i=1}^N (\hat{y}_i - y_i^*)^2}{\sum_{i=1}^N (y_i^* - \bar{y}^*)^2}$$

### 3.2 NASA Asymmetric Scoring Function
Defined by Saxena et al. (2008), the NASA scoring function penalizes late predictions (overestimating remaining life, risking unpredicted catastrophic inflight failure) exponentially more heavily than early predictions (underestimating remaining life, prompting premature inspection):
$$d_i = \hat{y}_i - y_i^*$$
$$S_{\text{NASA}} = \sum_{i=1}^N s_i, \quad \text{where } s_i = \begin{cases} \exp\left(-\frac{d_i}{13}\right) - 1, & \text{if } d_i < 0 \text{ (Early Prediction)} \\ \exp\left(\frac{d_i}{10}\right) - 1, & \text{if } d_i \ge 0 \text{ (Late / Hazardous Prediction)} \end{cases}$$

### 3.3 Canonical Hazardous Prediction Rate (HPR)
To evaluate the operational risk introduced by stealthy telemetry manipulation, we define the Canonical Hazardous Prediction Rate over the critical late-stage fleet subset $\mathcal{C}_{25} = \{i : y_i^* \le 25\}$:
$$\text{HPR} = \frac{|\{i \in \mathcal{C}_{25} : \hat{y}_i > 25\}|}{|\mathcal{C}_{25}|} \times 100\%$$
* In FD001, $|\mathcal{C}_{25}| = 19$ test engines.
* Under clean baseline conditions, $|\{i : y_i^* \le 25 \land \hat{y}_i > 25\}| = 3$, yielding $\text{HPR}_{\text{clean}} = 15.79\%$.
* An attack that elevates $\text{HPR} \gg 15.79\%$ delays mandatory hangar inspections for engines on the verge of breakdown.

---

## 4. Drift Detection & Censoring Asymmetry

### 4.1 Statistical Drift Detectors
AeroSentinel implements two continuous statistical monitors across all 14 active sensor channels:
1. **Two-Sample Kolmogorov-Smirnov (KS) Test:** Non-parametric test comparing empirical cumulative distribution functions $F_{\text{ref}}(s)$ and $F_{\text{eval}}(s)$:
   $$D_{\text{KS}} = \sup_x |F_{\text{ref}}(x) - F_{\text{eval}}(x)|$$
   A channel flags a drift warning if the asymptotic p-value satisfies $p < 0.05$.
2. **Population Stability Index (PSI):** Quantifies distributional divergence across $K=10$ quantile bins:
   $$\text{PSI} = \sum_{k=1}^K (P_k - Q_k) \ln\left(\frac{P_k}{Q_k}\right)$$
   Standard regulatory thresholds: $\text{PSI} < 0.10$ (Stable), $0.10 \le \text{PSI} < 0.25$ (Moderate Shift), $\text{PSI} \ge 0.25$ (Significant Drift Alert).

### 4.2 The Run-to-Failure Censoring Asymmetry
A critical scientific finding documented in this methodology is the **censoring asymmetry problem**:
* In `train_FD001.txt`, 100% of engine records terminate at complete failure ($RUL=0$). Thus, high-degradation operational states are heavily represented.
* In `test_FD001.txt`, engines are censored at arbitrary stages (mean terminal RUL $= 75.8$ cycles).
* **Consequence:** Comparing clean operational test telemetry directly to the training baseline results in **8 false-positive PSI alert channels** and 6 warning channels under pristine, unattacked conditions!
* **Resolution:** AeroSentinel establishes a **Dual-Baseline Architecture**:
  - *Baseline A (Training Reference):* Used for model training and offline calibration.
  - *Baseline B (Operational Test Reference):* Used for online telemetry anomaly screening to evaluate sensor manipulation without censoring-induced false alarms.

---

## 5. Synthetic Sensor Manipulation Scenarios

Telemetry attacks target sensor $s_{11}$ (static pressure at HPC outlet, the primary thermodynamic degradation indicator with highest feature importance):

| ID | Scenario | Mathematical Formulation | Physical Interpretation |
|---|---|---|---|
| `clean` | Clean Baseline | $s_j(t) = s_j^{\text{raw}}(t)$ | Pristine telemetry stream |
| `sc1` | Positive Bias ($+1\sigma$) | $s_{11}'(t) = s_{11}(t) + 1.0 \cdot \sigma(s_{11})$ | Pressure sensor offset upward |
| `sc2` | Positive Bias ($+2\sigma$) | $s_{11}'(t) = s_{11}(t) + 2.0 \cdot \sigma(s_{11})$ | Moderate positive offset |
| `sc3` | Negative Bias ($-1\sigma$) | $s_{11}'(t) = s_{11}(t) - 1.0 \cdot \sigma(s_{11})$ | Artificial masking of high pressure |
| `sc4` | Creeping Linear Ramp | $s_{11}'(t) = s_{11}(t) + 1.5\sigma \cdot \frac{t - T_{\text{start}}}{T_{\text{last}} - T_{\text{start}}}$ | Slow calibration drift starting at $t=30$ |
| `sc5` | Dual-Sensor Perturbation | $s_{11}' = s_{11} + 1.5\sigma$, $s_4' = s_4 + 1.0\sigma$ | Coordinated pressure & temperature shift |
| `sc6` | Frozen Buffer Replay | $s_j'(t) = s_j(t_{\text{freeze}})$ for $t \ge t_{\text{freeze}} = 20$ | Stale telemetry packet replay |
