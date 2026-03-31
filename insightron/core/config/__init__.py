from pathlib import Path
from typing import Any, Optional

from insightron.core.config.loader import (
    get_config,
    get_all_config,
    reload_config,
    CONFIG_FILE,
)
from insightron.core.config.models import (
    ModelConfig,
    DecodeConfig,
    AudioPreprocessConfig,
    DiarizationConfig,
    RealtimeConfig,
    PostProcessingConfig,
    TranscriptionConfig,
    MultiPassConfig,
    RuntimeConfig,
    ReportConfig,
)

# Backward compatibility - create singleton from TOML or defaults
_config_instance: Optional[Any] = None


def get_config_manager() -> "ConfigManager":
    """Get singleton ConfigManager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


class ConfigManager:
    """
    Unified configuration interface with O(1) lookup.
    Combines TOML fast loading with dataclass defaults.
    """

    def __init__(self):
        self._config = get_all_config()
        self._init_dataclasses()

    def _init_dataclasses(self):
        """Initialize dataclass configurations from TOML."""
        # Model config
        model_data = self._config.get("model", {})
        self.model = ModelConfig(
            name=model_data.get("name", "medium"),
            compute_type=model_data.get("compute_type", "int8"),
            device=model_data.get("device", "auto"),
            quality_mode=model_data.get("quality_mode", "balanced"),
            enable_vad=model_data.get("enable_vad", True),
            enable_retry=model_data.get("enable_retry", True),
            max_retries=model_data.get("max_retries", 2),
            adaptive_vad=model_data.get("adaptive_vad", False),
            batch_size=model_data.get("batch_size", 1),
            enable_warmup=model_data.get("enable_warmup", True),
            enable_dynamic_beam=model_data.get("enable_dynamic_beam", True),
        )

        # Decode config
        decode_data = model_data.get("decode", {})
        self.decode = DecodeConfig(
            beam_size=decode_data.get("beam_size", 5),
            best_of=decode_data.get("best_of", 5),
            temperature=decode_data.get("temperature", [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
            condition_on_previous_text=decode_data.get(
                "condition_on_previous_text", True
            ),
            compression_ratio_threshold=decode_data.get(
                "compression_ratio_threshold", 2.4
            ),
            log_prob_threshold=decode_data.get("log_prob_threshold", -1.0),
            no_speech_threshold=decode_data.get("no_speech_threshold", 0.6),
            word_timestamps=decode_data.get("word_timestamps", True),
            initial_prompt=decode_data.get("initial_prompt", ""),
        )

        # Audio preprocess config
        preprocess_data = self._config.get("audio_preprocess", {})
        self.audio_preprocess = AudioPreprocessConfig(
            enabled=preprocess_data.get("enabled", True),
            noise_reduction_enabled=preprocess_data.get("noise_reduction", {}).get(
                "enabled", True
            ),
            noise_reduction_stationary=preprocess_data.get("noise_reduction", {}).get(
                "stationary", True
            ),
            noise_reduction_prop_decrease=preprocess_data.get(
                "noise_reduction", {}
            ).get("prop_decrease", 0.75),
            loudness_enabled=preprocess_data.get("loudness", {}).get("enabled", True),
            loudness_target_lufs=preprocess_data.get("loudness", {}).get(
                "target_lufs", -23.0
            ),
            pre_emphasis_enabled=preprocess_data.get("pre_emphasis", {}).get(
                "enabled", True
            ),
            pre_emphasis_coeff=preprocess_data.get("pre_emphasis", {}).get(
                "coeff", 0.97
            ),
            trim_enabled=preprocess_data.get("trim", {}).get("enabled", True),
            trim_top_db=preprocess_data.get("trim", {}).get("top_db", 20.0),
        )

        # Diarization config
        diarization_data = self._config.get("diarization", {})
        self.diarization = DiarizationConfig(
            enabled=diarization_data.get("enabled", False),
            model=diarization_data.get("model", "pyannote/embedding"),
            cluster_threshold=diarization_data.get("cluster_threshold", 0.5),
        )

        # Realtime config
        realtime_data = self._config.get("realtime", {})
        self.realtime = RealtimeConfig(
            buffer_duration_seconds=realtime_data.get("buffer_duration_seconds", 30.0),
            chunk_duration_seconds=realtime_data.get("chunk_duration_seconds", 5.0),
            stride_seconds=realtime_data.get("stride_seconds", 1.0),
            silence_threshold=realtime_data.get("silence_threshold", 0.015),
            silence_duration=realtime_data.get("silence_duration", 0.5),
        )

        # Post-processing config
        post_data = self._config.get("post_processing", {})
        self.post_processing = PostProcessingConfig(
            formatting_profile=post_data.get("formatting_profile", "thinking_session"),
        )

        # Transcription config
        transcription_data = self._config.get("transcription", {})
        self.transcription = TranscriptionConfig(
            segment_merge_threshold=transcription_data.get(
                "segment_merge_threshold", -0.5
            ),
            enable_audio_preprocessing=transcription_data.get(
                "enable_audio_preprocessing", True
            ),
            min_confidence=transcription_data.get("min_confidence", -1.0),
            filename_template=transcription_data.get(
                "filename_template", "{stem}_transcription.md"
            ),
        )

        # Multi-pass config
        multipass_data = self._config.get("multi_pass", {})
        self.multi_pass = MultiPassConfig(
            enabled=multipass_data.get("enabled", True),
            chunk_duration=multipass_data.get("chunk_duration", 30.0),
            chunk_overlap=multipass_data.get("chunk_overlap", 2.0),
        )

        # Runtime config
        runtime_data = self._config.get("runtime", {})
        self.runtime = RuntimeConfig(
            worker_count=runtime_data.get("worker_count"),
            transcription_folder=Path(
                runtime_data.get("transcription_folder", "transcriptions")
            ),
            processed_audio_folder=Path(
                runtime_data.get("processed_audio_folder", "processed_audio")
            ),
        )

        # Report config
        report_data = self._config.get("report", {})
        self.report = ReportConfig(
            style=report_data.get("style", "classic"),
        )

    def get(self, path: str, default: Any = None) -> Any:
        """Get config by dot-notation path with O(1) lookup."""
        return get_config(path, default)

    def reload(self) -> None:
        """Reload configuration from file."""
        reload_config()
        self._config = get_all_config()
        self._init_dataclasses()

    @property
    def transcription_folder(self) -> Path:
        return self.runtime.transcription_folder

    @property
    def processed_audio_folder(self) -> Path:
        return self.runtime.processed_audio_folder


# Backward compatibility aliases
WHISPER_MODEL = "medium"
DEFAULT_LANGUAGE = "auto"
SUPPORTED_LANGUAGES = {
    "auto": "Auto Detect",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
}
TRANSCRIPTION_FOLDER = Path("transcriptions")
PROCESSED_AUDIO_FOLDER = Path("processed_audio")
OUTPUT_ENCODING = "utf-8"
ENSURE_UTF8_ENCODING = True
APP_VERSION = "4.1.0"


def get_config_with_fallback(path: str, default: Any = None) -> Any:
    """Get config with fallback to old YAML-based config."""
    # First try TOML
    value = get_config(path, None)
    if value is not None:
        return value

    # Fallback to ConfigManager
    try:
        manager = get_config_manager()
        return manager.get(path, default)
    except Exception:
        return default


def check_config_file() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()


def get_default_config_path() -> Path:
    """Get default config file path."""
    return CONFIG_FILE
