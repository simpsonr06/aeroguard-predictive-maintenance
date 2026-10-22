# Integrity-Assured Machine Learning for Aircraft Predictive Maintenance: Threat Modeling and Resilience Evaluation Using NASA C-MAPSS

**Simpson R\*$^{1}$, Sarveshwaran P$^{2}$, Sarathi Kannan K$^{3}$, Varun S$^{4}$**  
$^{1,2,3,4}$ Department of Cyber Security, Dhanalakshmi Srinivasan University, Tiruchirappalli, Tamil Nadu, India.  
Emails: simpsonranga06@gmail.com, sarveshwaran706@gmail.com, sarathikannan200@gmail.com, varunsakthivel46@gmail.com  
\* *Corresponding author: Simpson R, simpsonranga06@gmail.com*

---

### Abstract
Prognostics and Health Management (PHM) architectures increasingly deploy data-driven algorithms—predominantly gradient-boosted decision trees—to estimate the Remaining Useful Life (RUL) of aircraft turbofan engines from continuous flight telemetry. However, standard predictive maintenance implementations implicitly assume that model artifacts remain uncompromised throughout deployment and that incoming sensor streams represent genuine physical degradation. In this paper, we present **AeroSentinel**, a threat-modeled research framework that integrates Edwards-curve Digital Signature (Ed25519) model authentication with multi-sensor statistical drift monitoring for ground-side turbofan prognostics. Evaluating on the standard NASA C-MAPSS FD001 benchmark (100 run-to-failure training trajectories, 100 censored operational test trajectories), we first discover and characterize a survival censoring distribution shift: screening clean operational test telemetry directly against run-to-failure training distributions triggers 8 sensor-level alert channels and 6 warning channels (14 out of 15 active degradation sensors flagged) resulting from run-to-failure censoring truncation rather than physical faults or adversarial tampering. By establishing an operational reference baseline on a disjoint 50/50 engine partition (Engines 1–50 as calibration fleet, Engines 51–100 as evaluation fleet, exhibiting 0 alerts and 0 warnings under clean conditions), we evaluate the detection sensitivity of Two-Sample Kolmogorov-Smirnov (KS) and Population Stability Index (PSI) monitors under six synthetic sensor-manipulation scenarios targeting static High-Pressure Compressor outlet pressure ($s_{11}$). Our empirical findings reveal notable detection blind spots: single-channel positive step biases ($+1.0\sigma$ to $+2.0\sigma$) and creeping ramps trigger exactly one sensor-level PSI alert channel, leaving the overall fleet-level status at `warning` (below automated fleet rejection thresholds) while distorting RUL estimates by up to $-12.07$ cycles and degrading unclipped Root Mean Squared Error (RMSE) from $13.9044$ to $20.4374$. Crucially, negative bias injection ($-1.0\sigma$ on $s_{11}$) artificially masks physical wear, delaying predicted maintenance overhaul by $+5.16$ cycles on average, escalating the asymmetric NASA penalty score to $433.13$, and doubling the Canonical Hazardous Prediction Rate (HPR, over-predicting RUL $>25$ cycles when true RUL $\le 25$) from $15.79\%$ ($3/19$ critical engines) to $31.58\%$ ($6/19$ critical engines) while completely evading fleet drift alarms ($0$ alert channels, $1$ warning channel; overall fleet status `stable`). Frozen telemetry replay forces an HPR of $100.00\%$ ($19/19$ engines delayed) and surges the exponential NASA penalty to $791,878.67$. To secure the model supply chain against deserialization gadget exploits and artifact tampering, we implement Ed25519 signing over RFC 8785 canonical JSON metadata; microbenchmarks ($N=100$) confirm that fail-closed cryptographic verification executes in $0.13 \pm 0.02\text{ ms}$ (median $0.11\text{ ms}$), with SHA-256 digest validation across the authenticated dependency set (21.01 MB across 5 binary and metadata artifacts) requiring $14.93\text{ ms}$, contributing negligible overhead to total startup ($24.37\text{ ms}$) and batch inference ($1.34\text{ ms}$ for 100 engines, $13.4\ \mu\text{s}$ per engine). These findings highlight the necessity of combining cryptographic integrity controls with domain-informed multivariate consistency monitoring for aviation predictive analytics.

**Keywords:** Aircraft Predictive Maintenance, Prognostics and Health Management, Remaining Useful Life, Adversarial Machine Learning, Cryptographic Artifact Authentication, Ed25519, Statistical Drift Detection, Sensor Manipulation, NASA C-MAPSS.

---

## I. INTRODUCTION

Predictive maintenance in modern commercial and military aviation relies extensively on data-driven Prognostics and Health Management (PHM) architectures. By analyzing multi-sensor flight telematics—including rotational spool speeds, static bleed pressures, and gas temperatures—machine learning algorithms forecast the Remaining Useful Life (RUL) of critical components, such as turbofan gas turbines. Accurate RUL estimates enable airline operators to transition from rigid calendar-based maintenance schedules to condition-based maintenance, minimizing unscheduled Aircraft on Ground (AOG) events and mitigating catastrophic inflight mechanical failures [1], [2].

Despite considerable algorithmic advances in deep recurrent neural networks and gradient-boosted decision tree ensembles [2], [3], existing aircraft predictive maintenance models are engineered under the implicit assumption of a benign, uncorrupted operating environment. In-flight and ground-transmitted telemetry streams are assumed to accurately reflect true thermodynamic degradation, and serialized model artifacts are presumed to reside securely within trusted ground-station environments.

However, modern aviation telematics ecosystems are increasingly distributed and interconnected. Sensor readings and post-flight telemetry summaries are routinely transferred via the Aircraft Communications Addressing and Reporting System (ACARS), cellular ground data links (Gatelink), and portable data terminals during turnaround. This expanded data interface introduces potential attack vectors across both data-plane and control-plane channels [4], [12]:
1. **Supply-Chain Model-Artifact Tampering:** Adversaries with read/write access to maintenance server storage or package repositories may alter serialized estimator weights, feature scaler parameters, or metadata manifests to deliberately suppress maintenance warnings or execute malicious code via Python deserialization gadget chains [4], [6].
2. **Sensor Telemetry Manipulation:** Compromised telematics gateways or Man-in-the-Middle (MitM) interceptors can inject subtle mathematical biases, frozen packet replays, or creeping calibration drifts into thermodynamic sensor streams, skewing RUL forecasts without triggering coarse out-of-bounds alarms [7], [8].

