import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import librosa
import soundfile
import numpy as np
from functools import lru_cache

from insightron.core.config import get_config_manager
from insightron.core.resource_manager import ResourceManager

# Configure logging
logger = logging.getLogger(__name__)

class AudioLoader:
    """
    Signal Intake Engine for Insightron.
    Mental model: clean pipe, not smart brain.
    
    Responsibilities:
    - Normalize sample rate, channels, and format
    - Trim leading/trailing silence conservatively
    - Segment audio only by time
    - Emit timestamps with sample-accurate precision
    """

    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr
        self.supported_formats = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac', '.wma'}
        self.resource_manager = ResourceManager()

    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate if the audio file is supported and accessible."""
        audio = Path(audio_path)
        if not audio.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if audio.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {audio.suffix}")
        return True

    def load_and_preprocess(self, audio_path: str) -> Optional[np.ndarray]:
        """
        High-efficiency intake that can skip overly large files.

        Returns:
            numpy array with normalized signal, or None when the file
            exceeds the safe in-memory size recommended by ResourceManager.
        """
        path = Path(audio_path)

        # Fast existence check; callers rely on skip semantics only for size.
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            size_mb = path.stat().st_size / (1024 * 1024)
        except Exception:
            size_mb = None

        max_safe_mb = float(self.resource_manager.get_max_safe_file_load_size_mb())

        if size_mb is not None and size_mb > max_safe_mb:
            logger.warning(
                f"Skipping '{audio_path}' ({size_mb:.1f} MB) – exceeds safe load limit of {max_safe_mb:.1f} MB"
            )
            return None

        # Delegate to standard strict-loading path.
        self.validate_audio_file(audio_path)
        return self.load_signal(audio_path)

    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Extract metadata for signal preservation and tracking."""
        file_path = Path(audio_path)
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
        except Exception:
            file_size_mb = None
        try:
            info = soundfile.info(audio_path)
            return {
                'filename': file_path.name,
                'file_size_mb': float(file_size_mb) if file_size_mb is not None else None,
                'duration_seconds': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype
            }
        except Exception as e:
            logger.warning(f"Metadata extraction via soundfile failed: {e}. Falling back to librosa.")
            duration = librosa.get_duration(filename=audio_path)
            return {
                'filename': file_path.name,
                'file_size_mb': float(file_size_mb) if file_size_mb is not None else None,
                'duration_seconds': duration,
                'sample_rate': self.target_sr,
                'channels': 1,
                'format': 'unknown'
            }

    def load_signal(self, audio_path: str) -> np.ndarray:
        """
        Load audio with maximum signal preservation and strict normalization.
        Always returns 16kHz, Mono, Float32.
        """
        try:
            # Use soundfile for primary intake
            audio, sr = soundfile.read(audio_path, dtype='float32')
            
            # 1. Normalize channels (downmix to mono)
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # 2. Resample if necessary
            if sr != self.target_sr:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
            
            # 3. Conservative silence trimming
            # We use a low threshold to preserve subtle audio artifacts
            audio, _ = librosa.effects.trim(audio, top_db=40)
            
            # 4. Standard Peak Normalization
            max_val = np.abs(audio).max()
            if max_val > 0:
                audio = audio / max_val
                
            return audio.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Signal intake failed: {e}")
            raise RuntimeError(f"Could not load signal from {audio_path}: {e}")

    def segment_by_time(self, audio: np.ndarray, segment_seconds: float) -> list[Dict[str, Any]]:
        """
        Segment audio strictly by time. No semantic guessing.
        """
        samples_per_segment = int(segment_seconds * self.target_sr)
        segments = []
        
        for i in range(0, len(audio), samples_per_segment):
            chunk = audio[i:i + samples_per_segment]
            start_time = i / self.target_sr
            end_time = min((i + samples_per_segment) / self.target_sr, len(audio) / self.target_sr)
            
            segments.append({
                "signal": chunk,
                "start_sample": i,
                "end_sample": i + len(chunk),
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            })
            
        return segments
