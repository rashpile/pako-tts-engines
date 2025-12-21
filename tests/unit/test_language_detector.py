"""Unit tests for language detection service."""

from unittest.mock import MagicMock

from app.engines.base import TTSEngine
from app.engines.registry import EngineRegistry
from app.models.engine import EngineType, ModelInfo, ParameterSchema
from app.services.language_detector import LanguageDetectorService


class TestLanguageDetector:
    """Tests for LanguageDetectorService."""

    def test_detect_english_text(self) -> None:
        """Detect English text correctly."""
        detector = LanguageDetectorService()
        result = detector.detect("Hello, this is a test message in English.")
        assert result == "en"

    def test_detect_russian_text(self) -> None:
        """Detect Russian text correctly."""
        detector = LanguageDetectorService()
        result = detector.detect("Привет, это тестовое сообщение на русском языке.")
        assert result == "ru"

    def test_detect_romanian_text(self) -> None:
        """Detect Romanian text correctly."""
        detector = LanguageDetectorService()
        romanian_text = "Bună ziua, aceasta este un mesaj de test în limba română."
        result = detector.detect(romanian_text)
        assert result == "ro"

    def test_detect_empty_text_returns_none(self) -> None:
        """Empty text returns None."""
        detector = LanguageDetectorService()
        assert detector.detect("") is None
        assert detector.detect("   ") is None

    def test_detect_with_confidence_returns_tuple(self) -> None:
        """detect_with_confidence returns (code, confidence) tuple."""
        detector = LanguageDetectorService()
        code, confidence = detector.detect_with_confidence("Hello world")
        assert code == "en"
        assert 0.0 <= confidence <= 1.0

    def test_iso_code_mapping_exists(self) -> None:
        """Language to ISO code mapping exists for common languages."""
        assert LanguageDetectorService.LANGUAGE_TO_ISO["ENGLISH"] == "en"
        assert LanguageDetectorService.LANGUAGE_TO_ISO["RUSSIAN"] == "ru"
        assert LanguageDetectorService.LANGUAGE_TO_ISO["ROMANIAN"] == "ro"
        assert LanguageDetectorService.LANGUAGE_TO_ISO["GERMAN"] == "de"
        assert LanguageDetectorService.LANGUAGE_TO_ISO["FRENCH"] == "fr"
        assert LanguageDetectorService.LANGUAGE_TO_ISO["SPANISH"] == "es"


class TestEngineRegistryLanguageSelection:
    """Tests for engine selection by language in EngineRegistry."""

    def _create_mock_engine(
        self,
        name: str,
        languages: list[str],
        available: bool = True,
    ) -> MagicMock:
        """Create a mock engine with specified languages."""
        mock = MagicMock(spec=TTSEngine)
        mock.name = name
        mock.engine_type = EngineType.COQUI
        mock.model_info = ModelInfo(
            id=name,
            name=f"Mock {name}",
            engine_type=EngineType.COQUI,
            model_path=f"mock/{name}",
            languages=languages,
            default_language=languages[0] if languages else "en-US",
            parameters=ParameterSchema(parameters=[]),
            is_default=False,
            sample_rate=22050,
        )
        mock.is_available.return_value = available
        return mock

    def test_find_engine_for_english(self) -> None:
        """Find engine that supports English."""
        registry = EngineRegistry()

        engine_en = self._create_mock_engine("english", ["en-US", "en-GB"])
        engine_ru = self._create_mock_engine("russian", ["ru-RU"])

        registry.register(engine_en)
        registry.register(engine_ru)

        result = registry.find_engine_for_language("en")
        assert result is engine_en

    def test_find_engine_for_russian(self) -> None:
        """Find engine that supports Russian."""
        registry = EngineRegistry()

        engine_en = self._create_mock_engine("english", ["en-US"])
        engine_ru = self._create_mock_engine("russian", ["ru-RU"])

        registry.register(engine_en)
        registry.register(engine_ru)

        result = registry.find_engine_for_language("ru")
        assert result is engine_ru

    def test_find_engine_returns_first_match(self) -> None:
        """Return first engine when multiple support the language."""
        registry = EngineRegistry()

        engine1 = self._create_mock_engine("first", ["en-US"])
        engine2 = self._create_mock_engine("second", ["en-GB"])

        registry.register(engine1)
        registry.register(engine2)

        result = registry.find_engine_for_language("en")
        assert result is engine1  # First registered wins

    def test_find_engine_skips_unavailable(self) -> None:
        """Skip unavailable engines when searching."""
        registry = EngineRegistry()

        engine_unavailable = self._create_mock_engine(
            "unavailable", ["en-US"], available=False
        )
        engine_available = self._create_mock_engine("available", ["en-GB"])

        registry.register(engine_unavailable)
        registry.register(engine_available)

        result = registry.find_engine_for_language("en")
        assert result is engine_available

    def test_find_engine_no_match_returns_none(self) -> None:
        """Return None when no engine supports the language."""
        registry = EngineRegistry()

        engine_en = self._create_mock_engine("english", ["en-US"])
        registry.register(engine_en)

        result = registry.find_engine_for_language("ja")  # Japanese
        assert result is None

    def test_find_engine_matches_prefix(self) -> None:
        """Match language by prefix (e.g., 'en' matches 'en-US')."""
        registry = EngineRegistry()

        engine = self._create_mock_engine("multi", ["en-US", "en-GB", "de-DE"])
        registry.register(engine)

        assert registry.find_engine_for_language("en") is engine
        assert registry.find_engine_for_language("de") is engine
        assert registry.find_engine_for_language("fr") is None


