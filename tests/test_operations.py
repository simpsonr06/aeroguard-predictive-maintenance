"""Unit tests for maintenance operations, queue prioritization, and CSV export."""

import pandas as pd
import pytest

from aircraft_pm.operations import (
    build_maintenance_queue,
    classify_health_status,
    export_queue_to_csv,
    get_alert_rationale,
    get_maintenance_priority,
    get_recommended_action,
)


def test_classify_health_status_thresholds():
    """Verify classification under default and custom thresholds."""
    # Defaults: Critical <= 25, Warning <= 50
    assert classify_health_status(10.0) == "Critical"
    assert classify_health_status(25.0) == "Critical"
    assert classify_health_status(25.1) == "Advisory"
    assert classify_health_status(50.0) == "Advisory"
    assert classify_health_status(50.1) == "Healthy"
    assert classify_health_status(120.0) == "Healthy"

    # Custom thresholds: Critical <= 15, Warning <= 40
    assert classify_health_status(20.0, critical_threshold=15, warning_threshold=40) == "Advisory"
    assert classify_health_status(12.0, critical_threshold=15, warning_threshold=40) == "Critical"
    assert classify_health_status(45.0, critical_threshold=15, warning_threshold=40) == "Healthy"


def test_maintenance_priority_and_actions():
    """Verify priority codes and actionable recommendations."""
    assert get_maintenance_priority(10.0) == "P1 - Urgent"
    assert get_maintenance_priority(35.0) == "P2 - Advisory"
    assert get_maintenance_priority(75.0) == "P3 - Nominal"

    assert "borescope" in get_recommended_action(12.0).lower()
    assert "depot" in get_recommended_action(22.0).lower()
    assert "line maintenance" in get_recommended_action(45.0).lower()
    assert "nominal" in get_recommended_action(80.0).lower()


def test_build_maintenance_queue_prioritization():
    """Verify that build_maintenance_queue correctly sorts by urgency and filters."""
    fleet_data = pd.DataFrame(
        {
            "engine_id": [1, 2, 3, 4],
            "cycle": [150, 180, 210, 120],
            "pred_rul": [75.0, 12.0, 32.0, 110.0],
            "true_rul": [80.0, 10.0, 30.0, 105.0],
        }
    )

    # Ascending sort: engine 2 (12.0) -> engine 3 (32.0) -> engine 1 (75.0) -> engine 4 (110.0)
    queue = build_maintenance_queue(fleet_data, critical_threshold=20, warning_threshold=50)
    assert list(queue["engine_id"]) == [2, 3, 1, 4]
    assert queue.iloc[0]["priority"] == "P1 - Urgent"
    assert queue.iloc[1]["priority"] == "P2 - Advisory"
    assert queue.iloc[2]["priority"] == "P3 - Nominal"

    # Status filtering
    crit_only = build_maintenance_queue(fleet_data, critical_threshold=20, warning_threshold=50, filter_status="Critical")
    assert len(crit_only) == 1
    assert crit_only.iloc[0]["engine_id"] == 2


def test_export_queue_to_csv():
    """Verify export to CSV format with sanitized headers."""
    fleet_data = pd.DataFrame(
        {
            "engine_id": [1, 2],
            "cycle": [100, 150],
            "pred_rul": [20.0, 60.0],
            "true_rul": [18.0, 65.0],
        }
    )
    queue = build_maintenance_queue(fleet_data)
    csv_str = export_queue_to_csv(queue)

    assert "Engine_ID,Current_Cycle,Predicted_RUL_Cycles,Health_Status" in csv_str
    assert "P1 - Urgent" in csv_str
    assert "Ground_Truth_RUL_Cycles,Prediction_Error_Cycles" in csv_str
