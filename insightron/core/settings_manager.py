import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Manages application settings and persistence.
    """
    
    def __init__(self, config_file: str = "user_settings.json"):
        self.config_file = Path(config_file)
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        default_settings = {
            "model": "medium",
            "language": "English - en",
            "formatting": "Auto (Smart Paragraphs)",
            "theme": "Dark",
            "last_folder": str(Path.home())
        }
        
        if not self.config_file.exists():
            return default_settings
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**default_settings, **saved_settings}
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return default_settings

    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        self.settings[key] = value
        self.save_settings()