class TestSynthesisWithLanguageDetection:
    """Tests for synthesis service with language detection."""

    def test_synthesis_detects_language_when_not_provided(
        self, minimal_config_file: str, mock_engine: MagicMock
    ) -> None:
        """Synthesis detects language when not explicitly provided."""
        import os

        os.environ["CONFIG_PATH"] = minimal_config_file

        from app.config import load_config
        from app.engines.registry import get_registry
        from app.models.request import SynthesisRequest
        from app.services.synthesis import SynthesisService

        load_config(minimal_config_file)
        registry = get_registry()
        registry.register(mock_engine, is_default=True)

        service = SynthesisService()
        request = SynthesisRequest(text="Hello, this is English text.")

        # Should not raise - language will be detected
        result = service.synthesize(request)
        assert result.metadata.model_id == "mock-engine"

    def test_synthesis_uses_explicit_model_over_detection(
        self, minimal_config_file: str
    ) -> None:
        """Explicit model_id takes precedence over language detection."""
        import os
        from unittest.mock import MagicMock

        os.environ["CONFIG_PATH"] = minimal_config_file

        from app.config import load_config
        from app.engines.registry import get_registry
        from app.models.engine import EngineType, ModelInfo, ParameterSchema
        from app.models.request import SynthesisRequest
        from app.services.synthesis import SynthesisService

        load_config(minimal_config_file)
        registry = get_registry()

        # Create two mock engines
        mock_en = MagicMock()
        mock_en.name = "english-engine"
        mock_en.engine_type = EngineType.COQUI
        mock_en.model_info = ModelInfo(
            id="english-engine",
            name="English Engine",
            engine_type=EngineType.COQUI,
            model_path="mock/en",
            languages=["en-US"],
            default_language="en-US",
            parameters=ParameterSchema(parameters=[]),
            sample_rate=22050,
        )
        mock_en.is_available.return_value = True
        mock_en.sample_rate = 22050
        mock_en.synthesize.return_value = bytes(44)

        mock_ru = MagicMock()
        mock_ru.name = "russian-engine"
        mock_ru.engine_type = EngineType.COQUI
        mock_ru.model_info = ModelInfo(
            id="russian-engine",
            name="Russian Engine",
            engine_type=EngineType.COQUI,
            model_path="mock/ru",
            languages=["ru-RU"],
            default_language="ru-RU",
            parameters=ParameterSchema(parameters=[]),
            sample_rate=22050,
        )
        mock_ru.is_available.return_value = True
        mock_ru.sample_rate = 22050
        mock_ru.synthesize.return_value = bytes(44)

        registry.register(mock_en, is_default=True)
        registry.register(mock_ru)

        service = SynthesisService()

        # Russian text but explicitly request English engine
        request = SynthesisRequest(
            text="Привет мир",  # Russian text
            model_id="english-engine",  # Explicit model
        )

        result = service.synthesize(request)
        # Should use explicitly requested engine, not detected language
        assert result.metadata.model_id == "english-engine"
