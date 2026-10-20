"""Structured observability, request metrics instrumentation, and telemetry logging for AeroGuard 2.1."""

from collections import deque
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any, Callable, Deque, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure structured JSON logger
logger = logging.getLogger("aeroguard.observability")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class MetricsCollector:
    """In-memory sliding window metrics collector for API request telemetry."""

    def __init__(self, max_latency_samples: int = 1000):
        self.start_time: datetime = datetime.now(timezone.utc)
        self.total_requests: int = 0
        self.total_predictions: int = 0
        self.prediction_failures: int = 0
        self.endpoint_counts: Dict[str, int] = {}
        self.status_code_counts: Dict[str, int] = {}
        self._latencies: Deque[float] = deque(maxlen=max_latency_samples)

    def record_request(self, endpoint: str, status_code: int, duration_ms: float) -> None:
        self.total_requests += 1
        self.endpoint_counts[endpoint] = self.endpoint_counts.get(endpoint, 0) + 1
        code_str = str(status_code)
        self.status_code_counts[code_str] = self.status_code_counts.get(code_str, 0) + 1
        self._latencies.append(duration_ms)

        if endpoint == "/api/predict":
            self.total_predictions += 1
            if status_code >= 400:
                self.prediction_failures += 1

    def get_snapshot(self) -> Dict[str, Any]:
        uptime_s = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        latencies_list = list(self._latencies)

        if latencies_list:
            sorted_lat = sorted(latencies_list)
            p50 = float(sorted_lat[int(len(sorted_lat) * 0.50)])
            p95 = float(sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)])
            p99 = float(sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)])
            avg = float(sum(latencies_list) / len(latencies_list))
        else:
            p50 = p95 = p99 = avg = 0.0

        error_count = sum(count for code, count in self.status_code_counts.items() if int(code) >= 400)
        error_rate = (error_count / self.total_requests * 100.0) if self.total_requests > 0 else 0.0

        return {
            "service": "aeroguard-backend",
            "version": "2.1.0",
            "uptime_seconds": round(uptime_s, 1),
            "started_at": self.start_time.isoformat(),
            "requests_total": self.total_requests,
            "requests_by_endpoint": dict(self.endpoint_counts),
            "status_codes": dict(self.status_code_counts),
            "error_rate_pct": round(error_rate, 2),
            "predictions_total": self.total_predictions,
            "prediction_failures": self.prediction_failures,
            "latency_ms": {
                "mean": round(avg, 2),
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "samples_recorded": len(latencies_list),
            },
        }


# Global metrics instance
metrics_collector = MetricsCollector()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request latency profiling and structured audit logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Don't profile root health / metrics polling noise if desired, but keep transparent metrics
        start_time = time.perf_counter()
        endpoint = request.url.path

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Record metrics
            metrics_collector.record_request(endpoint, response.status_code, duration_ms)

            # Emit structured JSON log
            log_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO" if response.status_code < 400 else "WARNING",
                "method": request.method,
                "path": endpoint,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client": request.client.host if request.client else "unknown",
            }
            logger.info(json.dumps(log_record))

            response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            metrics_collector.record_request(endpoint, 500, duration_ms)

            log_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "ERROR",
                "method": request.method,
                "path": endpoint,
                "status_code": 500,
                "duration_ms": round(duration_ms, 2),
                "error": str(exc),
                "client": request.client.host if request.client else "unknown",
            }
            logger.error(json.dumps(log_record))
            raise
