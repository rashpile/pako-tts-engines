"""Configuration loading and validation."""

import os
from pathlib import Path

import structlog
import yaml

from app.models.config import ServiceConfig

logger = structlog.get_logger(__name__)

_config: ServiceConfig | None = None


def load_config(config_path: str | Path | None = None) -> ServiceConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yaml
                    in the current directory or CONFIG_PATH env var.

    Returns:
        Loaded and validated configuration.

    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config file is invalid.
    """
    global _config

    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config.yaml")

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path) as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}") from e

    if raw_config is None:
        raw_config = {}

    try:
        _config = ServiceConfig(**raw_config)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e

    logger.info(
        "config.loaded",
        engines_count=len(_config.engines),
        server_port=_config.server.port,
    )

    return _config


def get_config() -> ServiceConfig:
    """Get the current configuration.

    Returns:
        Current configuration.

    Raises:
        RuntimeError: If configuration has not been loaded.
    """
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config


def reset_config() -> None:
    """Reset configuration state. Used for testing."""
    global _config
    _config = None
