"""
Quality Metrics Module
Calculates comprehensive quality metrics for transcription output
"""

from typing import List, Dict, Any
import statistics
import logging

logger = logging.getLogger(__name__)

class QualityMetricsCalculator:
    """
    Calculates detailed quality metrics with weighted scoring.
    """
    
    def calculate_metrics(
        self,
        segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive quality metrics.
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Dictionary with detailed quality metrics:
            - confidence_weighted_avg: Confidence weighted by segment duration
            - confidence_percentiles: [p25, p50 (median), p75]
            - degradation_detected: Boolean indicating quality decline
            - segment_count: Number of segments
            - avg_segment_duration: Average segment length in seconds
            - quality_tier: 'excellent'|'good'|'acceptable'|'poor'
        """
        if not segments:
            return self._default_metrics()
        
        confidences = [
            seg.get('confidence', -1.0) 
            for seg in segments 
            if 'confidence' in seg
        ]
        
        if not confidences:
            return self._default_metrics()
        
        # Calculate segment durations for weighting
        durations = [
            seg['end'] - seg['start'] 
            for seg in segments 
            if 'start' in seg and 'end' in seg
        ]
        
        # Weighted confidence: longer segments carry more weight
        total_duration = sum(durations) if durations else 1.0
        weighted_confidences = []
        for i, seg in enumerate(segments):
            if i < len(durations) and 'confidence' in seg:
                weight = durations[i] / total_duration if total_duration > 0 else 1
                weighted_confidences.append(seg['confidence'] * weight)
        
        weighted_avg = sum(weighted_confidences) if weighted_confidences else 0.0
        
        # Calculate percentiles
        sorted_conf = sorted(confidences)
        p25_idx = int(len(sorted_conf) * 0.25)
        p50_idx = int(len(sorted_conf) * 0.50)
        p75_idx = int(len(sorted_conf) * 0.75)
        
        p25 = sorted_conf[p25_idx] if p25_idx < len(sorted_conf) else sorted_conf[0] if sorted_conf else 0.0
        p50 = sorted_conf[p50_idx] if p50_idx < len(sorted_conf) else sorted_conf[0] if sorted_conf else 0.0
        p75 = sorted_conf[p75_idx] if p75_idx < len(sorted_conf) else sorted_conf[-1] if sorted_conf else 0.0
        
        # Detect degradation: compare early segments to late segments
        mid_point = len(segments) // 2
        early_conf = confidences[:mid_point] if mid_point > 0 else []
        late_conf = confidences[mid_point:] if mid_point < len(confidences) else []
        
        early_avg = statistics.mean(early_conf) if early_conf else 0
        late_avg = statistics.mean(late_conf) if late_conf else 0
        
        degradation_detected = (early_avg - late_avg) > 0.3  # > 0.3 is significant
        
        # Determine quality tier
        avg_conf = statistics.mean(confidences)
        if avg_conf > -0.3 and not degradation_detected:
            quality_tier = 'excellent'
        elif avg_conf > -0.8:
            quality_tier = 'good'
        elif avg_conf > -1.2:
            quality_tier = 'acceptable'
        else:
            quality_tier = 'poor'
        
        return {
            'confidence_simple_avg': avg_conf,
            'confidence_weighted_avg': weighted_avg,
            'confidence_percentiles': {
                'p25': p25,
                'p50_median': p50,
                'p75': p75
            },
            'degradation_detected': degradation_detected,
            'early_vs_late_diff': early_avg - late_avg,
            'segment_count': len(segments),
            'avg_segment_duration': statistics.mean(durations) if durations else 0,
            'quality_tier': quality_tier,
            'confidence_std': statistics.stdev(confidences) if len(confidences) > 1 else 0
        }
    
    def _default_metrics(self) -> Dict[str, Any]:
        return {
            'confidence_simple_avg': 0.0,
            'confidence_weighted_avg': 0.0,
            'confidence_percentiles': {'p25': 0, 'p50_median': 0, 'p75': 0},
            'degradation_detected': False,
            'early_vs_late_diff': 0,
            'segment_count': 0,
            'avg_segment_duration': 0,
            'quality_tier': 'unknown',
            'confidence_std': 0
        }
