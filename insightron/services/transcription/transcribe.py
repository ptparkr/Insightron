import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

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
        # Initialize BaseTranscriber (creates ModelManager and ResourceManager)
        super().__init__(model_size, language)
        
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
        
        # Multi-pass transcriber (lazy initialized if needed)
        self.multi_pass_enabled = get_config('multi_pass.enabled', False)
        self.multi_pass_transcriber = None
        
        logger.info(f"AudioTranscriber initialized with model: {self.model_size}")
        logger.info(f"Modular components loaded: Loader, Engine, ResultHandler")
        logger.info(f"Multi-pass mode: {'enabled' if self.multi_pass_enabled else 'disabled'}")

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

    def transcribe(self, audio_path: str, **kwargs) -> tuple[Path, Dict[str, Any]]:
        """Alias for transcribe_file to satisfy BaseTranscriber contract."""
        return self.transcribe_file(audio_path, **kwargs)

    def transcribe_file(self, audio_path: str, progress_callback: Optional[Callable[[str], None]] = None, 
                       formatting_style: str = "auto", language: Optional[str] = None) -> tuple[Path, Dict[str, Any]]:
        """
        Transcribe audio file using modular components.
        Supports both single-pass (default) and multi-pass modes.
        """
        start_time = datetime.now()
        
        try:
            # 0. Resource Validation
            self.validate_resources()

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
            
            # Check if multi-pass mode is enabled
            if self.multi_pass_enabled:
                return self._transcribe_multipass(
                    audio_path,
                    metadata,
                    transcription_language,
                    formatting_style,
                    progress_callback,
                    start_time
                )
            
            # Single-pass mode (default/legacy behavior)
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
    
    def _transcribe_multipass(
        self,
        audio_path: str,
        metadata: Dict[str, Any],
        language: Optional[str],
        formatting_style: str,
        progress_callback: Optional[Callable[[str], None]],
        start_time: datetime
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Transcribe using multi-pass pipeline.
        
        Args:
            audio_path: Path to audio file
            metadata: Audio metadata
            language: Language code
            formatting_style: Text formatting style
            progress_callback: Progress callback
            start_time: Start time for timing
            
        Returns:
            Tuple of (output_path, transcription_data)
        """
        # Lazy initialize multi-pass transcriber
        if self.multi_pass_transcriber is None:
            self.multi_pass_transcriber = MultiPassTranscriber()
        
        logger.info("Using multi-pass transcription pipeline")
        
        # Execute multi-pass pipeline
        result = self.multi_pass_transcriber.transcribe_multipass(
            audio_path,
            language=language,
            progress_callback=progress_callback
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Use Pass 3 final text (with emotions) for output
        final_segments = result.segments
        
        # Create a mock TranscriptionInfo object for compatibility
        class MockInfo:
            def __init__(self, metadata):
                self.language = metadata.get('language', 'unknown')
                self.duration = metadata.get('duration', 0)
                self.language_probability = 1.0
        
        info = MockInfo(result.metadata)
        
        # Save result using existing handler
        output_path, transcription_data = self.handler.save_result(
            audio_path,
            final_segments,
            info,
            metadata,
            processing_time,
            formatting_style
        )
        
        # Add multi-pass specific metadata
        transcription_data['multi_pass'] = {
            'enabled': True,
            'pass1_text': result.pass1_raw_text[:200] + '...' if len(result.pass1_raw_text) > 200 else result.pass1_raw_text,
            'pass2_restoration_time': result.processing_times.get('pass2_restoration', 0),
            'pass3_emotion_time': result.processing_times.get('pass3_emotion', 0),
            'total_passes_time': result.processing_times.get('total', 0)
        }
        
        if progress_callback:
            progress_callback("✓ Multi-pass transcription completed!")
        
        logger.info(f"Multi-pass completed in {processing_time:.1f}s")
        logger.info(f"  - Pass 1 (Detection): {result.processing_times.get('pass1_detection', 0):.1f}s")
        logger.info(f"  - Pass 2 (Restoration): {result.processing_times.get('pass2_restoration', 0):.1f}s")
        logger.info(f"  - Pass 3 (Emotion): {result.processing_times.get('pass3_emotion', 0):.1f}s")
        
        return output_path, transcription_data
