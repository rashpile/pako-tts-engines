"""Health check handler."""

import time
from typing import ClassVar

from fastapi import APIRouter

from app.engines.registry import get_registry
from app.models.engine import EngineStatus, EngineType
from app.models.response import EngineHealth, HealthResponse

router = APIRouter()


class HealthService:
    """Service for health check operations."""

    _start_time: ClassVar[float] = time.time()

    @classmethod
    def get_uptime_seconds(cls) -> int:
        """Get service uptime in seconds."""
        return int(time.time() - cls._start_time)


@router.get("/health")
async def health() -> HealthResponse:
    """Get service health status.

    Returns:
        Health response with engine status.
    """
    registry = get_registry()
    engines = registry.list_all()

    # Build engine health list
    engine_health: list[EngineHealth] = []

    # Group engines by type
    engines_by_type: dict[EngineType, list[tuple[str, bool]]] = {}
    for engine in engines:
        engine_type = engine.engine_type
        if engine_type not in engines_by_type:
            engines_by_type[engine_type] = []
        engines_by_type[engine_type].append((engine.name, engine.is_available()))

    # Build health status per engine type
    for engine_type, engine_list in engines_by_type.items():
        available_count = sum(1 for _, available in engine_list if available)
        total_count = len(engine_list)

        if available_count == total_count:
            status = EngineStatus.AVAILABLE
        elif available_count > 0:
            status = EngineStatus.AVAILABLE  # Partially available
        else:
            status = EngineStatus.UNAVAILABLE

        engine_health.append(
            EngineHealth(
                name=engine_type.value,
                status=status,
                models_count=available_count,
                error=None,
            )
        )

    # Determine overall status
    if not engines:
        overall_status = "unhealthy"
    elif all(e.status == EngineStatus.AVAILABLE for e in engine_health):
        overall_status = "healthy"
    elif any(e.status == EngineStatus.AVAILABLE for e in engine_health):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        engines=engine_health,
        version="1.0.0",
        uptime_seconds=HealthService.get_uptime_seconds(),
    )
