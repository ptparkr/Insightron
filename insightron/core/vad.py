import numpy as np
import logging
from collections import deque
from typing import Deque, Iterable, Tuple

logger = logging.getLogger(__name__)

class EnergyVAD:
    """
    Efficient Energy-based Voice Activity Detector (VAD).
    Used to bypass heavy inference on non-speech segments at pre-processing stage.
    """
    
    def __init__(self, sample_rate: int = 16000, frame_duration_ms: int = 30):
        self.sample_rate = sample_rate
        self.frame_length = int(sample_rate * frame_duration_ms / 1000)
        
        # Adaptive thresholds
        self.energy_threshold = 0.005  # Base threshold
        self.noise_floor = 0.001
        self.adaptation_rate = 0.05
        
        # Statistics
        self.window_size = 50  # Keep last 50 frames for adaptation
        self.history: Deque[float] = deque(maxlen=self.window_size)

    def reset(self) -> None:
        """Reset adaptive state (noise floor + history)."""
        self.noise_floor = 0.001
        self.history.clear()
        
    def is_speech(self, audio_frame: np.ndarray, adaptive: bool = True) -> bool:
        """
        Determine if the audio frame contains speech.
        
        Args:
            audio_frame: Numpy array of float32 samples.
            adaptive: Whether to update noise floor dynamically.
            
        Returns:
            bool: True if speech is detected.
        """
        if audio_frame is None or len(audio_frame) == 0:
            return False

        # Ensure numeric stability
        if not np.isfinite(audio_frame).all():
            audio_frame = np.nan_to_num(audio_frame, nan=0.0, posinf=0.0, neginf=0.0)
            
        # Calculate Root Mean Square (RMS) amplitude
        rms = float(np.sqrt(np.mean(audio_frame.astype(np.float32) ** 2)))
        
        # Update history
        self.history.append(rms)
            
        # Adaptive thresholding logic
        if adaptive:
            # Estimate noise floor as the 10th percentile of recent energy
            # This assumes that at least 10% of the audio is silence/background noise
            # Percentile over a tiny window is cheap; keep it simple and deterministic.
            local_noise = float(np.percentile(list(self.history), 10)) if self.history else 0.001
            
            # Smoothly update noise floor
            self.noise_floor = (1 - self.adaptation_rate) * self.noise_floor + self.adaptation_rate * local_noise
            
            # Threshold is relative to noise floor + margin
            # We want to be sensitive enough to catch soft speech
            current_threshold = max(self.energy_threshold, self.noise_floor * 3.0)
        else:
            current_threshold = self.energy_threshold
            
        return rms > float(current_threshold)

    def get_energy_level(self) -> float:
        """Get current estimated energy level (RMS)."""
        return float(self.history[-1]) if self.history else 0.0

    def get_noise_floor(self) -> float:
        """Get current estimated noise floor."""
        return float(self.noise_floor)

    def iter_frames(self, signal: np.ndarray, hop_length: int | None = None) -> Iterable[np.ndarray]:
        """
        Iterate over fixed-size frames from a full signal.

        Args:
            signal: 1D mono float array
            hop_length: step between frames (defaults to frame_length)
        """
        if signal is None or len(signal) == 0:
            return

        step = int(hop_length or self.frame_length)
        frame_len = int(self.frame_length)
        for i in range(0, len(signal), step):
            yield signal[i : i + frame_len]

    def contains_speech(self, signal: np.ndarray, adaptive: bool = True) -> bool:
        """Return True if any frame is detected as speech."""
        for frame in self.iter_frames(signal):
            if self.is_speech(frame, adaptive=adaptive):
                return True
        return False
