"""
Segment analyzer utilities.

This module provides:
- Segment-level analysis: derive adaptive merge thresholds for adjacent segments
- Signal-level analysis: lightweight metrics for silence/noise characteristics
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Any
import statistics
import logging

import numpy as np

logger = logging.getLogger(__name__)


class SegmentAnalyzer:
    """
    Temporal Intelligence Engine for Insightron.
    Mental model: radar, not pilot.

    Responsibilities:
    - Derive adaptive merge thresholds from segments
    - Detect silence regions and estimate speech density from raw signal
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    # -------- Segment-level analysis (for merging) --------
    def analyze_segments(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze Whisper-style segments to derive an adaptive merge threshold.

        Returns a stable dict used by `should_merge_segments()`.
        """
        if not segments:
            return {
                "analysis_quality": "insufficient",
                "adaptive_threshold": 0.5,
                "speech_rate": 2.0,
                "speech_rate_wpm": 120.0,
            }

        durations: List[float] = [
            max(0.0, float(seg.get("end", 0.0) - seg.get("start", 0.0)))
            for seg in segments
        ]
        avg_duration = statistics.mean(durations) if durations else 0.5
        speech_rate = 1.0 / max(avg_duration, 0.1)
        speech_rate_wpm = speech_rate * 60.0

        # Adaptive gap threshold: allow slightly longer than typical segment duration.
        adaptive_threshold = max(0.25, min(1.5, avg_duration * 1.5))

        return {
            "analysis_quality": "ok",
            "adaptive_threshold": float(adaptive_threshold),
            "speech_rate": float(speech_rate),
            "speech_rate_wpm": float(speech_rate_wpm),
        }

    def should_merge_segments(
        self,
        current: Dict[str, Any],
        nxt: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Decide whether to merge two adjacent segments based on their time gap.

        Returns:
            (should_merge, reason)
        """
        current_end = float(current.get("end", 0.0))
        next_start = float(nxt.get("start", current_end))
        gap = next_start - current_end

        threshold = float(analysis.get("adaptive_threshold", 0.75))

        if gap < 0:
            return True, f"overlap gap={gap:.3f}s"
        if gap <= threshold:
            return True, f"short gap={gap:.3f}s <= {threshold:.3f}s"
        return False, f"gap={gap:.3f}s > {threshold:.3f}s"

    # -------- Signal-level analysis --------
    def analyze_signal(self, signal: np.ndarray) -> Dict[str, Any]:
        """Analyze raw audio signal for temporal metrics."""
        if signal is None or len(signal) == 0:
            return self._default_metrics()

        # Noise / energy estimates
        rms = float(np.sqrt(np.mean(signal**2)))
        noise_floor = float(np.percentile(np.abs(signal), 10))

        # Sliding window energies (25ms frame, 10ms hop)
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)

        if len(signal) < frame_length:
            # Too short to window: treat as one frame
            energies = np.array([rms], dtype=np.float32)
        else:
            energies = np.array(
                [
                    float(np.sqrt(np.mean(signal[i : i + frame_length] ** 2)))
                    for i in range(0, len(signal) - frame_length, hop_length)
                ],
                dtype=np.float32,
            )

        # Speech heuristic
        threshold = float(max(float(np.max(energies)) * 0.1, 0.01))
        is_speech = energies > threshold
        speech_density = float(np.mean(is_speech)) if len(is_speech) else 0.0

        # Silence run lengths
        silence_durations: List[float] = []
        current_silence = 0
        for speech in is_speech:
            if not speech:
                current_silence += 1
            elif current_silence > 0:
                silence_durations.append(current_silence * (hop_length / self.sample_rate))
                current_silence = 0
        if current_silence > 0:
            silence_durations.append(current_silence * (hop_length / self.sample_rate))

        avg_silence = float(np.mean(silence_durations)) if silence_durations else 0.0
        max_silence = float(np.max(silence_durations)) if silence_durations else 0.0

        energy_variance = float(np.var(energies)) if len(energies) else 0.0
        overlap_prob = float(min(1.0, energy_variance * 5.0))

        return {
            "overall_rms": rms,
            "noise_floor": noise_floor,
            "speech_density": speech_density,
            "silence_metrics": {
                "count": len(silence_durations),
                "average_duration": avg_silence,
                "max_duration": max_silence,
            },
            "overlap_probability": overlap_prob,
        }

    def _default_metrics(self) -> Dict[str, Any]:
        return {
            "overall_rms": 0.0,
            "noise_floor": 0.0,
            "speech_density": 0.0,
            "silence_metrics": {"count": 0, "average_duration": 0.0, "max_duration": 0.0},
            "overlap_probability": 0.0,
        }

