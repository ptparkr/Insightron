"""
Core module for Insightron.

This module provides foundational components including:
- Configuration management (ConfigManager)
- Model management (ModelManager)
- Utility functions (formatting, markdown creation)
- Settings persistence (SettingsManager)
"""

from insightron.core.config import ConfigManager, get_config_manager
from insightron.core.model_manager import ModelManager
from insightron.core.settings_manager import SettingsManager
from insightron.core.utils import (
    create_markdown,
    create_realtime_note,
    format_text,
    format_duration,
    sanitize_filename
)

__all__ = [
    'ConfigManager',
    'get_config_manager',
    'ModelManager',
    'SettingsManager',
    'create_markdown',
    'create_realtime_note',
    'format_text',
    'format_duration',
    'sanitize_filename',
]
