"""Maintenance operations, risk classification, and decision-support queue logic.

Provides transparent advisory prioritization and CSV export capabilities
without implying certified flight dispatch authority.
"""

from typing import Dict, List, Optional
import pandas as pd

from aircraft_pm.config import HEALTH_CRITICAL, HEALTH_WARNING


def classify_health_status(
    pred_rul: float,
    critical_threshold: float = HEALTH_CRITICAL,
    warning_threshold: float = HEALTH_WARNING,
) -> str:
    """Classify engine prognostic health into explicit operational tiers.

    Args:
        pred_rul: Model predicted Remaining Useful Life in cycles.
        critical_threshold: RUL at or below which an alert is deemed Critical.
        warning_threshold: RUL at or below which an alert is deemed Advisory.

    Returns:
        Status string: 'Critical', 'Advisory', or 'Healthy'.
    """
    if pred_rul <= critical_threshold:
        return "Critical"
    elif pred_rul <= warning_threshold:
        return "Advisory"
    return "Healthy"


def get_maintenance_priority(
    pred_rul: float,
    critical_threshold: float = HEALTH_CRITICAL,
    warning_threshold: float = HEALTH_WARNING,
) -> str:
    """Assign actionable maintenance priority tag based on predicted RUL.

    Args:
        pred_rul: Model predicted Remaining Useful Life in cycles.
        critical_threshold: Threshold for P1 escalation.
        warning_threshold: Threshold for P2 escalation.

    Returns:
        Priority code string (P1 Urgent, P2 Advisory, P3 Nominal).
    """
    if pred_rul <= critical_threshold:
        return "P1 - Urgent"
    elif pred_rul <= warning_threshold:
        return "P2 - Advisory"
    return "P3 - Nominal"


def get_alert_rationale(
    pred_rul: float,
    current_cycle: int,
    critical_threshold: float = HEALTH_CRITICAL,
    warning_threshold: float = HEALTH_WARNING,
) -> str:
    """Generate technical engineering rationale for decision-support review.

    Args:
        pred_rul: Predicted remaining cycles before functional end-of-life.
        current_cycle: Operating cycles logged to date.
        critical_threshold: Critical threshold cutoff.
        warning_threshold: Warning threshold cutoff.

    Returns:
        Concise rationale description string.
    """
    if pred_rul <= 15:
        return f"Severe HPC margin degradation at cycle {current_cycle}; estimated {pred_rul:.0f} cycles to functional limit."
    elif pred_rul <= critical_threshold:
        return f"Predicted RUL ({pred_rul:.0f} cycles) breached critical threshold (≤ {critical_threshold:.0f} c). Requires depot queue."
    elif pred_rul <= warning_threshold:
        return f"Accelerating sensor drift on HPC/LPT channels; {pred_rul:.0f} cycles remaining. Flag for line check."
    return f"Stable telemetry baseline at cycle {current_cycle}; {pred_rul:.0f} cycles buffer exceeds advisory threshold."


def get_recommended_action(
    pred_rul: float,
    critical_threshold: float = HEALTH_CRITICAL,
    warning_threshold: float = HEALTH_WARNING,
) -> str:
    """Provide structured decision-support maintenance recommendation.

    Disclaimer: These are computational recommendations for triage, not certified FAA/EASA airworthiness releases.
    """
    if pred_rul <= 15:
        return "Immediate borescope inspection & grounding for HPC module replacement."
    elif pred_rul <= critical_threshold:
        return "Schedule depot-level overhaul queue within 10 flight cycles."
    elif pred_rul <= warning_threshold:
        return "Perform line maintenance check: inspect bleed enthalpy & oil static pressure."
    return "Nominal operations: retain standard visual turnaround inspection."


def build_maintenance_queue(
    fleet_summary: pd.DataFrame,
    critical_threshold: float = HEALTH_CRITICAL,
    warning_threshold: float = HEALTH_WARNING,
    filter_status: str = "All",
) -> pd.DataFrame:
    """Build prioritized maintenance review queue with configurable thresholds.

    Args:
        fleet_summary: DataFrame with engine_id, cycle, pred_rul, and optionally true_rul.
        critical_threshold: User-selected critical threshold (cycles).
        warning_threshold: User-selected advisory warning threshold (cycles).
        filter_status: 'All', 'Critical', 'Advisory', or 'Healthy'.

    Returns:
        Sorted DataFrame prioritized by urgency (ascending predicted RUL).
    """
    df = fleet_summary.copy()

    df["health_status"] = df["pred_rul"].apply(
        lambda r: classify_health_status(r, critical_threshold, warning_threshold)
    )
    df["priority"] = df["pred_rul"].apply(
        lambda r: get_maintenance_priority(r, critical_threshold, warning_threshold)
    )
    df["action_recommendation"] = df["pred_rul"].apply(
        lambda r: get_recommended_action(r, critical_threshold, warning_threshold)
    )
    df["rationale"] = df.apply(
        lambda row: get_alert_rationale(
            row["pred_rul"], int(row["cycle"]), critical_threshold, warning_threshold
        ),
        axis=1,
    )

    if "true_rul" in df.columns:
        df["prediction_error"] = df["pred_rul"] - df["true_rul"]

    # Filter if requested
    if filter_status != "All":
        df = df[df["health_status"] == filter_status]

    # Prioritize: Critical/P1 first (lowest pred_rul first)
    df = df.sort_values(by=["pred_rul", "engine_id"], ascending=[True, True]).reset_index(drop=True)
    return df


def export_queue_to_csv(queue_df: pd.DataFrame) -> str:
    """Export the prioritized maintenance queue to a clean CSV string for operations download."""
    export_cols = [
        "engine_id",
        "cycle",
        "pred_rul",
        "health_status",
        "priority",
        "action_recommendation",
        "rationale",
    ]
    if "true_rul" in queue_df.columns:
        export_cols.extend(["true_rul", "prediction_error"])

    available_cols = [c for c in export_cols if c in queue_df.columns]
    renamed = {
        "engine_id": "Engine_ID",
        "cycle": "Current_Cycle",
        "pred_rul": "Predicted_RUL_Cycles",
        "health_status": "Health_Status",
        "priority": "Maintenance_Priority",
        "action_recommendation": "Recommended_Action",
        "rationale": "Engineering_Rationale",
        "true_rul": "Ground_Truth_RUL_Cycles",
        "prediction_error": "Prediction_Error_Cycles",
    }
    subset = queue_df[available_cols].rename(columns=renamed)
    return subset.to_csv(index=False)
