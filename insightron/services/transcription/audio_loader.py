import logging
from pathlib import Path
from typing import Dict, Any, Optional
import librosa
import soundfile
import numpy as np
from functools import lru_cache

from insightron.core.config import get_config_manager

# Configure logging
logger = logging.getLogger(__name__)

class AudioLoader:
    """
    Handles audio file validation, metadata extraction, loading, and preprocessing.
    """

    def __init__(self):
        config = get_config_manager()
        self.enable_audio_normalization = config.get('insightron.services.transcription.enable_audio_normalization', True)
        self.enable_audio_preprocessing = config.get('insightron.services.transcription.enable_audio_preprocessing', True)
        
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac', '.wma'}

    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate if the audio file is supported and accessible."""
        audio = Path(audio_path)
        
        if not audio.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if audio.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {audio.suffix}")
        
        # Check file size
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
            # Duration, Samplerate, Channels
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

    def load_and_preprocess(self, audio_path: str) -> Optional[np.ndarray]:
        """
        Load and preprocess audio for optimal transcription quality.
        Includes normalization, resampling, and simple noise reduction hints.
        """
        if not self.enable_audio_preprocessing:
            return None
        
        try:
            # Optimization: Use soundfile for faster loading
            try:
                audio, sr = soundfile.read(audio_path, dtype='float32')
                
                # Handle multi-channel audio (convert to mono)
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                
                # Resample if necessary (Whisper expects 16kHz)
                if sr != 16000:
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                    
            except Exception as sf_error:
                logger.debug(f"Soundfile load failed ({sf_error}), falling back to librosa")
                audio, sr = librosa.load(audio_path, sr=16000, mono=True, dtype=np.float32)
            
            # Normalize audio if enabled
            if self.enable_audio_normalization:
                max_val = np.abs(audio).max()
                if max_val > 0:
                    audio = audio / max_val * 0.95  # Leave 5% headroom
            
            # Simple high-pass filter to remove DC offset/low-freq noise
            if len(audio) > 100:
                audio -= np.mean(audio)
            
            return audio
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}, using original file path")
            return None
