"""API response models."""

from pydantic import BaseModel, Field

from app.models.engine import (
    EngineStatus,
    EngineType,
    OutputFormat,
    ParameterDefinition,
)


class SynthesisResponse(BaseModel):
    """Metadata about synthesized audio."""

    model_id: str = Field(..., description="Model used")
    language: str = Field(..., description="Language used")
    output_format: OutputFormat = Field(..., description="Audio format")
    sample_rate: int = Field(..., description="Audio sample rate in Hz")
    duration_ms: int = Field(..., description="Audio duration in milliseconds")
    audio_size_bytes: int = Field(..., description="Audio file size")


class EngineHealth(BaseModel):
    """Health status of a TTS engine."""

    name: str = Field(..., description="Engine name")
    status: EngineStatus = Field(..., description="Engine status")
    models_count: int = Field(..., description="Number of available models")
    error: str | None = Field(None, description="Error message if unavailable")


class HealthResponse(BaseModel):
    """Service health response."""

    status: str = Field(..., description="Overall service health status")
    engines: list[EngineHealth] = Field(..., description="Engine health status")
    version: str | None = Field(None, description="Service version")
    uptime_seconds: int | None = Field(None, description="Service uptime in seconds")


class ModelSummary(BaseModel):
    """Summary of a TTS model for listing."""

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    engine: EngineType = Field(..., description="Engine type")
    languages: list[str] = Field(..., description="Supported language codes")
    is_available: bool = Field(..., description="Whether model is currently available")
    is_default: bool = Field(False, description="Whether this is the default model")


class ModelsListResponse(BaseModel):
    """Response for listing available models."""

    models: list[ModelSummary] = Field(..., description="Available models")
    default_model_id: str | None = Field(None, description="ID of the default model")


class ModelDetailResponse(BaseModel):
    """Detailed information about a TTS model."""

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    engine: EngineType = Field(..., description="Engine type")
    languages: list[str] = Field(..., description="Supported language codes")
    default_language: str | None = Field(
        None, description="Default language if not specified"
    )
    sample_rate: int = Field(..., description="Output audio sample rate in Hz")
    parameters: list[ParameterDefinition] = Field(
        ..., description="Available parameters"
    )
    is_available: bool = Field(..., description="Whether model is currently available")
    is_default: bool = Field(False, description="Whether this is the default model")
