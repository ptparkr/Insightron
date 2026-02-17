import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import numpy as np

from insightron.core.config import (
    WHISPER_MODEL, 
    DEFAULT_LANGUAGE, 
    SUPPORTED_LANGUAGES,
    get_config
)

# New components
from insightron.services.transcription.audio_loader import AudioLoader
from insightron.services.transcription.transcription_engine import TranscriptionEngine
from insightron.services.transcription.result_handler import ResultHandler
from insightron.services.base_transcriber import BaseTranscriber

# Multi-pass components
from insightron.services.transcription.multi_pass_transcriber import MultiPassTranscriber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriber(BaseTranscriber):
    """
    Execution Orchestrator for Insightron.
    Mental model: conductor, not musician.
    
    Responsibilities:
    - Chunk audio deterministically
    - Pass correct context windows
    - Handle retries and failures cleanly
    - Guarantee order preservation and timestamp integrity
    """
    
    def __init__(self, model_size: str = WHISPER_MODEL, language: str = DEFAULT_LANGUAGE):
        super().__init__(model_size=model_size)
        self.loader = AudioLoader()
        self.engine = TranscriptionEngine()
        self.handler = ResultHandler()
        self.language = language
        self.max_retries = 3

    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive audio metadata for integration tests and callers.

        Wraps `AudioLoader.get_audio_metadata` and adds:
        - `duration_formatted` (MM:SS)
        - `file_extension`
        """
        metadata = self.loader.get_audio_metadata(audio_path)
        duration = float(metadata.get("duration_seconds") or 0.0)

        if duration > 0:
            # Round total duration first so that fractional seconds correctly
            # carry over into minutes (e.g. 59.5s -> 1:00 instead of 0:60).
            total_seconds = int(round(duration))
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            metadata["duration_formatted"] = f"{minutes}:{seconds:02d}"
        else:
            metadata["duration_formatted"] = "Unknown"

        from pathlib import Path

        metadata["file_extension"] = Path(audio_path).suffix.lower()
        return metadata

    def transcribe_file(
        self, 
        audio_path: str, 
        progress_callback: Optional[Callable[[str], None]] = None,
        formatting_style: str = "auto",
        language: Optional[str] = None,
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Coordinate the transcription execution flow.
        """
        start_time = datetime.now()
        target_language = language or self.language
        
        try:
            # 0. Resource Validation
            self.validate_resources()

            # 1. Signal Intake
            self.loader.validate_audio_file(audio_path)
            metadata = self.loader.get_audio_metadata(audio_path)
            signal = self.loader.load_signal(audio_path)
            
            if progress_callback:
                progress_callback(f"Signal intake complete. Analyzing {metadata['filename']}...")

            # 2. Deterministic Chunking (30s windows)
            # This ensures stable processing for long files
            chunks = self.loader.segment_by_time(signal, segment_seconds=30.0)
            
            all_segments = []
            num_chunks = len(chunks)
            
            # 3. Execution Loop
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(f"Processing chunk {i+1}/{num_chunks}...")
                
                # Retry Logic
                chunk_segments = self._execute_chunk_with_retry(
                    chunk["signal"], 
                    target_language,
                    chunk["start_time"]
                )
                
                all_segments.extend(chunk_segments)

            processing_time = (datetime.now() - start_time).total_seconds()

            # 4. Final Export Contract
            output_path, result_data = self.handler.save_result(
                audio_path=audio_path,
                segments=all_segments,
                metadata=metadata,
                processing_time=processing_time,
                model_size=self.model_size,
                language=target_language,
                formatting_style=formatting_style,
            )

            if progress_callback:
                progress_callback("✓ Pipeline execution complete.")

            return output_path, result_data

        except Exception as e:
            logger.error(f"Execution Orchestrator failure: {e}")
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise

    def _execute_chunk_with_retry(self, signal: np.ndarray, language: str, offset_time: float) -> List[Dict[str, Any]]:
        """Execute transcription for a chunk with basic retry logic."""
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Delegate to the Brain (TranscriptionEngine)
                return self.engine.process_signal_single_pass(
                    signal, 
                    language=language, 
                    offset_time=offset_time
                )
            except Exception as e:
                attempt += 1
                logger.warning(f"Chunk execution attempt {attempt} failed: {e}")
                if attempt >= self.max_retries:
                    raise
        return []
