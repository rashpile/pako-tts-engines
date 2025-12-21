"""Synthesis service for TTS operations."""

import time

import structlog

from app.api.middleware.logging import record_synthesis
from app.config import get_config
from app.engines.base import TTSEngine
from app.engines.registry import get_registry
from app.models.errors import APIError, ErrorCode
from app.models.request import SynthesisRequest
from app.models.response import SynthesisResponse
from app.services.language_detector import get_language_detector

logger = structlog.get_logger(__name__)


class SynthesisResult:
    """Result of a synthesis operation."""

    def __init__(
        self,
        audio_data: bytes,
        metadata: SynthesisResponse,
    ) -> None:
        self.audio_data = audio_data
        self.metadata = metadata


class SynthesisService:
    """Service for handling TTS synthesis requests."""

    def __init__(self) -> None:
        """Initialize synthesis service."""
        self._config = get_config()

    def validate_request(self, request: SynthesisRequest) -> None:
        """Validate a synthesis request.

        Args:
            request: Request to validate.

        Raises:
            APIError: If request is invalid.
        """
        # Check text is not empty
        if not request.text or not request.text.strip():
            raise APIError(
                ErrorCode.TEXT_EMPTY,
                "Text cannot be empty",
            )

        # Check text length
        max_length = self._config.server.max_text_length
        if len(request.text) > max_length:
            raise APIError(
                ErrorCode.TEXT_TOO_LONG,
                f"Text exceeds maximum length of {max_length} characters",
                {
                    "max_length": max_length,
                    "actual_length": len(request.text),
                },
            )

    def get_engine(
        self,
        model_id: str | None,
        detected_language: str | None = None,
    ) -> TTSEngine:
        """Get the TTS engine for the request.

        Args:
            model_id: Model ID or None for auto-selection.
            detected_language: ISO 639-1 code from language detection.

        Returns:
            TTS engine.

        Raises:
            APIError: If model not found or unavailable.
        """
        registry = get_registry()

        engine: TTSEngine
        if model_id:
            # Explicit model requested
            engine = registry.get_or_raise(model_id)
        elif detected_language:
            # Try to find engine by detected language
            found_engine = registry.find_engine_for_language(detected_language)
            if found_engine is None:
                logger.info(
                    "synthesis.no_engine_for_language",
                    detected_language=detected_language,
                    fallback="default",
                )
                engine = registry.get_default_or_raise()
            else:
                engine = found_engine
        else:
            # No model or language, use default
            engine = registry.get_default_or_raise()

        if not engine.is_available():
            raise APIError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Model '{engine.name}' is not available",
            )

        return engine

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        """Synthesize text to audio.

        Args:
            request: Synthesis request.

        Returns:
            Synthesis result with audio data and metadata.

        Raises:
            APIError: If synthesis fails.
        """
        start_time = time.perf_counter()

        # Validate request
        self.validate_request(request)

        # Detect language if not provided and no explicit model
        detected_iso_code: str | None = None
        effective_language = request.language

        if not request.model_id and not request.language:
            # Auto-detect language
            detector = get_language_detector()
            detected_iso_code = detector.detect(request.text)

            if detected_iso_code:
                preview = request.text[:50] if len(request.text) > 50 else request.text
                logger.info(
                    "synthesis.language_detected",
                    detected_iso_code=detected_iso_code,
                    text_preview=preview,
                )

        # Get engine (may use detected language for selection)
        engine = self.get_engine(request.model_id, detected_iso_code)

        # Determine effective language for synthesis
        # Priority: explicit request > detected > engine default
        if request.language:
            effective_language = request.language
        elif detected_iso_code:
            # Find the first matching BCP-47 code from the engine
            prefix = f"{detected_iso_code}-"
            for lang in engine.model_info.languages:
                if lang.startswith(prefix) or lang == detected_iso_code:
                    effective_language = lang
                    break
            else:
                effective_language = engine.model_info.default_language
        else:
            effective_language = engine.model_info.default_language

        logger.info(
            "synthesis.starting",
            model_id=engine.name,
            text_length=len(request.text),
            language=effective_language,
            detected_language=detected_iso_code,
        )

        # Perform synthesis
        try:
            audio_data = engine.synthesize(
                text=request.text,
                language=effective_language,
                parameters=request.parameters,
            )
        except APIError:
            raise
        except Exception as e:
            logger.error(
                "synthesis.failed",
                model_id=engine.name,
                error=str(e),
            )
            raise APIError(
                ErrorCode.SYNTHESIS_FAILED,
                f"Synthesis failed: {e}",
            ) from e

        # Calculate duration
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Calculate audio duration from WAV data
        audio_duration_ms = self._calculate_audio_duration(
            audio_data, engine.sample_rate
        )

        # Record metrics
        record_synthesis(duration_ms)

        # Build response metadata
        metadata = SynthesisResponse(
            model_id=engine.name,
            language=effective_language,
            output_format=request.output_format,
            sample_rate=engine.sample_rate,
            duration_ms=audio_duration_ms,
            audio_size_bytes=len(audio_data),
        )

        logger.info(
            "synthesis.completed",
            model_id=engine.name,
            audio_bytes=len(audio_data),
            audio_duration_ms=audio_duration_ms,
            processing_ms=duration_ms,
        )

        return SynthesisResult(audio_data=audio_data, metadata=metadata)

    def _calculate_audio_duration(self, audio_data: bytes, sample_rate: int) -> int:
        """Calculate audio duration from WAV data.

        Args:
            audio_data: WAV audio bytes.
            sample_rate: Sample rate in Hz.

        Returns:
            Duration in milliseconds.
        """
        # WAV header is 44 bytes, audio data follows
        if len(audio_data) < 44:
            return 0

        # Get data size from header (bytes 40-43)
        data_size = int.from_bytes(audio_data[40:44], "little")

        # Assuming 16-bit mono audio
        bytes_per_sample = 2
        num_samples = data_size // bytes_per_sample

        # Calculate duration
        if sample_rate > 0:
            duration_seconds = num_samples / sample_rate
            return int(duration_seconds * 1000)

        return 0


# Global service instance
_synthesis_service: SynthesisService | None = None


def get_synthesis_service() -> SynthesisService:
    """Get the global synthesis service.

    Returns:
        Global synthesis service.
    """
    global _synthesis_service
    if _synthesis_service is None:
        _synthesis_service = SynthesisService()
    return _synthesis_service


def reset_synthesis_service() -> None:
    """Reset the global synthesis service. Used for testing."""
    global _synthesis_service
    _synthesis_service = None
