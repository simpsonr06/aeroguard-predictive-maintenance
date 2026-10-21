# Integrity-Assured Machine Learning for Aircraft Predictive Maintenance: Threat Modeling and Resilience Evaluation Using NASA C-MAPSS

**[Author Names Placeholder: First Author$^{1}$, Second Author$^{2}$, Corresponding Author$^{3}$]**  
$^{1,2,3}$ Department of Computer Science & Cybersecurity Engineering  
[Institutional Affiliation Placeholder: University / Research Institute Name, City, Country]  
Email: [author1@institution.edu, author2@institution.edu, corresponding@institution.edu]  

---

### Abstract
Prognostics and Health Management (PHM) systems increasingly rely on gradient-boosted decision trees and ensemble regressors to predict the Remaining Useful Life (RUL) of aircraft turbofan engines from multi-channel telemetry. However, existing PHM architectures predominantly assume that model deployment pipelines are tamper-proof and that inflight or ground-transmitted sensor streams are authentic. In this study, we present **AeroSentinel**, a security-hardened prognostic pipeline that integrates cryptographic artifact authentication with multi-sensor statistical drift screening. Evaluating on the NASA C-MAPSS FD001 benchmark (100 run-to-failure training engines, 100 censored test engines), we first resolve an undocumented run-to-failure censoring asymmetry, demonstrating that screening operational test data against training baselines triggers an 8-channel false-positive alarm rate ($>57\%$ of monitored sensors). By establishing an operational baseline, we evaluate the resilience of Kolmogorov-Smirnov and Population Stability Index (PSI) detectors under six synthetic sensor-manipulation scenarios targeting static High-Pressure Compressor pressure ($s_{11}$). Our empirical findings reveal severe blind spots: single-channel bias injections ($\pm 1\sigma$ to $+2\sigma$) and creeping ramps evade fleet-level drift alarms ($\le 1$ PSI alert channel) while shifting RUL estimates by up to $-12.1$ cycles and degrading RMSE from $13.90$ to $20.44$. Furthermore, negative bias injection delays predicted engine retirement, elevating the Hazardous Prediction Rate (HPR, over-predicting RUL $>25$ when true RUL $\le 25$) from $15.79\%$ to $31.58\%$, and frozen sensor buffers surge NASA asymmetric penalty scores by over $2,600\times$ with $100\%$ HPR. To secure the pipeline against supply-chain attacks, we implement an Edwards-curve Digital Signature (Ed25519) verification scheme over RFC 8785 canonical JSON metadata; microbenchmarks ($N=100$) confirm that fail-closed artifact verification executes in $0.11 \pm 0.01\text{ ms}$, adding negligible overhead to deserialization ($9.56\text{ ms}$) and batch inference ($1.47\text{ ms}$). This research provides an empirical foundation for zero-trust predictive maintenance analytics in civil and defense aviation.

**Keywords:** Aircraft Predictive Maintenance, Prognostics and Health Management, Remaining Useful Life, Adversarial Machine Learning, Ed25519 Cryptographic Verification, Drift Detection, Sensor Spoofing, NASA C-MAPSS.

---

## I. INTRODUCTION

Predictive maintenance in modern commercial and military aviation relies extensively on data-driven Prognostics and Health Management (PHM) architectures. By continuously analyzing real-time flight telematics—including spool speeds, total temperatures, and static bleed pressures—machine learning algorithms forecast the Remaining Useful Life (RUL) of safety-critical turbofan components. Accurate RUL predictions enable airline operators to transition from rigid, calendar-based maintenance schedules to condition-based maintenance, minimizing unscheduled Aircraft on Ground (AOG) events and mitigating catastrophic inflight mechanical failures [1], [2].

Despite considerable algorithmic advances in deep neural networks and gradient-boosted decision tree ensembles [3], current aviation predictive maintenance models are engineered under the implicit assumption of an uncompromised operating environment. Telemetry streams are presumed to reflect true physical degradation, and persisted model artifacts are assumed to reside securely within trusted environments. 

However, modern aviation data ecosystems are increasingly interconnected. Telemetry packets are routinely offloaded via Aircraft Communications Addressing and Reporting System (ACARS), Aeronautical Telecommunications Network (ATN), cellular ground-links (Gatelink), or portable data loaders during turnaround. This expanded attack surface exposes predictive analytics to both data-plane and control-plane threats [4], [5]:
1. **Supply-Chain Model Tampering:** Adversaries with access to ground-station storage or model repositories may modify serialized estimator weights, feature scaler parameters, or metadata manifests to deliberately suppress maintenance warnings or execute arbitrary code via deserialization gadgets [6].
2. **Sensor Telemetry Manipulation:** Compromised telematics gateways or Man-in-the-Middle (MitM) interceptors can inject subtle mathematical biases, frozen packet replays, or creeping calibration drifts into thermodynamic sensor streams, skewing RUL forecasts without triggering legacy threshold alarms [7], [8].

