"""Configuration models."""

from typing import Any

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0", description="Bind address")
    port: int = Field(default=8000, description="Listen port")
    max_queue_size: int = Field(default=100, description="Request queue limit")
    max_text_length: int = Field(default=5000, description="Maximum text characters")
    synthesis_timeout: int = Field(
        default=30, description="Synthesis timeout in seconds"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="info", description="Log level: debug, info, warning, error"
    )
    format: str = Field(default="json", description="Log format: json, text")


class EngineConfig(BaseModel):
    """Configuration for a TTS engine/model."""

    name: str = Field(..., description="Model identifier")
    type: str = Field(..., description="Engine type: coqui or silero")
    model: str = Field(..., description="Model path or identifier")
    languages: list[str] = Field(..., description="Supported language codes")
    default: bool = Field(False, description="Is this the default model")
    speaker: str | None = Field(None, description="Speaker ID for multi-speaker models")
    parameters: dict[str, Any] | None = Field(
        None, description="Default parameter values"
    )


class ServiceConfig(BaseModel):
    """Root service configuration."""

    server: ServerConfig = ServerConfig()
    engines: list[EngineConfig] = Field(default_factory=list)
    logging: LoggingConfig = LoggingConfig()
