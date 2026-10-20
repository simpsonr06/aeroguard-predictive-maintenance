"""AeroGuard — Commercial Aircraft Fleet Prognostics & Predictive Maintenance Dashboard.

Built using the Yafa-UI analytical dashboard design system:
- 4-layer shell: white sidebar, top bar, page identity bar, #f8fafd analytical canvas
- Multi-color analytical palette (cyan, blue, green, violet, pink, amber)
- Standard KPI card anatomy with 3-4px top accent strips and dotted-underlined description affordances
- Semantic statuses rendered strictly as 6px dots + plain neutral text (anti-capsule invariant)
- Rectangular anti-bubble geometry (0-8px corners)
- Code-native Lucide SVG icons
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from aircraft_pm.config import (
    CONSTANT_OR_LOW_VARIANCE_COLS,
    FIGURES_DIR,
    HEALTH_CRITICAL,
    HEALTH_WARNING,
    INFORMATIVE_SENSOR_COLS,
    MODELS_DIR,
    REPORTS_DIR,
    SENSOR_DESCRIPTIONS,
)
from aircraft_pm.data import load_test_data, load_train_data
from aircraft_pm.features import CMAPSSPreprocessor
from aircraft_pm.operations import (
    build_maintenance_queue,
    classify_health_status,
    export_queue_to_csv,
    get_alert_rationale,
    get_maintenance_priority,
    get_recommended_action,
)
from aircraft_pm.yafa_ui import (
    YAFA_TOKENS,
    get_lucide_svg,
    render_yafa_brand_mark,
    render_yafa_callout,
    render_yafa_kpi_card,
    render_yafa_page_header,
    render_yafa_status_dot,
)

# -------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="AeroGuard | Fleet Prognostics",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# YAFA-UI MATPLOTLIB & SEABORN PLOT STYLING
# -------------------------------------------------------------
def apply_yafa_plot_style():
    """Apply Yafa-UI analytical instrument styling to Matplotlib and Seaborn."""
    plt.style.use("default")
    plt.rcParams.update({
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#ffffff",
        "axes.edgecolor": "#dadce0",
        "axes.labelcolor": "#3c4043",
        "axes.titlecolor": "#202124",
        "xtick.color": "#5f6368",
        "ytick.color": "#5f6368",
        "grid.color": "#e8eef6",
        "grid.alpha": 0.8,
        "grid.linestyle": "--",
        "legend.facecolor": "#ffffff",
        "legend.edgecolor": "#dadce0",
        "legend.labelcolor": "#202124",
        "text.color": "#202124",
        "font.family": "sans-serif",
    })

apply_yafa_plot_style()

# -------------------------------------------------------------
# YAFA-UI DESIGN SYSTEM CSS INJECTION
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Body and Canvas */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .stApp {
        background-color: #f8fafd;
        color: #202124;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dadce0;
        box-shadow: none;
    }

    /* White Analytical Cards */
    .yafa-card {
        background: #ffffff;
        border: 1px solid #dadce0;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    .yafa-card-title {
        font-size: 14px;
        font-weight: 600;
        color: #202124;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Rectangular Anti-Bubble Controls */
    button, input, select {
        border-radius: 6px !important;
    }
    button[kind="primary"], .stDownloadButton button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: 1px solid #1d4ed8 !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        border-radius: 6px !important;
        height: 38px !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2) !important;
    }
    button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #3c4043 !important;
        border: 1px solid #dadce0 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border-radius: 6px !important;
    }

    /* Navigation Radio Items with 3px Left Accent */
    div[data-testid="stRadio"] > div {
        gap: 4px;
    }
    div[data-testid="stRadio"] label {
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13.5px;
        font-weight: 500;
        color: #3c4043;
        transition: all 0.15s ease;
    }
    div[data-testid="stRadio"] label:hover {
        background-color: #f1f5f9;
        color: #0f172a;
    }

    /* Dataframe Container */
    div[data-testid="stDataFrame"] {
        border: 1px solid #dadce0;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# DATA & MODEL LOADERS
# -------------------------------------------------------------
@st.cache_data
def load_all_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """Cache and load training data, test trajectories, test ground truth, and model registry."""
    train_df, _ = load_train_data()
    test_df, test_last, _ = load_test_data()

    registry_path = MODELS_DIR / "model_registry.json"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {}

    return train_df, test_df, test_last, registry


@st.cache_resource
def load_production_model():
    """Load serialized production preprocessor and model."""
    prep_path = MODELS_DIR / "preprocessor.joblib"
    model_path = MODELS_DIR / "best_model.joblib"

    if prep_path.exists() and model_path.exists():
        preprocessor = joblib.load(prep_path)
        model = joblib.load(model_path)
        return preprocessor, model
    return None, None


train_df, test_df, test_last, registry = load_all_data()
preprocessor, prod_model = load_production_model()


@st.cache_data
def get_fleet_predictions():
    """Generate and cache fleet-wide RUL predictions on the official test set."""
    if preprocessor is None or prod_model is None:
        return None, None
    X_test_scaled, test_feat = preprocessor.transform(test_df)
    preds = prod_model.predict(X_test_scaled)
    # Clip training policy ceiling (125 cycles)
    preds = np.clip(preds, 0, 125)
    test_feat = test_feat.copy()
    test_feat["pred_rul"] = preds

    # Final observed cycle per test engine
    fleet_summary = test_feat.groupby("engine_id").last().reset_index()
    # Merge with ground truth
    fleet_summary = pd.merge(
        fleet_summary,
        test_last[["engine_id", "rul"]].rename(columns={"rul": "true_rul"}),
        on="engine_id",
    )
    return test_feat, fleet_summary


test_feat, fleet_summary = get_fleet_predictions()

# -------------------------------------------------------------
# SIDEBAR SHELL (YAFA-UI SPECIFICATION)
# -------------------------------------------------------------
with st.sidebar:
    # Terse Sidebar Header: Yafa-UI mark + Product Name
    mark_svg = render_yafa_brand_mark(26)
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; padding: 12px 0 16px 0;
                    border-bottom: 1px solid #dadce0; margin-bottom: 18px;">
            {mark_svg}
            <div>
                <div style="font-size: 17px; font-weight: 800; color: #202124; letter-spacing: -0.01em; line-height: 1.1;">
                    Aero<span style="color: #2563eb;">Guard</span>
                </div>
                <div style="font-size: 11px; font-weight: 600; color: #5f6368; text-transform: uppercase; letter-spacing: 0.06em;">
                    Turbofan Prognostics
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Registered Destination Routes
    page = st.radio(
        "Navigation",
        [
            "Overview · Fleet Command",
            "Twin · Engine Explorer",
            "Sensors · Diagnostics",
            "Models · Benchmarks",
            "Operations · Review Queue",
            "Inference · Prognostic Lab",
        ],
        index=0,
    )

    st.markdown('<div style="border-bottom: 1px solid #e8eaed; margin: 18px 0 14px 0;"></div>', unsafe_allow_html=True)

    # Operational Lenses in Sidebar
    st.markdown(
        """
        <div style="font-size: 11.5px; font-weight: 700; text-transform: uppercase;
                    letter-spacing: 0.06em; color: #5f6368; margin-bottom: 10px;">
            Advisory Lenses
        </div>
        """,
        unsafe_allow_html=True,
    )

    crit_threshold = st.slider(
        "Critical Cutoff (Cycles)",
        min_value=10,
        max_value=40,
        value=HEALTH_CRITICAL,
        step=5,
        help="Engines with predicted RUL at or below this value are flagged for P1 depot overhaul.",
    )

    adv_threshold = st.slider(
        "Advisory Cutoff (Cycles)",
        min_value=30,
        max_value=80,
        value=HEALTH_WARNING,
        step=5,
        help="Engines with predicted RUL between critical and this cutoff are flagged for P2 line maintenance.",
    )

    st.markdown('<div style="border-bottom: 1px solid #e8eaed; margin: 18px 0 14px 0;"></div>', unsafe_allow_html=True)

    # Scope Metadata (Single-Context)
    st.markdown(
        """
        <div style="font-size: 11.5px; color: #5f6368; line-height: 1.55;">
            <div style="font-weight: 700; color: #3c4043; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.04em;">
                Context Scope
            </div>
            • <b>Benchmark</b>: NASA C-MAPSS FD001<br>
            • <b>Spool</b>: Sea-Level Commercial HPC<br>
            • <b>Fleet Scope</b>: 100 Active Turbofans<br>
            • <b>Selected Model</b>: HistGradientBoosting<br>
            • <b>Official Test RMSE</b>: 13.90 cycles
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================
# ROUTE 1: FLEET COMMAND CENTER (CYAN ROUTE ACCENT)
# =============================================================
if page == "Overview · Fleet Command":
    # 1. Page Header (Yafa-UI Identity Bar)
    st.markdown(
        render_yafa_page_header(
            title="Fleet Command Center",
            subtitle="Global prognostic health monitoring and Remaining Useful Life distribution across 100 commercial turbofans",
            route_family="cyan",
            icon_name="layout-dashboard",
            badge_label="NASA C-MAPSS FD001",
        ),
        unsafe_allow_html=True,
    )

    # Disclaimer Callout Box (Yafa-UI Pale Tint + 4px Accent Rule)
    st.markdown(
        render_yafa_callout(
            text="<b>PROGNOSTIC DECISION-SUPPORT NOTICE:</b> Fleet telemetry displayed reflects historical NASA C-MAPSS FD001 benchmark "
            "simulations (sea-level, high-pressure compressor degradation). Predictions are algorithmic prognostic estimates for maintenance staging "
            "and do not constitute certified flight dispatch authority.",
            callout_type="info",
            title="Operational Context",
        ),
        unsafe_allow_html=True,
    )

    if fleet_summary is not None:
        current_queue = build_maintenance_queue(
            fleet_summary,
            critical_threshold=crit_threshold,
            warning_threshold=adv_threshold,
        )

        total_engines = len(current_queue)
        crit_count = (current_queue["health_status"] == "Critical").sum()
        adv_count = (current_queue["health_status"] == "Advisory").sum()
        healthy_count = (current_queue["health_status"] == "Healthy").sum()
        avg_rul = current_queue["pred_rul"].mean()
        min_rul = current_queue["pred_rul"].min()

        # 2. Multi-Color KPI Strip (Order: Cyan, Blue, Green, Violet, Amber)
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(
                render_yafa_kpi_card(
                    title="Monitored Fleet",
                    value=f"{total_engines}",
                    accent_family="cyan",
                    tooltip_desc="Total active commercial turbofan units logged in fleet telemetry",
                    delta_text="100% active coverage",
                    delta_type="neutral",
                ),
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                render_yafa_kpi_card(
                    title="Fleet Mean RUL",
                    value=f"{avg_rul:.1f}",
                    accent_family="blue",
                    tooltip_desc="Average expected remaining cycles across all active monitored engines",
                    delta_text=f"Min: {min_rul:.1f} cycles",
                    delta_type="neutral",
                ),
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                render_yafa_kpi_card(
                    title="Healthy Fleet",
                    value=f"{healthy_count}",
                    accent_family="green",
                    tooltip_desc="Engines with predicted RUL strictly exceeding the advisory threshold",
                    delta_text=f"> {adv_threshold} cycles",
                    delta_type="success",
                ),
                unsafe_allow_html=True,
            )
        with k4:
            st.markdown(
                render_yafa_kpi_card(
                    title="Advisory Queue",
                    value=f"{adv_count}",
                    accent_family="violet",
                    tooltip_desc="Engines requiring P2 line inspection within the advisory window",
                    delta_text=f"{crit_threshold} - {adv_threshold} c",
                    delta_type="warning",
                ),
                unsafe_allow_html=True,
            )
        with k5:
            st.markdown(
                render_yafa_kpi_card(
                    title="Critical Alerts",
                    value=f"{crit_count}",
                    accent_family="amber",
                    tooltip_desc="Engines at or below critical threshold requiring immediate P1 depot scheduling",
                    delta_text=f"≤ {crit_threshold} cycles",
                    delta_type="danger",
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 3. Primary Analytical Charts (Yafa-UI Light Analytical Instrument)
        c_left, c_right = st.columns([1.6, 1.0])

        with c_left:
            st.markdown(
                """
                <div class="yafa-card">
                    <div class="yafa-card-title">Fleet Remaining Useful Life Distribution (Cycles)</div>
                """,
                unsafe_allow_html=True,
            )
            fig, ax = plt.subplots(figsize=(7.5, 3.8))
            palette = {"Healthy": "#059669", "Advisory": "#d97706", "Critical": "#dc2626"}
            sns.histplot(
                data=current_queue,
                x="pred_rul",
                hue="health_status",
                palette=palette,
                bins=20,
                kde=True,
                ax=ax,
                edgecolor="#dadce0",
                alpha=0.85,
            )
            ax.axvline(
                crit_threshold,
                color="#dc2626",
                linestyle="--",
                linewidth=1.8,
                label=f"Critical Threshold (≤ {crit_threshold} c)",
            )
            ax.axvline(
                adv_threshold,
                color="#d97706",
                linestyle=":",
                linewidth=1.8,
                label=f"Advisory Threshold (≤ {adv_threshold} c)",
            )
            ax.set_xlabel("Predicted Remaining Useful Life (Cycles)", fontsize=9.5, color="#3c4043")
            ax.set_ylabel("Engine Count", fontsize=9.5, color="#3c4043")
            ax.legend(framealpha=0.9, fontsize=8.5)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_right:
            st.markdown(
                """
                <div class="yafa-card">
                    <div class="yafa-card-title">Fleet Operational Readiness</div>
                """,
                unsafe_allow_html=True,
            )
            fig_pie, ax_pie = plt.subplots(figsize=(4.8, 3.8))
            sizes = [healthy_count, adv_count, crit_count]
            labels = [
                f"Healthy (> {adv_threshold} c)",
                f"Advisory ({crit_threshold}-{adv_threshold} c)",
                f"Critical (≤ {crit_threshold} c)",
            ]
            colors = ["#86efac", "#fbbf24", "#f87171"]

            wedges, texts, autotexts = ax_pie.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=140,
                pctdistance=0.72,
                wedgeprops=dict(width=0.48, edgecolor="#ffffff", linewidth=2),
            )
            for t in texts:
                t.set_color("#3c4043")
                t.set_fontsize(8.5)
            for at in autotexts:
                at.set_color("#202124")
                at.set_fontweight("bold")
                at.set_fontsize(9)
            ax_pie.axis("equal")
            plt.tight_layout()
            st.pyplot(fig_pie)
            plt.close(fig_pie)
            st.markdown("</div>", unsafe_allow_html=True)

        # 4. Dense Evidence Table: Top 10 Priority Units
        st.markdown(
            """
            <div class="yafa-card">
                <div class="yafa-card-title">Priority Triage Queue · Top 10 Units Nearest Operational Limit</div>
                <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                    Sorted by lowest predicted RUL. Statuses rendered strictly with 6px semantic dots without capsule pills.
                </div>
            """,
            unsafe_allow_html=True,
        )

        top_critical = current_queue.head(10)[
            ["engine_id", "cycle", "pred_rul", "true_rul", "prediction_error", "health_status", "priority", "action_recommendation"]
        ].copy()
        top_critical.columns = [
            "Engine ID",
            "Current Cycle",
            "Predicted RUL (c)",
            "Ground Truth (c)",
            "Residual (c)",
            "Health Status",
            "Priority Tier",
            "Recommended Maintenance Action",
        ]

        def format_status_text(val):
            if val == "Critical":
                return "color: #dc2626; font-weight: 600;"
            elif val == "Advisory":
                return "color: #d97706; font-weight: 600;"
            return "color: #059669; font-weight: 600;"

        styler = top_critical.style
        if hasattr(styler, "map"):
            styler = styler.map(format_status_text, subset=["Health Status"])
        else:
            styler = styler.applymap(format_status_text, subset=["Health Status"])

        st.dataframe(
            styler.format({
                "Predicted RUL (c)": "{:.1f}",
                "Ground Truth (c)": "{:.1f}",
                "Residual (c)": "{:+.1f}",
            }),
            width="stretch",
            height=380,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# ROUTE 2: ENGINE DIGITAL TWIN (BLUE ROUTE ACCENT)
# =============================================================
elif page == "Twin · Engine Explorer":
    st.markdown(
        render_yafa_page_header(
            title="Engine Digital Twin & Degradation Explorer",
            subtitle="Cycle-by-cycle telemetry inspection, observed cutoff timelines, and multi-sensor degradation curves",
            route_family="blue",
            icon_name="activity",
            badge_label="Digital Twin",
        ),
        unsafe_allow_html=True,
    )

    fleet_choice = st.radio(
        "Fleet Scope:",
        ["Official Test Fleet (Active Cutoff Trajectories)", "Training Fleet (Run-to-Failure Historical Baselines)"],
        horizontal=True,
    )

    if fleet_choice.startswith("Official"):
        selected_engine = st.selectbox("Select Active Test Engine ID:", sorted(test_df["engine_id"].unique()), index=0)
        eng_data = test_df[test_df["engine_id"] == selected_engine].copy()
        last_rec = fleet_summary[fleet_summary["engine_id"] == selected_engine].iloc[0]
        curr_cycle = int(eng_data["cycle"].max())
        pred_rul = float(last_rec["pred_rul"])
        true_rul = float(last_rec["true_rul"])
        health_status = classify_health_status(pred_rul, crit_threshold, adv_threshold)
        is_test_unit = True
    else:
        selected_engine = st.selectbox("Select Training Engine ID:", sorted(train_df["engine_id"].unique()), index=0)
        eng_data = train_df[train_df["engine_id"] == selected_engine].copy()
        curr_cycle = int(eng_data["cycle"].max())
        pred_rul = 0.0
        true_rul = 0.0
        health_status = "Critical (Reached Functional Limit)"
        is_test_unit = False

    # KPI Strip for Inspected Engine
    e1, e2, e3, e4, e5 = st.columns(5)
    with e1:
        st.markdown(
            render_yafa_kpi_card(
                title="Engine Unit",
                value=f"#{selected_engine}",
                accent_family="cyan",
                tooltip_desc="Specific commercial turbofan unit under inspection",
                delta_text="Active In-Service" if is_test_unit else "Historical Run-to-Failure",
                delta_type="neutral",
            ),
            unsafe_allow_html=True,
        )
    with e2:
        st.markdown(
            render_yafa_kpi_card(
                title="Observed Cycles",
                value=f"{curr_cycle}",
                accent_family="blue",
                tooltip_desc="Operating flight cycles logged prior to telemetry cutoff",
                delta_text="Data Cutoff Point",
                delta_type="neutral",
            ),
            unsafe_allow_html=True,
        )
    with e3:
        st.markdown(
            render_yafa_kpi_card(
                title="Predicted RUL",
                value=f"{pred_rul:.1f}",
                accent_family="green",
                tooltip_desc="Model-predicted remaining cycles until functional end-of-life",
                delta_text=f"{health_status}",
                delta_type="danger" if pred_rul <= crit_threshold else "warning" if pred_rul <= adv_threshold else "success",
            ),
            unsafe_allow_html=True,
        )
    with e4:
        st.markdown(
            render_yafa_kpi_card(
                title="Ground Truth RUL",
                value=f"{true_rul:.1f}",
                accent_family="violet",
                tooltip_desc="Official NASA benchmark remaining life from RUL_FD001.txt",
                delta_text=f"{pred_rul - true_rul:+.1f} cycles error",
                delta_type="success" if abs(pred_rul - true_rul) <= 10 else "danger",
            ),
            unsafe_allow_html=True,
        )
    with e5:
        # Anti-capsule status card
        st.markdown(
            f"""
            <div style="background: #ffffff; border: 1px solid #dadce0; border-top: 3px solid #fbbf24;
                        border-radius: 8px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); min-height: 120px;">
                <div style="font-size: 13.5px; font-weight: 600; color: #3c4043; border-bottom: 1px dotted #8792a2;">
                    Decision Tier
                </div>
                <div style="border-bottom: 1px solid #e8eaed; margin: 10px 0 14px 0;"></div>
                <div style="padding-top: 4px;">
                    {render_yafa_status_dot(health_status if is_test_unit else 'Critical')}
                </div>
                <div style="font-size: 11.5px; color: #5f6368; margin-top: 8px;">
                    Advisory Category
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Cutoff Callout
    if is_test_unit:
        st.markdown(
            render_yafa_callout(
                text=f"<b>OBSERVATION CUTOFF EXPLANATION:</b> Engine #{selected_engine} telemetry is logged up to <b>Cycle {curr_cycle}</b>. "
                f"In this operational test regime, functional failure has <b>not yet occurred</b>; true remaining life is {true_rul:.0f} cycles "
                f"(total lifespan = {curr_cycle + true_rul:.0f} cycles). AeroGuard predicts <b>{pred_rul:.1f} cycles</b> remaining. "
                f"Future cycles are estimated algorithmically; no synthetic or fabricated future readings are rendered.",
                callout_type="info",
                title="Telemetry Boundary",
            ),
            unsafe_allow_html=True,
        )

    # Multi-Sensor Degradation Explorer
    st.markdown(
        """
        <div class="yafa-card">
            <div class="yafa-card-title">Multi-Sensor Degradation Trajectories</div>
            <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                Raw telemetry signals (solid cyan) plotted against 5-cycle causal moving averages (dashed rose).
            </div>
        """,
        unsafe_allow_html=True,
    )

    selected_sensors = st.multiselect(
        "Select Telemetry Channels to Visualize:",
        INFORMATIVE_SENSOR_COLS,
        default=["sensor_2", "sensor_3", "sensor_4", "sensor_11", "sensor_12", "sensor_15"],
    )

    if selected_sensors:
        n_plots = len(selected_sensors)
        cols_per_row = 2
        rows = (n_plots + 1) // cols_per_row
        fig, axes = plt.subplots(rows, cols_per_row, figsize=(13.5, 3.2 * rows), sharex=True)
        if rows == 1 and cols_per_row == 1:
            axes = np.array([axes])
        axes = np.array(axes).flatten()

        for idx, s in enumerate(selected_sensors):
            ax = axes[idx]
            desc = SENSOR_DESCRIPTIONS.get(s, {}).get("name", s)
            unit = SENSOR_DESCRIPTIONS.get(s, {}).get("unit", "-")

            ax.plot(eng_data["cycle"], eng_data[s], color="#0891b2", linewidth=1.5, label="Raw Sensor Signal", alpha=0.85)
            smooth = eng_data[s].rolling(window=5, min_periods=1).mean()
            ax.plot(eng_data["cycle"], smooth, color="#db2777", linestyle="--", linewidth=1.6, label="5-Cycle Moving Avg")

            ax.set_title(f"{desc} [{s}]", fontsize=10, fontweight="bold", color="#202124", pad=6)
            ax.set_ylabel(f"Magnitude ({unit})", fontsize=8.5, color="#3c4043")
            ax.set_xlabel("Operational Flight Cycle", fontsize=8.5, color="#3c4043")
            ax.legend(loc="upper left", fontsize=8, framealpha=0.9)

        for j in range(idx + 1, len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("🔬 View Observed Telemetry Records"):
        st.dataframe(eng_data.tail(25), width="stretch")


# =============================================================
# ROUTE 3: SENSOR INTELLIGENCE (GREEN ROUTE ACCENT)
# =============================================================
elif page == "Sensors · Diagnostics":
    st.markdown(
        render_yafa_page_header(
            title="Sensor Intelligence & Physical Diagnostics",
            subtitle="Variance analysis, physics-informed feature pruning, and lifetime degradation trends for NASA C-MAPSS FD001",
            route_family="green",
            icon_name="radio",
            badge_label="Physics Diagnostics",
        ),
        unsafe_allow_html=True,
    )

    tab_pruning, tab_trajectories, tab_correlations = st.tabs([
        "🔬 Variance Profile & Feature Pruning",
        "📈 Normalized Lifetime Trajectories",
        "🔗 Correlation Heatmap & Coupling",
    ])

    with tab_pruning:
        st.markdown(
            """
            <div class="yafa-card">
                <div class="yafa-card-title">Physical Sensor Mapping & Invariant Feature Pruning</div>
                <div style="font-size: 13px; color: #3c4043; line-height: 1.5; margin-bottom: 14px;">
                    In <b>FD001</b> (sea-level ambient conditions, single HPC degradation mode), several sensor channels operate at fixed boundary conditions 
                    and exhibit <b>zero or near-zero variance across all 20,631 operational cycles</b>. 
                    Pruning these <b>7 invariant features</b> eliminates rank deficiency in linear models and spurious splits in tree ensembles.
                </div>
            """,
            unsafe_allow_html=True,
        )

        sensor_rows = []
        for s, meta in SENSOR_DESCRIPTIONS.items():
            is_const = s in CONSTANT_OR_LOW_VARIANCE_COLS
            sensor_rows.append({
                "Telemetry Channel": s,
                "Subsystem / Parameter": meta["name"],
                "Engineering Unit": meta["unit"],
                "Physical Description": meta["desc"],
                "Variance Status": "Pruned (Constant / Zero Variance)" if is_const else "Informative Degradation Signal",
            })

        df_sensors = pd.DataFrame(sensor_rows)

        def highlight_pruned(val):
            if "Pruned" in val:
                return "color: #5f6368; font-style: italic;"
            return "color: #059669; font-weight: 600;"

        styler_s = df_sensors.style
        if hasattr(styler_s, "map"):
            styler_s = styler_s.map(highlight_pruned, subset=["Variance Status"])
        else:
            styler_s = styler_s.applymap(highlight_pruned, subset=["Variance Status"])

        st.dataframe(styler_s, width="stretch", height=420)

        var_fig_path = FIGURES_DIR / "sensor_variance_profile.png"
        if var_fig_path.exists():
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
            st.image(str(var_fig_path), caption="Log-scale standard deviations across training trajectories", width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_trajectories:
        st.markdown(
            """
            <div class="yafa-card">
                <div class="yafa-card-title">Degradation Trends Across Normalized Engine Lifetime</div>
                <div style="font-size: 13px; color: #3c4043; line-height: 1.5; margin-bottom: 14px;">
                    This analysis maps operational flight cycles to a normalized lifetime percentage (0% = Initial Deployment, 100% = Functional Failure).
                    Notice the steep upward drift in HPC Outlet Temperature (T30) and Static Pressure (Ps30), contrasted against the downward drop in Core Speed (NRc)
                    as compressor blade tip clearances widen.
                </div>
            """,
            unsafe_allow_html=True,
        )
        traj_fig_path = FIGURES_DIR / "sensor_degradation_trajectories.png"
        if traj_fig_path.exists():
            st.image(str(traj_fig_path), caption="Sensor Degradation Trajectories Across Normalized Lifetime (0% to 100%)", width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_correlations:
        st.markdown(
            """
            <div class="yafa-card">
                <div class="yafa-card-title">Spearman Rank Correlation with Remaining Useful Life</div>
                <div style="font-size: 13px; color: #3c4043; line-height: 1.5; margin-bottom: 14px;">
                    Rank correlations capture non-linear monotonic relationships between sensor degradation signals and RUL.
                    Sensors with high absolute rank correlation serve as the primary predictive drivers in our gradient-boosted ensemble.
                </div>
            """,
            unsafe_allow_html=True,
        )
        corr_fig_path = FIGURES_DIR / "sensor_correlations.png"
        if corr_fig_path.exists():
            st.image(str(corr_fig_path), caption="Spearman Rank Correlation Heatmap (Sensors vs Remaining Useful Life)", width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# ROUTE 4: MODEL INTELLIGENCE (VIOLET ROUTE ACCENT)
# =============================================================
elif page == "Models · Benchmarks":
    st.markdown(
        render_yafa_page_header(
            title="Model Intelligence & Evaluation Benchmarks",
            subtitle="Machine learning benchmarks comparing baseline, regularized linear, and ensemble models across four evaluation regimes",
            route_family="violet",
            icon_name="layers",
            badge_label="ML Benchmarks",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        render_yafa_callout(
            text="<b>METHODOLOGY INTEGRITY POLICY:</b> All performance metrics displayed below are read directly from <code>models/model_registry.json</code>. "
            "Cross-validation designs (GroupKFold by engine) strictly isolate training and validation engines without data leakage. "
            "<b>Official test set labels are used exclusively for held-out benchmark scoring</b>; they are never snooped during model training or cross-validation.",
            callout_type="info",
            title="Evaluation Protocol",
        ),
        unsafe_allow_html=True,
    )

    if registry:
        cv_regime = st.radio(
            "Evaluation Regime:",
            [
                "1. Official Held-Out Test Set (100 Unseen Test Engines at Final Cutoff)",
                "2. In-Service Cutoff Cross-Validation (Simulated Operational Inspections, 5-Fold)",
                "3. Full-Trajectory Cross-Validation (All 20,631 Engine Cycles, 5-Fold)",
                "4. Terminal Failure-Point Cross-Validation (Run-to-Failure Endpoint, 5-Fold)",
            ],
            index=0,
        )

        test_data = registry.get("official_test", {})
        cv_data = registry.get("cross_validation", {})

        st.markdown('<div class="yafa-card">', unsafe_allow_html=True)

        if cv_regime.startswith("1."):
            st.markdown(
                """
                <div class="yafa-card-title">Primary Benchmark: Official FD001 Held-Out Test Set</div>
                <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                    Evaluated strictly at the final logged cycle of each of the 100 official test engines using NASA ground-truth RUL_FD001.txt.
                </div>
                """,
                unsafe_allow_html=True,
            )
            test_rows = []
            for m_name, metrics in test_data.items():
                test_rows.append({
                    "Model Architecture": m_name,
                    "Official Test RMSE": f"{metrics.get('test_rmse_official', 0):.2f}",
                    "Clipped Test RMSE (≤125)": f"{metrics.get('test_rmse_clipped', 0):.2f}",
                    "Official Test MAE": f"{metrics.get('test_mae_official', 0):.2f}",
                    "Official Test R²": f"{metrics.get('test_r2_official', 0):.3f}",
                    "NASA PHM Total Score": f"{metrics.get('test_nasa_score_official', 0):.1f}",
                    "NASA Score / Engine": f"{metrics.get('test_nasa_score_official_per_engine', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(test_rows), width="stretch")

        elif cv_regime.startswith("2."):
            st.markdown(
                """
                <div class="yafa-card-title">In-Service Cutoff 5-Fold Cross-Validation</div>
                <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                    Evaluated by sampling an inspection cutoff uniformly between 40% and 85% of engine max cycle.
                </div>
                """,
                unsafe_allow_html=True,
            )
            cutoff_rows = []
            for m_name, cv_sub in cv_data.items():
                m = cv_sub.get("in_service_cutoff", {})
                cutoff_rows.append({
                    "Model Architecture": m_name,
                    "Cutoff CV RMSE": f"{m.get('rmse_mean', 0):.2f} ± {m.get('rmse_std', 0):.2f}",
                    "Cutoff CV MAE": f"{m.get('mae_mean', 0):.2f} ± {m.get('mae_std', 0):.2f}",
                    "Cutoff CV R²": f"{m.get('r2_mean', 0):.3f} ± {m.get('r2_std', 0):.3f}",
                    "NASA Score / Engine": f"{m.get('nasa_score_per_engine_mean', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(cutoff_rows), width="stretch")

        elif cv_regime.startswith("3."):
            st.markdown(
                """
                <div class="yafa-card-title">Full-Trajectory 5-Fold Cross-Validation</div>
                <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                    Evaluated across all 20,631 cycles of the training engines using 5-Fold GroupKFold (target clipped at 125 cycles).
                </div>
                """,
                unsafe_allow_html=True,
            )
            ft_rows = []
            for m_name, cv_sub in cv_data.items():
                m = cv_sub.get("full_trajectory", {})
                ft_rows.append({
                    "Model Architecture": m_name,
                    "Full-Trajectory CV RMSE": f"{m.get('rmse_mean', 0):.2f} ± {m.get('rmse_std', 0):.2f}",
                    "Full-Trajectory CV MAE": f"{m.get('mae_mean', 0):.2f} ± {m.get('mae_std', 0):.2f}",
                    "Full-Trajectory CV R²": f"{m.get('r2_mean', 0):.3f} ± {m.get('r2_std', 0):.3f}",
                    "NASA Score / Sample": f"{m.get('nasa_score_per_sample_mean', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(ft_rows), width="stretch")

        else:
            st.markdown(
                """
                <div class="yafa-card-title">Terminal Failure-Point 5-Fold Cross-Validation</div>
                <div style="font-size: 13px; color: #5f6368; margin-bottom: 12px;">
                    Evaluated strictly at the final failure cycle of run-to-failure engines (RUL = 0).
                </div>
                """,
                unsafe_allow_html=True,
            )
            fp_rows = []
            for m_name, cv_sub in cv_data.items():
                m = cv_sub.get("failure_point", {})
                fp_rows.append({
                    "Model Architecture": m_name,
                    "Terminal CV RMSE": f"{m.get('rmse_mean', 0):.2f} ± {m.get('rmse_std', 0):.2f}",
                    "Terminal CV MAE": f"{m.get('mae_mean', 0):.2f} ± {m.get('mae_std', 0):.2f}",
                    "NASA Score / Engine": f"{m.get('nasa_score_per_engine_mean', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(fp_rows), width="stretch")

        st.markdown("</div>", unsafe_allow_html=True)

        # Visual Diagnostics
        c1, c2 = st.columns(2)
        with c1:
            pred_fig = FIGURES_DIR / "model_test_predictions.png"
            if pred_fig.exists():
                st.markdown(
                    """
                    <div class="yafa-card">
                        <div class="yafa-card-title">Predicted vs True RUL (Safe vs Late Risk Zones)</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.image(str(pred_fig), width="stretch")
                st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            res_fig = FIGURES_DIR / "model_residuals.png"
            if res_fig.exists():
                st.markdown(
                    """
                    <div class="yafa-card">
                        <div class="yafa-card-title">Residual Error Distribution on Held-Out Test Set</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.image(str(res_fig), width="stretch")
                st.markdown("</div>", unsafe_allow_html=True)

        fi_fig = FIGURES_DIR / "feature_importances.png"
        if fi_fig.exists():
            st.markdown(
                """
                <div class="yafa-card">
                    <div class="yafa-card-title">Top 20 Degradation Feature Importances (Random Forest Gini Impurity)</div>
                """,
                unsafe_allow_html=True,
            )
            st.image(str(fi_fig), width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# ROUTE 5: MAINTENANCE OPERATIONS (AMBER ROUTE ACCENT)
# =============================================================
elif page == "Operations · Review Queue":
    st.markdown(
        render_yafa_page_header(
            title="Maintenance Operations & Review Queue",
            subtitle="Configurable advisory prioritization, actionable engineering recommendations, and exportable worklists",
            route_family="amber",
            icon_name="wrench",
            badge_label="Worklist Triage",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        render_yafa_callout(
            text="<b>AIRWORTHINESS COMPLIANCE DISCLAIMER:</b> Automated maintenance advisories generated by AeroGuard provide algorithmic "
            "decision-support triage. They do not supersede certified Maintenance Planning Documents (MPD), OEM Engine Manuals (EMM), "
            "or regulatory airworthiness release protocols.",
            callout_type="warning",
            title="Operational Mandate",
        ),
        unsafe_allow_html=True,
    )

    if fleet_summary is not None:
        f_col1, f_col2, f_col3 = st.columns([1.2, 1.4, 1.4])
        with f_col1:
            status_filter = st.selectbox(
                "Filter Queue Severity:",
                ["All", "Critical", "Advisory", "Healthy"],
                index=0,
            )
        with f_col2:
            st.markdown(
                f"""
                <div style="padding-top: 26px; font-size: 13px; color: #5f6368;">
                    Thresholds: <span style="color:#dc2626; font-weight:700;">Critical ≤ {crit_threshold} c</span> | 
                    <span style="color:#d97706; font-weight:700;">Advisory ≤ {adv_threshold} c</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f_col3:
            active_queue = build_maintenance_queue(
                fleet_summary,
                critical_threshold=crit_threshold,
                warning_threshold=adv_threshold,
                filter_status=status_filter,
            )
            csv_data = export_queue_to_csv(active_queue)
            st.markdown('<div style="padding-top: 18px;">', unsafe_allow_html=True)
            st.download_button(
                label="📥 Export Work Queue to CSV",
                data=csv_data,
                file_name=f"aeroguard_maintenance_queue_{status_filter.lower()}.csv",
                mime="text/csv",
                help="Download prioritized schedule for dispatch and depot staging.",
            )
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="yafa-card">
                <div class="yafa-card-title">Prioritized Maintenance Schedule ({len(active_queue)} Units)</div>
            """,
            unsafe_allow_html=True,
        )

        display_queue = active_queue[
            [
                "engine_id",
                "cycle",
                "pred_rul",
                "priority",
                "health_status",
                "action_recommendation",
                "rationale",
                "true_rul",
                "prediction_error",
            ]
        ].copy()
        display_queue.columns = [
            "Engine ID",
            "Current Cycle",
            "Predicted RUL (c)",
            "Priority Code",
            "Health Tier",
            "Recommended Maintenance Action",
            "Technical Alert Rationale",
            "Ground Truth (c)",
            "Residual (c)",
        ]

        def highlight_priority_col(val):
            if "P1" in val:
                return "color: #dc2626; font-weight: 700;"
            elif "P2" in val:
                return "color: #d97706; font-weight: 700;"
            return "color: #059669; font-weight: 600;"

        styler_q = display_queue.style
        if hasattr(styler_q, "map"):
            styler_q = styler_q.map(highlight_priority_col, subset=["Priority Code"])
        else:
            styler_q = styler_q.applymap(highlight_priority_col, subset=["Priority Code"])

        st.dataframe(
            styler_q.format({
                "Predicted RUL (c)": "{:.1f}",
                "Ground Truth (c)": "{:.1f}",
                "Residual (c)": "{:+.1f}",
            }),
            width="stretch",
            height=440,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# ROUTE 6: RUL INFERENCE LAB (PINK ROUTE ACCENT)
# =============================================================
elif page == "Inference · Prognostic Lab":
    st.markdown(
        render_yafa_page_header(
            title="Prognostic Inference & Sensitivity Lab",
            subtitle="Interactive simulation, temporal sequence slicing, and Remaining Useful Life prediction on arbitrary operational states",
            route_family="pink",
            icon_name="sliders",
            badge_label="Inference Lab",
        ),
        unsafe_allow_html=True,
    )

    if prod_model is not None and preprocessor is not None:
        st.markdown(
            render_yafa_callout(
                text="<b>CAUSAL INFERENCE INTEGRITY:</b> When evaluating a past operational cycle <i>t</i>, AeroGuard computes features strictly "
                "using observations up to <i>t</i> (temporal causality). Zero future lookahead is permitted.",
                callout_type="info",
                title="Causal Guarantee",
            ),
            unsafe_allow_html=True,
        )

        c_eng, c_cyc = st.columns([1, 1])
        with c_eng:
            test_engine_id = st.slider("Select Engine Unit ID:", min_value=1, max_value=100, value=1)

        eng_raw = test_df[test_df["engine_id"] == test_engine_id]
        total_cyc = len(eng_raw)

        with c_cyc:
            cycle_point = st.slider(
                "Select Operational Snapshot Cycle:",
                min_value=1,
                max_value=total_cyc,
                value=total_cyc,
                help=f"Unit #{test_engine_id} logged {total_cyc} cycles prior to cutoff.",
            )

        # Slice sequence causally
        sub_seq = eng_raw[eng_raw["cycle"] <= cycle_point].copy()

        # Run feature pipeline and inference
        X_scaled, feat_df = preprocessor.transform(sub_seq)
        raw_pred = float(prod_model.predict(X_scaled[-1:])[0])
        clipped_pred = float(np.clip(raw_pred, 0, 125))

        # Ground truth
        true_final_rul = float(test_last[test_last["engine_id"] == test_engine_id]["rul"].values[0])
        inferred_true_rul = true_final_rul + (total_cyc - cycle_point)
        pred_error = clipped_pred - inferred_true_rul
        status = classify_health_status(clipped_pred, crit_threshold, adv_threshold)

        # KPI Strip
        inf1, inf2, inf3, inf4, inf5 = st.columns(5)
        with inf1:
            st.markdown(
                render_yafa_kpi_card(
                    title="Snapshot Cycle",
                    value=f"{cycle_point}",
                    accent_family="cyan",
                    tooltip_desc="Current operational cycle evaluated in telemetry sequence",
                    delta_text=f"of {total_cyc} cycles",
                    delta_type="neutral",
                ),
                unsafe_allow_html=True,
            )
        with inf2:
            st.markdown(
                render_yafa_kpi_card(
                    title="Predicted RUL",
                    value=f"{clipped_pred:.1f}",
                    accent_family="blue",
                    tooltip_desc="Production model prediction capped at 125 cycles",
                    delta_text="Capped at 125 c",
                    delta_type="danger" if clipped_pred <= crit_threshold else "warning" if clipped_pred <= adv_threshold else "success",
                ),
                unsafe_allow_html=True,
            )
        with inf3:
            st.markdown(
                render_yafa_kpi_card(
                    title="Raw Model Output",
                    value=f"{raw_pred:.1f}",
                    accent_family="green",
                    tooltip_desc="Unclipped regression prediction before piecewise policy cap",
                    delta_text="Unclipped",
                    delta_type="neutral",
                ),
                unsafe_allow_html=True,
            )
        with inf4:
            st.markdown(
                render_yafa_kpi_card(
                    title="Actual RUL",
                    value=f"{inferred_true_rul:.1f}",
                    accent_family="violet",
                    tooltip_desc="Benchmark ground-truth remaining life at this cycle point",
                    delta_text=f"{pred_error:+.1f} error",
                    delta_type="success" if abs(pred_error) <= 10 else "danger",
                ),
                unsafe_allow_html=True,
            )
        with inf5:
            st.markdown(
                f"""
                <div style="background: #ffffff; border: 1px solid #dadce0; border-top: 3px solid #f9a8d4;
                            border-radius: 8px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); min-height: 120px;">
                    <div style="font-size: 13.5px; font-weight: 600; color: #3c4043; border-bottom: 1px dotted #8792a2;">
                        Prognostic State
                    </div>
                    <div style="border-bottom: 1px solid #e8eaed; margin: 10px 0 14px 0;"></div>
                    <div style="padding-top: 4px;">
                        {render_yafa_status_dot(status)}
                    </div>
                    <div style="font-size: 11.5px; color: #5f6368; margin-top: 8px;">
                        Decision Tier
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Action Guidance Callout
        action = get_recommended_action(clipped_pred, crit_threshold, adv_threshold)
        rationale = get_alert_rationale(clipped_pred, cycle_point, crit_threshold, adv_threshold)

        if status == "Critical":
            st.markdown(
                render_yafa_callout(
                    text=f"<b>P1 CRITICAL ACTION REQUIRED:</b> {action}<br><span style='font-size:12px;'>Rationale: {rationale}</span>",
                    callout_type="danger",
                    title="Maintenance Escalation",
                ),
                unsafe_allow_html=True,
            )
        elif status == "Advisory":
            st.markdown(
                render_yafa_callout(
                    text=f"<b>P2 ADVISORY NOTICE:</b> {action}<br><span style='font-size:12px;'>Rationale: {rationale}</span>",
                    callout_type="warning",
                    title="Maintenance Advisory",
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                render_yafa_callout(
                    text=f"<b>P3 NOMINAL:</b> {action}<br><span style='font-size:12px;'>Rationale: {rationale}</span>",
                    callout_type="success",
                    title="Nominal Condition",
                ),
                unsafe_allow_html=True,
            )

        with st.expander("🔍 Inspect 122 Engineered Causal Features at Selected Cycle"):
            st.dataframe(feat_df.iloc[[-1]], width="stretch")

        with st.expander("📋 View Raw Sensor Telemetry Snapshot at Selected Cycle"):
            st.dataframe(sub_seq.iloc[[-1]], width="stretch")

    else:
        st.error("Production model and preprocessor are not found in models/. Please run training pipeline first.")
