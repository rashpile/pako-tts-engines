"""API route registration."""

from fastapi import FastAPI


def register_routes(app: FastAPI) -> None:
    """Register all API routes.

    Args:
        app: FastAPI application.
    """
    from app.api.handlers import health, models, openapi, tts

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(tts.router, prefix="/api/v1", tags=["TTS"])
    app.include_router(models.router, prefix="/api/v1", tags=["Models"])
    app.include_router(openapi.router, tags=["Documentation"])
