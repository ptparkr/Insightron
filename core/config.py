"""
Configuration file for Insightron
Contains paths and settings for the transcription application
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration Dataclasses
# ============================================================================

@dataclass
class ModelConfig:
    """Model configuration settings."""
    name: str = "small"
    compute_type: str = "int8"
    device: str = "auto"
    
    def __post_init__(self):
        """Validate model configuration."""
        valid_models = {
            'tiny', 'base', 'small', 'medium', 'large', 'large-v2',
            'distil-medium.en', 'distil-large-v2'
        }
        if self.name not in valid_models:
            logger.warning(f"Invalid model name '{self.name}'. Defaulting to 'medium'.")
            self.name = "medium"
        
        valid_compute_types = {'float16', 'int8_float16', 'int8', 'float32'}
        if self.compute_type not in valid_compute_types:
            logger.warning(f"Invalid compute_type '{self.compute_type}'. Defaulting to 'int8'.")
            self.compute_type = "int8"
        
        valid_devices = {'auto', 'cpu', 'cuda'}
        if self.device not in valid_devices:
            logger.warning(f"Invalid device '{self.device}'. Defaulting to 'auto'.")
            self.device = "auto"


@dataclass
class RuntimeConfig:
    """Runtime configuration settings."""
    transcription_folder: str = r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Notes"
    recordings_folder: str = r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Recordings"
    processed_audio_folder: str = r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Processed"
    max_file_size_mb: int = 500
    log_level: str = "INFO"
    worker_count: Optional[int] = None  # None = auto-detect
    
    def __post_init__(self):
        """Validate runtime configuration."""
        # Validate max_file_size_mb
        if self.max_file_size_mb <= 0:
            logger.warning(f"Invalid max_file_size_mb '{self.max_file_size_mb}'. Setting to 500.")
            self.max_file_size_mb = 500
        
        # Validate log_level
        valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.log_level.upper() not in valid_log_levels:
            logger.warning(f"Invalid log_level '{self.log_level}'. Defaulting to 'INFO'.")
            self.log_level = "INFO"
        
        # Validate worker_count
        if self.worker_count is not None and self.worker_count <= 0:
            logger.warning(f"Invalid worker_count '{self.worker_count}'. Using auto-detection.")
            self.worker_count = None


@dataclass
class RealtimeConfig:
    """Realtime transcription settings."""
    sample_rate: int = 16000
    buffer_duration_seconds: int = 30
    chunk_duration_seconds: int = 5
    stride_seconds: int = 1
    silence_threshold: float = 0.015
    silence_duration: float = 0.5
    
    def __post_init__(self):
        """Validate realtime configuration."""
        if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
            logger.warning(f"Unusual sample_rate '{self.sample_rate}'. Recommended: 16000.")
        
        if self.buffer_duration_seconds <= 0 or self.buffer_duration_seconds > 300:
            logger.warning(f"Invalid buffer_duration_seconds '{self.buffer_duration_seconds}'. Setting to 30.")
            self.buffer_duration_seconds = 30
        
        if self.chunk_duration_seconds <= 0 or self.chunk_duration_seconds > self.buffer_duration_seconds:
            logger.warning(f"Invalid chunk_duration_seconds '{self.chunk_duration_seconds}'. Setting to 5.")
            self.chunk_duration_seconds = 5
        
        if self.stride_seconds <= 0 or self.stride_seconds > self.chunk_duration_seconds:
            logger.warning(f"Invalid stride_seconds '{self.stride_seconds}'. Setting to 1.")
            self.stride_seconds = 1
        
        if self.silence_threshold < 0 or self.silence_threshold > 1:
            logger.warning(f"Invalid silence_threshold '{self.silence_threshold}'. Setting to 0.015.")
            self.silence_threshold = 0.015


@dataclass
class PostProcessingConfig:
    """Post-processing configuration."""
    enable_language_detection: bool = False
    cache_size: int = 128
    formatting_style: str = "auto"
    
    def __post_init__(self):
        """Validate post-processing configuration."""
        valid_styles = {'auto', 'paragraphs', 'minimal'}
        if self.formatting_style not in valid_styles:
            logger.warning(f"Invalid formatting_style '{self.formatting_style}'. Defaulting to 'auto'.")
            self.formatting_style = "auto"
        
        if self.cache_size <= 0:
            logger.warning(f"Invalid cache_size '{self.cache_size}'. Setting to 128.")
            self.cache_size = 128


# ============================================================================
# Configuration Manager
# ============================================================================

class ConfigManager:
    """
    Singleton configuration manager for Insightron.
    Loads, validates, and provides access to configuration settings.
    """
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls, config_path: str = "config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: str = "config.yaml"):
        if self._initialized:
            return
        
        self._initialized = True
        self.config_path = config_path
        self._raw_config: Dict[str, Any] = {}
        
        # Load configuration
        self._load()
        
        # Initialize config sections
        self.model = self._init_model_config()
        self.runtime = self._init_runtime_config()
        self.realtime = self._init_realtime_config()
        self.post_processing = self._init_post_processing_config()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _load(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f) or {}
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found. Using defaults.")
            self._raw_config = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}. Using defaults.")
            self._raw_config = {}
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}. Using defaults.")
            self._raw_config = {}
    
    def _init_model_config(self) -> ModelConfig:
        """Initialize model configuration."""
        model_data = self._raw_config.get('model', {})
        return ModelConfig(
            name=model_data.get('name', 'small'),
            compute_type=model_data.get('compute_type', 'int8'),
            device=model_data.get('device', 'auto')
        )
    
    def _init_runtime_config(self) -> RuntimeConfig:
        """Initialize runtime configuration."""
        runtime_data = self._raw_config.get('runtime', {})
        return RuntimeConfig(
            transcription_folder=runtime_data.get('transcription_folder', r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Notes"),
            recordings_folder=runtime_data.get('recordings_folder', r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Recordings"),
            processed_audio_folder=runtime_data.get('processed_audio_folder', r"D:\2. Areas\IdeaVerse\Areas\Inner Library\Processed"),
            max_file_size_mb=runtime_data.get('max_file_size_mb', 500),
            log_level=runtime_data.get('log_level', 'INFO'),
            worker_count=runtime_data.get('worker_count')
        )
    
    def _init_realtime_config(self) -> RealtimeConfig:
        """Initialize realtime configuration."""
        realtime_data = self._raw_config.get('realtime', {})
        return RealtimeConfig(
            sample_rate=realtime_data.get('sample_rate', 16000),
            buffer_duration_seconds=realtime_data.get('buffer_duration_seconds', 30),
            chunk_duration_seconds=realtime_data.get('chunk_duration_seconds', 5),
            stride_seconds=realtime_data.get('stride_seconds', 1),
            silence_threshold=realtime_data.get('silence_threshold', 0.015),
            silence_duration=realtime_data.get('silence_duration', 0.5)
        )
    
    def _init_post_processing_config(self) -> PostProcessingConfig:
        """Initialize post-processing configuration."""
        pp_data = self._raw_config.get('post_processing', {})
        return PostProcessingConfig(
            enable_language_detection=pp_data.get('enable_language_detection', False),
            cache_size=pp_data.get('cache_size', 128),
            formatting_style=pp_data.get('formatting_style', 'auto')
        )
    
    def _ensure_directories(self):
        """Ensure that configured directories exist."""
        try:
            Path(self.runtime.transcription_folder).mkdir(parents=True, exist_ok=True)
            Path(self.runtime.recordings_folder).mkdir(parents=True, exist_ok=True)
            Path(self.runtime.processed_audio_folder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
    
    def reload(self):
        """Reload configuration from file."""
        self._load()
        self.model = self._init_model_config()
        self.runtime = self._init_runtime_config()
        self.realtime = self._init_realtime_config()
        self.post_processing = self._init_post_processing_config()
        self._ensure_directories()
        logger.info("Configuration reloaded")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Dot-separated key path (e.g., 'model.name')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        val = self._raw_config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default


# ============================================================================
# Module-level API (Backward Compatible)
# ============================================================================

def load_config(config_path="config.yaml"):
    """Load configuration from a YAML file (legacy function)."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


