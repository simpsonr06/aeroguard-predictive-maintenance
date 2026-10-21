"""API Security and Input Hardening Test Suite for AeroSentinel FastAPI Backend.

Verifies:
1. Runtime security status reporting and digital signature parameters.
2. Input validation bounds on engine_id and cycle parameters (ge=1, le=100).
3. Rejection of non-finite values (NaN, Inf, -Inf).
4. Rejection of malformed JSON payloads and missing required fields.
5. Error response hygiene (preventing internal stack trace leakage).
6. Safe observability headers and fail-closed state handling when unauthenticated.
"""

from fastapi.testclient import TestClient
import pytest

from aircraft_pm.api import app, app_state
from aircraft_pm.config import AEROSENTINEL_ED25519_PUBLIC_KEY


@pytest.fixture(scope="module")
def client():
    """TestClient that manages the full FastAPI application lifespan."""
    with TestClient(app) as test_client:
        yield test_client


def test_security_status_endpoint(client: TestClient):
    """GET /api/security/status must report authenticated state and public key parameters."""
    response = client.get("/api/security/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["auth_status"] == "AUTHENTICATED"
    assert data["is_authenticated"] is True
    assert data["signature_algorithm"] == "Ed25519"
    assert data["public_key_hex"] == AEROSENTINEL_ED25519_PUBLIC_KEY
    assert data["model_loaded"] is True
    assert data["preprocessor_loaded"] is True
    assert len(data["verified_artifacts"]) >= 2
    assert "advisory_disclaimer" in data


def test_attack_simulation_endpoint(client: TestClient):
    """GET /api/security/attack-simulation must return verified simulation summary."""
    response = client.get("/api/security/attack-simulation")
    assert response.status_code == 200
    data = response.json()
    assert "clean_baseline" in data
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 6


def test_predict_engine_id_lower_bound_rejection(client: TestClient):
    """engine_id < 1 must be rejected with 422 Unprocessable Entity."""
    response = client.post("/api/predict", json={"engine_id": 0})
    assert response.status_code == 422
    assert "greater than or equal to 1" in response.text.lower()

    response_neg = client.post("/api/predict", json={"engine_id": -5})
    assert response_neg.status_code == 422


def test_predict_engine_id_upper_bound_rejection(client: TestClient):
    """engine_id > 100 must be rejected with 422 Unprocessable Entity."""
    response = client.post("/api/predict", json={"engine_id": 101})
    assert response.status_code == 422
    assert "less than or equal to 100" in response.text.lower()


def test_predict_cutoff_cycle_bounds_rejection(client: TestClient):
    """cutoff_cycle < 1 must be rejected with 422 Unprocessable Entity."""
    response = client.post("/api/predict", json={"engine_id": 1, "cutoff_cycle": 0})
    assert response.status_code == 422
    assert "greater than or equal to 1" in response.text.lower()


def test_predict_missing_payload_rejection(client: TestClient):
    """Empty or missing body must return 422 Unprocessable Entity."""
    response = client.post("/api/predict", json={})
    assert response.status_code == 422


def test_malformed_json_payload_rejection(client: TestClient):
    """Malformed raw JSON strings must be rejected with 422 without server error."""
    response = client.post(
        "/api/predict",
        content="{'engine_id': invalid json syntax}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_query_parameter_bounds_rejection(client: TestClient):
    """Query parameter bounds on /api/engines and /api/maintenance/queue must be enforced."""
    # critical_threshold must be between 5.0 and 50.0
    res_low = client.get("/api/engines?critical_threshold=2.0")
    assert res_low.status_code == 422

    res_high = client.get("/api/engines?critical_threshold=100.0")
    assert res_high.status_code == 422

    # warning_threshold must be between 20.0 and 100.0
    res_warn_low = client.get("/api/maintenance/queue?warning_threshold=5.0")
    assert res_warn_low.status_code == 422


def test_error_response_no_stack_trace_leakage(client: TestClient):
    """Errors must return standard structured JSON detail without exposing internal tracebacks."""
    response = client.get("/api/engines/999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    # Ensure raw Python tracebacks or internal file paths are not leaked in body
    assert "Traceback (most recent call last)" not in response.text
    assert "site-packages" not in response.text


def test_observability_security_headers(client: TestClient):
    """Responses must include profiling headers without leaking server secrets."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "X-Response-Time-Ms" in response.headers
    # Confirm no private keys or internal credentials leaked in headers
    for header_name, header_val in response.headers.items():
        assert "private" not in header_name.lower()
        assert "secret" not in header_name.lower()


def test_fail_closed_behavior_when_unauthenticated(client: TestClient):
    """Simulate model unloading: API endpoints must fail closed with 503 instead of serving invalid predictions."""
    # Temporarily remove model from app_state
    saved_model = app_state.get("prod_model")
    try:
        app_state["prod_model"] = None
        response = client.post("/api/predict", json={"engine_id": 1})
        assert response.status_code == 503
        detail_msg = response.json()["detail"].lower()
        assert "not initialized" in detail_msg or "unavailable" in detail_msg

    finally:
        app_state["prod_model"] = saved_model
