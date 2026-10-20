"""Unit and integration tests for AeroGuard FastAPI backend."""

import pytest
from fastapi.testclient import TestClient

from aircraft_pm.api import app, lifespan


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI test client with lifespan context active."""
    with TestClient(app) as test_client:
        yield test_client


def test_api_health(client):
    """Verify /api/health reports readiness and loaded artifacts."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["preprocessor_loaded"] is True
    assert data["dataset_loaded"] is True
    assert data["n_test_engines"] == 100
    assert data["n_train_engines"] == 100


def test_api_fleet_summary(client):
    """Verify /api/fleet/summary returns correct fleet counts and distribution."""
    response = client.get("/api/fleet/summary?critical_threshold=25&warning_threshold=50")
    assert response.status_code == 200
    data = response.json()
    assert data["total_engines"] == 100
    assert data["healthy_count"] + data["warning_count"] + data["critical_count"] == 100
    assert data["mean_predicted_rul"] > 0
    assert len(data["rul_distribution"]) > 0
    assert len(data["top_critical_engines"]) <= 5
    # Verification of top critical ordering
    if len(data["top_critical_engines"]) >= 2:
        assert data["top_critical_engines"][0]["pred_rul"] <= data["top_critical_engines"][1]["pred_rul"]


def test_api_engines_list(client):
    """Verify /api/engines returns 100 test engines."""
    response = client.get("/api/engines?fleet_type=test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100
    assert all("engine_id" in eng and "pred_rul" in eng for eng in data)


def test_api_engine_detail_valid(client):
    """Verify /api/engines/{id} returns telemetry and prognostics."""
    response = client.get("/api/engines/1?fleet_type=test")
    assert response.status_code == 200
    data = response.json()
    assert data["engine_id"] == 1
    assert data["total_logged_cycles"] == 31  # FD001 test engine 1 has 31 cycles
    assert len(data["observations"]) == 31
    assert data["pred_rul"] > 0
    assert data["true_rul"] == 112.0  # Official ground truth for engine 1 is 112


def test_api_engine_detail_with_cutoff(client):
    """Verify /api/engines/{id} respects cutoff cycle."""
    response = client.get("/api/engines/1?cutoff_cycle=15&fleet_type=test")
    assert response.status_code == 200
    data = response.json()
    assert data["cutoff_cycle"] == 15
    assert len(data["observations"]) == 15
    # Ground truth at cycle 15 = 112 + (31 - 15) = 128
    assert data["true_rul"] == 128.0


def test_api_engine_detail_not_found(client):
    """Verify /api/engines/{id} returns 404 for invalid engine ID."""
    response = client.get("/api/engines/999")
    assert response.status_code == 404


def test_api_predict_valid(client):
    """Verify POST /api/predict calculates causal RUL prediction."""
    payload = {"engine_id": 1, "cutoff_cycle": 20, "fleet_type": "test"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["engine_id"] == 1
    assert data["cutoff_cycle"] == 20
    assert 0 <= data["pred_rul"] <= 125
    assert "clipping_policy" in data
    assert data["model_name"] == "HistGradientBoostingRegressor"


def test_api_predict_out_of_bounds_cutoff(client):
    """Verify POST /api/predict returns 400 for out-of-bounds cutoff."""
    payload = {"engine_id": 1, "cutoff_cycle": 999, "fleet_type": "test"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 400


def test_api_predict_invalid_engine(client):
    """Verify POST /api/predict returns 422 or 404 for invalid engine."""
    # ge=1, le=100 in schema triggers 422 for 999
    payload = {"engine_id": 999, "cutoff_cycle": 10, "fleet_type": "test"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_api_sensors_summary(client):
    """Verify /api/sensors/summary returns 24 channels and 7 invariant channels."""
    response = client.get("/api/sensors/summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data["sensors"]) == 24  # 3 settings + 21 sensors
    assert len(data["invariant_channels"]) == 7
    assert len(data["informative_channels"]) == 15
    assert "pruning_rationale" in data


def test_api_models_metrics(client):
    """Verify /api/models/metrics returns official test and CV regimes."""
    response = client.get("/api/models/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "official_test" in data
    assert "cross_validation" in data
    assert data["best_model"] == "HistGradientBoosting"


def test_api_maintenance_queue_and_export(client):
    """Verify /api/maintenance/queue and /api/maintenance/export."""
    q_resp = client.get("/api/maintenance/queue?critical_threshold=25&warning_threshold=50")
    assert q_resp.status_code == 200
    queue = q_resp.json()
    assert len(queue) == 100
    assert queue[0]["pred_rul"] <= queue[-1]["pred_rul"]

    exp_resp = client.get("/api/maintenance/export?critical_threshold=25&warning_threshold=50")
    assert exp_resp.status_code == 200
    assert exp_resp.headers["content-type"].startswith("text/csv")
    csv_text = exp_resp.text
    assert "Engine_ID,Current_Cycle,Predicted_RUL_Cycles" in csv_text


def test_api_metrics_endpoint(client):
    """Verify /api/metrics exposes structured request telemetry, latency percentiles, and error rate."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "aeroguard-backend"
    assert "requests_total" in data
    assert "latency_ms" in data
    assert "p95" in data["latency_ms"]
    assert "error_rate_pct" in data


def test_api_drift_endpoint(client):
    """Verify /api/drift computes KS and PSI distribution shifts across informative channels."""
    response = client.get("/api/drift")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "features" in data
    assert "statistical_methods" in data
    assert "caveat" in data
    assert data["sample_size_reference"] > 0
    assert data["sample_size_comparison"] > 0


def test_api_models_lineage_endpoint(client):
    """Verify /api/models/lineage returns cryptographic manifest with SHA-256 artifact hashes."""
    response = client.get("/api/models/lineage")
    assert response.status_code == 200
    data = response.json()
    assert data["manifest_version"] == "2.1.0"
    assert data["algorithm"] == "HistGradientBoostingRegressor"
    assert "artifacts_sha256" in data
    assert "best_model_joblib" in data["artifacts_sha256"]
    assert len(data["artifacts_sha256"]["best_model_joblib"]) == 64
    assert "datasets_sha256" in data
    assert "train_FD001" in data["datasets_sha256"]