In aviation maintenance, prediction errors carry fundamentally asymmetric operational consequences. An early prediction (under-predicting RUL) prompts premature engine inspection, incurring unnecessary operational downtime and maintenance labor costs. Conversely, a delayed prediction (over-predicting RUL) is potentially hazardous: it allows an engine on the verge of mechanical failure to remain dispatched, risking severe in-flight damage [1], [2]. Despite this asymmetry, the degree to which lightweight statistical drift monitors can detect subtle sensor manipulation and the proportion of hazardous predictions that can escape detection remain insufficiently quantified.

To investigate these questions, we present **AeroSentinel**, an integrity-assured predictive maintenance framework evaluated on the NASA C-MAPSS FD001 turbofan benchmark. This study provides the following specific contributions:
* **Dual-Protocol Baseline Disambiguation:** We formalize and evaluate two historically conflated C-MAPSS evaluation regimes: Protocol A (raw, unclipped terminal ground truth, achieving RMSE $13.9044$ and MAE $10.4044$) and Protocol B (piecewise-linear ground truth clipped at 125 cycles, achieving RMSE $13.0082$ and MAE $9.3344$), establishing reproducible ground-truth baselines.
* **Censoring Asymmetry Characterization and Resolution:** We demonstrate that evaluating operational test telemetry directly against run-to-failure training baselines reveals an 8-alert-channel distribution shift ($>53\%$ of 15 monitored channels) due to physical censoring differences, and we resolve this by establishing an operational reference via a disjoint 50/50 engine partition.
* **Resilience Evaluation of Sensor Drift Detectors:** We evaluate six synthetic sensor-manipulation scenarios targeting High-Pressure Compressor (HPC) static pressure ($s_{11}$) against Two-Sample Kolmogorov-Smirnov and Population Stability Index (PSI) monitors, demonstrating that single-channel step biases ($\pm 1.0\sigma$ to $+2.0\sigma$) evade fleet-level alarm thresholds ($\le 1$ PSI alert channel).
* **Quantification of Asymmetric Operational Risk:** We show that negative bias injection masks degradation, elevating the Canonical Hazardous Prediction Rate (HPR) from $15.79\%$ ($3/19$ engines) to $31.58\%$ ($6/19$ engines delayed past the 25-cycle safety boundary) with zero PSI alert channels under disjoint evaluation.
* **Sub-Millisecond Cryptographic Artifact Verification:** We implement an Edwards-curve Digital Signature (Ed25519) scheme over RFC 8785 canonical JSON lineage metadata. Microbenchmarks ($N=100$) confirm that fail-closed artifact verification executes in $0.13 \pm 0.02\text{ ms}$ (median $0.11\text{ ms}$), providing robust tamper evidence against unauthorized bytecode substitution across the authenticated artifact set.

---

## II. RELATED WORK & RESEARCH GAP

### A. Aircraft Prognostics & Benchmark Methodologies
The NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) benchmark released by Saxena et al. [1] is the primary standard for data-driven turbofan prognostics. In the FD001 sub-dataset, high-pressure compressor degradation is modeled under steady-state sea-level conditions across 100 training and 100 test trajectories. Ramasso and Saxena [2] surveyed over 70 C-MAPSS studies and documented pervasive benchmark reporting discrepancies, specifically highlighting the conflation of raw physical targets with piecewise-linear clipped targets ($RUL_{\max} = 125$ cycles). While deep learning (e.g., LSTM networks by Zheng et al. [3]) and gradient-boosted decision trees achieve high predictive fidelity on clean benchmark data, these studies focus exclusively on regression accuracy, omitting integrity controls or adversarial evaluation.

### B. Machine Learning Integrity & Artifact Authentication
The security of serialized machine learning models has gained increased attention as pipelines are integrated into critical infrastructure [4], [6]. Traditional persistence formats (such as Python `pickle` and `joblib`) deserialize arbitrary object state, exposing host environments to code execution vulnerabilities if model files are modified. Gu et al. [4] demonstrated that machine learning supply chains can harbor backdoors and modified weights without degrading clean accuracy. The National Institute of Standards and Technology (NIST) Special Publication 800-218 [6] explicitly recommends cryptographic signing of software and data artifacts. Bernstein et al. [5] introduced Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519), offering 128-bit security, high-speed verification, and resilience to side-channel timing attacks. However, standard predictive maintenance platforms commonly rely on unsigned SHA-256 checksums, which cannot prevent manifest rewrite attacks by an adversary with write access.

### C. Adversarial Attacks on Prognostic Time-Series & Sensor Streams
Adversarial machine learning research has expanded to sequential and cyber-physical time-series systems [7], [8], [12]. Fawaz et al. [7] and Karim et al. [8] demonstrated that subtle, bounded perturbations in sequential inputs can cause severe classification errors. Mo et al. [12] analyzed replay and sensor bias attacks on cyber-physical systems, proving that intelligent replay can evade traditional linear Kalman filter residual checks.

Directly relevant to turbofan prognostics, two notable studies have investigated adversarial attacks on neural network RUL estimation:
* **Basak et al. (2021) [14]:** Investigated Universal Adversarial Perturbations (UAPs) tailored for deep learning prognostics across NASA C-MAPSS (FD001–FD004). Rather than crafting instance-specific perturbations, the authors used white-box gradient optimization across input sequences to formulate a single, dataset-wide perturbation vector that degraded RUL predictions in Deep CNNs, LSTMs, and GRUs.
* **Mode & Hoque (2020) [15]:** Evaluated the Fast Gradient Sign Method (FGSM) and Basic Iterative Method (BIM) on multivariate time-series regression for C-MAPSS and energy benchmarks using vanilla LSTMs, stacked LSTMs, and CNNs, establishing that gradient-based adversarial examples exhibit black-box transferability across neural network architectures.

