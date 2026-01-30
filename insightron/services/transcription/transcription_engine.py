import logging
from typing import Optional, Iterator, Dict, Any, Callable, List
import numpy as np
from faster_whisper.transcribe import TranscriptionInfo, Segment

from insightron.core.model_manager import ModelManager
from insightron.core.config import get_config_manager

# Configure logging
logger = logging.getLogger(__name__)

from insightron.services.base_transcriber import BaseTranscriber

class TranscriptionEngine:
    """
    Single-Pass Brain for Insightron.
    Mental model: first draft that must be usable.
    
    Responsibilities:
    - Resolve obvious ASR errors
    - Fix boundary breaks
    - Apply light normalization
    
    You may NOT:
    - Look ahead multiple times
    - Rewrite stylistically
    - Summarize
    """

    def __init__(self):
        self.literal_transcriber = BaseTranscriber()
        config = get_config_manager()
        self.min_confidence_threshold = config.get('insightron.services.transcription.min_confidence', -1.0)

    def process_signal_single_pass(
        self,
        signal: np.ndarray,
        language: Optional[str] = None,
        offset_time: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Process audio signal in a single forward pass.
        Refines literal output into a stable first draft.
        """
        refined_segments = []
        
        # 1. Get Literal Ground Truth
        # We iterate over the literal stream and refine on-the-fly
        literal_stream = self.literal_transcriber.transcribe_literal(signal, language)
        
        for lit_seg in literal_stream:
            # 2. Light Normalization & Correction
            # - Fix obvious boundary whitespace
            # - Adjust timestamps by chunk offset
            # - Filter extreme low-confidence artifacts
            
            text = lit_seg["text"].strip()
            if not text:
                continue
                
            # Basic ASR Error Resolution (e.g., repeated characters/words from model artifacts)
            # This is a 'brain' function to make the literal truth usable.
            text = self._resolve_obvious_errors(text)
            
            # 3. Create Refined Segment
            refined_seg = {
                "start": lit_seg["start"] + offset_time,
                "end": lit_seg["end"] + offset_time,
                "text": text,
                "confidence": lit_seg["avg_logprob"],
                "words": [
                    {
                        "word": w["word"],
                        "start": w["start"] + offset_time,
                        "end": w["end"] + offset_time,
                        "probability": w["probability"]
                    } for w in lit_seg["words"]
                ]
            }
            
            refined_segments.append(refined_seg)
            
        return refined_segments

    def _resolve_obvious_errors(self, text: str) -> str:
        """Fix obvious ASR artifacts without changing meaning."""
        # Example: Whisper sometimes repeats the same word infinitely in silence
        words = text.split()
        if not words:
            return text
            
        # Very simple deduplication of extreme repeats
        if len(words) > 10:
            # If the same 2-word phrase repeats 3+ times, it's likely an artifact
            for i in range(len(words) - 5):
                phrase = words[i:i+2]
                if words[i+2:i+4] == phrase and words[i+4:i+6] == phrase:
                    logger.warning(f"Detected potential ASR artifact: '{phrase}' repeating. Truncating.")
                    return " ".join(words[:i+2]) + " [ARTIFACT DETECTED]"
                    
        return text
