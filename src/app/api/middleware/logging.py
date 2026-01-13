"""Request logging middleware."""

import time
import uuid
from typing import Any

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log request and response details.

        Args:
            request: Incoming request.
            call_next: Next middleware/handler.

        Returns:
            Response from handler.
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Add request ID to request state for access in handlers
        request.state.request_id = request_id

        # Use DEBUG level for health endpoint to reduce log noise
        log_fn = logger.debug if request.url.path.endswith("/health") else logger.info

        # Log request
        log_fn(
            "request.received",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        log_fn(
            "request.completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id

        return response


# Metrics tracking (simple in-memory counters)
_metrics: dict[str, Any] = {
    "request_count": 0,
    "error_count": 0,
    "synthesis_count": 0,
    "total_synthesis_ms": 0.0,
}


def increment_request_count() -> None:
    """Increment request counter."""
    _metrics["request_count"] += 1


def increment_error_count() -> None:
    """Increment error counter."""
    _metrics["error_count"] += 1


def record_synthesis(duration_ms: float) -> None:
    """Record a synthesis operation.

    Args:
        duration_ms: Duration in milliseconds.
    """
    _metrics["synthesis_count"] += 1
    _metrics["total_synthesis_ms"] += duration_ms


def get_metrics() -> dict[str, Any]:
    """Get current metrics.

    Returns:
        Dictionary of metrics.
    """
    avg_synthesis_ms = 0.0
    if _metrics["synthesis_count"] > 0:
        avg_synthesis_ms = _metrics["total_synthesis_ms"] / _metrics["synthesis_count"]

    return {
        "request_count": _metrics["request_count"],
        "error_count": _metrics["error_count"],
        "synthesis_count": _metrics["synthesis_count"],
        "avg_synthesis_ms": round(avg_synthesis_ms, 2),
    }


def reset_metrics() -> None:
    """Reset all metrics. Used for testing."""
    global _metrics
    _metrics = {
        "request_count": 0,
        "error_count": 0,
        "synthesis_count": 0,
        "total_synthesis_ms": 0.0,
    }