While these foundational studies established the susceptibility of differentiable deep architectures to gradient-optimized noise, they leave critical questions unaddressed. Industrial predictive maintenance pipelines widely favor gradient-boosted decision tree ensembles (such as XGBoost, LightGBM, and HistGradientBoostingRegressor) applied to tabular rolling features because of their superior interpretability, low latency, and robustness on small-to-medium fleet datasets. Decision trees are non-differentiable step functions, rendering first-order gradient attacks (such as FGSM) ineffective. Furthermore, prior studies evaluated symmetric regression errors (RMSE, MAE) and omitted operational drift screening, survival censoring effects, and cryptographic model integrity.

### D. Statistical Drift Screening in Operational ML
For continuous covariate monitoring, production systems frequently employ non-parametric tests, such as the Two-Sample Kolmogorov-Smirnov (KS) test [11] and the Population Stability Index (PSI) [10]. However, Rabanser et al. [9] demonstrated in empirical studies (*Failing Loudly*) that statistical divergence tests can fail to alert under localized, task-relevant shifts. In aviation prognostics, the interaction between multi-sensor drift detection, physical censoring distributions, and stealthy sensor manipulation has not been systematically characterized.

### E. Prior-Work Comparison Matrix
Table I compares AeroSentinel with directly relevant prior publications in adversarial time-series and predictive maintenance security.

```
TABLE I
COMPARATIVE TAXONOMY OF ADVERSARIAL TIME-SERIES AND PROGNOSTIC SECURITY RESEARCH
-----------------------------------------------------------------------------------------------------------------------------------------
Study               Model Architecture        Attack Mechanism                  Dataset           Evaluation Scope    Defense / Integrity
-----------------------------------------------------------------------------------------------------------------------------------------
Basak et al. [14]   Deep CNN, LSTM, GRU       Universal Adversarial Noise (UAP) NASA C-MAPSS      RMSE, NASA Score    None (Attacker)
Mode & Hoque [15]   Vanilla/Stacked LSTM, CNN FGSM, BIM Gradient Perturbations  C-MAPSS & SWaT    RMSE, MAE           None (Attacker)
Fawaz et al. [7]    ResNet, InceptionTime     BIM / FGSM Time-Series Noise      UCR/UEA Archive   Classification Acc  Adversarial Training
Karim et al. [8]    LSTM-FCN, ALSTM           Adversarial Transformation (BIM)  UCR Archive       Classification Acc  None (Transferability)
Gu et al. [4]       Convolutional Networks    Supply-Chain Trojan / BadNets     Vision Benchmarks Attack Success Rate None (Integrity Audit)
AeroSentinel (Ours) HistGradientBoosting      Domain-Informed Sensor Tampering  NASA C-MAPSS      Dual Protocols,     Univariate PSI / KS
                    on 122 Rolling Features   (Bias, Creeping Ramp, Replay)     FD001 (100 Eng)   NASA Score, HPR     + Ed25519 Signing
-----------------------------------------------------------------------------------------------------------------------------------------
```

### F. Identified Research Gap
Prior literature exhibits three core limitations: (1) Conflation of evaluation baselines (raw vs. clipped ground-truth) without explicit protocol separation; (2) Overlooking survival censoring asymmetry when applying statistical drift detectors across training and operational test data; and (3) An absence of unified evaluations quantifying cryptographic artifact verification overhead alongside sensor-manipulation resilience on standardized aviation benchmarks.

---

## III. SYSTEM ARCHITECTURE & THREAT MODEL

### A. Architectural Overview
AeroSentinel is designed as a ground-side advisory analytics service receiving turbofan telemetry post-flight. The architecture comprises four modular stages:
1. **Cryptographic Lineage Verifier:** Evaluates the digital signature of the deployed model pipeline before loading into memory.
2. **API Input Hardening Layer:** Enforces Pydantic v2 schema constraints, dimensional checks, and non-finite value rejection (`NaN`, `Inf`) on incoming telemetry packets [13].
3. **Dual-Baseline Covariate Drift Detector:** Computes Two-Sample KS statistics and Population Stability Index (PSI) values across all monitored sensor channels against an operational baseline.
4. **Gradient-Boosted RUL Regressor:** Generates causal RUL estimates, risk categorizations, and maintenance scheduling advisories.

### B. Threat Model & Trust Boundaries
We model threat actors using the STRIDE methodology:
* **Adversary $\mathcal{A}_{\text{art}}$ (Supply-Chain Tamperer):** Possesses read/write access to storage volumes or local caches. $\mathcal{A}_{\text{art}}$ can alter bytes in `best_model.joblib` or edit metadata manifests, but does not possess the offline Ed25519 private key ($sk_{\text{ed25519}}$).
* **Adversary $\mathcal{A}_{\text{sen}}$ (Telemetry Manipulator):** Intercepts telemetry in transit between aircraft offload and analytics ingestion. $\mathcal{A}_{\text{sen}}$ can inject additive sensor biases ($\delta \in [-2.0\sigma, +2.0\sigma]$), creeping linear ramps, or frozen packet replays, but cannot modify true historical ground-truth labels.
* **Security Invariants:**
  1. *Invariant 1 (Fail-Closed Execution):* Deserialization (`joblib.load`) is blocked if cryptographic verification fails, manifest metadata is modified, or an untrusted public key is presented.
  2. *Invariant 2 (Dual Protocol Separation):* Raw physical RUL evaluations (Protocol A) and clipped evaluations (Protocol B) remain strictly isolated.
  3. *Invariant 3 (Offline Ground-Truth Isolation):* True terminal RUL labels ($y^*$) are quarantined exclusively for offline evaluation and are never accessed during inference or drift screening.
* **Operational Scope and Advisory Boundary:** AeroSentinel is strictly a ground-side predictive maintenance advisory service. It does not interface with airborne flight-control avionics, Full Authority Digital Engine Control (FADEC), or real-time fly-by-wire buses. Synthetic manipulations represent offline data perturbations and do not claim airworthiness certification compliance (e.g., RTCA DO-178C or DO-326A).

### C. Cryptographic Authentication Specification
AeroSentinel implements the Edwards-curve Digital Signature Algorithm over Curve25519 (**Ed25519**, RFC 8032) [5]. To prevent signature invalidation caused by dictionary key reordering or whitespace formatting variations, manifest payloads are serialized using the **RFC 8785 JSON Canonicalization Scheme (JCS)**.

