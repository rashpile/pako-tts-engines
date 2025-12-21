"""Unit tests for TTS engines."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.engine import (
    EngineType,
)
from app.models.errors import APIError, ErrorCode


class TestParameterValidation:
    """Tests for parameter validation in TTSEngine base class."""

    def test_validate_float_parameter(self) -> None:
        """Float parameter is validated correctly."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        # Create a mock engine with speed parameter
        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="test",
                type="coqui",
                model="test/model",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)
            engine._is_available = True

        # Valid speed
        result = engine.validate_parameters({"speed": 1.5})
        assert result["speed"] == 1.5

    def test_validate_float_parameter_min_violation(self) -> None:
        """Float parameter below minimum raises error."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="test",
                type="coqui",
                model="test/model",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)
            engine._is_available = True

        with pytest.raises(APIError) as exc_info:
            engine.validate_parameters({"speed": 0.1})
        assert exc_info.value.code == ErrorCode.INVALID_PARAMETER

    def test_validate_float_parameter_max_violation(self) -> None:
        """Float parameter above maximum raises error."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="test",
                type="coqui",
                model="test/model",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)
            engine._is_available = True

        with pytest.raises(APIError) as exc_info:
            engine.validate_parameters({"speed": 3.0})
        assert exc_info.value.code == ErrorCode.INVALID_PARAMETER

    def test_validate_uses_default_when_not_provided(self) -> None:
        """Default value is used when parameter not provided."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="test",
                type="coqui",
                model="test/model",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)
            engine._is_available = True

        result = engine.validate_parameters({})
        assert result["speed"] == 1.0  # Default value


class TestCoquiEngine:
    """Tests for Coqui TTS engine adapter."""

    def test_coqui_engine_properties(self) -> None:
        """Coqui engine has correct properties."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="coqui-english",
                type="coqui",
                model="tts_models/en/ljspeech/vits",
                languages=["en-US", "en-GB"],
            )
            engine = CoquiEngine(config)

        assert engine.name == "coqui-english"
        assert engine.engine_type == EngineType.COQUI
        assert "en-US" in engine.supported_languages

    def test_coqui_engine_has_speed_parameter(self) -> None:
        """Coqui engine exposes speed parameter."""
        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        with patch.object(CoquiEngine, "_load_model"):
            config = EngineConfig(
                name="coqui-english",
                type="coqui",
                model="tts_models/en/ljspeech/vits",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)

        schema = engine.parameter_schema
        param_names = [p.name for p in schema.parameters]
        assert "speed" in param_names

    def test_coqui_engine_unavailable_when_model_fails(self) -> None:
        """Coqui engine is unavailable when model loading fails."""
        import sys
        from unittest.mock import MagicMock

        from app.engines.coqui import CoquiEngine
        from app.models.config import EngineConfig

        # Mock TTS module to raise an exception
        mock_tts_module = MagicMock()
        mock_tts_module.api.TTS.side_effect = Exception("Model not found")
        sys.modules["TTS"] = mock_tts_module
        sys.modules["TTS.api"] = mock_tts_module.api

        try:
            config = EngineConfig(
                name="coqui-english",
                type="coqui",
                model="non/existent/model",
                languages=["en-US"],
            )
            engine = CoquiEngine(config)
            assert not engine.is_available()
        finally:
            # Clean up
            if "TTS" in sys.modules:
                del sys.modules["TTS"]
            if "TTS.api" in sys.modules:
                del sys.modules["TTS.api"]


class TestEngineRegistry:
    """Tests for engine registry."""

    def test_register_engine(self) -> None:
        """Engine can be registered."""
        from app.engines.registry import EngineRegistry

        registry = EngineRegistry()
        mock_engine = MagicMock()
        mock_engine.name = "test-engine"
        mock_engine.is_available.return_value = True

        registry.register(mock_engine)

        assert registry.get("test-engine") is mock_engine

    def test_get_nonexistent_engine_returns_none(self) -> None:
        """Getting non-existent engine returns None."""
        from app.engines.registry import EngineRegistry

        registry = EngineRegistry()
        assert registry.get("nonexistent") is None

    def test_get_or_raise_raises_for_nonexistent(self) -> None:
        """get_or_raise raises APIError for non-existent engine."""
        from app.engines.registry import EngineRegistry

        registry = EngineRegistry()
        with pytest.raises(APIError) as exc_info:
            registry.get_or_raise("nonexistent")
        assert exc_info.value.code == ErrorCode.MODEL_NOT_FOUND

    def test_default_engine_is_first_registered(self) -> None:
        """First registered engine becomes default."""
        from app.engines.registry import EngineRegistry

        registry = EngineRegistry()
        mock_engine = MagicMock()
        mock_engine.name = "first-engine"
        mock_engine.is_available.return_value = True

        registry.register(mock_engine)

        assert registry.default_engine_id == "first-engine"

    def test_explicit_default_engine(self) -> None:
        """Explicitly set default engine takes precedence."""
        from app.engines.registry import EngineRegistry

        registry = EngineRegistry()
        mock_engine1 = MagicMock()
        mock_engine1.name = "first-engine"
        mock_engine1.is_available.return_value = True

        mock_engine2 = MagicMock()
        mock_engine2.name = "second-engine"
        mock_engine2.is_available.return_value = True

        registry.register(mock_engine1)
        registry.register(mock_engine2, is_default=True)

        assert registry.default_engine_id == "second-engine"
