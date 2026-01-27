import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

from insightron.core.config import (
    WHISPER_MODEL, 
    DEFAULT_LANGUAGE, 
    SUPPORTED_LANGUAGES
)

# New components
from insightron.services.transcription.audio_loader import AudioLoader
from insightron.services.transcription.transcription_engine import TranscriptionEngine
from insightron.services.transcription.result_handler import ResultHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriber:
    """
    High-Performance Audio Transcriber using faster-whisper (CTranslate2).
    Refactored to use modular components:
    - AudioLoader: IO and preprocessing
    - TranscriptionEngine: Inference loop
    - ResultHandler: Formatting and metrics
    """
    
    def __init__(self, model_size: str = WHISPER_MODEL, language: str = DEFAULT_LANGUAGE):
        """
        Initialize the transcriber facade.
        """
        # Initialize components
        self.loader = AudioLoader()
        self.engine = TranscriptionEngine()
        self.handler = ResultHandler()
        
        # Check if requested model matches loaded model
        # The Engine uses ModelManager singleton, so we check through it
        current_model = self.engine.model_size
        if model_size != current_model:
            logger.warning(f"Requested model '{model_size}' but ModelManager is configured for '{current_model}'. Using ModelManager's model.")
            
        self.model_size = current_model
        
        self.supported_languages = SUPPORTED_LANGUAGES
        self.language = language
        
        # Optimization: Set beam size based on model type
        self.beam_size = 1 if "distil" in self.model_size else 5
        
        logger.info(f"AudioTranscriber initialized with model: {self.model_size}")
        logger.info("Modular components loaded: Loader, Engine, ResultHandler")

    def set_language(self, language: str) -> bool:
        """Set the transcription language."""
        if language not in self.supported_languages and language != 'auto':
            logger.warning(f"Language '{language}' not in supported languages. Using auto-detection.")
            self.language = 'auto'
            return False
        
        self.language = language
        logger.info(f"Language set to: {language}")
        return True

    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported languages."""
        return self.supported_languages.copy()

    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate if the audio file is supported and accessible."""
        return self.loader.validate_audio_file(audio_path)

    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Extract comprehensive audio metadata with caching."""
        return self.loader.get_audio_metadata(audio_path)
    
    # Backward compatibility methods (internal)
    def _preprocess_audio(self, audio_path: str):
        return self.loader.load_and_preprocess(audio_path)
        
    def _merge_segments_smart(self, segments):
        return self.handler.merge_segments(segments)
        
    def _calculate_quality_metrics(self, segments):
        return self.handler.calculate_quality_metrics(segments)

    def transcribe_file(self, audio_path: str, progress_callback: Optional[Callable[[str], None]] = None, 
                       formatting_style: str = "auto", language: Optional[str] = None) -> tuple[Path, Dict[str, Any]]:
        """
        Transcribe audio file using modular components.
        """
        start_time = datetime.now()
        
        try:
            # 1. Validation and Metadata (Loader)
            self.loader.validate_audio_file(audio_path)
            metadata = self.loader.get_audio_metadata(audio_path)
            
            if progress_callback:
                progress_callback("Initializing transcription...")
            
            logger.info(f"Transcribing: {metadata['filename']}")
            
            # Determine language
            transcription_language = None
            if language and language != 'auto':
                transcription_language = language
            elif self.language and self.language != 'auto':
                transcription_language = self.language
            
            # 2. Loading and Preprocessing (Loader)
            preprocessed_audio = self.loader.load_and_preprocess(audio_path)
            audio_input = preprocessed_audio if preprocessed_audio is not None else str(audio_path)
            
            # 3. Transcription (Engine)
            transcribed_segments, info = self.engine.transcribe(
                audio_input,
                language=transcription_language,
                beam_size=self.beam_size,
                progress_callback=progress_callback
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 4. Result Handling (Handler)
            output_path, transcription_data = self.handler.save_result(
                audio_path,
                transcribed_segments,
                info,
                metadata,
                processing_time,
                formatting_style
            )
            
            if progress_callback:
                progress_callback("✓ Transcription completed!")
            
            logger.info(f"Completed in {processing_time:.1f}s")
            return output_path, transcription_data
            
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Error: {str(e)}")
            raise Exception(error_msg)
