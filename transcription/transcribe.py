import os
import logging
import wave
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
import librosa
import soundfile
import numpy as np
from functools import lru_cache


from core.utils import create_markdown
from core.config import (
    get_config_manager,
    WHISPER_MODEL, 
    TRANSCRIPTION_FOLDER, 
    SUPPORTED_LANGUAGES, 
    DEFAULT_LANGUAGE, 
    ENSURE_UTF8_ENCODING, 
    OUTPUT_ENCODING
)
from transcription.segment_analyzer import SegmentAnalyzer
from transcription.quality_metrics import QualityMetricsCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriber:
    """
    High-Performance Audio Transcriber using faster-whisper (CTranslate2).
    Delivers up to 4x faster transcription with lower memory usage.
    """
    
    def __init__(self, model_size: str = WHISPER_MODEL, language: str = DEFAULT_LANGUAGE):
        """
        Initialize the transcriber using the ModelManager singleton.
        
        Args:
            model_size: Size of the model (managed by ModelManager, argument kept for compatibility but logged if different)
            language: Default language code
        """
        from core.model_manager import ModelManager
        
        self.model_manager = ModelManager()
        
        # Check if requested model matches loaded model
        if model_size != self.model_manager.model_size:
            logger.warning(f"Requested model '{model_size}' but ModelManager is configured for '{self.model_manager.model_size}'. Using ModelManager's model.")
            
        self.model_size = self.model_manager.model_size
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac', '.wma'}
        self.supported_languages = SUPPORTED_LANGUAGES
        self.language = language
        
        # Optimization: Set beam size based on model type
        self.beam_size = 1 if "distil" in self.model_size else 5
        
        # Load performance optimization settings from config
        config = get_config_manager()
        self.segment_merge_threshold = config.get('transcription.segment_merge_threshold', -0.5)
        self.min_segment_duration = config.get('transcription.min_segment_duration', 0.1)
        self.progress_update_frequency = config.get('transcription.progress_update_frequency', 5)
        self.enable_segment_filtering = config.get('transcription.enable_segment_filtering', True)
        self.enable_audio_normalization = config.get('transcription.enable_audio_normalization', True)
        self.enable_audio_preprocessing = config.get('transcription.enable_audio_preprocessing', True)
        
        # Performance optimizations
        self.segment_cache_size = config.get('transcription.segment_cache_size', 1000)
        self.enable_parallel_segment_processing = config.get('transcription.enable_parallel_segments', False)
        
        # Add segment analyzer and quality metrics calculator
        self.segment_analyzer = SegmentAnalyzer()
        self.quality_metrics_calculator = QualityMetricsCalculator()
        
        logger.info(f"AudioTranscriber initialized with model: {self.model_size}")
        logger.info(f"AudioTranscriber initialized with adaptive segment merging")
        logger.debug(f"Optimization settings: merge_threshold={self.segment_merge_threshold}, "
                    f"min_duration={self.min_segment_duration}s, progress_freq={self.progress_update_frequency}%, "
                    f"normalization={self.enable_audio_normalization}, preprocessing={self.enable_audio_preprocessing}")

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
        audio = Path(audio_path)
        
        if not audio.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if audio.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {audio.suffix}")
        
        # Check file size (faster-whisper handles larger files better, but let's keep a sane limit)
        # Increased limit to 2GB since we process efficiently
        file_size_mb = audio.stat().st_size / (1024 * 1024)
        if file_size_mb > 2048:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB. Maximum size is 2GB.")
        
        logger.info(f"Audio file validation passed: {audio.name} ({file_size_mb:.1f}MB)")
        return True

    @lru_cache(maxsize=100)
    def _get_audio_info_cached(self, audio_path: str) -> tuple:
        """Cached audio info extraction for performance."""
        try:
            info = soundfile.info(audio_path)
            return (info.duration, info.samplerate, info.channels)
        except Exception:
            try:
                duration = librosa.get_duration(filename=audio_path)
                return (duration, 16000, 1)  # Default assumptions
            except Exception:
                return (0, 16000, 1)
    
    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Extract comprehensive audio metadata with caching."""
        try:
            audio = Path(audio_path)
            file_size = audio.stat().st_size
            
            # Use cached info extraction
            duration, sample_rate, channels = self._get_audio_info_cached(str(audio))
            
            metadata = {
                'filename': audio.name,
                'file_size_mb': file_size / (1024 * 1024),
                'duration_seconds': duration,
                'duration_formatted': f"{int(duration // 60)}:{(duration % 60):02.0f}" if duration else "Unknown",
                'file_extension': audio.suffix.lower(),
                'sample_rate': sample_rate,
                'channels': channels
            }
            return metadata
            
        except Exception as e:
            logger.error(f"Could not extract metadata: {e}")
            return {
                'filename': Path(audio_path).name,
                'file_size_mb': 0,
                'duration_seconds': 0,
                'duration_formatted': "Unknown",
                'file_extension': Path(audio_path).suffix.lower(),
                'sample_rate': 16000,
                'channels': 1
            }
    
    def _preprocess_audio(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Preprocess audio for optimal transcription quality.
        Includes normalization, resampling, and noise reduction hints.
        Optimized to use soundfile for faster loading.
        """
        if not self.enable_audio_preprocessing:
            return None
        
        try:
            # Optimization: Use soundfile for faster loading
            # It's significantly faster than librosa for standard formats
            try:
                audio, sr = soundfile.read(audio_path, dtype='float32')
                
                # Handle multi-channel audio (convert to mono)
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                
                # Resample if necessary (Whisper expects 16kHz)
                if sr != 16000:
                    # Use librosa only for resampling if needed, as it's good at it
                    # But we can use a faster method if available, e.g. scipy or soxr
                    # For now, stick to librosa.resample but on the already loaded array
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                    
            except Exception as sf_error:
                logger.debug(f"Soundfile load failed ({sf_error}), falling back to librosa")
                # Fallback to librosa if soundfile fails (e.g. obscure formats)
                audio, sr = librosa.load(audio_path, sr=16000, mono=True, dtype=np.float32)
            
            # Normalize audio if enabled
            if self.enable_audio_normalization:
                # Peak normalization to prevent clipping
                # Optimized: Use numpy max directly
                max_val = np.abs(audio).max()
                if max_val > 0:
                    audio = audio / max_val * 0.95  # Leave 5% headroom
            
            # Simple high-pass filter to remove low-frequency noise
            # (This is a lightweight filter, not full noise reduction)
            if len(audio) > 100:
                # Remove DC offset
                # Optimized: In-place subtraction
                audio -= np.mean(audio)
            
            return audio
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}, using original file")
            return None

    def _merge_segments_adaptive(
        self, 
        segments: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Intelligently merge segments using adaptive thresholds.
        
        Args:
            segments: List of segment dictionaries
            analysis: Segment analysis results with adaptive parameters
            
        Returns:
            List of merged segments
        """
        if not segments or len(segments) <= 1:
            return segments
        
        merged = []
        current = segments[0].copy()
        
        for i in range(1, len(segments)):
            next_seg = segments[i]
            
            # Get merge decision
            should_merge, reason = self.segment_analyzer.should_merge_segments(
                current, next_seg, analysis
            )
            
            if should_merge:
                # Merge segments
                current['end'] = next_seg['end']
                current['text'] = current['text'] + ' ' + next_seg['text']
                
                # Weighted confidence average by duration
                if 'confidence' in current and 'confidence' in next_seg:
                    dur_current = current.get('_original_duration', current['end'] - current['start'])
                    dur_next = next_seg.get('_original_duration', next_seg['end'] - next_seg['start'])
                    total_dur = dur_current + dur_next
                    
                    weighted_conf = (
                        (current['confidence'] * dur_current + next_seg['confidence'] * dur_next) 
                        / total_dur
                    )
                    current['confidence'] = weighted_conf
                
                logger.debug(f"Merged segments: {reason}")
            else:
                # Save current and start new
                merged.append(current)
                current = next_seg.copy()
        
        merged.append(current)
        
        logger.info(f"Segment merging: {len(segments)} → {len(merged)} segments "
                   f"({(1 - len(merged)/len(segments))*100:.1f}% reduction)")
        return merged
    
    def _merge_segments_smart(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Legacy method for backward compatibility.
        Delegates to adaptive merging with default analysis.
        """
        if not segments or len(segments) <= 1:
            return segments
        
        analysis = self.segment_analyzer.analyze_segments(segments)
        return self._merge_segments_adaptive(segments, analysis)

    def _calculate_quality_metrics(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate quality metrics for transcribed segments.
        Delegates to QualityMetricsCalculator for consistency.
        
        Args:
            segments: List of segment dictionaries with confidence scores
            
        Returns:
            Dictionary with quality metrics (backward compatible format)
        """
        metrics = self.quality_metrics_calculator.calculate_metrics(segments)
        
        # Return backward-compatible format
        confidences = [seg.get('confidence', 0.0) for seg in segments if 'confidence' in seg]
        return {
            "avg_confidence": metrics['confidence_simple_avg'],
            "low_confidence_count": sum(1 for c in confidences if c < self.segment_merge_threshold),
            "total_segments": metrics['segment_count'],
            "min_confidence": min(confidences) if confidences else 0.0,
            "max_confidence": max(confidences) if confidences else 0.0,
            # Add new metrics
            "quality_tier": metrics['quality_tier'],
            "degradation_detected": metrics['degradation_detected'],
            "confidence_weighted_avg": metrics['confidence_weighted_avg']
        }


    def transcribe_file(self, audio_path: str, progress_callback: Optional[Callable[[str], None]] = None, 
                       formatting_style: str = "auto", language: Optional[str] = None) -> tuple[Path, Dict[str, Any]]:
        """
        Transcribe audio file using the shared ModelManager instance.
        
        Args:
            audio_path: Path to the audio file.
            progress_callback: Optional callback for progress updates.
            formatting_style: Formatting style for the output markdown.
            language: Language code to force transcription in specific language.
            
        Returns:
            Tuple containing the path to the generated markdown file and the transcription data dictionary.
        """
        start_time = datetime.now()
        
        try:
            self.validate_audio_file(audio_path)
            metadata = self.get_audio_metadata(audio_path)
            
            if progress_callback:
                progress_callback("Initializing transcription...")
            
            logger.info(f"Transcribing: {metadata['filename']}")
            
            # Determine language
            transcription_language = None
            if language and language != 'auto':
                transcription_language = language
            elif self.language and self.language != 'auto':
                transcription_language = self.language
            
            # Preprocess audio if enabled (for better quality)
            preprocessed_audio = self._preprocess_audio(audio_path)
            audio_input = preprocessed_audio if preprocessed_audio is not None else str(audio_path)
            
            # Transcribe with optimized parameters
            # Use preprocessed audio if available, otherwise use file path
            segments, info = self.model_manager.transcribe(
                audio_input,
                beam_size=self.beam_size,
                language=transcription_language,
                task="transcribe"
            )
            
            if progress_callback:
                progress_callback(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
            
            # Process segments with optimizations
            total_duration = info.duration
            last_progress_percent = -1
            
            # Pre-allocate list capacity estimate for better performance
            estimated_segments = int(total_duration / 3) if total_duration > 0 else 100
            transcribed_segments = []
            text_parts = []
            
            # Process segments with optimized loop
            segment_count = 0
            for segment in segments:
                segment_count += 1
                # Smart segment filtering: skip very short, low-confidence segments
                segment_duration = segment.end - segment.start
                if self.enable_segment_filtering:
                    if segment_duration < self.min_segment_duration:
                        if hasattr(segment, 'avg_logprob') and segment.avg_logprob < self.segment_merge_threshold:
                            logger.debug(f"Filtered micro-segment: {segment_duration:.2f}s, confidence: {segment.avg_logprob:.2f}")
                            continue
                
                # Store segment data (optimized dict creation)
                segment_data = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()  # Strip whitespace immediately
                }
                
                # Add confidence if available
                if hasattr(segment, 'avg_logprob'):
                    segment_data["confidence"] = float(segment.avg_logprob)
                
                transcribed_segments.append(segment_data)
                # Use pre-stripped text for efficiency
                text_parts.append(segment_data["text"])
                
                # Optimized progress updates: only update on significant changes
                if progress_callback and total_duration > 0:
                    current_percent = int((segment.end / total_duration) * 100)
                    # Update only if percent changed by at least progress_update_frequency
                    if current_percent - last_progress_percent >= self.progress_update_frequency:
                        progress_callback(f"Transcribing: {current_percent}% ({int(segment.end)}s/{int(total_duration)}s)")
                        last_progress_percent = current_percent
            
            # Efficient text assembly using join with space separator (O(n) vs O(n²) concatenation)
            final_text = " ".join(text_parts).strip()
            
            # Prepare result data
            now = datetime.now()
            processing_time = (now - start_time).total_seconds()
            
            # Apply adaptive segment merging for better quality
            analysis = self.segment_analyzer.analyze_segments(transcribed_segments)
            speech_rate_wpm = analysis.get('speech_rate_wpm', analysis['speech_rate'] * 60)
            logger.info(f"Segment analysis: {analysis['analysis_quality']} quality, "
                       f"adaptive_threshold={analysis['adaptive_threshold']:.3f}s, "
                       f"speech_rate={speech_rate_wpm:.1f} WPM ({analysis['speech_rate']:.2f} WPS)")
            
            transcribed_segments = self._merge_segments_adaptive(
                transcribed_segments, 
                analysis
            )
            
            # Calculate quality metrics using QualityMetricsCalculator
            quality_metrics = self.quality_metrics_calculator.calculate_metrics(transcribed_segments)
            
            transcription_data = {
                'filename': Path(audio_path).stem,
                'text': final_text,
                'date': now.strftime("%Y-%m-%d %H:%M:%S"),
                'duration': metadata['duration_formatted'],
                'duration_seconds': metadata['duration_seconds'],
                'file_size_mb': metadata['file_size_mb'],
                'model': self.model_size,
                'language': info.language,
                'segments': transcribed_segments,
                'formatting_style': formatting_style,
                'processing_time_seconds': processing_time,
                'characters_per_second': len(final_text) / processing_time if processing_time > 0 else 0,
                'quality_metrics': quality_metrics
            }
            
            # Save to Markdown
            markdown_text = create_markdown(**transcription_data)
            TRANSCRIPTION_FOLDER.mkdir(parents=True, exist_ok=True)
            
            output_path = TRANSCRIPTION_FOLDER / f"{Path(audio_path).stem}.md"
            
            # Atomic write
            temp_path = output_path.with_suffix('.tmp')
            encoding = OUTPUT_ENCODING if ENSURE_UTF8_ENCODING else "utf-8"
            temp_path.write_text(markdown_text, encoding=encoding)
            if output_path.exists():
                output_path.unlink()
            temp_path.rename(output_path)
            
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
