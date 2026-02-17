import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from insightron.core.utils import create_timestamps_section, save_processed_audio
from insightron.core.config import (
    TRANSCRIPTION_FOLDER, 
    PROCESSED_AUDIO_FOLDER,
    ENSURE_UTF8_ENCODING, 
    OUTPUT_ENCODING,
    get_config_manager
)
from insightron.services.transcription.segment_analyzer import SegmentAnalyzer
from insightron.services.transcription.quality_metrics import QualityMetricsCalculator
from insightron.services.transcription.text_formatter import TextFormatter
from insightron.core.config import get_config

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

    def __init__(self) -> None:
        config = get_config_manager()
        self.segment_merge_threshold = config.get(
            "insightron.services.transcription.segment_merge_threshold", -0.5
        )

        self.segment_analyzer = SegmentAnalyzer()
        self.quality_metrics_calculator = QualityMetricsCalculator()

        # Core collaborators for formatting and quality/risk scoring
        self.formatter = TextFormatter()
        self.quality_calc = QualityMetricsCalculator()

        # Output directory for markdown reports
        self.output_dir = Path(get_config("insightron.paths.output_dir", "output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        """
        Calculate detailed quality metrics for transcribed segments.

        This is a convenience wrapper around the underlying calculator and
        is safe to call independently of save_result.
        """
        return self.quality_metrics_calculator.calculate_metrics(segments)

    def save_result(
        self,
        audio_path: str,
        segments: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        processing_time: float,
        model_size: str,
        language: str,
        formatting_style: str = "auto"
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Execute the final contract: format, analyze risk, and save.
        """
        # 1. Human Readability (Text Formatting)
        final_text = self.formatter.format_structure(segments, style=formatting_style)
        
        # 2. Truth Scoring (Quality/Risk)
        quality_analysis = self.quality_calc.calculate_risk_metrics(segments)
        
        # 3. Standardized Result Schema
        result_data = {
            "version": "3.1.0-antigravity",
            "metadata": metadata,
            "transcription": {
                "full_text": final_text,
                "segments": segments,
                "language": language,
                "model": model_size
            },
            "quality": quality_analysis,
            "stats": {
                "processing_time": processing_time,
                "rtf": processing_time / metadata.get('duration_seconds', 1.0) if metadata.get('duration_seconds', 1.0) > 0 else 0
            }
        }
        
        # 4. Deterministic Persistence
        output_filename = f"{Path(audio_path).stem}_transcription.md"
        output_path = self.output_dir / output_filename
        
        # Generate Markdown with clear uncertainty exposure
        self._write_markdown(output_path, result_data)
        
        # 7. Save Processed Audio (optional, but good practice to keep together)
        try:
            save_processed_audio(audio_path, PROCESSED_AUDIO_FOLDER)
        except Exception as e:
            logger.warning(f"Failed to save processed audio: {e}")

        return output_path, result_data

    def _write_markdown(self, path: Path, data: Dict[str, Any]) -> None:
        """Write a standardized, human-readable report."""
        risk = data["quality"]
        action = risk["action_recommendation"]
        
        # Color indicator for risk
        color = "🟢" if action == "Accept" else "🟡" if action == "Flag" else "🔴"

        # Optional timestamps section for detailed navigation
        segments = data["transcription"].get("segments", [])
        timestamps_section = ""
        if segments:
            timestamps_section = "\n## Timestamps\n\n" + create_timestamps_section(segments)

        lines = [
            f"# Insightron Transcription: {data['metadata']['filename']}",
            f"## Quality Report {color}",
            f"- **Status**: {action}",
            f"- **Risk Score**: {risk['risk_score']:.2f}",
            f"- **Audio Confidence**: {risk['metrics']['average_confidence']:.2f}",
            f"- **Consistency**: {risk['metrics']['language_consistency_score']:.2f}",
            "",
            "---",
            "## Transcript",
            "",
            data["transcription"]["full_text"],
            "",
            timestamps_section.strip() if timestamps_section else "",
            "",
            "---",
            "## Metadata",
            f"- **Model**: {data['transcription']['model']}",
            f"- **Processing Time**: {data['stats']['processing_time']:.1f}s",
            f"- **RTF**: {data['stats']['rtf']:.3f}",
        ]

        with open(path, "w", encoding="utf-8") as f:
            # Preserve intentional blank lines ("" entries) for markdown spacing,
            # while still skipping any accidental None values.
            f.write("\n".join(line for line in lines if line is not None))
