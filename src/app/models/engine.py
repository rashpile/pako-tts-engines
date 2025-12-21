"""Engine and model domain models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EngineType(str, Enum):
    """Supported TTS engine types."""

    COQUI = "coqui"
    SILERO = "silero"


class OutputFormat(str, Enum):
    """Audio output formats."""

    WAV = "wav"
    MP3 = "mp3"


class ParameterType(str, Enum):
    """Parameter value types."""

    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOL = "bool"


class EngineStatus(str, Enum):
    """Engine availability status."""

    LOADING = "loading"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


class ParameterDefinition(BaseModel):
    """Definition of a model-specific parameter."""

    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(..., description="Parameter value type")
    description: str = Field(..., description="Human-readable description")
    default: Any = Field(..., description="Default value")
    min_value: float | None = Field(None, description="Minimum value for numeric types")
    max_value: float | None = Field(None, description="Maximum value for numeric types")
    allowed_values: list[Any] | None = Field(
        None, description="Allowed values for enum types"
    )


class ParameterSchema(BaseModel):
    """Schema for model-specific parameters."""

    parameters: list[ParameterDefinition] = Field(
        default_factory=list, description="List of parameter definitions"
    )


class ModelInfo(BaseModel):
    """Information about a TTS model."""

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    engine_type: EngineType = Field(..., description="Engine type")
    model_path: str = Field(..., description="Model path or identifier")
    languages: list[str] = Field(..., description="Supported language codes")
    default_language: str = Field(..., description="Default language code")
    parameters: ParameterSchema = Field(
        default_factory=ParameterSchema, description="Parameter schema"
    )
    is_default: bool = Field(False, description="Is this the default model")
    sample_rate: int = Field(22050, description="Output sample rate in Hz")
    speaker: str | None = Field(None, description="Speaker ID for multi-speaker models")
    is_available: bool = Field(True, description="Runtime availability status")
