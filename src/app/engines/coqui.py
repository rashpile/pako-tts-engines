"""Coqui TTS engine adapter."""

import io
import struct
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt

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


class CoquiEngine(TTSEngine):
    """Coqui TTS engine adapter."""

    def __init__(self, config: EngineConfig) -> None:
        """Initialize Coqui engine.

        Args:
            config: Engine configuration.
        """
        self._config = config
        self._tts: Any = None
        self._is_available = False
        self._error_message: str | None = None
        self._sample_rate = 22050

        # Define parameter schema with speed
        self._parameter_schema = ParameterSchema(
            parameters=[
                ParameterDefinition(
                    name="speed",
                    type=ParameterType.FLOAT,
                    description="Speech rate multiplier",
                    default=1.0,
                    min_value=0.5,
                    max_value=2.0,
                    allowed_values=None,
                ),
            ]
        )

        # Build model info
        default_language = config.languages[0] if config.languages else "en-US"
        self._model_info = ModelInfo(
            id=config.name,
            name=self._get_display_name(config),
            engine_type=EngineType.COQUI,
            model_path=config.model,
            languages=config.languages,
            default_language=default_language,
            parameters=self._parameter_schema,
            is_default=config.default,
            sample_rate=self._sample_rate,
            speaker=config.speaker,
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
        # Extract language from model path for display name
        parts = config.model.split("/")
        if len(parts) >= 3:
            lang = parts[1].upper()
            return f"Coqui {lang} ({config.name})"
        return f"Coqui ({config.name})"

    def _load_model(self) -> None:
        """Load the TTS model."""
        try:
            from TTS.api import TTS  # type: ignore[import-untyped]

            logger.info(
                "coqui.loading_model",
                model=self._config.model,
                name=self._config.name,
            )

            self._tts = TTS(model_name=self._config.model, progress_bar=False)
            self._is_available = True

            # Get actual sample rate from model if available
            synthesizer = getattr(self._tts, "synthesizer", None)
            if synthesizer and hasattr(synthesizer, "output_sample_rate"):
                self._sample_rate = synthesizer.output_sample_rate
                self._model_info.sample_rate = self._sample_rate

            logger.info(
                "coqui.model_loaded",
                model=self._config.model,
                name=self._config.name,
                sample_rate=self._sample_rate,
            )
        except Exception as e:
            self._is_available = False
            self._error_message = str(e)
            logger.error(
                "coqui.model_load_failed",
                model=self._config.model,
                name=self._config.name,
                error=str(e),
            )

    @property
    def engine_type(self) -> EngineType:
        """Get the engine type."""
        return EngineType.COQUI

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
        if not self._is_available or self._tts is None:
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
        speed = params.get("speed", 1.0)

        try:
            logger.info(
                "coqui.synthesizing",
                model=self._config.name,
                text_length=len(text),
                language=effective_language,
                speed=speed,
            )

            # Synthesize to numpy array
            wav = self._tts.tts(text=text, speed=speed)

            # Convert to WAV bytes
            audio_bytes = self._numpy_to_wav(wav, self._sample_rate)

            logger.info(
                "coqui.synthesis_complete",
                model=self._config.name,
                audio_bytes=len(audio_bytes),
            )

            return audio_bytes

        except Exception as e:
            logger.error(
                "coqui.synthesis_failed",
                model=self._config.name,
                error=str(e),
            )
            raise APIError(
                ErrorCode.SYNTHESIS_FAILED,
                f"Synthesis failed: {e}",
                {"model": self._config.name, "error": str(e)},
            ) from e

    def _numpy_to_wav(
        self,
        audio_data: "npt.NDArray[np.float32] | list[float]",
        sample_rate: int,
    ) -> bytes:
        """Convert numpy audio array to WAV bytes.

        Args:
            audio_data: Numpy array of audio samples.
            sample_rate: Sample rate in Hz.

        Returns:
            WAV file as bytes.
        """
        import numpy as np

        # Ensure audio is in correct format
        audio_arr: npt.NDArray[np.float32]
        if isinstance(audio_data, list):
            audio_arr = np.array(audio_data, dtype=np.float32)
        else:
            audio_arr = audio_data

        # Normalize to int16 range
        audio_arr = np.clip(audio_arr, -1.0, 1.0)
        audio_int16 = (audio_arr * 32767).astype(np.int16)

        # Build WAV file
        buffer = io.BytesIO()

        # WAV header
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
        buffer.write(struct.pack("<I", 16))  # Subchunk1Size
        buffer.write(struct.pack("<H", 1))  # AudioFormat (PCM)
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
