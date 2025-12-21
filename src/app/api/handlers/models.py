"""Models list and detail handlers."""

from fastapi import APIRouter

from app.engines.registry import get_registry
from app.models.response import (
    ModelDetailResponse,
    ModelsListResponse,
    ModelSummary,
)

router = APIRouter()


@router.get("/models")
async def list_models() -> ModelsListResponse:
    """List all available TTS models.

    Returns:
        List of available models.
    """
    registry = get_registry()
    models = registry.list_models()

    summaries = [
        ModelSummary(
            id=model.id,
            name=model.name,
            engine=model.engine_type,
            languages=model.languages,
            is_available=model.is_available,
            is_default=model.is_default,
        )
        for model in models
    ]

    return ModelsListResponse(
        models=summaries,
        default_model_id=registry.default_engine_id,
    )


@router.get("/models/{model_id}")
async def get_model(model_id: str) -> ModelDetailResponse:
    """Get detailed information about a specific model.

    Args:
        model_id: Model identifier.

    Returns:
        Model details including parameter schema.
    """
    registry = get_registry()
    model = registry.get_model(model_id)

    return ModelDetailResponse(
        id=model.id,
        name=model.name,
        engine=model.engine_type,
        languages=model.languages,
        default_language=model.default_language,
        sample_rate=model.sample_rate,
        parameters=model.parameters.parameters,
        is_available=model.is_available,
        is_default=model.is_default,
    )
