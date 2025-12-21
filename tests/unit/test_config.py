"""Unit tests for configuration loading and validation."""

import os
import tempfile
from collections.abc import Generator

import pytest

from app.config import get_config, load_config, reset_config


@pytest.fixture(autouse=True)
def clean_state() -> Generator[None, None, None]:
    """Reset config state before and after each test."""
    reset_config()
    yield
    reset_config()


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_load_valid_config(self) -> None:
        """Valid config file is loaded successfully."""
        config_content = """
server:
  host: "127.0.0.1"
  port: 9000

engines:
  - name: test-engine
    type: coqui
    model: test/model
    languages: [en-US]

logging:
  level: debug
  format: text
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.server.host == "127.0.0.1"
            assert config.server.port == 9000
            assert len(config.engines) == 1
            assert config.engines[0].name == "test-engine"
        finally:
            os.unlink(temp_path)

    def test_load_config_with_defaults(self) -> None:
        """Config with missing optional fields uses defaults."""
        config_content = """
engines: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            # Check defaults are applied
            assert config.server.host == "0.0.0.0"
            assert config.server.port == 8000
            assert config.server.max_queue_size == 100
            assert config.logging.level == "info"
            assert config.logging.format == "json"
        finally:
            os.unlink(temp_path)

    def test_load_missing_config_raises_error(self) -> None:
        """Missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_invalid_yaml_raises_error(self) -> None:
        """Invalid YAML raises ValueError."""
        config_content = """
server:
  - this is invalid
  port: "not a number
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_config_before_load_raises_error(self) -> None:
        """Getting config before loading raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Configuration not loaded"):
            get_config()

    def test_config_from_env_variable(self) -> None:
        """Config path from environment variable is used."""
        config_content = """
server:
  port: 8888
engines: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            os.environ["CONFIG_PATH"] = temp_path
            config = load_config()
            assert config.server.port == 8888
        finally:
            os.unlink(temp_path)
            del os.environ["CONFIG_PATH"]


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_engine_config_requires_name(self) -> None:
        """Engine config without name is rejected."""
        config_content = """
engines:
  - type: coqui
    model: test/model
    languages: [en-US]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_engine_config_requires_type(self) -> None:
        """Engine config without type is rejected."""
        config_content = """
engines:
  - name: test
    model: test/model
    languages: [en-US]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_engine_config_requires_languages(self) -> None:
        """Engine config without languages is rejected."""
        config_content = """
engines:
  - name: test
    type: coqui
    model: test/model
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestGracefulDegradation:
    """Tests for graceful degradation with unavailable engines."""

    def test_empty_engine_list_is_valid(self) -> None:
        """Empty engine list is valid (graceful degradation)."""
        config_content = """
engines: []
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert len(config.engines) == 0
        finally:
            os.unlink(temp_path)

    def test_multiple_engines_with_default(self) -> None:
        """Multiple engines with one default is valid."""
        config_content = """
engines:
  - name: engine1
    type: coqui
    model: test/model1
    languages: [en-US]
    default: false

  - name: engine2
    type: coqui
    model: test/model2
    languages: [en-GB]
    default: true
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert len(config.engines) == 2

            default_engines = [e for e in config.engines if e.default]
            assert len(default_engines) == 1
            assert default_engines[0].name == "engine2"
        finally:
            os.unlink(temp_path)
