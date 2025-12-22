"""Silero TTS engine adapter."""

import io
import struct
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    import torch

from app.engines.base import TTSEngine
from app.models.config import EngineConfig
from app.models.engine import (
    EngineType,
    ModelInfo,
    ParameterDefinition,
    ParameterSchema,
    ParameterType,
)
from app.models.errors import APIError, ErrorCode

logger = structlog.get_logger(__name__)


class SileroEngine(TTSEngine):
    """Silero TTS engine adapter."""

    AVAILABLE_SPEAKERS = ["aidar", "baya", "kseniya", "xenia", "eugene"]
    AVAILABLE_SAMPLE_RATES = [8000, 24000, 48000]

    def __init__(self, config: EngineConfig) -> None:
        """Initialize Silero engine.

        Args:
            config: Engine configuration.
        """
        self._config = config
        self._model: Any = None
        self._is_available = False
        self._error_message: str | None = None
        self._sample_rate = 48000  # Default Silero sample rate
        self._speaker = config.speaker or "xenia"

        # Define parameter schema with speaker and sample_rate
        self._parameter_schema = ParameterSchema(
            parameters=[
                ParameterDefinition(
                    name="speaker",
                    type=ParameterType.STRING,
                    description="Voice speaker ID",
                    default=self._speaker,
                    min_value=None,
                    max_value=None,
                    allowed_values=self.AVAILABLE_SPEAKERS,
                ),
                ParameterDefinition(
                    name="sample_rate",
                    type=ParameterType.INT,
                    description="Audio sample rate in Hz",
                    default=48000,
                    min_value=None,
                    max_value=None,
                    allowed_values=self.AVAILABLE_SAMPLE_RATES,
                ),
            ]
        )

        # Build model info
        default_language = config.languages[0] if config.languages else "ru-RU"
        self._model_info = ModelInfo(
            id=config.name,
            name=self._get_display_name(config),
            engine_type=EngineType.SILERO,
            model_path=config.model,
            languages=config.languages,
            default_language=default_language,
            parameters=self._parameter_schema,
            is_default=config.default,
            sample_rate=self._sample_rate,
            speaker=self._speaker,
            is_available=False,  # Will be set after model load
        )

        # Try to load the model
        self._load_model()

    def _get_display_name(self, config: EngineConfig) -> str:
        """Generate a display name for the model.

        Args:
            config: Engine configuration.

        Returns:
            Human-readable display name.
        """
        return f"Silero ({config.name})"

    def _load_model(self) -> None:
        """Load the Silero TTS model via torch.hub."""
        try:
            import torch

            logger.info(
                "silero.loading_model",
                model=self._config.model,
                name=self._config.name,
            )

            # Load Silero model from torch hub
            self._model, _ = torch.hub.load(  # type: ignore[no-untyped-call]
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker=self._config.model,  # e.g., "v4_ru"
                trust_repo=True,
            )
            self._is_available = True

            logger.info(
                "silero.model_loaded",
                model=self._config.model,
                name=self._config.name,
                speaker=self._speaker,
            )
        except Exception as e:
            self._is_available = False
            self._error_message = str(e)
            logger.error(
                "silero.model_load_failed",
                model=self._config.model,
                name=self._config.name,
                error=str(e),
            )

    @property
    def engine_type(self) -> EngineType:
        """Get the engine type."""
        return EngineType.SILERO

    @property
    def model_info(self) -> ModelInfo:
        """Get model information."""
        return self._model_info

    def is_available(self) -> bool:
        """Check if the engine is available."""
        return self._is_available

    def synthesize(
        self,
        text: str,
        language: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> bytes:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize.
            language: Language code (uses default if not specified).
            parameters: Model-specific parameters.

        Returns:
            Audio data as WAV bytes.

        Raises:
            APIError: If synthesis fails.
        """
        if not self._is_available or self._model is None:
            raise APIError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Model '{self._config.name}' is not available",
                {"error": self._error_message},
            )

        # Validate language
        effective_language = language or self._model_info.default_language
        if effective_language not in self._model_info.languages:
            model_name = self._config.name
            raise APIError(
                ErrorCode.LANGUAGE_NOT_SUPPORTED,
                f"Language '{effective_language}' not supported by '{model_name}'",
                {
                    "language": effective_language,
                    "supported_languages": self._model_info.languages,
                },
            )

        # Validate and apply parameters
        params = self.validate_parameters(parameters or {})
        speaker = params.get("speaker", self._speaker)
        sample_rate = params.get("sample_rate", self._sample_rate)

        try:
            logger.info(
                "silero.synthesizing",
                model=self._config.name,
                text_length=len(text),
                language=effective_language,
                speaker=speaker,
                sample_rate=sample_rate,
            )

            # Synthesize using Silero
            audio = self._model.apply_tts(
                text=text,
                speaker=speaker,
                sample_rate=sample_rate,
            )

            # Convert to WAV bytes
            audio_bytes = self._tensor_to_wav(audio, sample_rate)

            logger.info(
                "silero.synthesis_complete",
                model=self._config.name,
                audio_bytes=len(audio_bytes),
            )

            return audio_bytes

        except Exception as e:
            logger.error(
                "silero.synthesis_failed",
                model=self._config.name,
                error=str(e),
            )
            raise APIError(
                ErrorCode.SYNTHESIS_FAILED,
                f"Synthesis failed: {e}",
                {"model": self._config.name, "error": str(e)},
            ) from e

    def _tensor_to_wav(
        self,
        audio_tensor: "torch.Tensor | npt.NDArray[np.float32]",
        sample_rate: int,
    ) -> bytes:
        """Convert PyTorch tensor to WAV bytes.

        Args:
            audio_tensor: PyTorch tensor of audio samples.
            sample_rate: Sample rate in Hz.

        Returns:
            WAV file as bytes.
        """
        import numpy as np

        # Convert tensor to numpy
        audio_data: npt.NDArray[np.float32]
        if hasattr(audio_tensor, "numpy"):
            audio_data = audio_tensor.numpy()
        else:
            audio_data = np.array(audio_tensor)

        # Flatten if needed
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()

        # Normalize to int16 range
        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Build WAV file
        buffer = io.BytesIO()

        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(audio_int16) * block_align
        file_size = 36 + data_size

        # Write RIFF header
        buffer.write(b"RIFF")
        buffer.write(struct.pack("<I", file_size))
        buffer.write(b"WAVE")

        # Write fmt chunk
        buffer.write(b"fmt ")
        buffer.write(struct.pack("<I", 16))
        buffer.write(struct.pack("<H", 1))  # PCM
        buffer.write(struct.pack("<H", num_channels))
        buffer.write(struct.pack("<I", sample_rate))
        buffer.write(struct.pack("<I", byte_rate))
        buffer.write(struct.pack("<H", block_align))
        buffer.write(struct.pack("<H", bits_per_sample))

        # Write data chunk
        buffer.write(b"data")
        buffer.write(struct.pack("<I", data_size))
        buffer.write(audio_int16.tobytes())

        return buffer.getvalue()
