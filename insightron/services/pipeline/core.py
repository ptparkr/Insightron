"""
Transcription Pipeline - Unified single-pass pipeline

Merges:
- base_transcriber.py (literal transcription)
- transcription_engine.py (error resolution)
- transcribe.py (orchestration)

Features:
- O(1) component lookup
- Lazy loading
- Event-driven progress
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Transcription result container."""

    output_path: Path
    full_text: str
    segments: list[dict]
    metadata: dict
    processing_time: float


class TranscriptionPipeline:
    """
    Unified transcription pipeline.
    Single entry point for all transcription needs.
    """

    def __init__(self, model_size: str = "medium", language: str = "auto"):
        self.model_size = model_size
        self.language = language
        self._model_manager = None
        self._loader = None
        self._formatter = None

    @property
    def model_manager(self):
        """Lazy load model manager."""
        if self._model_manager is None:
            from insightron.core.model import get_model_manager

            self._model_manager = get_model_manager()
        return self._model_manager

    @property
    def loader(self):
        """Lazy load audio loader."""
        if self._loader is None:
            from insightron.services.audio import get_loader

            self._loader = get_loader()
        return self._loader

    @property
    def formatter(self):
        """Lazy load formatter."""
        if self._formatter is None:
            from insightron.services.audio.formatter import get_formatter

            self._formatter = get_formatter()
        return self._formatter

    def transcribe(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
        formatting_style: str = "auto",
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Main transcription entry point."""
        import time
        from datetime import datetime

        start_time = time.time()
        target_lang = language or self.language

        if progress_callback:
            progress_callback(f"Loading {Path(audio_path).name}...")

        # 1. Validate and load
        self.loader.validate(audio_path)
        signal = self.loader.load(audio_path)
        metadata = self.loader.get_metadata(audio_path)

        if progress_callback:
            progress_callback(f"Transcribing ({metadata.duration_seconds:.1f}s)...")

        # 2. Transcribe with model
        segments, info = self.model_manager.model.transcribe(
            signal,
            language=target_lang,
            word_timestamps=True,
        )

        # Convert to list
        segment_list = []
        for seg in segments:
            segment_list.append(
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "confidence": getattr(seg, "avg_logprob", 0),
                    "words": getattr(seg, "words", []),
                }
            )

        # 3. Format output
        if progress_callback:
            progress_callback("Formatting...")

        from insightron.services.audio.formatter import get_formatter

        formatter = get_formatter(formatting_style)
        full_text = formatter.format_segments(segment_list)

        # 4. Save result
        output_path = self._save_result(audio_path, segment_list, full_text, metadata)

        processing_time = time.time() - start_time

        return TranscriptionResult(
            output_path=output_path,
            full_text=full_text,
            segments=segment_list,
            metadata={
                "filename": metadata.filename,
                "duration_seconds": metadata.duration_seconds,
                "language": target_lang,
                "model": self.model_size,
            },
            processing_time=processing_time,
        )

    def transcribe_chunk(
        self,
        signal,
        language: Optional[str] = None,
        offset_time: float = 0.0,
    ) -> list[dict]:
        """Transcribe a single chunk."""
        segments, _ = self.model_manager.model.transcribe(
            signal,
            language=language or self.language,
            word_timestamps=True,
        )

        result = []
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue

            # Light normalization
            text = self._fix_artifacts(text)

            result.append(
                {
                    "start": seg.start + offset_time,
                    "end": seg.end + offset_time,
                    "text": text,
                    "confidence": getattr(seg, "avg_logprob", 0),
                }
            )

        return result

    def _fix_artifacts(self, text: str) -> str:
        """Fix obvious ASR artifacts."""
        words = text.split()
        if not words:
            return text

        # Detect repeating phrases
        if len(words) > 10:
            for i in range(len(words) - 5):
                phrase = words[i : i + 2]
                if words[i + 2 : i + 4] == phrase and words[i + 4 : i + 6] == phrase:
                    return " ".join(words[: i + 2]) + " [ARTIFACT]"

        return text

    def _save_result(
        self, audio_path: str, segments: list, text: str, metadata
    ) -> Path:
        """Save transcription to file."""
        from insightron.core.config import get_config_manager
        from datetime import datetime

        config = get_config_manager()
        output_dir = config.transcription_folder
        output_dir.mkdir(parents=True, exist_ok=True)

        stem = Path(audio_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"{stem}_{timestamp}.md"

        content = f"""# Transcription: {metadata.filename}

## Metadata
- Duration: {metadata.duration_seconds:.1f}s
- Model: {self.model_size}

---

{text}
"""

        output_path.write_text(content, encoding="utf-8")
        logger.info(f"Saved: {output_path}")

        return output_path


def get_pipeline(
    model_size: str = "medium", language: str = "auto"
) -> TranscriptionPipeline:
    """Get transcription pipeline instance."""
    return TranscriptionPipeline(model_size, language)