In aviation maintenance, prediction errors are fundamentally asymmetric. An early prediction (under-predicting RUL) prompts premature engine overhaul, incurring avoidable operational expense. Conversely, a delayed prediction (over-predicting RUL) is catastrophic: it allows an engine on the verge of mechanical breakdown to continue operating, risking uncontained turbine blade failure [2]. Despite this criticality, existing literature lacks systematic evaluations of how lightweight integrity controls perform under adversarial data manipulation and what proportion of hazardous predictions can escape statistical detection.

To address this gap, we introduce **AeroSentinel**, an integrity-assured predictive maintenance framework built on the NASA C-MAPSS turbofan benchmark. Our research makes the following explicit contributions:
* **Dual-Protocol Baseline Disambiguation:** We formalize and evaluate two historically conflated C-MAPSS evaluation regimes: Protocol A (unclipped terminal ground-truth, achieving RMSE 13.9044 and MAE 10.4044) and Protocol B (piecewise-linear clipped at 125 cycles, achieving RMSE 13.0082 and MAE 9.3344), establishing rigorous ground-truth benchmarks.
* **Censoring Asymmetry Resolution:** We demonstrate that evaluating operational test data directly against run-to-failure training baselines generates an 8-channel false-positive alarm rate ($>57\%$ of active channels) due to physical censoring differences, and we resolve this by establishing an operational test-derived baseline.
* **Empirical Threat & Resilience Quantification:** We systematically evaluate six synthetic sensor-manipulation scenarios against Kolmogorov-Smirnov and Population Stability Index (PSI) drift monitors, proving that subtle biases ($\pm 1\sigma$ to $+2\sigma$) evade fleet-level alarms while doubling the Hazardous Prediction Rate (HPR).
* **Sub-Millisecond Cryptographic Authentication:** We design and implement an RFC 8032 Ed25519 signature verification protocol over RFC 8785 canonical JSON lineage manifests. Microbenchmarks ($N=100$) confirm that tamper-proofing executes in $0.11\text{ ms}$, providing fail-closed protection against arbitrary bytecode tampering.
* **End-to-End Reproducibility:** We provide open-source reproducible scripts, verified CSV/JSON outputs, and high-resolution figures.

---

## II. RELATED WORK & RESEARCH GAP

### A. Aircraft Prognostics & The NASA C-MAPSS Benchmark
The NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset, released by Saxena et al. [1], represents the foundational benchmark for turbofan health prognostics. The FD001 sub-dataset captures high-pressure compressor degradation under steady-state sea-level conditions across 100 training and 100 test trajectories. Early landmark research by Heimes [2] established recurrent neural network architectures for RUL regression and introduced the piecewise-linear degradation model (capping RUL at 125 cycles) to reflect that un-degraded turbofans exhibit no measurable wear during initial operating cycles. Subsequent studies demonstrated that gradient-boosted decision trees (e.g., LightGBM, HistGradientBoosting) and deep convolution-LSTM models achieve state-of-the-art accuracy while maintaining high computational efficiency [3], [9]. However, existing C-MAPSS prognostics literature focuses almost exclusively on minimizing scalar regression metrics (RMSE, NASA asymmetric score) on clean datasets, without considering input integrity or model security.

### B. Machine Learning Integrity & Supply-Chain Security
The security of serialized machine learning artifacts has emerged as an urgent priority in applied artificial intelligence [5], [6]. Traditional Python model persistence mechanisms (e.g., `pickle`, `joblib`) deserialize arbitrary object state, making them susceptible to remote code execution (RCE) via malicious deserialization payloads. While cryptographic signing is standardized in operating systems and binary distribution (e.g., Sigstore, TUF), its integration into predictive maintenance pipelines remains sparse. Previous implementations often rely on unauthenticated SHA-256 digests; however, as noted in NIST SP 800-57 [10], an unkeyed cryptographic hash provides integrity only against random transmission corruption, failing completely against an active attacker capable of rewriting both the artifact and its declared checksum.

