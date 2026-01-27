import logging
from typing import Optional, Iterator, Dict, Any, Callable
from faster_whisper.transcribe import TranscriptionInfo, Segment

from insightron.core.model_manager import ModelManager
from insightron.core.config import get_config_manager

# Configure logging
logger = logging.getLogger(__name__)

class TranscriptionEngine:
    """
    Manages the transcription process, interacting with ModelManager
    and handling the segment generation loop.
    """

    def __init__(self):
        self.model_manager = ModelManager()
        
        config = get_config_manager()
        self.min_segment_duration = config.get('insightron.services.transcription.min_segment_duration', 0.1)
        self.progress_update_frequency = config.get('insightron.services.transcription.progress_update_frequency', 5)
        self.enable_segment_filtering = config.get('insightron.services.transcription.enable_segment_filtering', True)
        self.segment_merge_threshold = config.get('insightron.services.transcription.segment_merge_threshold', -0.5)

    @property
    def model_size(self):
        return self.model_manager.model_size

    def transcribe(
        self,
        audio_input: Any,
        language: Optional[str] = None,
        beam_size: int = 5,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> tuple[list[Dict[str, Any]], TranscriptionInfo]:
        """
        Run the transcription and return raw segments and info.
        Handles segment filtering and progress updates.
        """
        
        # 1. Call ModelManager
        # Note: ModelManager.transcribe returns (Iterator[Segment], TranscriptionInfo)
        segments_iter, info = self.model_manager.transcribe(
            audio_input,
            beam_size=beam_size,
            language=language,
            task="transcribe"
        )
        
        if progress_callback:
            progress_callback(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
        # 2. Process segments loop
        transcribed_segments = []
        total_duration = info.duration
        last_progress_percent = -1
        
        for segment in segments_iter:
            # Smart segment filtering
            segment_duration = segment.end - segment.start
            if self.enable_segment_filtering:
                if segment_duration < self.min_segment_duration:
                    if hasattr(segment, 'avg_logprob') and segment.avg_logprob < self.segment_merge_threshold:
                        logger.debug(f"Filtered micro-segment: {segment.text} ({segment_duration:.2f}s)")
                        continue
            
            # Convert to dict
            segment_data = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            }
            if hasattr(segment, 'avg_logprob'):
                segment_data["confidence"] = float(segment.avg_logprob)
            
            transcribed_segments.append(segment_data)
            
            # Progress updates
            if progress_callback and total_duration > 0:
                current_percent = int((segment.end / total_duration) * 100)
                if current_percent - last_progress_percent >= self.progress_update_frequency:
                    progress_callback(f"Transcribing: {current_percent}% ({int(segment.end)}s/{int(total_duration)}s)")
                    last_progress_percent = current_percent
                    
        return transcribed_segments, info
