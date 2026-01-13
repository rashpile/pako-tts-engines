"""FastAPI application entry point."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI

from app.api.middleware.error import ErrorHandlingMiddleware
from app.api.middleware.logging import RequestLoggingMiddleware
from app.api.routes import register_routes
from app.config import get_config, load_config
from app.engines.base import TTSEngine
from app.engines.registry import get_registry


class HealthCheckFilter(logging.Filter):
    """Filter to suppress health check endpoint logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out health check requests.

        Args:
            record: Log record to check.

        Returns:
            False to suppress the log, True to keep it.
        """
        message = record.getMessage()
        return "/health" not in message


def configure_logging(level: str = "info", format: str = "json") -> None:
    """Configure structured logging.

    Args:
        level: Log level (debug, info, warning, error).
        format: Log format (json, text).
    """
    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Filter health check requests from uvicorn access logs
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addFilter(HealthCheckFilter())

    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def init_engines() -> None:
    """Initialize TTS engines from configuration."""
    from app.engines.coqui import CoquiEngine
    from app.engines.silero import SileroEngine

    logger = structlog.get_logger(__name__)
    config = get_config()
    registry = get_registry()

    for engine_config in config.engines:
        try:
            engine: TTSEngine
            if engine_config.type == "coqui":
                engine = CoquiEngine(engine_config)
                registry.register(engine, is_default=engine_config.default)
            elif engine_config.type == "silero":
                engine = SileroEngine(engine_config)
                registry.register(engine, is_default=engine_config.default)
            else:
                logger.warning(
                    "engine.unknown_type",
                    engine_name=engine_config.name,
                    engine_type=engine_config.type,
                )
        except Exception as e:
            logger.error(
                "engine.init_failed",
                engine_name=engine_config.name,
                error=str(e),
            )

    if registry.is_empty():
        logger.warning("engine.none_available", message="No TTS engines available")
    else:
        available = registry.list_available()
        logger.info(
            "engine.init_complete",
            total_engines=len(registry.list_all()),
            available_engines=len(available),
            default_engine=registry.default_engine_id,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Args:
        app: FastAPI application.

    Yields:
        Nothing, just manages startup/shutdown.
    """
    logger = structlog.get_logger(__name__)

    # Startup
    logger.info("app.starting", version="1.0.0")
    init_engines()
    logger.info("app.started")

    yield

    # Shutdown
    logger.info("app.stopping")
    # Cleanup if needed
    logger.info("app.stopped")


def create_app(config_path: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configured FastAPI application.
    """
    # Load configuration
    config = load_config(config_path)

    # Configure logging
    configure_logging(
        level=config.logging.level,
        format=config.logging.format,
    )

    # Create application
    app = FastAPI(
        title="TTS API Service",
        description="Local TTS synthesis with multiple engine backends.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Register routes
    register_routes(app)

    return app


# Default application instance for uvicorn
app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    config = get_config()
    uvicorn.run(
        "app.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