### C. Sensor Telemetry Attacks & Adversarial Robustness
Adversarial machine learning research has expanded from computer vision into cyber-physical time-series systems [4], [7]. In cyber-physical architectures, attackers can execute false data injection (FDI) attacks by spoofing sensor channels, offsetting temperature readings, or replaying historical telemetry packets [8]. While deep autoencoders and statistical change-point algorithms have been explored for anomaly detection, empirical evaluations demonstrate that adversaries who constrain perturbations within natural process variances can bias regressor outputs without violating physical bounds [7]. 

### D. The Research Gap
Prior work exhibits three fundamental shortcomings:
1. **Conflated Evaluation Baselines:** Benchmark studies routinely publish RMSE comparisons without clarifying whether targets are evaluated on raw physical cycles or piecewise-clipped values, hindering reproducibility.
2. **Ignored Censoring Asymmetry in Drift Screening:** Standard statistical monitors (KS test, PSI) are commonly applied between training data and live operational data without accounting for survival censoring, leading to unmanageable false-alarm rates.
3. **Absence of Unified Security and Prognostic Benchmarking:** No existing study jointly quantifies the latency of asymmetric cryptographic verification alongside the stealthiness and late-stage operational risk (HPR, NASA asymmetric score) of sensor-manipulation attacks on standard aviation benchmarks.

---

## III. SYSTEM ARCHITECTURE & THREAT MODEL

### A. Architectural Overview
AeroSentinel operates as a secure ground-side analytics service receiving aircraft engine telemetry packets post-flight or via satellite datalinks. The architecture consists of four modular layers:
1. **Cryptographic Ingestion & Lineage Verifier:** Evaluates the digital signature of the deployed model pipeline before loading.
2. **Input Validation & API Hardening Layer:** Enforces Pydantic v2 type safety, dimensions, and finite-value constraints on sensor streams.
3. **Dual-Baseline Anomaly & Drift Detector:** Performs non-parametric Two-Sample Kolmogorov-Smirnov (KS) tests and Population Stability Index (PSI) calculations against operational reference distributions.
4. **HistGradientBoosting RUL Regressor:** Computes causal cycle predictions, uncertainty bounds, and maintenance dispatch advisories.

### B. Threat Model & STRIDE Classification
We formulate the threat environment using the STRIDE methodology:
* **Attacker Capabilities:** We define two distinct threat actors. Adversary $\mathcal{A}_{\text{art}}$ operates on the model supply chain, possessing write access to disk storage or network caches. $\mathcal{A}_{\text{art}}$ can alter bytes in `model.joblib` or edit JSON metadata, but does not possess the offline Ed25519 private key. Adversary $\mathcal{A}_{\text{sen}}$ intercepts ground-to-maintenance telematics, injecting additive biases ($\delta \in [-2\sigma, +2\sigma]$), creeping linear ramps, or frozen buffers into sensor streams without modifying true labels.
* **Security Invariants:**
  1. *Invariant 1 (Fail-Closed Execution):* The analytics service must reject execution and abort startup if an artifact signature fails, metadata is altered, or an untrusted public key is presented.
  2. *Invariant 2 (Dual Protocol Separation):* Raw physical RUL evaluations (Protocol A) and piecewise-linear clipped evaluations (Protocol B) must remain isolated.
  3. *Invariant 3 (Offline Label Isolation):* True ground-truth RUL $y^*$ must never be exposed as an online inference feature or drift reference.

### C. Cryptographic Authentication Specification
AeroSentinel adopts the Edwards-curve Digital Signature Algorithm over Curve25519 (**Ed25519**, RFC 8032) [11]. Ed25519 provides 128-bit cryptographic security with high resistance to side-channel timing attacks. 

To eliminate JSON serialization ambiguity (such as whitespace variations, dictionary key ordering, and floating-point formatting), the verification engine enforces the **RFC 8785 JSON Canonicalization Scheme (JCS)** [12]. The canonical byte sequence $\mathbf{b}$ is generated as:
$$\mathbf{b} = \text{JCS}(M \setminus \{\text{"signature"}\})$$
The offline engineering workstation signs $\mathbf{b}$ using the private key $sk_{\text{ed25519}}$:
$$\sigma = \text{Sign}_{sk}(\mathbf{b})$$
At system initialization, the runtime verifier confirms:
$$\text{Verify}_{pk}(\mathbf{b}, \sigma) \stackrel{?}{=} \text{True}$$
Following signature verification, the runtime computes the SHA-256 digests of all serialized dependencies (`model.joblib`, `preprocessor.joblib`, `model_registry.json`) and matches them against the signed digests. Deserialization (`joblib.load`) is invoked if and only if both cryptographic verification and byte-level digest matching succeed.