At initialization, the runtime verifier confirms:
$$\text{Verify}_{pk}(\text{JCS}(M_{\text{payload}}), \sigma) \stackrel{?}{=} \text{True}$$
Following signature verification, the runtime computes SHA-256 digests of all serialized dependencies declared in the manifest payload:
$$\text{Artifacts} = \{\texttt{best\_model.joblib}, \texttt{preprocessor.joblib}, \texttt{histgradientboosting.joblib}, \texttt{random\_forest.joblib}, \texttt{model\_registry.json}\}$$
Together with the signed manifest (`model_manifest.json`), this establishes cryptographic authentication across the full set of six on-disk model artifacts. Deserialization is invoked if and only if both cryptographic verification and byte-level digest matching succeed.

---

## IV. EXPERIMENTAL METHODOLOGY

### A. Dataset & Preprocessing Pipeline
We evaluate our framework on the NASA C-MAPSS FD001 dataset:
* **Training Fleet:** 100 turbofan units, 20,631 total cycles, simulated from initial nominal conditions to functional failure.
* **Test Fleet:** 100 turbofan units, 13,096 cycles, censored at an arbitrary cycle prior to functional breakdown.
* **Ground Truth:** Official terminal Remaining Useful Life vector $\mathbf{y}^* \in \mathbb{R}^{100}$ from `RUL_FD001.txt`.

Of the 21 recorded sensors and 3 operational settings, 6 sensors with invariant readings ($s_1, s_5, s_{10}, s_{16}, s_{18}, s_{19}$) and setting 3 are discarded. The pipeline extracts **15 active degradation channels**:
$$\mathcal{S}_{\text{active}} = \{s_2, s_3, s_4, s_6, s_7, s_8, s_9, s_{11}, s_{12}, s_{13}, s_{14}, s_{15}, s_{17}, s_{20}, s_{21}\}$$
Along with 2 retained operating settings ($setting_1, setting_2$), the causal feature pipeline constructs **122 engineered features**:
* 2 operational settings ($setting_1, setting_2$).
* 15 raw sensor signals ($s_j$).
* 30 rolling means over windows $w \in [5, 15]$ cycles ($s_j\_\text{roll\_mean\_5}$, $s_j\_\text{roll\_mean\_15}$).
* 30 rolling standard deviations over windows $w \in [5, 15]$ cycles ($s_j\_\text{roll\_std\_5}$, $s_j\_\text{roll\_std\_15}$).
* 30 lag differences over backward steps $l \in [1, 5]$ cycles ($s_j\_\text{diff\_1}$, $s_j\_\text{diff\_5}$).
* 15 baseline drift signals measuring deviation from the engine's initial cycle-1 observation ($s_j\_\text{drift} = s_j(t) - s_j(1)$).
All features are standardized via `StandardScaler` fitted strictly on training data without cross-engine leakage.

### B. Dual Evaluation Protocols
To resolve historical ambiguities in C-MAPSS reporting [2], we evaluate the regressor across two separate ground-truth target policies:
* **Protocol A (Raw Physical Ground Truth):** Evaluates predictions directly against unclipped official terminal RUL values:
  $$y_i^* \in [7, 145] \text{ cycles}$$
* **Protocol B (Piecewise-Linear Clipped Ground Truth):** Evaluates predictions against ground-truth clipped at the standard threshold of 125 cycles [1], [2]:
  $$y_{\text{clip}, i}^* = \min(y_i^*, 125) \text{ cycles}$$

### C. Mathematical Evaluation Metrics
Model predictive accuracy is quantified via standard regression metrics:
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (\hat{y}_i - y_i^*)^2}, \quad \text{MAE} = \frac{1}{N} \sum_{i=1}^N |\hat{y}_i - y_i^*|, \quad R^2 = 1 - \frac{\sum_{i=1}^N (\hat{y}_i - y_i^*)^2}{\sum_{i=1}^N (y_i^* - \bar{y}^*)^2}$$

Asymmetric maintenance risk is evaluated via the NASA scoring function [1]:
$$d_i = \hat{y}_i - y_i^*, \quad S_{\text{NASA}} = \sum_{i=1}^N s_i, \quad s_i = \begin{cases} \exp\left(-\frac{d_i}{13}\right) - 1, & d_i < 0 \text{ (Early Prediction)} \\ \exp\left(\frac{d_i}{10}\right) - 1, & d_i \ge 0 \text{ (Late / Hazardous Prediction)} \end{cases}$$

### D. Canonical Hazardous Prediction Rate (HPR)
To isolate late-stage operational hazards, we evaluate the Canonical Hazardous Prediction Rate over the critical subset of test engines whose true remaining life is within 25 cycles ($\mathcal{C}_{25} = \{i : y_i^* \le 25\}$):
$$\text{HPR} = \frac{|\{i \in \mathcal{C}_{25} : \hat{y}_i > 25\}|}{|\mathcal{C}_{25}|} \times 100\%$$
In FD001, exactly $|\mathcal{C}_{25}| = 19$ test engines fall within this critical health window. Falsely forecasting $>25$ cycles for an engine with $\le 25$ cycles delays mandatory inspection, increasing the likelihood of an in-service failure. In this work, all HPR figures are reported with both the explicit fractional count and percentage to maintain rigorous statistical clarity.

### E. Drift Detection & Censoring Asymmetry Resolution
Drift is monitored per sensor using two statistical formulations:
1. **Two-Sample Kolmogorov-Smirnov (KS) Test [11]:** Evaluates supremum divergence $D_{\text{KS}} = \sup_x |F_{\text{ref}}(x) - F_{\text{eval}}(x)|$, flagging channels with asymptotic $p < 0.01$ and $D_{\text{KS}} > 0.15$.
2. **Population Stability Index (PSI) [10]:** Evaluates quantile shift across $K=10$ reference bins:
   $$\text{PSI} = \sum_{k=1}^K (P_k - Q_k) \ln\left(\frac{P_k}{Q_k}\right)$$
   Standard regulatory thresholds: $\text{PSI} < 0.10$ (Stable), $0.10 \le \text{PSI} < 0.25$ (Moderate Shift / Warning), $\text{PSI} \ge 0.25$ (Significant Drift / Alert).

