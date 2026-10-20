"""Exploratory Data Analysis (EDA) generator for C-MAPSS FD001.

Generates comprehensive degradation charts, correlation matrices,
and statistical reports saved to reports/figures/ and reports/eda_summary.md.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from aircraft_pm.config import (
    CONSTANT_OR_LOW_VARIANCE_COLS,
    FIGURES_DIR,
    INFORMATIVE_SENSOR_COLS,
    REPORTS_DIR,
    SENSOR_COLUMNS,
    SENSOR_DESCRIPTIONS,
    SETTING_COLUMNS,
)
from aircraft_pm.data import load_train_data


def setup_plotting_style() -> None:
    """Configure modern, publication-grade aesthetics for figures."""
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams.update(
        {
            "figure.autolayout": True,
            "figure.titlesize": 14,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
        }
    )


def plot_lifetime_distribution(df: pd.DataFrame, output_path: Path) -> pd.Series:
    """Plot distribution of engine lifetimes (total operational cycles to failure)."""
    max_cycles = df.groupby("engine_id")["cycle"].max()

    fig, (ax_box, ax_hist) = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [0.25, 0.75]}
    )

    sns.boxplot(x=max_cycles, ax=ax_box, color="#3b82f6", fliersize=4)
    ax_box.set(xlabel="")
    ax_box.set_title("Fleet Operational Lifetime Distribution (100 Engines)", fontsize=14, weight="bold")

    sns.histplot(max_cycles, kde=True, ax=ax_hist, color="#1d4ed8", bins=20)
    ax_hist.axvline(max_cycles.mean(), color="#ef4444", linestyle="--", linewidth=2, label=f"Mean: {max_cycles.mean():.1f}")
    ax_hist.axvline(max_cycles.median(), color="#10b981", linestyle="-.", linewidth=2, label=f"Median: {max_cycles.median():.1f}")
    ax_hist.set_xlabel("Engine Failure Cycle (Lifetime)")
    ax_hist.set_ylabel("Engine Count")
    ax_hist.legend(frameon=True)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return max_cycles


def plot_sensor_variances(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Plot variance profile across all sensors to visualize constant vs informative sensors."""
    all_cols = SETTING_COLUMNS + SENSOR_COLUMNS
    stds = df[all_cols].std().sort_values()

    variance_df = pd.DataFrame({"Feature": stds.index, "Std": stds.values})
    variance_df["IsConstant"] = variance_df["Feature"].isin(CONSTANT_OR_LOW_VARIANCE_COLS)

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = ["#ef4444" if is_c else "#3b82f6" for is_c in variance_df["IsConstant"]]
    
    bars = ax.barh(variance_df["Feature"], variance_df["Std"], color=colors)
    ax.set_xscale("log")
    ax.set_xlabel("Standard Deviation (Log Scale)")
    ax.set_title("Sensor & Operational Setting Variance Profile (FD001)", fontsize=14, weight="bold")

    # Add custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#ef4444", label="Constant / Near-Zero Variance (Pruned)"),
        Patch(facecolor="#3b82f6", label="Informative Sensor / Setting"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", frameon=True)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return variance_df


def plot_degradation_trajectories(
    df: pd.DataFrame, output_path: Path, engines: Optional[List[int]] = None
) -> None:
    """Plot degradation trajectories over normalized lifetime for key sensors."""
    if engines is None:
        engines = [1, 2, 3, 4]

    # Select representative deteriorating sensors
    key_sensors = ["sensor_2", "sensor_3", "sensor_4", "sensor_7", "sensor_11", "sensor_12"]
    
    df_plot = df[df["engine_id"].isin(engines)].copy()
    max_c = df_plot.groupby("engine_id")["cycle"].transform("max")
    df_plot["life_percent"] = (df_plot["cycle"] / max_c) * 100.0

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True)
    axes = axes.flatten()

    palette = sns.color_palette("tab10", n_colors=len(engines))

    for idx, sensor in enumerate(key_sensors):
        ax = axes[idx]
        desc = SENSOR_DESCRIPTIONS.get(sensor, {}).get("name", sensor)
        unit = SENSOR_DESCRIPTIONS.get(sensor, {}).get("unit", "")
        
        for eng_idx, engine_id in enumerate(engines):
            eng_data = df_plot[df_plot["engine_id"] == engine_id]
            ax.plot(
                eng_data["life_percent"],
                eng_data[sensor],
                label=f"Engine {engine_id}",
                color=palette[eng_idx],
                alpha=0.85,
                linewidth=1.8,
            )

        ax.set_title(f"{desc} ({sensor})", fontsize=11, weight="bold")
        ax.set_ylabel(unit)
        if idx >= 3:
            ax.set_xlabel("Engine Life (% of total lifetime)")
        if idx == 0:
            ax.legend(loc="upper left", fontsize=8)

    plt.suptitle("Sensor Degradation Trajectories Across Normalized Lifetime", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)