# Load config using ConfigManager
_config_manager = ConfigManager()

# Legacy config dict for backward compatibility
_config = _config_manager._raw_config


def get_config(key: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation (legacy function).
    
    Args:
        key: Dot-separated key path (e.g., 'model.name')
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    return _config_manager.get(key, default)


def get_config_manager() -> ConfigManager:
    """Get the singleton ConfigManager instance."""
    return _config_manager


# ============================================================================
# Exported Configuration Constants (Backward Compatible)
# ============================================================================

# Whisper model configuration
WHISPER_MODEL = _config_manager.model.name
ENABLE_INT8_QUANTIZATION = _config_manager.model.compute_type == "int8"

# Directory Configuration
TRANSCRIPTION_FOLDER = Path(_config_manager.runtime.transcription_folder)
RECORDINGS_FOLDER = Path(_config_manager.runtime.recordings_folder)
PROCESSED_AUDIO_FOLDER = Path(_config_manager.runtime.processed_audio_folder)

# Backward compatibility alias
OBSIDIAN_VAULT_PATH = TRANSCRIPTION_FOLDER  # Deprecated: use TRANSCRIPTION_FOLDER instead

# Supported audio formats
SUPPORTED_FORMATS = {
    '.mp3', '.wav', '.m4a', '.flac', 
    '.mp4', '.ogg', '.aac', '.wma'
}

# Whisper model information
WHISPER_MODELS = {
    'tiny': {'size': '~39M params', 'speed': 'Fastest', 'accuracy': 'Good'},
    'base': {'size': '~74M params', 'speed': 'Fast', 'accuracy': 'Better'},
    'small': {'size': '~244M params', 'speed': 'Moderate', 'accuracy': 'Good'},
    'medium': {'size': '~769M params', 'speed': 'Slower', 'accuracy': 'Very Good'},
    'large-v2': {'size': '~1550M params', 'speed': 'Slowest', 'accuracy': 'Best'},
    'distil-medium.en': {'size': '~394M params', 'speed': 'Very Fast', 'accuracy': 'Very Good'},
    'distil-large-v2': {'size': '~756M params', 'speed': 'Fast', 'accuracy': 'Best'}
}

# Optimization Settings
REALTIME_BUFFER_SECONDS = _config_manager.realtime.buffer_duration_seconds
REALTIME_SILENCE_THRESHOLD = _config_manager.realtime.silence_threshold

# Formatting styles
FORMATTING_STYLES = {
    'auto': 'Smart paragraph breaks based on content',
    'paragraphs': 'New paragraph every 3 sentences',
    'minimal': 'New paragraph every 5 sentences'
}

# Application metadata
APP_NAME = "Insightron"
APP_VERSION = "2.2.0"
APP_DESCRIPTION = "AI-powered audio transcription with Whisper - Multi-language support"

# Maximum file size (in MB)
MAX_FILE_SIZE_MB = _config_manager.runtime.max_file_size_mb

# Logging configuration
LOG_LEVEL = _config_manager.runtime.log_level

# Multi-language support configuration
SUPPORTED_LANGUAGES = {
    'auto': 'Auto-detect language',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'tr': 'Turkish',
    'pl': 'Polish',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'el': 'Greek',
    'he': 'Hebrew',
    'fa': 'Persian',
    'ur': 'Urdu',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'gu': 'Gujarati',
    'pa': 'Punjabi',
    'mr': 'Marathi',
    'ne': 'Nepali',
    'si': 'Sinhala',
    'my': 'Burmese',
    'km': 'Khmer',
    'lo': 'Lao',
    'ka': 'Georgian',
    'am': 'Amharic',
    'sw': 'Swahili',
    'zu': 'Zulu',
    'af': 'Afrikaans',
    'sq': 'Albanian',
    'az': 'Azerbaijani',
    'eu': 'Basque',
    'be': 'Belarusian',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'cy': 'Welsh',
    'eo': 'Esperanto',
    'gl': 'Galician',
    'is': 'Icelandic',
    'ga': 'Irish',
    'mk': 'Macedonian',
    'mt': 'Maltese',
    'mn': 'Mongolian',
    'ms': 'Malay',
    'oc': 'Occitan',
    'ps': 'Pashto',
    'rm': 'Romansh',
    'sn': 'Shona',
    'so': 'Somali',
    'tg': 'Tajik',
    'tk': 'Turkmen',
    'uk': 'Ukrainian',
    'uz': 'Uzbek',
    'yi': 'Yiddish',
    'yo': 'Yoruba'
}

# Language detection configuration
DEFAULT_LANGUAGE = "auto"  # Auto-detect by default
ENABLE_LANGUAGE_DETECTION = True
ENABLE_MANUAL_LANGUAGE_SELECTION = True

# UTF-8 encoding configuration
ENSURE_UTF8_ENCODING = True
OUTPUT_ENCODING = "utf-8"

print(f"[OK] Insightron Config Loaded v{APP_VERSION}")
print(f"  - Model: {WHISPER_MODEL}")
print(f"  - Output: {TRANSCRIPTION_FOLDER}")
print(f"  - Languages: {len(SUPPORTED_LANGUAGES)} supported")
