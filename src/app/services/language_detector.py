"""Language detection service using lingua."""

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from lingua import LanguageDetector as LinguaDetector

logger = structlog.get_logger(__name__)


class LanguageDetectorService:
    """Service for detecting text language using lingua."""

    # Mapping from lingua Language enum to ISO 639-1 codes
    # lingua uses full language names, we need 2-letter codes for BCP-47 matching
    LANGUAGE_TO_ISO: dict[str, str] = {
        "AFRIKAANS": "af",
        "ALBANIAN": "sq",
        "ARABIC": "ar",
        "ARMENIAN": "hy",
        "AZERBAIJANI": "az",
        "BASQUE": "eu",
        "BELARUSIAN": "be",
        "BENGALI": "bn",
        "BOKMAL": "nb",
        "BOSNIAN": "bs",
        "BULGARIAN": "bg",
        "CATALAN": "ca",
        "CHINESE": "zh",
        "CROATIAN": "hr",
        "CZECH": "cs",
        "DANISH": "da",
        "DUTCH": "nl",
        "ENGLISH": "en",
        "ESPERANTO": "eo",
        "ESTONIAN": "et",
        "FINNISH": "fi",
        "FRENCH": "fr",
        "GANDA": "lg",
        "GEORGIAN": "ka",
        "GERMAN": "de",
        "GREEK": "el",
        "GUJARATI": "gu",
        "HEBREW": "he",
        "HINDI": "hi",
        "HUNGARIAN": "hu",
        "ICELANDIC": "is",
        "INDONESIAN": "id",
        "IRISH": "ga",
        "ITALIAN": "it",
        "JAPANESE": "ja",
        "KAZAKH": "kk",
        "KOREAN": "ko",
        "LATIN": "la",
        "LATVIAN": "lv",
        "LITHUANIAN": "lt",
        "MACEDONIAN": "mk",
        "MALAY": "ms",
        "MAORI": "mi",
        "MARATHI": "mr",
        "MONGOLIAN": "mn",
        "NYNORSK": "nn",
        "PERSIAN": "fa",
        "POLISH": "pl",
        "PORTUGUESE": "pt",
        "PUNJABI": "pa",
        "ROMANIAN": "ro",
        "RUSSIAN": "ru",
        "SERBIAN": "sr",
        "SHONA": "sn",
        "SLOVAK": "sk",
        "SLOVENE": "sl",
        "SOMALI": "so",
        "SOTHO": "st",
        "SPANISH": "es",
        "SWAHILI": "sw",
        "SWEDISH": "sv",
        "TAGALOG": "tl",
        "TAMIL": "ta",
        "TELUGU": "te",
        "THAI": "th",
        "TSONGA": "ts",
        "TSWANA": "tn",
        "TURKISH": "tr",
        "UKRAINIAN": "uk",
        "URDU": "ur",
        "VIETNAMESE": "vi",
        "WELSH": "cy",
        "XHOSA": "xh",
        "YORUBA": "yo",
        "ZULU": "zu",
    }

    def __init__(self) -> None:
        """Initialize language detector."""
        self._detector: LinguaDetector | None = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy initialization of lingua detector."""
        if self._initialized:
            return

        try:
            from lingua import LanguageDetectorBuilder

            # Build detector with all languages for maximum coverage
            self._detector = (
                LanguageDetectorBuilder.from_all_languages()
                .with_preloaded_language_models()
                .build()
            )
            self._initialized = True
            logger.info("language_detector.initialized")
        except Exception as e:
            logger.error("language_detector.init_failed", error=str(e))
            self._initialized = True  # Don't retry on failure

    def detect(self, text: str) -> str | None:
        """Detect the language of the given text.

        Args:
            text: Text to analyze.

        Returns:
            ISO 639-1 language code (e.g., "en", "ru", "ro") or None if detection fails.
        """
        if not text or not text.strip():
            return None

        self._ensure_initialized()

        if self._detector is None:
            logger.warning("language_detector.not_available")
            return None

        try:
            detected = self._detector.detect_language_of(text)

            if detected is None:
                logger.debug(
                    "language_detector.no_match",
                    text_preview=text[:50] if len(text) > 50 else text,
                )
                return None

            # Convert lingua Language enum to ISO 639-1 code
            lang_name = detected.name
            iso_code = self.LANGUAGE_TO_ISO.get(lang_name)

            if iso_code is None:
                logger.warning(
                    "language_detector.unknown_mapping",
                    lingua_language=lang_name,
                )
                return None

            logger.debug(
                "language_detector.detected",
                iso_code=iso_code,
                lingua_language=lang_name,
                text_preview=text[:50] if len(text) > 50 else text,
            )
            return iso_code

        except Exception as e:
            logger.error(
                "language_detector.detection_failed",
                error=str(e),
            )
            return None

    def detect_with_confidence(
        self, text: str
    ) -> tuple[str | None, float]:
        """Detect language with confidence score.

        Args:
            text: Text to analyze.

        Returns:
            Tuple of (ISO 639-1 code or None, confidence 0.0-1.0).
        """
        if not text or not text.strip():
            return None, 0.0

        self._ensure_initialized()

        if self._detector is None:
            return None, 0.0

        try:
            # Get confidence values for all languages
            confidences = self._detector.compute_language_confidence_values(text)

            if not confidences:
                return None, 0.0

            # Get the highest confidence result
            top_result = confidences[0]
            lang_name = top_result.language.name
            confidence = top_result.value

            iso_code = self.LANGUAGE_TO_ISO.get(lang_name)

            return iso_code, confidence

        except Exception as e:
            logger.error(
                "language_detector.confidence_failed",
                error=str(e),
            )
            return None, 0.0


# Global detector instance
_language_detector: LanguageDetectorService | None = None


def get_language_detector() -> LanguageDetectorService:
    """Get the global language detector.

    Returns:
        Global language detector instance.
    """
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetectorService()
    return _language_detector


def reset_language_detector() -> None:
    """Reset the global language detector. Used for testing."""
    global _language_detector
    _language_detector = None
