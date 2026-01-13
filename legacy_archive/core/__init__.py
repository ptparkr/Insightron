"""
Core module for Insightron.

Provides foundational components including configuration management,
model management, utilities, and settings.
"""

from core.model_manager import ModelManager
from core.config import get_config
from core.utils import create_markdown, create_realtime_note
from core.settings_manager import SettingsManager

__all__ = [
    'ModelManager',
    'get_config',
    'create_markdown',
    'create_realtime_note',
    'SettingsManager',
]
