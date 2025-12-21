"""API request models."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.engine import OutputFormat


class SynthesisRequest(BaseModel):
    """Request to synthesize text to speech."""

    text: str = Field(..., description="Text to synthesize (1-5000 characters)")
    model_id: str | None = Field(
        None, description="Model to use (uses default if not specified)"
    )
    language: str | None = Field(
        None, description="Language code (uses model default if not specified)"
    )
    output_format: OutputFormat = Field(
        OutputFormat.WAV, description="Audio output format"
    )
    parameters: dict[str, Any] | None = Field(
        None, description="Model-specific parameters"
    )