**The Censoring Distribution Shift Finding:** In `train_FD001.txt`, all engines progress to complete failure ($y^* = 0$), so high-degradation states dominate the late cycles. In contrast, test engines are censored at arbitrary operational stages (mean terminal RUL $= 75.8$ cycles). Comparing clean test telemetry directly against the training baseline reveals a substantial distribution shift: **8 sensor channels trigger PSI alerts** ($s_2, s_4, s_7, s_{11}, s_{12}, s_{15}, s_{20}, s_{21}$ with $\text{PSI} \ge 0.25$) and **6 channels trigger warnings** ($s_3, s_8, s_9, s_{13}, s_{14}, s_{17}$ with $0.10 \le \text{PSI} < 0.25$), leaving only $s_6$ stable. This reflects a structural survival-censoring divergence between training and operational monitoring distributions, rather than an adversarial attack or sensor malfunction. If a monitoring architecture naively adopts the run-to-failure training set as its operational drift baseline, it would operate in a persistent state of false alarm.

To eliminate these false alarms without in-sample self-comparison dependencies, AeroSentinel introduces a **Dual-Baseline Architecture** with disjoint engine partitioning:
* *Model Training Baseline:* Derived from `train_FD001.txt` for regression training and scaler fitting.
* *Disjoint Operational Calibration Baseline:* Test engines are partitioned into **Calibration Engines 1–50** ($\mathcal{E}_{\text{cal}}$, uncorrupted reference) and **Evaluation Engines 51–100** ($\mathcal{E}_{\text{eval}}$). Evaluating clean $\mathcal{E}_{\text{eval}}$ against $\mathcal{E}_{\text{cal}}$ yields **0 alert channels and 0 warning channels (overall fleet status: `stable`)**, demonstrating a verified baseline on the tested evaluation partition under stationary C-MAPSS FD001 conditions.
* *Fleet Aggregation Rules:* System status is categorized as:
  - `stable`: 0 alert channels and $\le 2$ warning channels.
  - `warning`: exactly 1 alert channel, or $3\text{--}4$ warning channels.
  - `drift_alert`: $\ge 2$ alert channels, or $\ge 5$ total alert/warning channels.

### F. Synthetic Attack Scenarios
We formulate six synthetic attack scenarios targeting sensor $s_{11}$ (static pressure at HPC outlet, highest feature importance). Perturbation scales $\sigma(s_j)$ are calibrated strictly from the uncorrupted training baseline (`train_FD001.txt`) to preserve operational realism and ensure zero data leakage from evaluation trajectories:
* **Scenario 1 (`sc1_bias_s11_pos_1sigma`):** Additive step bias $s_{11}'(t) = s_{11}(t) + 1.0\sigma(s_{11})$ at onset cycle $t \ge 0.60 \cdot T_{\text{last}}$.
* **Scenario 2 (`sc2_bias_s11_pos_2sigma`):** Additive step bias $s_{11}'(t) = s_{11}(t) + 2.0\sigma(s_{11})$ at onset cycle $t \ge 0.60 \cdot T_{\text{last}}$.
* **Scenario 3 (`sc3_bias_s11_neg_1sigma`):** Negative step bias $s_{11}'(t) = s_{11}(t) - 1.0\sigma(s_{11})$ at onset cycle $t \ge 0.60 \cdot T_{\text{last}}$ (artificially masking pressure drop).
* **Scenario 4 (`sc4_ramp_s11_pos_2sigma`):** Creeping linear ramp accumulating to $+2.0\sigma$ from $t \ge 0.50 \cdot T_{\text{last}}$ to terminal cycle $T_{\text{last}}$.
* **Scenario 5 (`sc5_multisensor_bias`):** Coordinated multi-sensor shift: $+1.0\sigma$ on $s_{11}$ (HPC static pressure), $s_9$ (core speed), and $s_4$ (LPT exit temperature).
* **Scenario 6 (`sc6_frozen_replay`):** Frozen telemetry replay: freezing all 15 active sensors at early-life cycle $t = 0.40 \cdot T_{\text{last}}$ through flight termination.

---

## V. EXPERIMENTAL RESULTS & ANALYSIS

### A. Clean Baseline Model Performance & Protocol Disambiguation
Table II summarizes the baseline performance of the trained `HistGradientBoostingRegressor` on the 100 unseen held-out test engines across both evaluation protocols.

```
TABLE II
CLEAN BASELINE PERFORMANCE ACROSS EVALUATION PROTOCOLS (N = 100 TEST ENGINES)
------------------------------------------------------------------------------------------------------
Protocol      Target Policy      RMSE     MAE      R²      NASA Score  NASA / Eng  HPR (Count)  HPR (%)
------------------------------------------------------------------------------------------------------
Protocol A    Raw Unclipped     13.9044  10.4044  0.8880    301.97       3.02        3 / 19     15.79%
Protocol B    Clipped at 125    13.0082   9.3344  0.8946    280.35       2.80        3 / 19     15.79%
------------------------------------------------------------------------------------------------------
```

Both protocols demonstrate strong predictive fidelity ($R^2 \ge 0.888$), with Protocol B yielding lower RMSE ($13.0082$ vs. $13.9044$) due to saturation target clipping at 125 cycles. Under clean conditions, 16 of the 19 critical engines are correctly identified, resulting in a baseline Canonical HPR of $15.79\%$ ($3/19$ engines). Fig. 1 illustrates the comparative distribution and error bounds across both protocols.

```
+-----------------------------------------------------------------------+
|  [Figure 1: Clean Baseline Performance & Dual Protocol Disambiguation] |
|  Scatter and error density plots demonstrating 100-engine predictions  |
|  under Protocol A (unclipped) vs. Protocol B (clipped at 125).        |
|  Source: reports/research/figures/fig1_baseline_protocols.png          |
+-----------------------------------------------------------------------+
```

### B. Sensor Manipulation Resilience & Evasion Dynamics
Table III presents the empirical outcomes across Scenarios 1 through 6 evaluated on the held-out test fleet and the dual-baseline drift monitors.

