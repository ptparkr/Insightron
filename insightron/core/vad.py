import numpy as np
import logging

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
        self.history = []
        self.window_size = 50  # Keep last 50 frames for adaptation
        
    def is_speech(self, audio_frame: np.ndarray, adaptive: bool = True) -> bool:
        """
        Determine if the audio frame contains speech.
        
        Args:
            audio_frame: Numpy array of float32 samples.
            adaptive: Whether to update noise floor dynamically.
            
        Returns:
            bool: True if speech is detected.
        """
        if len(audio_frame) == 0:
            return False
            
        # Calculate Root Mean Square (RMS) amplitude
        rms = np.sqrt(np.mean(audio_frame**2))
        
        # Update history
        self.history.append(rms)
        if len(self.history) > self.window_size:
            self.history.pop(0)
            
        # Adaptive thresholding logic
        if adaptive:
            # Estimate noise floor as the 10th percentile of recent energy
            # This assumes that at least 10% of the audio is silence/background noise
            local_noise = np.percentile(self.history, 10) if self.history else 0.001
            
            # Smoothly update noise floor
            self.noise_floor = (1 - self.adaptation_rate) * self.noise_floor + self.adaptation_rate * local_noise
            
            # Threshold is relative to noise floor + margin
            # We want to be sensitive enough to catch soft speech
            current_threshold = max(self.energy_threshold, self.noise_floor * 3.0)
        else:
            current_threshold = self.energy_threshold
            
        return rms > current_threshold

    def get_energy_level(self) -> float:
        """Get current estimated energy level (RMS)."""
        return self.history[-1] if self.history else 0.0

    def get_noise_floor(self) -> float:
        """Get current estimated noise floor."""
        return self.noise_floor