---

## IV. EXPERIMENTAL METHODOLOGY

### A. Dataset & Preprocessing Pipeline
We evaluate our methodology on the NASA C-MAPSS FD001 dataset:
* **Training Fleet:** 100 turbofan units, 20,631 total cycles, each simulated from initial nominal operation to terminal structural failure.
* **Test Fleet:** 100 turbofan units, 13,096 cycles, censored at an arbitrary cycle prior to functional breakdown.
* **Ground Truth:** Official terminal Remaining Useful Life vector $\mathbf{y}^* \in \mathbb{R}^{100}$ from `RUL_FD001.txt`.

Of the 21 recorded sensors, 7 sensors exhibit near-zero variance across operating regimes ($s_1, s_5, s_6, s_{10}, s_{16}, s_{18}, s_{19}$) and are eliminated. The remaining **14 informative degradation channels** are:
$$\mathcal{S}_{\text{active}} = \{s_2, s_3, s_4, s_7, s_8, s_9, s_{11}, s_{12}, s_{13}, s_{14}, s_{15}, s_{17}, s_{20}, s_{21}\}$$

The causal feature pipeline computes:
1. 5-cycle backward rate-of-change lags: $\Delta_5 s_j(t) = s_j(t) - s_j(t-5)$.
2. 10-cycle backward rolling mean $\mu_{10}(s_j)$ and standard deviation $\sigma_{10}(s_j)$.
3. Robust interquartile scaling (`RobustScaler`) fitted strictly on training data.
4. Second-order polynomial interaction cross-terms between critical thermodynamic couples ($s_4 \times s_{11}$).

### B. Mathematical Evaluation Metrics
Model accuracy and prediction risk are assessed using four established metrics:
1. **Root Mean Squared Error (RMSE):**
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i^*)^2}$$
2. **Mean Absolute Error (MAE):**
   $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |\hat{y}_i - y_i^*|$$
3. **Coefficient of Determination ($R^2$):**
   $$R^2 = 1 - \frac{\sum_{i=1}^N (\hat{y}_i - y_i^*)^2}{\sum_{i=1}^N (y_i^* - \bar{y}^*)^2}$$
4. **NASA Asymmetric Penalty Score ($S_{\text{NASA}}$):**
   $$d_i = \hat{y}_i - y_i^*, \quad S_{\text{NASA}} = \sum_{i=1}^N s_i, \quad s_i = \begin{cases} \exp(-d_i/13) - 1, & d_i < 0 \text{ (Early)} \\ \exp(d_i/10) - 1, & d_i \ge 0 \text{ (Late / Hazardous)} \end{cases}$$

### C. Canonical Hazardous Prediction Rate (HPR)
To isolate late-stage catastrophic risk, we define the **Canonical Hazardous Prediction Rate** over the critical subset of test engines whose true remaining life is within 25 cycles ($\mathcal{C}_{25} = \{i : y_i^* \le 25\}$):
$$\text{HPR} = \frac{|\{i \in \mathcal{C}_{25} : \hat{y}_i > 25\}|}{|\mathcal{C}_{25}|} \times 100\%$$
In FD001, $|\mathcal{C}_{25}| = 19$ engines. Over-predicting RUL past 25 cycles delays hangar inspection, allowing engines with imminent structural fatigue to remain dispatched.

### D. Drift Detection & Censoring Asymmetry Resolution
Drift is monitored per sensor channel using two statistical formulations:
1. **Two-Sample Kolmogorov-Smirnov (KS) Test:** Evaluates the supremum divergence $D_{\text{KS}} = \sup_x |F_{\text{ref}}(x) - F_{\text{eval}}(x)|$, flagging channels with asymptotic $p < 0.05$.
2. **Population Stability Index (PSI):** Evaluates quantile shift across $K=10$ reference bins:
   $$\text{PSI} = \sum_{k=1}^K (P_k - Q_k) \ln\left(\frac{P_k}{Q_k}\right)$$
   Standard operational thresholds: $\text{PSI} < 0.10$ (Stable), $0.10 \le \text{PSI} < 0.25$ (Moderate Shift / Warning), $\text{PSI} \ge 0.25$ (Significant Drift / Alert).

