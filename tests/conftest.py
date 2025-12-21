"""Shared test fixtures."""

import os
import tempfile
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import reset_config
from app.engines.registry import reset_registry
from app.services.language_detector import reset_language_detector
from app.services.queue import reset_request_queue
from app.services.synthesis import reset_synthesis_service


@pytest.fixture
def temp_config_file() -> Generator[str, None, None]:
    """Create a temporary config file for testing.

    Yields:
        Path to temporary config file.
    """
    config_content = """
server:
  host: "127.0.0.1"
  port: 8000
  max_queue_size: 10
  max_text_length: 1000
  synthesis_timeout: 5

engines:
  - name: test-engine
    type: coqui
    model: tts_models/en/ljspeech/vits
    languages: [en-US]
    default: true

logging:
  level: debug
  format: text
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def minimal_config_file() -> Generator[str, None, None]:
    """Create a minimal config file for testing without engines.

    Yields:
        Path to temporary config file.
    """
    config_content = """
server:
  host: "127.0.0.1"
  port: 8000
  max_text_length: 1000

engines: []

logging:
  level: debug
  format: text
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    """Reset global state before and after each test."""
    reset_config()
    reset_registry()
    reset_synthesis_service()
    reset_request_queue()
    reset_language_detector()
    yield
    reset_config()
    reset_registry()
    reset_synthesis_service()
    reset_request_queue()
    reset_language_detector()


@pytest.fixture
def mock_engine() -> Any:
    """Create a mock TTS engine for testing.

    Returns:
        Mock engine instance.
    """
    from unittest.mock import MagicMock

    from app.engines.base import TTSEngine
    from app.models.engine import EngineType, ModelInfo, ParameterSchema

    mock = MagicMock(spec=TTSEngine)
    mock.engine_type = EngineType.COQUI
    mock.name = "mock-engine"
    mock.model_info = ModelInfo(
        id="mock-engine",
        name="Mock Engine",
        engine_type=EngineType.COQUI,
        model_path="mock/model",
        languages=["en-US"],
        default_language="en-US",
        parameters=ParameterSchema(parameters=[]),
        is_default=True,
        sample_rate=22050,
    )
    mock.supported_languages = ["en-US"]
    mock.parameter_schema = ParameterSchema(parameters=[])
    mock.sample_rate = 22050
    mock.is_available.return_value = True

    # Return minimal WAV audio (44 byte header + 0 samples)
    wav_header = bytes(
        [
            0x52,
            0x49,
            0x46,
            0x46,  # "RIFF"
            0x24,
            0x00,
            0x00,
            0x00,  # ChunkSize (36 bytes)
            0x57,
            0x41,
            0x56,
            0x45,  # "WAVE"
            0x66,
            0x6D,
            0x74,
            0x20,  # "fmt "
            0x10,
            0x00,
            0x00,
            0x00,  # Subchunk1Size (16 for PCM)
            0x01,
            0x00,  # AudioFormat (1 = PCM)
            0x01,
            0x00,  # NumChannels (1 = mono)
            0x22,
            0x56,
            0x00,
            0x00,  # SampleRate (22050)
            0x44,
            0xAC,
            0x00,
            0x00,  # ByteRate (22050 * 1 * 2)
            0x02,
            0x00,  # BlockAlign (1 * 2)
            0x10,
            0x00,  # BitsPerSample (16)
            0x64,
            0x61,
            0x74,
            0x61,  # "data"
            0x00,
            0x00,
            0x00,
            0x00,  # Subchunk2Size (0 bytes of audio)
        ]
    )
    mock.synthesize.return_value = wav_header

    return mock


@pytest.fixture
def test_client(minimal_config_file: str, mock_engine: Any) -> TestClient:
    """Create a test client with mocked engine.

    Args:
        minimal_config_file: Path to minimal config file.
        mock_engine: Mock TTS engine.

    Returns:
        TestClient for the application.
    """
    import os

    os.environ["CONFIG_PATH"] = minimal_config_file

    from app.engines.registry import get_registry
    from app.main import create_app

    # Reset state
    reset_config()
    reset_registry()

    # Create app
    app = create_app(minimal_config_file)

    # Register mock engine
    registry = get_registry()
    registry.register(mock_engine, is_default=True)

    return TestClient(app)