```
TABLE III
SENSOR MANIPULATION IMPACT ON PREDICTIONS AND DRIFT EVASION (N = 100 ENGINES)
------------------------------------------------------------------------------------------------------------------------------------
Scenario ID  Description                 Mean Shift   RMSE     MAE    NASA Score  HPR (Count)  HPR (%)  Alerts  Warns Disjoint Status
------------------------------------------------------------------------------------------------------------------------------------
baseline     Clean Operational Baseline      0.00c   13.9044  10.4044   301.97      3 / 19     15.79%     0       0       stable
sc1          Step Bias (+1.0σ on S11)       -9.52c   18.1647  13.5201   452.46      1 / 19      5.26%     1       0      warning
sc2          Step Bias (+2.0σ on S11)      -12.07c   20.4374  15.5462   577.97      1 / 19      5.26%     1       0      warning
sc3          Negative Bias (-1.0σ on S11)   +5.16c   15.7392  12.3014   433.13      6 / 19     31.58%     0       1       stable
sc4          Creeping Ramp (+2.0σ on S11)  -11.74c   20.1812  15.3778   564.54      1 / 19      5.26%     1       0      warning
sc5          Multi-Sensor (+1.0σ S11/S9/S4)-21.55c   28.5856  21.8959  1673.13      0 / 19      0.00%     3       0    drift_alert
sc6          Frozen Replay (Cycle 40%)     +42.16c   58.3342  45.9051 791878.67    19 / 19    100.00%     3       8    drift_alert
------------------------------------------------------------------------------------------------------------------------------------
```

The empirical results reveal several critical security insights:
1. **Drift Screening Evasion:** Single-channel step biases up to $+2.0\sigma$ (`sc1`, `sc2`) and gradual creeping ramps (`sc4`) trigger **at most 1 PSI alert channel** ($s_{11}$) across the 15 monitored features. Under disjoint engine evaluation, `sc1`, `sc2`, and `sc4` produce a system status of `warning`, remaining below the automated fleet rejection threshold ($\ge 2$ alert channels or $\ge 5$ total warning/alert channels) despite shifting RUL predictions by up to $-12.07$ cycles and degrading RMSE to $20.4374$.
2. **Asymmetric Hazard Escalation:** Scenario 3 (`sc3`, negative bias on $s_{11}$) depresses measured static pressure, deceiving the model into predicting the engine as healthier than its true physical state. This delays predicted overhaul by $+5.16$ cycles on average, escalating the NASA asymmetric penalty to $433.13$. Crucially, **the Canonical Hazardous Prediction Rate doubles from $15.79\%$ ($3/19$) to $31.58\%$ ($6/19$ critical engines delayed past the 25-cycle safety boundary)**. Under disjoint engine evaluation, `sc3` triggers **0 alert channels and 1 warning channel** ($s_{11}$), yielding an overall system status of `stable` and completely evading drift alarms.
3. **Catastrophic Replay Impact:** In Scenario 6 (`sc6`), replaying healthy telemetry packets frozen at early-life cruise cycles results in an **HPR of $100.00\%$ ($19/19$ critical engines approaching physical failure are predicted as safe)**. This elevates the NASA exponential penalty to $791,878.67$ (a $>2,600\times$ surge). While multi-channel drift monitors flag 3 alert channels and 8 warning channels (`drift_alert`), 4 channels remain un-alerted due to distribution overlap in early-life operating regimes.

Figs. 2, 3, and 4 illustrate the RUL prediction shift distributions, exponential NASA score escalations, and multi-sensor PSI drift heatmaps, respectively.

```
+-----------------------------------------------------------------------+
|  [Figure 2: RUL Prediction Shift & Residual Error Distributions]      |
|  Distribution of prediction degradation across all 6 attack scenarios.|
|  Source: reports/research/figures/fig2_attack_rul_shifts.png          |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|  [Figure 3: Asymmetric NASA Risk Penalty Escalation]                  |
|  Exponential penalty surge under delayed prediction and frozen replay.|
|  Source: reports/research/figures/fig3_asymmetric_nasa_surge.png      |
+-----------------------------------------------------------------------+

+-----------------------------------------------------------------------+
|  [Figure 4: Multi-Sensor Population Stability Index (PSI) Heatmap]    |
|  Fleet-wide sensor distribution drift (PSI) evaluated across the full  |
|  100-engine test fleet relative to clean operational telemetry         |
|  (drift_clean), illustrating detection evasion in single-sensor bias  |
|  and ramp attacks. Table III reports corresponding operational        |
|  detection under the disjoint 50/50 calibration/evaluation partition  |
|  (drift_disjoint).                                                    |
|  Source: reports/research/figures/fig4_drift_psi_heatmap.png          |
+-----------------------------------------------------------------------+
```

### C. Cryptographic Authentication & Tamper-Proofing Verification
To evaluate control-plane integrity, the Ed25519 verified loader was tested against 12 distinct attack vectors. Table IV presents the verification outcomes.

