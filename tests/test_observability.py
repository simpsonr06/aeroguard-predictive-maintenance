"""Deterministic tests for structured observability and request metrics in AeroGuard 2.1."""

from fastapi.testclient import TestClient
import pytest

from aircraft_pm.api import app
from aircraft_pm.observability import MetricsCollector, metrics_collector


def test_metrics_collector_recording():
    """Verify metrics collector records counts, status codes, and latencies."""
    collector = MetricsCollector(max_latency_samples=50)

    collector.record_request("/api/health", 200, 5.2)
    collector.record_request("/api/predict", 200, 15.8)
    collector.record_request("/api/predict", 500, 22.4)

    snapshot = collector.get_snapshot()

    assert snapshot["requests_total"] == 3
    assert snapshot["predictions_total"] == 2
    assert snapshot["prediction_failures"] == 1
    assert snapshot["status_codes"]["200"] == 2
    assert snapshot["status_codes"]["500"] == 1
    assert snapshot["error_rate_pct"] == pytest.approx(33.33, 0.1)
    assert snapshot["latency_ms"]["mean"] > 0
    assert snapshot["latency_ms"]["p95"] >= snapshot["latency_ms"]["p50"]


def test_observability_middleware_response_header():
    """FastAPI requests must include X-Response-Time-Ms response header."""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert "X-Response-Time-Ms" in response.headers
        duration_ms = float(response.headers["X-Response-Time-Ms"])
        assert duration_ms >= 0.0


def test_observability_metrics_live_snapshot():
    """Live metrics endpoint reflects requests executed by TestClient."""
    with TestClient(app) as client:
        client.get("/api/health")
        client.get("/api/metrics")

        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "aeroguard-backend"
        assert data["requests_total"] >= 2
        assert "/api/health" in data["requests_by_endpoint"]