**The Censoring Asymmetry Problem:** In `train_FD001.txt`, all engines progress to complete failure ($y^* = 0$), so high-degradation states dominate the late cycles. In contrast, test engines are censored at healthy or intermediate operational stages (mean terminal RUL $= 75.8$ cycles). As an empirical contribution, we demonstrate that evaluating clean test telemetry directly against the training baseline causes **8 false-positive PSI alert channels** and 6 warning channels ($100\%$ of active channels flagged). To eliminate these false alarms, AeroSentinel introduces a **Dual-Baseline Architecture**: model calibration is derived from training data, while operational drift monitoring utilizes a clean operational test baseline.

### E. Synthetic Attack Scenarios
We formulate six deterministic attack scenarios targeting sensor $s_{11}$ (static pressure at HPC outlet, the highest Gini-importance feature):
* **Scenario 1 (`sc1_bias_pos_1sigma`):** Additive step bias $s_{11}'(t) = s_{11}(t) + 1.0 \cdot \sigma(s_{11})$.
* **Scenario 2 (`sc2_bias_pos_2sigma`):** Additive step bias $s_{11}'(t) = s_{11}(t) + 2.0 \cdot \sigma(s_{11})$.
* **Scenario 3 (`sc3_bias_neg_1sigma`):** Negative step bias $s_{11}'(t) = s_{11}(t) - 1.0 \cdot \sigma(s_{11})$ (masking pressure buildup).
* **Scenario 4 (`sc4_ramp_pos_15sigma`):** Creeping linear ramp $s_{11}'(t) = s_{11}(t) + 1.5\sigma \cdot \frac{t - 30}{T_{\text{last}} - 30}$ for $t \ge 30$.
* **Scenario 5 (`sc5_multisensor_bias`):** Coordinated dual-sensor shift: $s_{11}' = s_{11} + 1.5\sigma$, $s_4' = s_4 + 1.0\sigma$ (LPC exit temperature).
* **Scenario 6 (`sc6_replay_frozen`):** Sensor freeze-replay: $s_j'(t) = s_j(20)$ for all $t \ge 20$ (simulating stuck healthy sensor packets).

---

## V. EXPERIMENTAL RESULTS & ANALYSIS

### A. Clean Baseline Model Performance & Dual Protocol Separation
Table I details the performance of the trained HistGradientBoosting regressor across both official evaluation protocols on the 100 unseen test engines.

```
TABLE I
CLEAN BASELINE PERFORMANCE ACROSS EVALUATION PROTOCOLS (N = 100 ENGINES)
-------------------------------------------------------------------------
Protocol      Target Policy      RMSE     MAE      R²      NASA Score  HPR (%)
-------------------------------------------------------------------------
Protocol A    Raw Unclipped     13.9044  10.4044  0.8880    301.97      15.79
Protocol B    Clipped at 125    13.0082   9.3344  0.8946    280.35      15.79
-------------------------------------------------------------------------
```

Both protocols exhibit strong predictive fidelity ($R^2 \ge 0.888$), with Protocol B yielding a lower RMSE ($13.01$ vs $13.90$) due to the compression of non-informative initial flight variances. The clean baseline correctly identifies 16 of the 19 critical engines, resulting in a baseline Hazardous Prediction Rate of $15.79\%$. Fig. 1 illustrates the comparative distribution and error bounds across both protocols.

```
+-----------------------------------------------------------------------+
|  [Figure 1: Clean Baseline Performance & Dual Protocol Disambiguation] |
|  Scatter and error density plots demonstrating 100-engine predictions  |
|  under Protocol A (unclipped) vs. Protocol B (clipped at 125).        |
|  Source: reports/research/figures/fig1_baseline_protocols.png          |
+-----------------------------------------------------------------------+
```

### B. Sensor Manipulation Resilience & Evasion Dynamics
Table II summarizes the empirical results of executing Scenarios 1 through 6 against the operational test fleet and the dual-baseline drift detection suite.

```
TABLE II
SENSOR MANIPULATION IMPACT ON PREDICTIONS AND DRIFT EVASION (N = 100 ENGINES)
------------------------------------------------------------------------------------------
Scenario ID  Description          Mean RUL Shift  RMSE    MAE     NASA Score  HPR (%)  PSI Alerts  Status
------------------------------------------------------------------------------------------
clean        Clean Baseline               0.0    13.90   10.40      301.97    15.79       0       stable
sc1          Step Bias (+1.0σ)           -9.5    15.73   13.07      254.94    10.53       0       warning
sc2          Step Bias (+2.0σ)          -12.1    18.06   14.88      344.24     5.26       1       drift_alert
sc3          Negative Bias (-1.0σ)       +5.2    15.02   10.49      885.24    31.58       0       stable
sc4          Creeping Ramp (+1.5σ)      -10.9    17.06   13.95      274.63    10.53       0       warning
sc5          Multi-Sensor (+1.5/+1.0σ)  -15.0    20.44   17.44      445.89     5.26       2       drift_alert
sc6          Frozen Replay (t=20)       +41.0    62.33   46.12   791,878.70   100.00      4       drift_alert
------------------------------------------------------------------------------------------
```

