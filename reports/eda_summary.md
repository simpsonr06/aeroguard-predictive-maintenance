# Aircraft Predictive Maintenance - Exploratory Data Analysis (EDA) Report
**Dataset**: NASA C-MAPSS FD001 (Commercial Modular Aero-Propulsion System Simulation)  
**Operating Condition**: Sea Level (Single regime)  
**Fault Mode**: High-Pressure Compressor (HPC) Degradation  

---

## 1. Dataset Dimensions & Integrity
- **Total Operational Records**: 20,631 cycles
- **Total Engine Fleet**: 100 unique engines
- **Total Variables**: 28 (2 index columns, 3 operational settings, 21 sensor measurements)
- **Missing Values**: 0 (Complete data integrity)
- **Monotonicity**: Continuous integer cycles from 1 to failure for all engines.

---

## 2. Fleet Lifetime Characteristics
- **Shortest Engine Life**: 128 cycles (Engine 39)
- **Longest Engine Life**: 362 cycles (Engine 69)
- **Mean Fleet Lifetime**: 206.31 ± 46.34 cycles
- **Median Fleet Lifetime**: 199.0 cycles
- **Interquartile Range**: [177.0, 229.2] cycles

---

## 3. Sensor Variance & Pruning Analysis
The following 7 variables exhibit zero or negligible variance (std < 1e-4) under Sea Level operations and are pruned to eliminate noise and collinearity:
- `setting_3`: Throttle Resolver Angle (constant 100.0)
- `sensor_1`: Fan Inlet Temperature T2 (constant 518.67 °R)
- `sensor_5`: Fan Inlet Pressure P2 (constant 14.62 psia)
- `sensor_10`: Engine Pressure Ratio epr (constant 1.30)
- `sensor_16`: Burner Fuel-Air Ratio farB (constant 0.03)
- `sensor_18`: Demanded Fan Speed Nf_dmd (constant 2388 rpm)
- `sensor_19`: Demanded Corrected Fan Speed PCNfR_dmd (constant 100.0 rpm)

The remaining **14 sensors** and **2 operational settings** carry distinct degradation signatures.

---

## 4. Top Degradation Sensors Correlated with RUL
Sensors showing the strongest monotonic relationship with Remaining Useful Life:

| Sensor | Physical Description | Unit | Pearson Correlation with RUL | Degradation Direction |
|---|---|---|---|---|
| `sensor_11` | HPC Static Outlet Pressure (Ps30) | psia | -0.696 | Increases as failure approaches |
| `sensor_4` | LPT Outlet Temperature (T50) | °R | -0.679 | Increases as failure approaches |
| `sensor_12` | Fuel Flow to Ps30 Ratio (Phi) | pps/psi | 0.672 | Decreases as failure approaches |
| `sensor_7` | HPC Outlet Pressure (P30) | psia | 0.657 | Decreases as failure approaches |
| `sensor_2` | LPC Outlet Temperature (T24) | °R | -0.606 | Increases as failure approaches |
| `sensor_15` | Bypass Ratio (BPR) | - | -0.643 | Increases as failure approaches |

---

## 5. Artifacts Generated
- Lifetime Distribution: `reports/figures/engine_lifetime_distribution.png`
- Sensor Variance Profile: `reports/figures/sensor_variance_profile.png`
- Sensor Degradation Trajectories: `reports/figures/sensor_degradation_trajectories.png`
- Correlation Heatmap: `reports/figures/sensor_correlations.png`
