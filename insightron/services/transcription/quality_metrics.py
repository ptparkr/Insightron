"""
Quality Metrics Module
Calculates comprehensive quality metrics for transcription output
"""

import statistics
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class QualityMetricsCalculator:
    """
    Truth Scoring Engine for Insightron.
    Mental model: risk analyst.
    
    Responsibilities:
    - Evaluate quality WITHOUT knowing the truth
    - Measure stability, consistency, and confidence
    - Output actionable risk scores
    """
    
    def calculate_risk_metrics(
        self,
        segments: List[Dict[str, Any]],
        language_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate objective quality markers and risk scores.
        """
        if not segments:
            return self._default_metrics()

        # 1. Audio Confidence (Whisper logprobs)
        confidences = [seg.get("confidence", -1.0) for seg in segments]
        avg_conf = statistics.mean(confidences)
        low_conf_ratio = sum(1 for c in confidences if c < -1.0) / len(confidences)
        
        # 2. Boundary Stability
        # Measure gap variance or extreme short/long segments
        durations = [seg["end"] - seg["start"] for seg in segments]
        duration_var = statistics.variance(durations) if len(durations) > 1 else 0
        
        # 3. Language Consistency
        # (Heuristic: high non-alpha ratio often indicates failure)
        text = " ".join([seg["text"] for seg in segments])
        if text:
            non_alpha_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        else:
            non_alpha_ratio = 1.0

        # 4. Error Likelihood (Risk Scoring)
        # Combine metrics into a risk probability
        risk_score = (low_conf_ratio * 0.5) + (min(1.0, non_alpha_ratio * 5) * 0.3) + (min(1.0, duration_var / 10.0) * 0.2)
        
        # Decision Logic
        if risk_score < 0.2:
            action = "Accept"
        elif risk_score < 0.5:
            action = "Flag"
        else:
            action = "Reprocess"

        return {
            "risk_score": float(risk_score),
            "action_recommendation": action,
            "metrics": {
                "average_confidence": float(avg_conf),
                "low_confidence_ratio": float(low_conf_ratio),
                "boundary_stability": float(1.0 - min(1.0, duration_var / 20.0)),
                "language_consistency_score": float(1.0 - non_alpha_ratio)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _default_metrics(self) -> Dict[str, Any]:
        return {
            "risk_score": 1.0,
            "action_recommendation": "Reprocess",
            "metrics": {
                "average_confidence": 0.0,
                "low_confidence_ratio": 1.0,
                "boundary_stability": 0.0,
                "language_consistency_score": 0.0
            }
        }