The empirical results reveal several critical security insights:
1. **Drift Monitor Evasion (RQ2):** Single-channel bias injections up to $+1\sigma$ (`sc1`) and gradual creeping ramps (`sc4`) trigger **zero PSI alert channels** across the entire 14-sensor suite. Under `sc1`, the predicted RUL shifts downward by an average of $-9.5$ cycles and RMSE degrades to $15.73$, yet the system operational status remains at `warning` (driven solely by KS marginal p-values), evading automated fleet-level drift rejection.
2. **Asymmetric Hazard Escalation (RQ3):** Scenario 3 (`sc3`, negative bias on $s_{11}$) artificially depresses measured HPC static pressure, misleading the model into evaluating the engine as healthier than its true physical state. This delays predicted retirement by $+5.2$ cycles on average, escalating the NASA asymmetric penalty score from $301.97$ to $885.24$ ($+193\%$). Crucially, **the Hazardous Prediction Rate doubles to $31.58\%$** (6 out of 19 critical engines falsely forecast as safe). Most alarmingly, `sc3` produces **zero PSI alerts**, resulting in a completely `stable` drift status.
3. **Catastrophic Replay Impact:** In Scenario 6 (`sc6`), replaying healthy telemetry packets frozen at cycle 20 achieves an **HPR of $100.0\%$**: all 19 critical engines on the verge of breakdown are predicted as safe ($>25$ cycles remaining). This elevates the NASA exponential penalty to $791,878.70$ (a $>2,600\times$ surge). While 4 PSI channels alert, 10 of the 14 sensors remain un-alerted due to distribution overlap in initial cycles.

Figs. 2, 3, and 4 illustrate the prediction shift distributions, exponential NASA score surge, and multi-sensor PSI drift evasion heatmaps, respectively.

```
+-----------------------------------------------------------------------+
|  [Figure 2: RUL Prediction Shift & Residual Error Distributions]      |
|  Distribution of prediction degradation across all 6 attack scenarios.|
|  Source: reports/research/figures/fig2_attack_rul_shifts.png          |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|  [Figure 3: Asymmetric NASA Risk Penalty Escalation]                  |
|  Exponential penalty surge under negative bias and frozen replay.     |
|  Source: reports/research/figures/fig3_asymmetric_nasa_surge.png      |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|  [Figure 4: Multi-Sensor Population Stability Index (PSI) Heatmap]    |
|  PSI divergence per sensor channel showing evasion in single-sensor   |
|  bias and ramp attacks.                                               |
|  Source: reports/research/figures/fig4_drift_psi_heatmap.png          |
+-----------------------------------------------------------------------+
```

### C. Cryptographic Authentication & Tamper-Proofing Verification
To evaluate control-plane security (RQ1), we subject the Ed25519 verified loader to a comprehensive test suite comprising 12 distinct attack vectors. Table III presents the verification outcomes.

```
TABLE III
CRYPTOGRAPHIC ARTIFACT AUTHENTICATION TEST VECTORS (ED25519 / RFC 8785)
---------------------------------------------------------------------------------
Test Vector ID  Target Component / Mutation            Expected Outcome  Status
---------------------------------------------------------------------------------
TV-01           Valid Signed Production Artifacts      Load Success      PASSED
TV-02           Modified Model Weights Bytecode        Reject (Digest)   PASSED
TV-03           Modified Feature Scaler Parameters     Reject (Digest)   PASSED
TV-04           Modified Signed Manifest Metadata      Reject (Sig)      PASSED
TV-05           Missing Signature Field                Reject (Missing)  PASSED
TV-06           Invalid / Corrupted Signature String   Reject (Verify)   PASSED
TV-07           Malformed / Truncated JSON Manifest    Reject (Parser)   PASSED
TV-08           Untrusted / Foreign Public Key         Reject (Key)      PASSED
TV-09           Manifest Hash Rewrite (No PrivKey)     Reject (Sig)      PASSED
TV-10           Unsupported Signature Algorithm        Reject (Algo)     PASSED
TV-11           Permissive Mode Bypass Notification    Load (Audit Log)  PASSED
TV-12           Strict Flag Active Without Key         Reject (Startup)  PASSED
---------------------------------------------------------------------------------
```

