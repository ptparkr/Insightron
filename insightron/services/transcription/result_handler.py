import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from insightron.core.utils import create_markdown, save_processed_audio
from insightron.core.config import (
    TRANSCRIPTION_FOLDER, 
    PROCESSED_AUDIO_FOLDER,
    ENSURE_UTF8_ENCODING, 
    OUTPUT_ENCODING,
    get_config_manager
)
from insightron.services.transcription.segment_analyzer import SegmentAnalyzer
from insightron.services.transcription.quality_metrics import QualityMetricsCalculator

# Configure logging
logger = logging.getLogger(__name__)

class ResultHandler:
    """
    Handles post-processing of transcription results:
    - Segment merging (adaptive/smart)
    - Quality metrics calculation
    - Output formatting (Markdown generation)
    - File saving
    """

    def __init__(self):
        config = get_config_manager()
        self.segment_merge_threshold = config.get('insightron.services.transcription.segment_merge_threshold', -0.5)
        
        self.segment_analyzer = SegmentAnalyzer()
        self.quality_metrics_calculator = QualityMetricsCalculator()

    def merge_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Intelligently merge segments using adaptive thresholds.
        """
        if not segments or len(segments) <= 1:
            return segments
        
        # Analyze first
        analysis = self.segment_analyzer.analyze_segments(segments)
        speech_rate_wpm = analysis.get('speech_rate_wpm', analysis['speech_rate'] * 60)
        logger.info(f"Segment analysis: {analysis['analysis_quality']} quality, "
                   f"adaptive_threshold={analysis['adaptive_threshold']:.3f}s, "
                   f"speech_rate={speech_rate_wpm:.1f} WPM")

        merged = []
        current = segments[0].copy()
        
        for i in range(1, len(segments)):
            next_seg = segments[i]
            
            should_merge, reason = self.segment_analyzer.should_merge_segments(
                current, next_seg, analysis
            )
            
            if should_merge:
                current['end'] = next_seg['end']
                current['text'] = current['text'] + ' ' + next_seg['text']
                
                # Weighted confidence average by duration
                if 'confidence' in current and 'confidence' in next_seg:
                    dur_current = current.get('_original_duration', current['end'] - current['start'])
                    dur_next = next_seg.get('_original_duration', next_seg['end'] - next_seg['start'])
                    total_dur = dur_current + dur_next
                    if total_dur > 0:
                        weighted_conf = (
                            (current['confidence'] * dur_current + next_seg['confidence'] * dur_next) 
                            / total_dur
                        )
                        current['confidence'] = weighted_conf
                
                logger.debug(f"Merged segments: {reason}")
            else:
                merged.append(current)
                current = next_seg.copy()
        
        merged.append(current)
        
        logger.info(f"Segment merging: {len(segments)} -> {len(merged)} segments "
                   f"({(1 - len(merged)/len(segments))*100:.1f}% reduction)")
        return merged

    def calculate_quality_metrics(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for transcribed segments."""
        metrics = self.quality_metrics_calculator.calculate_metrics(segments)
        
        # Return backward-compatible format + new metrics
        confidences = [seg.get('confidence', 0.0) for seg in segments if 'confidence' in seg]
        return {
            "avg_confidence": metrics['confidence_simple_avg'],
            "low_confidence_count": sum(1 for c in confidences if c < self.segment_merge_threshold),
            "total_segments": metrics['segment_count'],
            "min_confidence": min(confidences) if confidences else 0.0,
            "max_confidence": max(confidences) if confidences else 0.0,
            "quality_tier": metrics['quality_tier'],
            "degradation_detected": metrics['degradation_detected'],
            "confidence_weighted_avg": metrics['confidence_weighted_avg']
        }

    def save_result(self, 
                   audio_path: str, 
                   segments: List[Dict[str, Any]], 
                   info: Any,
                   metadata: Dict[str, Any],
                   processing_time: float,
                   formatting_style: str = "auto") -> tuple[Path, Dict[str, Any]]:
        """
        Format results to Markdown and save to file.
        """
        # 1. Merge segments
        final_segments = self.merge_segments(segments)
        
        # 2. Build final text
        # Efficient join
        final_text = " ".join([seg['text'] for seg in final_segments]).strip()
        
        # 3. Calculate metrics
        quality_metrics = self.calculate_quality_metrics(final_segments)
        
        # 4. Prepare data dictionary
        now = datetime.now()
        data = {
            'filename': Path(audio_path).stem,
            'text': final_text,
            'date': now.strftime("%Y-%m-%d %H:%M:%S"),
            'duration': metadata['duration_formatted'],
            'duration_seconds': metadata['duration_seconds'],
            'file_size_mb': metadata['file_size_mb'],
            'model': info.model_size if hasattr(info, 'model_size') else "unknown", 
            # Note: TranscriptionInfo from faster-whisper doesn't strictly have model_size, needs passing or standardizing
            # We'll handle this in the facade to pass model name correctly if needed, or rely on info having it if we hacked it.
            # Actually standard TranscriptionInfo has: language, language_probability, duration.
            # We should pass model name into this method or add it to info object wrapper.
            # For now let's assume 'model' is passed in 'info' or we add it to data map outside.
            'language': info.language,
            'segments': final_segments,
            'formatting_style': formatting_style,
            'processing_time_seconds': processing_time,
            'characters_per_second': len(final_text) / processing_time if processing_time > 0 else 0,
            'quality_metrics': quality_metrics
        }
        
        # 5. Create Markdown
        markdown_text = create_markdown(**data)
        
        # 6. Save File
        TRANSCRIPTION_FOLDER.mkdir(parents=True, exist_ok=True)
        output_path = TRANSCRIPTION_FOLDER / f"{Path(audio_path).stem}.md"
        
        temp_path = output_path.with_suffix('.tmp')
        encoding = OUTPUT_ENCODING if ENSURE_UTF8_ENCODING else "utf-8"
        try:
            temp_path.write_text(markdown_text, encoding=encoding)
            if output_path.exists():
                output_path.unlink()
            temp_path.rename(output_path)
        except Exception as e:
            logger.error(f"Failed to write output file: {e}")
            raise

        # 7. Save Processed Audio (optional, but good practice to keep together)
        try:
            save_processed_audio(audio_path, PROCESSED_AUDIO_FOLDER)
        except Exception as e:
            logger.warning(f"Failed to save processed audio: {e}")
            
        return output_path, data
