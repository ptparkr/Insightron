"""
Transcription services module.

Provides backward compatibility while using new optimized pipeline.
"""

import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Re-export from new optimized pipeline
from insightron.services.pipeline.core import (
    TranscriptionPipeline,
    TranscriptionResult,
    get_pipeline,
)

# Import new components
from insightron.services.audio.loader import AudioLoader as _NewAudioLoader
from insightron.services.audio.formatter import TextFormatter as _NewFormatter

# Legacy imports for compatibility
from insightron.core.config import (
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


class AudioTranscriber:
    """
    Backward compatible transcriber.
    Uses new optimized pipeline internally.
    """

    def __init__(
        self, model_size: str = WHISPER_MODEL, language: str = DEFAULT_LANGUAGE
    ):
        warnings.warn(
            "AudioTranscriber is deprecated. Use TranscriptionPipeline instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self._pipeline = TranscriptionPipeline(model_size, language)
        self.model_size = model_size
        self.language = language
        self.max_retries = 3
        self.loader = _NewAudioLoader()

    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        meta = self.loader.get_metadata(audio_path)
        duration = meta.duration_seconds
        if duration > 0:
            total_seconds = int(round(duration))
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration_formatted = f"{minutes}:{seconds:02d}"
        else:
            duration_formatted = "Unknown"

        return {
            "filename": meta.filename,
            "duration_seconds": meta.duration_seconds,
            "sample_rate": meta.sample_rate,
            "channels": meta.channels,
            "file_size_mb": meta.file_size_mb,
            "duration_formatted": duration_formatted,
            "file_extension": Path(audio_path).suffix.lower(),
        }

    def transcribe_file(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        formatting_style: str = "auto",
        language: Optional[str] = None,
    ) -> tuple[Path, Dict[str, Any]]:
        result = self._pipeline.transcribe(
            audio_path=audio_path,
            progress_callback=progress_callback,
            formatting_style=formatting_style,
            language=language,
        )

        result_data = {
            "version": "4.1.0",
            "metadata": {
                "filename": result.metadata.get("filename"),
                "duration_seconds": result.metadata.get("duration_seconds"),
                "source_path": audio_path,
            },
            "transcription": {
                "full_text": result.full_text,
                "segments": result.segments,
                "language": result.metadata.get("language"),
                "model": result.metadata.get("model"),
            },
            "stats": {
                "processing_time": result.processing_time,
            },
        }

        return result.output_path, result_data

    def validate_resources(self) -> None:
        from insightron.core.resources import get_resource_pool

        pool = get_resource_pool()
        health = pool.check_health()
        if health.get("status") == "critical":
            raise RuntimeError(f"Critical: {health.get('warnings')}")


# Backward compatible exports
def get_audio_loader() -> _NewAudioLoader:
    return _NewAudioLoader()


def get_text_formatter(view: str = "auto") -> _NewFormatter:
    return _NewFormatter(view)


__all__ = [
    "AudioTranscriber",
    "TranscriptionPipeline",
    "TranscriptionResult",
    "get_pipeline",
    "get_audio_loader",
    "get_text_formatter",
]
