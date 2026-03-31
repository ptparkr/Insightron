"""
Insightron Configuration - Backward Compatibility Layer

Migrated to TOML-based config in v4.1.0.
This module provides backward compatibility for legacy code.
"""

# Re-export from new modular config system
from insightron.core.config import (
    ConfigManager,
    get_config_manager,
    get_config,
    get_all_config,
    check_config_file,
    get_default_config_path,
    # Legacy constants
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    TRANSCRIPTION_FOLDER,
    PROCESSED_AUDIO_FOLDER,
    OUTPUT_ENCODING,
    ENSURE_UTF8_ENCODING,
)

# Backward compatibility - lazy fallback to YAML
import warnings
from pathlib import Path as _Path

_CONFIG_YAML = _Path(__file__).parent.parent.parent / "config.yaml"


def _warn_yaml():
    warnings.warn(
        "config.yaml is deprecated. Use config.toml instead.",
        DeprecationWarning,
        stacklevel=2,
    )


# Keep YAML loading for transition period
try:
    import yaml

    if _CONFIG_YAML.exists():
        with open(_CONFIG_YAML) as f:
            _yaml_config = yaml.safe_load(f)

        # Override with YAML values if they exist
        if _yaml_config:
            _warn_yaml()
except Exception:
    _yaml_config = {}

__all__ = [
    "ConfigManager",
    "get_config_manager",
    "get_config",
    "get_all_config",
    "check_config_file",
    "get_default_config_path",
    # Legacy
    "WHISPER_MODEL",
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "TRANSCRIPTION_FOLDER",
    "PROCESSED_AUDIO_FOLDER",
    "OUTPUT_ENCODING",
    "ENSURE_UTF8_ENCODING",
]