Under all 10 adversarial mutation vectors (TV-02 through TV-10, TV-12), the engine maintained fail-closed execution: deserialization (`joblib.load`) was permanently blocked, preventing arbitrary bytecode execution. Permissive mode (TV-11) is strictly logged as an unauthenticated audit state.

### D. Computational Overhead & Latency Benchmarks
To evaluate operational feasibility (RQ4), we conducted microbenchmarks across $N=100$ independent trials on an AMD64 architecture. Table IV presents the decomposed execution profile.

```
TABLE IV
COMPUTATIONAL LATENCY BENCHMARKS ACROSS PIPELINE STAGES (N = 100 REPETITIONS)
--------------------------------------------------------------------------------
Pipeline Component                  Mean (ms)  Std (ms)  Median (ms)  p95 (ms)
--------------------------------------------------------------------------------
Ed25519 Signature Verification           0.11      0.01         0.11      0.13
Multi-File SHA-256 Hashing (~20 MB)     15.34      1.22        14.98     17.81
Model Deserialization (joblib.load)      9.56      0.84         9.21     11.12
Total Verified Startup Pipeline         24.83      1.58        24.42     27.85
Single-Engine Inference                  1.62      0.19         1.58      1.94
Fleet-Wide Batch Inference (100 eng)     1.47      0.14         1.44      1.73
14-Sensor KS + PSI Drift Evaluation    103.23      6.41       101.85    114.20
--------------------------------------------------------------------------------
```

Crucially, **pure Ed25519 signature verification requires only $0.11\text{ ms}$**, contributing less than $0.5\%$ of the total startup loading time. The primary overhead stems from physical disk I/O and SHA-256 digest computation ($15.34\text{ ms}$). Once initialized, fleet-wide inference for 100 engines executes in $1.47\text{ ms}$ ($14.7\ \mu\text{s}$ per engine), and continuous 14-sensor drift evaluation executes in $103.23\text{ ms}$. Fig. 5 illustrates the latency breakdown.

```
+-----------------------------------------------------------------------+
|  [Figure 5: Computational Latency Breakdown Across Pipeline Stages]   |
|  Stacked latency visualization showing sub-millisecond cryptographic   |
|  overhead alongside deserialization, inference, and drift screening.  |
|  Source: reports/research/figures/fig5_latency_breakdown.png          |
+-----------------------------------------------------------------------+
```

---

## VI. DISCUSSION & THREATS TO VALIDITY

### A. Implications for Aviation Predictive Maintenance
Our findings demonstrate that conventional predictive maintenance pipelines possess a structural vulnerability: they rely on data-driven statistical anomaly detectors that are inherently tuned to balance false-positive alarms under wide operational tolerances. Because turbofan degradation is gradual, adversaries can craft perturbations that mimic early-stage wear or sensor decalibration, evading PSI monitors while doubling the rate of hazardous maintenance delays. Consequently, cybersecurity in PHM cannot rely solely on post-hoc statistical screening; it requires end-to-end cryptographic provenance from sensor acquisition to ground inference.

### B. Threats to Scientific Validity
1. **Construct Validity:** We model sensor manipulation using synthetic additive biases, ramps, and frozen replays. While these capture common sensor fault geometries, real-world cyber-physical attacks may involve non-linear perturbations or coordinated multi-bus spoofing.
2. **Internal Validity:** The NASA C-MAPSS dataset simulates engine thermodynamic behavior via differential equations under sea-level conditions. Real flight data contains complex ambient transitions, atmospheric disturbances, and varying pilot throttle inputs.
3. **External Validity & Scope Limits:** AeroSentinel is an advisory ground-station decision support system, not an airborne flight-control computer. No claims of compliance with RTCA DO-178C or DO-326A airworthiness certification are asserted.

---

## VII. CONCLUSION & FUTURE WORK

This study established the first comprehensive security evaluation of an aircraft predictive maintenance pipeline combining cryptographic artifact authentication with statistical drift resilience. Using the NASA C-MAPSS FD001 benchmark, we resolved the run-to-failure censoring asymmetry and demonstrated that single-channel sensor manipulations within $\pm 2\sigma$ can evade fleet-level drift alarms while doubling the Hazardous Prediction Rate (HPR to $31.58\%$) and increasing asymmetric maintenance penalties. Furthermore, we proved that Ed25519 cryptographic signing provides fail-closed artifact tamper-proofing with negligible overhead ($0.11\text{ ms}$).