```
TABLE IV
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

Under all adversarial mutation vectors (TV-02 through TV-10, TV-12), the engine maintained fail-closed execution: deserialization (`joblib.load`) was blocked, preventing arbitrary bytecode execution.

### D. Computational Overhead & Latency Benchmarks
Microbenchmarks were conducted across $N=100$ independent trials with warm-up cycles on an AMD64 architecture. Table V presents the decomposed execution profile.

```
TABLE V
COMPUTATIONAL LATENCY BENCHMARKS ACROSS PIPELINE STAGES (N = 100 REPETITIONS)
--------------------------------------------------------------------------------
Pipeline Component                  Mean (ms)  Std (ms)  Median (ms)  p95 (ms)
--------------------------------------------------------------------------------
Ed25519 Signature Verification           0.13      0.02         0.11      0.25
Multi-File SHA-256 Hashing (~20 MB)     14.93      0.82        14.77     16.40
Model Deserialization (joblib.load)      9.47      1.96         8.65     14.32
Total Verified Startup Pipeline         24.37      1.45        23.90     26.71
Feature Engineering (13,096 cycles)    135.96      3.12       135.62    141.53
Single-Engine Inference (1x122)          1.39      0.44         1.16      2.43
Fleet Batch Inference (100x122)          1.34      0.32         1.17      2.11
15-Sensor KS + PSI Drift Screening     100.73      2.56       100.29    105.32
--------------------------------------------------------------------------------
```

Crucially, **pure Ed25519 signature verification requires only $0.13 \pm 0.02\text{ ms}$** (median $0.11\text{ ms}$), contributing less than $0.6\%$ of the total startup latency ($24.37\text{ ms}$). To interpret these performance figures accurately across deployment scenarios, four latency regimes must be distinguished:
1. *Artifact-Loading Overhead:* A one-time initialization cost ($24.37\text{ ms}$ composite mean, $23.90\text{ ms}$ median) incurred during process startup or model hot-reload. The composite timing encompasses reading and parsing `model_manifest.json` from storage, Ed25519 signature verification ($0.13\text{ ms}$ mean, $0.11\text{ ms}$ median), SHA-256 digest computation across the five declared dependency artifacts ($14.93\text{ ms}$ mean, $14.77\text{ ms}$ median across 21.01 MB on disk: `best_model.joblib`, `preprocessor.joblib`, `histgradientboosting.joblib`, `random_forest.joblib`, and `model_registry.json`), and joblib deserialization of the active production model and preprocessor ($9.47\text{ ms}$ mean, $8.65\text{ ms}$ median). Isolated component timings sum to $24.53\text{ ms}$; the slight variance with composite measurement ($<0.7\%$) reflects separate execution loops and manifest disk-parsing orchestration rather than runtime non-determinism. Across independent benchmarking iterations (e.g., initial profiling plotted in Fig. 5 with 0.11 ms Ed25519, 15.34 ms SHA-256, 9.56 ms deserialization; Table V with 24.37 ms composite mean; and a companion re-benchmark recorded in `performance_benchmarks.csv` with 0.105 ms Ed25519, 14.04 ms SHA-256, 8.35 ms deserialization, 23.01 ms composite mean), individual component measurements vary by up to 19.2% for Ed25519 and 11.9% for deserialization, while composite startup varies by 5.6%. In all recorded trials, pure Ed25519 verification consistently executes in $\le 0.13\text{ ms}$, confirming that asymmetric cryptographic signing contributes negligible overhead ($<0.6\%$) relative to physical disk I/O and deserialization.
2. *Single-Request Inference Latency:* Evaluating an individual engine ($1 \times 122$ feature vector) requires $1.39\text{ ms}$ mean ($1.16\text{ ms}$ median). Profiling indicates that $\approx 1.1\text{ ms}$ is consumed by Scikit-learn array validation (`check_array`) and Python-to-C wrapper dispatch.
3. *Fleet Batch Inference Latency:* Evaluating an entire 100-engine fleet ($100 \times 122$ matrix) in a single invocation executes in $1.34\text{ ms}$ mean ($1.17\text{ ms}$ median). Because tree traversals execute across a contiguous NumPy buffer in compiled C routines, batch dispatch amortizes the fixed invocation overhead to **$13.4\ \mu\text{s}$ per engine**.
4. *Covariate Drift Screening Overhead:* Periodic multi-sensor drift detection (KS tests and 10-bin PSI across all 15 active channels) requires $100.73\text{ ms}$ across 13,096 operational cycles, well suited for post-flight background batch execution. Fig. 5 illustrates the execution latency profile.

```
+-----------------------------------------------------------------------+
|  [Figure 5: Computational Latency Breakdown Across Pipeline Stages]   |
|  Latency breakdown illustrating sub-millisecond Ed25519 verification  |
|  alongside physical SHA-256 disk hashing, model deserialization,      |
|  batch inference, and drift screening. Component values illustrate the |
|  initial profiling run (summing to 25.01 ms composite), while Table V  |
|  reports the multi-trial microbenchmark distribution (24.37 ms mean); |
|  across all runs, signature overhead remains under 0.15 ms (<0.6% of  |
|  startup).                                                            |
|  Source: reports/research/figures/fig5_latency_breakdown.png          |
+-----------------------------------------------------------------------+
```

---

## VI. DISCUSSION, THREATS TO VALIDITY & LIMITATIONS

### A. The Asymmetric Maintenance Risk Dilemma
Our empirical findings demonstrate an inherent architectural challenge: standard statistical anomaly detectors (KS test, PSI) are calibrated at the fleet level to tolerate natural operational variance and avoid false-positive maintenance grounding. Adversaries can exploit this tolerance window by crafting perturbations that mimic early-stage mechanical wear, shifting RUL estimates and doubling the Hazardous Prediction Rate while remaining below PSI alert thresholds. Consequently, predictive maintenance pipelines cannot rely exclusively on post-hoc statistical screening; they require end-to-end cryptographic provenance from sensor ingestion to ground analytics, supplemented by physics-based invariant checks.

### B. Detection Blind Spots of Univariate Drift Monitors
Univariate statistical metrics, including PSI and KS tests, analyze each sensor dimension independently. While computationally efficient, this independent channel evaluation creates a blind spot: subtle multivariate correlations and thermodynamic conservation laws (such as temperature-pressure relationships across compressor stages) can be violated without any single sensor exceeding its marginal distribution shift threshold. This explains why Scenario 3 evades detection and Scenarios 1, 2, and 4 generate only single-channel warnings. Mitigating this blind spot requires multivariate density estimators or physics-informed neural network (PINN) invariants that model inter-sensor thermodynamic coupling.

### C. Methodological Threats to Validity & Operational Limitations
1. **Simulation Benchmark Fidelity:** NASA C-MAPSS models engine thermodynamic degradation via differential equations under steady-state sea-level conditions. Real operational flights experience non-linear atmospheric transitions and varying flight envelopes.
2. **Fixed Operational Partitioning:** Our disjoint operational baseline utilized a fixed 50/50 partition (Engines 1–50 calibration, Engines 51–100 evaluation). While this prevented in-sample leakage and established zero false alarms on clean evaluation engines, future work should explore multi-fold cross-validation or Monte Carlo permutations to assess partition variance.
3. **Synthetic Offline Attack Ground-Truth:** Sensor manipulations are synthetically constructed deterministic perturbations. They demonstrate mathematical sensitivity and detector blind spots, but do not simulate low-level electronic warfare or ARINC 429 datalink exploitation.
4. **Operational Scope:** AeroSentinel is strictly a ground-side advisory decision-support system. It does not interface with Full Authority Digital Engine Control (FADEC) or certified avionics, and no compliance with RTCA DO-178C or DO-326A airworthiness standards is claimed.

---

## VII. CONCLUSION & FUTURE WORK

This study evaluated integrity controls and sensor-manipulation resilience in a turbofan predictive maintenance pipeline using NASA C-MAPSS FD001. We characterized the run-to-failure censoring distribution shift, established a disjoint operational reference baseline, demonstrated that single-channel sensor manipulations can evade fleet-level drift alarms while doubling the Hazardous Prediction Rate to $31.58\%$ ($6/19$ critical engines delayed), and confirmed that Ed25519 cryptographic signing provides fail-closed artifact protection with negligible computational overhead ($0.13\text{ ms}$).

Future research will extend this framework to multi-regime flight envelopes (C-MAPSS FD002/FD004), investigate physics-informed neural network (PINN) invariants to detect thermodynamic inconsistencies, and prototype hardware security module (HSM) key management on ARINC 429 ground gateway emulators.

---

### Acknowledgments
The authors express gratitude to the NASA Ames Prognostics Center of Excellence for making the C-MAPSS turbofan simulation benchmark publicly available.

### Declarations
* **Funding:** No external commercial grant or corporate sponsorship was received for this investigation.
* **Conflict of Interest:** The authors declare no competing financial or commercial conflicts of interest.
* **Data Availability:** All experimental scripts, evaluation manifests, cryptographic public keys, and benchmark generation tools are accessible within the AeroSentinel research repository for scientific verification.

---

## REFERENCES

[1] A. Saxena, K. Goebel, D. Simon, and N. Eklund, "Damage propagation modeling for aircraft engine run-to-failure simulation," in *Proc. 2008 Int. Conf. Prognostics and Health Management (PHM)*, Denver, CO, USA, Oct. 2008, pp. 1–9, doi: 10.1109/PHM.2008.4711414.

[2] E. Ramasso and A. Saxena, "Performance benchmarking and analysis of prognostic methods for CMAPSS datasets," *Int. J. Prognostics and Health Management*, vol. 5, no. 2, pp. 1–15, Dec. 2014, doi: 10.36001/ijphm.2014.v5i2.2217.

[3] S. Zheng, K. Ristovski, A. Farahat, and C. Gupta, "Long short-term memory network for remaining useful life estimation," in *Proc. 2017 IEEE Conf. Prognostics and Health Management (ICPHM)*, Dallas, TX, USA, Jun. 2017, pp. 88–95, doi: 10.1109/ICPHM.2017.7998311.

[4] T. Gu, B. Dolan-Gavitt, and S. Garg, "BadNets: Identifying vulnerabilities in the machine learning model supply chain," *IEEE Access*, vol. 7, pp. 47230–47244, Apr. 2019, doi: 10.1109/ACCESS.2019.2923408.

[5] D. J. Bernstein, N. Duif, T. Lange, P. Schwabe, and B.-Y. Yang, "High-speed high-security signatures," *J. Cryptographic Engineering*, vol. 2, no. 2, pp. 77–89, Sep. 2012, doi: 10.1007/s13389-012-0027-1.

[6] National Institute of Standards and Technology (NIST), "Secure Software Development Framework (SSDF) version 1.1: Recommendations for mitigating the risk of software supply chain attacks," *NIST Special Publication 800-218*, Gaithersburg, MD, USA, Feb. 2022, doi: 10.6028/NIST.SP.800-218.

[7] H. I. Fawaz, G. Forestier, J. Weber, L. Idoumghar, and P.-A. Muller, "Adversarial attacks on deep neural networks for time series classification," in *Proc. 2019 Int. Joint Conf. Neural Networks (IJCNN)*, Budapest, Hungary, Jul. 2019, pp. 1–8, doi: 10.1109/IJCNN.2019.8851936.

[8] F. Karim, S. Majumdar, and H. Darabi, "Adversarial attacks on time series," *IEEE Access*, vol. 8, pp. 81718–81726, Apr. 2020, doi: 10.1109/ACCESS.2020.2980424.

[9] S. Rabanser, S. Günnemann, and Z. C. Lipton, "Failing loudly: An empirical study of methods for detecting dataset shift," in *Advances in Neural Information Processing Systems (NeurIPS 32)*, Vancouver, BC, Canada, Dec. 2019, pp. 1396–1408.

[10] N. Siddiqi, *Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring*. Hoboken, NJ, USA: John Wiley & Sons, 2006, doi: 10.1002/9781119201731.

[11] F. J. Massey, "The Kolmogorov-Smirnov test for goodness of fit," *J. American Statistical Association*, vol. 46, no. 253, pp. 68–78, Mar. 1951, doi: 10.1080/01621459.1951.10500769.

[12] Y. Mo, R. Chabukswar, and B. Sinopoli, "Detecting integrity attacks on cyber-physical systems," *IEEE Trans. Control Systems Technology*, vol. 22, no. 4, pp. 1396–1407, Jul. 2014, doi: 10.1109/TCST.2013.2280899.

[13] OWASP Foundation, "OWASP API Security Top 10 2023," Open Worldwide Application Security Project, Jun. 2023. [Online]. Available: https://owasp.org/www-project-api-security/

[14] A. Basak, P. Rathore, S. H. Nistala, S. Srinivas, and V. Runkana, "Universal adversarial attack on deep learning based prognostics," in *Proc. 2021 IEEE Int. Conf. Big Data (Big Data)*, Orlando, FL, USA, Dec. 2021, pp. 4363–4370, doi: 10.1109/BigData52589.2021.9671607.

[15] G. R. Mode and K. A. Hoque, "Adversarial examples in deep learning for multivariate time series regression," in *Proc. 2020 IEEE Applied Imagery Pattern Recognition Workshop (AIPR)*, Washington, DC, USA, Oct. 2020, pp. 1–10, doi: 10.1109/AIPR50011.2020.9425190.
