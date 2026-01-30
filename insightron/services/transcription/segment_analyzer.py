"""
Segment Analysis Module
Provides advanced metrics and pattern detection for transcription segments
"""

from typing import List, Dict, Tuple, Any, Optional
import statistics
import logging
import numpy as np

logger = logging.getLogger(__name__)

class SegmentAnalyzer:
    """
    Temporal Intelligence Engine for Insightron.
    Mental model: radar, not pilot.
    
    Responsibilities:
    - Detect silence regions
    - Measure speech density
    - Estimate noise levels
    - Calculate overlap probability
    
    Do NOT:
    - Guess words
    - Modify audio
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def analyze_signal(self, signal: np.ndarray) -> Dict[str, Any]:
        """
        Analyze raw audio signal for temporal metrics.
        """
        if len(signal) == 0:
            return self._default_metrics()

        # 1. Measure Noise Level (RMS of silence-like regions or overall floor)
        rms = np.sqrt(np.mean(signal**2))
        noise_floor = np.percentile(np.abs(signal), 10) # Simple noise floor estimate
        
        # 2. Detect Silence Regions (Energy based)
        # Using a simple sliding window energy calculation
        frame_length = int(0.025 * self.sample_rate) # 25ms frames
        hop_length = int(0.010 * self.sample_rate)  # 10ms hop
        
        energies = np.array([
            np.sqrt(np.mean(signal[i:i+frame_length]**2))
            for i in range(0, len(signal) - frame_length, hop_length)
        ])
        
        # Threshold for silence: 20% of peak or a fixed floor
        threshold = max(np.max(energies) * 0.1, 0.01)
        is_speech = energies > threshold
        
        # 3. Speech Density
        speech_density = np.mean(is_speech) if len(is_speech) > 0 else 0
        
        # 4. Silence Regions
        # Find contiguous false regions in is_speech
        silence_durations = []
        current_silence = 0
        for speech in is_speech:
            if not speech:
                current_silence += 1
            else:
                if current_silence > 0:
                    silence_durations.append(current_silence * (hop_length / self.sample_rate))
                current_silence = 0
        if current_silence > 0:
            silence_durations.append(current_silence * (hop_length / self.sample_rate))
            
        avg_silence = np.mean(silence_durations) if silence_durations else 0
        max_silence = np.max(silence_durations) if silence_durations else 0
        
        # 5. Overlap Probability (Simplified: high energy variance often indicates overlap/noise)
        energy_variance = np.var(energies) if len(energies) > 0 else 0
        overlap_prob = min(1.0, energy_variance * 5.0) # Heuristic

        return {
            "overall_rms": float(rms),
            "noise_floor": float(noise_floor),
            "speech_density": float(speech_density),
            "silence_metrics": {
                "count": len(silence_durations),
                "average_duration": float(avg_silence),
                "max_duration": float(max_silence)
            },
            "overlap_probability": float(overlap_prob)
        }

    def _default_metrics(self) -> Dict[str, Any]:
        return {
            "overall_rms": 0.0,
            "noise_floor": 0.0,
            "speech_density": 0.0,
            "silence_metrics": {"count": 0, "average_duration": 0.0, "max_duration": 0.0},
            "overlap_probability": 0.0
        }