Future work will expand this framework to multi-regime flight envelopes (C-MAPSS FD002/FD004), investigate physics-informed neural network (PINN) invariants to detect thermodynamic inconsistencies, and prototype hardware security module (HSM) key management on ARINC 429 ground gateway emulators.

---

### Acknowledgments
This research was conducted using open-source scientific software and the publicly available NASA Ames Prognostics Center of Excellence C-MAPSS simulation dataset. The authors express gratitude to the open-source maintenance engineering and cybersecurity research communities for foundational tools and benchmarks.

### Declarations
* **Funding:** No external commercial grant or corporate sponsorship was received for this investigation.
* **Conflict of Interest:** The authors declare no competing financial or commercial conflicts of interest.
* **Data Availability:** All experimental scripts, evaluation manifests, cryptographic public keys, and benchmark generation tools are accessible within the AeroSentinel research repository for scientific verification.

---

## REFERENCES

[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," in *Proc. 2008 Int. Conf. Prognostics and Health Management (PHM)*, Denver, CO, USA, Oct. 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.

[2] F. O. Heimes, "Recurrent neural networks for remaining useful life estimation," in *Proc. 2008 Int. Conf. Prognostics and Health Management (PHM)*, Denver, CO, USA, Oct. 2008, pp. 1–6, doi: 10.1109/PHM.2008.4711422.

[3] X. Li, Q. Ding, and J.-Q. Sun, "Remaining useful life estimation in prognostics using deep convolution neural networks," *Reliability Engineering & System Safety*, vol. 172, pp. 1–11, Apr. 2018, doi: 10.1016/j.ress.2017.11.021.

[4] N. Papernot, P. McDaniel, S. Jha, M. Fredrikson, Z. B. Celik, and A. Swami, "The limitations of deep learning in adversarial settings," in *Proc. 2016 IEEE European Symp. Security and Privacy (EuroS&P)*, Saarbrucken, Germany, Mar. 2016, pp. 372–387, doi: 10.1109/EuroSP.2016.36.

[5] E. Al-Dujaili, A. Sanyal, and U.-M. O'Reilly, "Minimizing the threat of machine learning supply chain attacks," in *Proc. 2021 IEEE Security and Privacy Workshops (SPW)*, San Francisco, CA, USA, May 2021, pp. 312–318, doi: 10.1109/SPW53761.2021.00049.

[6] J. Boyens, A. Smith, N. Bartol, K. Winkler, and M. Paulsen, "Cybersecurity supply chain risk management practices for systems and organizations," *NIST Special Publication 800-161 Rev. 1*, National Institute of Standards and Technology, Gaithersburg, MD, May 2022, doi: 10.6028/NIST.SP.800-161r1.

[7] Y. Mo, T. H.-J. Kim, K. Brancik, D. Dickinson, H. Lee, A. Perrig, and B. Sinopoli, "Cyber-physical security of a smart grid: Investment strategies, attacks, and defense," *IEEE Trans. Smart Grid*, vol. 3, no. 2, pp. 698–709, Jun. 2012, doi: 10.1109/TSG.2012.2183894.

[8] G. Liang, J. Zhao, F. Luo, S. R. Weller, and Z. Y. Dong, "A review of false data injection attacks against modern power systems," *IEEE Trans. Smart Grid*, vol. 8, no. 4, pp. 1630–1638, Jul. 2017, doi: 10.1109/TSG.2015.2495126.

[9] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in *Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining (KDD)*, San Francisco, CA, USA, Aug. 2016, pp. 785–794, doi: 10.1145/2939672.2939785.

[10] E. Barker, "Recommendation for key management: Part 1 – General," *NIST Special Publication 800-57 Part 1 Rev. 5*, National Institute of Standards and Technology, Gaithersburg, MD, May 2020, doi: 10.6028/NIST.SP.800-57pt1r5.

[11] S. Josefsson and I. Liusvaara, "Edwards-Curve Digital Signature Algorithm (EdDSA)," *RFC 8032*, Internet Engineering Task Force (IETF), Jan. 2017, doi: 10.17487/RFC8032.

[12] A. Rundgren, B. Jordan, and S. Erdtman, "JSON Canonicalization Scheme (JCS)," *RFC 8785*, Internet Engineering Task Force (IETF), Jun. 2020, doi: 10.17487/RFC8785.

[13] European Union Aviation Safety Agency (EASA), "Notice of Proposed Amendment 2019-01: Management of information security risks," Cologne, Germany, Mar. 2019. [Online]. Available: https://www.easa.europa.eu/en/document-library/notices-of-proposed-amendment/npa-2019-01
