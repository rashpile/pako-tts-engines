"""Engine registration and discovery."""

import structlog

from app.engines.base import TTSEngine
from app.models.engine import EngineStatus, ModelInfo
from app.models.errors import APIError, ErrorCode

logger = structlog.get_logger(__name__)


class EngineRegistry:
    """Registry for managing TTS engines."""

    def __init__(self) -> None:
        self._engines: dict[str, TTSEngine] = {}
        self._default_engine_id: str | None = None
        self._engine_status: dict[str, EngineStatus] = {}

    def register(self, engine: TTSEngine, is_default: bool = False) -> None:
        """Register a TTS engine.

        Args:
            engine: Engine to register.
            is_default: Whether this is the default engine.
        """
        engine_id = engine.name
        self._engines[engine_id] = engine

        if engine.is_available():
            self._engine_status[engine_id] = EngineStatus.AVAILABLE
        else:
            self._engine_status[engine_id] = EngineStatus.UNAVAILABLE

        if is_default or self._default_engine_id is None:
            self._default_engine_id = engine_id

        logger.info(
            "engine.registered",
            engine_id=engine_id,
            engine_type=engine.engine_type.value,
            is_default=is_default,
            status=self._engine_status[engine_id].value,
        )

    def get(self, engine_id: str) -> TTSEngine | None:
        """Get an engine by ID.

        Args:
            engine_id: Engine/model ID.

        Returns:
            Engine if found, None otherwise.
        """
        return self._engines.get(engine_id)

    def get_or_raise(self, engine_id: str) -> TTSEngine:
        """Get an engine by ID or raise an error.

        Args:
            engine_id: Engine/model ID.

        Returns:
            Engine if found.

        Raises:
            APIError: If engine not found.
        """
        engine = self.get(engine_id)
        if engine is None:
            raise APIError(
                ErrorCode.MODEL_NOT_FOUND,
                f"Model '{engine_id}' not found",
                {"model_id": engine_id, "available_models": list(self._engines.keys())},
            )
        return engine

    def get_default(self) -> TTSEngine | None:
        """Get the default engine.

        Returns:
            Default engine if set, None otherwise.
        """
        if self._default_engine_id is None:
            return None
        return self._engines.get(self._default_engine_id)

    def get_default_or_raise(self) -> TTSEngine:
        """Get the default engine or raise an error.

        Returns:
            Default engine.

        Raises:
            APIError: If no default engine configured.
        """
        engine = self.get_default()
        if engine is None:
            raise APIError(
                ErrorCode.MODEL_UNAVAILABLE,
                "No default model configured",
            )
        return engine

    @property
    def default_engine_id(self) -> str | None:
        """Get the default engine ID."""
        return self._default_engine_id

    def list_all(self) -> list[TTSEngine]:
        """List all registered engines.

        Returns:
            List of all engines.
        """
        return list(self._engines.values())

    def list_available(self) -> list[TTSEngine]:
        """List all available engines.

        Returns:
            List of available engines.
        """
        return [e for e in self._engines.values() if e.is_available()]

    def find_engine_for_language(self, iso_code: str) -> TTSEngine | None:
        """Find the first available engine that supports a language.

        Matches engines where any supported language starts with the ISO code.
        For example, iso_code="en" matches engines with "en-US", "en-GB", etc.

        Engine order is determined by registration order (config.yaml order).

        Args:
            iso_code: ISO 639-1 language code (e.g., "en", "ru", "ro").

        Returns:
            First matching available engine, or None if no match found.
        """
        prefix = f"{iso_code}-"

        for engine in self._engines.values():
            if not engine.is_available():
                continue

            # Check if any supported language matches the ISO code
            for lang in engine.model_info.languages:
                if lang.startswith(prefix) or lang == iso_code:
                    logger.debug(
                        "registry.found_engine_for_language",
                        iso_code=iso_code,
                        matched_language=lang,
                        engine_id=engine.name,
                    )
                    return engine

        logger.debug(
            "registry.no_engine_for_language",
            iso_code=iso_code,
        )
        return None

    def list_models(self) -> list[ModelInfo]:
        """List all model information.

        Returns:
            List of model info for all engines.
        """
        models = []
        for engine in self._engines.values():
            info = engine.model_info
            # Update is_default based on registry
            info_dict = info.model_dump()
            info_dict["is_default"] = engine.name == self._default_engine_id
            info_dict["is_available"] = engine.is_available()
            models.append(ModelInfo(**info_dict))
        return models

    def get_model(self, model_id: str) -> ModelInfo:
        """Get detailed model information.

        Args:
            model_id: Model ID.

        Returns:
            Model information.

        Raises:
            APIError: If model not found.
        """
        engine = self.get_or_raise(model_id)
        info = engine.model_info
        info_dict = info.model_dump()
        info_dict["is_default"] = engine.name == self._default_engine_id
        info_dict["is_available"] = engine.is_available()
        return ModelInfo(**info_dict)

    def get_status(self, engine_id: str) -> EngineStatus | None:
        """Get engine status.

        Args:
            engine_id: Engine/model ID.

        Returns:
            Engine status if found, None otherwise.
        """
        return self._engine_status.get(engine_id)

    def set_status(self, engine_id: str, status: EngineStatus) -> None:
        """Set engine status.

        Args:
            engine_id: Engine/model ID.
            status: New status.
        """
        if engine_id in self._engines:
            self._engine_status[engine_id] = status
            logger.info(
                "engine.status_changed",
                engine_id=engine_id,
                status=status.value,
            )

    def is_empty(self) -> bool:
        """Check if registry is empty.

        Returns:
            True if no engines registered.
        """
        return len(self._engines) == 0

    def clear(self) -> None:
        """Clear all registered engines."""
        self._engines.clear()
        self._engine_status.clear()
        self._default_engine_id = None


# Global registry instance
_registry: EngineRegistry | None = None


def get_registry() -> EngineRegistry:
    """Get the global engine registry.

    Returns:
        Global engine registry.
    """
    global _registry
    if _registry is None:
        _registry = EngineRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry. Used for testing."""
    global _registry
    if _registry is not None:
        _registry.clear()
    _registry = None
