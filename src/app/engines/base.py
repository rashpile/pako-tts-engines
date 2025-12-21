"""TTS engine protocol and base classes."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.engine import EngineType, ModelInfo, ParameterSchema


class TTSEngine(ABC):
    """Abstract base class for TTS engine adapters."""

    @property
    @abstractmethod
    def engine_type(self) -> EngineType:
        """Get the engine type."""
        ...

    @property
    @abstractmethod
    def model_info(self) -> ModelInfo:
        """Get model information."""
        ...

    @property
    def name(self) -> str:
        """Get the model name/ID."""
        return self.model_info.id

    @property
    def supported_languages(self) -> list[str]:
        """Get supported language codes."""
        return self.model_info.languages

    @property
    def parameter_schema(self) -> ParameterSchema:
        """Get the parameter schema for this engine."""
        return self.model_info.parameters

    @property
    def sample_rate(self) -> int:
        """Get the output sample rate in Hz."""
        return self.model_info.sample_rate

    @abstractmethod
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
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available and ready.

        Returns:
            True if engine is ready for synthesis.
        """
        ...

    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize parameters.

        Args:
            parameters: Parameters to validate.

        Returns:
            Validated and normalized parameters.

        Raises:
            APIError: If parameters are invalid.
        """
        from app.models.errors import APIError, ErrorCode

        validated = {}
        schema = self.parameter_schema

        for param_def in schema.parameters:
            name = param_def.name
            if name in parameters:
                value = parameters[name]

                # Type validation
                if param_def.type.value == "float":
                    try:
                        value = float(value)
                    except (TypeError, ValueError) as e:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be a number",
                            {"parameter": name, "expected_type": "float"},
                        ) from e

                    # Range validation
                    if param_def.min_value is not None and value < param_def.min_value:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be >= {param_def.min_value}",
                            {
                                "parameter": name,
                                "value": value,
                                "min_value": param_def.min_value,
                            },
                        )
                    if param_def.max_value is not None and value > param_def.max_value:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be <= {param_def.max_value}",
                            {
                                "parameter": name,
                                "value": value,
                                "max_value": param_def.max_value,
                            },
                        )

                elif param_def.type.value == "int":
                    try:
                        value = int(value)
                    except (TypeError, ValueError) as e:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be an integer",
                            {"parameter": name, "expected_type": "int"},
                        ) from e

                    if param_def.min_value is not None and value < param_def.min_value:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be >= {int(param_def.min_value)}",
                            {
                                "parameter": name,
                                "value": value,
                                "min_value": int(param_def.min_value),
                            },
                        )
                    if param_def.max_value is not None and value > param_def.max_value:
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be <= {int(param_def.max_value)}",
                            {
                                "parameter": name,
                                "value": value,
                                "max_value": int(param_def.max_value),
                            },
                        )

                elif param_def.type.value == "string":
                    value = str(value)
                    if (
                        param_def.allowed_values
                        and value not in param_def.allowed_values
                    ):
                        allowed = param_def.allowed_values
                        raise APIError(
                            ErrorCode.INVALID_PARAMETER,
                            f"Parameter '{name}' must be one of: {allowed}",
                            {
                                "parameter": name,
                                "value": value,
                                "allowed_values": param_def.allowed_values,
                            },
                        )

                elif param_def.type.value == "bool":
                    if isinstance(value, bool):
                        pass
                    elif isinstance(value, str):
                        value = value.lower() in ("true", "1", "yes")
                    else:
                        value = bool(value)

                validated[name] = value
            else:
                # Use default value
                validated[name] = param_def.default

        return validated
