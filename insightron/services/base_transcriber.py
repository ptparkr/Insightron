from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, Iterator, List
import logging
from pathlib import Path
from insightron.core.model_manager import ModelManager
from insightron.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

class BaseTranscriber:
    """
    Ground Truth Layer for Insightron.
    Mental model: camera, not editor.
    
    Lowest-level transcription interface. Converts audio -> text literally.
    
    Rules:
    - No cleanup, no formatting, no guessing
    - Preserve hesitations, repetitions, and uncertainty
    """
    
    def __init__(self, model_size: str = "medium"):
        self.model_manager = ModelManager()
        self.resource_manager = ResourceManager()
        self.model_size = model_size

    def transcribe_literal(
        self, 
        audio: Any, 
        language: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Execute raw, literal transcription.
        Preserves all verbal artifacts and uncertainty.
        """
        # 1. Resource Validation
        health = self.resource_manager.check_health()
        if health["status"] == "critical":
            raise RuntimeError(f"Critical resource shortage: {health['warnings']}")

        # 2. Call ModelManager with 'literal' parameters
        # condition_on_previous_text=False prevents the model from "smoothing" the text
        # beam_size=1 (greedy) can sometimes be more literal, but beam_size=5 is standard for accuracy.
        # We'll use beam_size=5 but disable text conditioning for truth preservation.
        segments_iter, info = self.model_manager.transcribe(
            audio,
            language=language,
            condition_on_previous_text=False,
            # We want RAW output, so we don't suppress any tokens if possible
            # suppress_tokens=None, 
            word_timestamps=True # Crucial for literal ground truth
        )

        logger.info(f"Literal transcription started: {info.language} (p={info.language_probability:.4f})")
        
        for segment in segments_iter:
            # Yield raw segment data
            yield {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text, # Raw text including fillers
                "avg_logprob": segment.avg_logprob,
                "words": [
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "probability": w.probability
                    } for w in (segment.words or [])
                ]
            }

    def _handle_error(self, e: Exception, context: str = ""):
        error_msg = f"Ground Truth Error in {context}: {str(e)}"
        logger.error(error_msg)
        return error_msg