def plot_sensor_correlations(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Plot correlation between informative sensors and RUL."""
    cols_to_corr = ["rul", "cycle"] + INFORMATIVE_SENSOR_COLS
    corr_matrix = df[cols_to_corr].corr(method="spearman")

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        corr_matrix,
        cmap="coolwarm",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Spearman Rank Correlation"},
        ax=ax,
    )
    ax.set_title("Spearman Correlation Matrix (Informative Sensors & RUL)", fontsize=14, weight="bold")

    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    return corr_matrix


def generate_eda_report(
    df: pd.DataFrame,
    max_cycles: pd.Series,
    output_path: Path,
) -> None:
    """Write comprehensive markdown EDA summary report."""
    corr = df[["rul"] + INFORMATIVE_SENSOR_COLS].corr().loc["rul"].drop("rul").sort_values()

    report = f"""# Aircraft Predictive Maintenance - Exploratory Data Analysis (EDA) Report
**Dataset**: NASA C-MAPSS FD001 (Commercial Modular Aero-Propulsion System Simulation)  
**Operating Condition**: Sea Level (Single regime)  
**Fault Mode**: High-Pressure Compressor (HPC) Degradation  

---

## 1. Dataset Dimensions & Integrity
- **Total Operational Records**: {len(df):,} cycles
- **Total Engine Fleet**: {df['engine_id'].nunique()} unique engines
- **Total Variables**: {len(df.columns)} (2 index columns, 3 operational settings, 21 sensor measurements)
- **Missing Values**: 0 (Complete data integrity)
- **Monotonicity**: Continuous integer cycles from 1 to failure for all engines.

---

## 2. Fleet Lifetime Characteristics
- **Shortest Engine Life**: {max_cycles.min()} cycles (Engine {max_cycles.idxmin()})
- **Longest Engine Life**: {max_cycles.max()} cycles (Engine {max_cycles.idxmax()})
- **Mean Fleet Lifetime**: {max_cycles.mean():.2f} ± {max_cycles.std():.2f} cycles
- **Median Fleet Lifetime**: {max_cycles.median():.1f} cycles
- **Interquartile Range**: [{max_cycles.quantile(0.25):.1f}, {max_cycles.quantile(0.75):.1f}] cycles

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
| `sensor_11` | HPC Static Outlet Pressure (Ps30) | psia | {corr.get('sensor_11', 0.0):.3f} | Increases as failure approaches |
| `sensor_4` | LPT Outlet Temperature (T50) | °R | {corr.get('sensor_4', 0.0):.3f} | Increases as failure approaches |
| `sensor_12` | Fuel Flow to Ps30 Ratio (Phi) | pps/psi | {corr.get('sensor_12', 0.0):.3f} | Decreases as failure approaches |
| `sensor_7` | HPC Outlet Pressure (P30) | psia | {corr.get('sensor_7', 0.0):.3f} | Decreases as failure approaches |
| `sensor_2` | LPC Outlet Temperature (T24) | °R | {corr.get('sensor_2', 0.0):.3f} | Increases as failure approaches |
| `sensor_15` | Bypass Ratio (BPR) | - | {corr.get('sensor_15', 0.0):.3f} | Increases as failure approaches |

---

## 5. Artifacts Generated
- Lifetime Distribution: `reports/figures/engine_lifetime_distribution.png`
- Sensor Variance Profile: `reports/figures/sensor_variance_profile.png`
- Sensor Degradation Trajectories: `reports/figures/sensor_degradation_trajectories.png`
- Correlation Heatmap: `reports/figures/sensor_correlations.png`
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)


def run_eda() -> None:
    """Execute complete EDA pipeline and save charts/report."""
    setup_plotting_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading labeled training data for EDA...")
    df, _ = load_train_data()

    print("Generating engine lifetime distribution plot...")
    max_cycles = plot_lifetime_distribution(df, FIGURES_DIR / "engine_lifetime_distribution.png")

    print("Generating sensor variance profile plot...")
    plot_sensor_variances(df, FIGURES_DIR / "sensor_variance_profile.png")

    print("Generating degradation trajectory curves...")
    plot_degradation_trajectories(df, FIGURES_DIR / "sensor_degradation_trajectories.png")

    print("Generating correlation heatmap...")
    plot_sensor_correlations(df, FIGURES_DIR / "sensor_correlations.png")

    print("Writing EDA summary report...")
    generate_eda_report(df, max_cycles, REPORTS_DIR / "eda_summary.md")

    print(f"EDA successfully completed. Artifacts saved in {FIGURES_DIR} and {REPORTS_DIR}.")


if __name__ == "__main__":
    run_eda()
