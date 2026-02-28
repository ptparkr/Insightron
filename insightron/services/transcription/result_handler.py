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
    get_config_manager,
)
from insightron.services.transcription.segment_analyzer import SegmentAnalyzer
from insightron.services.transcription.quality_metrics import QualityMetricsCalculator
from insightron.services.transcription.text_formatter import TextFormatter
from insightron.services.transcription.metrics_calculator import MetricsCalculator
from insightron.services.transcription.markdown_renderer import MarkdownRenderer
from insightron.services.transcription.contracts import DiarizationResult
from insightron.services.transcription.diarization import Diarizer
from insightron.services.transcription.speaker_attribution import SpeakerAttribution

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
            "transcription.segment_merge_threshold", -0.5
        )
        self.filename_template = config.get(
            "transcription.filename_template", "{stem}_transcription.md"
        )

        self.segment_analyzer = SegmentAnalyzer()
        self.quality_metrics_calculator = QualityMetricsCalculator()

        # Core collaborators for formatting and quality/risk scoring
        self.formatter = TextFormatter()
        self.quality_calc = QualityMetricsCalculator()

        # Output directory for markdown reports (inside the main transcription workspace)
        self.output_dir = TRANSCRIPTION_FOLDER
        self.report_style = config.get("report.style", "classic")
        self.metrics_calc = MetricsCalculator()
        self.renderer = MarkdownRenderer()

    def _resolve_style(self, config_profile: str, cli_format: str) -> str:
        """
        Resolve the effective formatting style given the config profile and any
        CLI override.

        - If cli_format is "auto", use the post_processing.formatting_profile.
        - Otherwise, prefer the explicit CLI-provided style.
        - If the resolved style is unknown to TextFormatter, fall back to "auto".
        """
        chosen = config_profile if cli_format == "auto" else cli_format
        if chosen not in self.formatter.views:
            logger.warning(
                f"Unknown formatting style '{chosen}', falling back to 'auto'."
            )
            return "auto"
        return chosen

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
        formatting_style: str = "auto",
        diarization: Optional[DiarizationResult] = None,
        asr_info: Any = None,
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Execute the final contract: format, analyze risk, and save.
        """
        # 0. Optional diarization + speaker attribution (single-phase enrichment)
        if diarization is None:
            diarization = Diarizer().run(audio_path)

        if diarization is not None and diarization.turns:
            # Only apply if speakers are missing (idempotent safety)
            if any(seg.get("speaker") is None for seg in (segments or [])):
                segments = SpeakerAttribution().apply(segments, diarization)

        # 1. Human Readability (Text Formatting)
        formatting_profile = get_config_manager().get(
            "post_processing.formatting_profile", "thinking_session"
        )
        effective_style = self._resolve_style(formatting_profile, formatting_style)
        final_text = self.formatter.format_structure(segments, style=effective_style)
        
        # 2. Truth Scoring (Quality/Risk)
        quality_analysis = self.quality_calc.calculate_risk_metrics(segments)

        # 2b. Dashboard Metrics (word-level + temporal)
        duration_seconds = float(metadata.get("duration_seconds") or 0.0)
        lang_detected = getattr(asr_info, "language", None) or language or "unknown"
        lang_prob = float(getattr(asr_info, "language_probability", 0.0) or 0.0)
        no_speech_prob = float(getattr(asr_info, "no_speech_prob", 0.0) or 0.0)
        compression_ratio = float(getattr(asr_info, "compression_ratio", 1.0) or 1.0)
        metrics = self.metrics_calc.compute(
            segments,
            language_detected=str(lang_detected),
            language_confidence=float(lang_prob),
            duration_seconds=duration_seconds,
            no_speech_probability=no_speech_prob,
            compression_ratio=compression_ratio,
        )
        
        # 3. Standardized Result Schema
        result_data = {
            "version": "4.0.0",
            "metadata": metadata,
            "transcription": {
                "full_text": final_text,
                "segments": segments,
                "language": language,
                "model": model_size,
                "formatting_style": effective_style,
            },
            "analysis": {
                "metrics": metrics,
                "diarization": diarization,
            },
            "quality": quality_analysis,
            "stats": {
                "processing_time": processing_time,
                "rtf": processing_time / metadata.get('duration_seconds', 1.0) if metadata.get('duration_seconds', 1.0) > 0 else 0
            }
        }
        
        # 4. Deterministic Persistence
        source_path = Path(audio_path)
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H%M%S")

        template_context = {
            "stem": source_path.stem,
            "date": date_str,
            "time": time_str,
            "calendar_date": metadata.get("calendar_date", date_str),
        }

        try:
            output_filename = self.filename_template.format(**template_context)
        except Exception as e:
            logger.warning(
                f"Failed to apply filename template '{self.filename_template}': {e}. "
                "Falling back to default pattern."
            )
            output_filename = f"{source_path.stem}_transcription.md"

        if Path(output_filename).suffix.lower() != ".md":
            output_filename = f"{output_filename}.md"

        output_path = self.output_dir / output_filename
        
        # Generate Markdown with clear uncertainty exposure
        self._write_markdown(output_path, result_data)
        
        # 7. Save Processed Audio (optional, but good practice to keep together)
        try:
            processed_audio_path = save_processed_audio(audio_path, PROCESSED_AUDIO_FOLDER)
            artifacts = result_data.setdefault("artifacts", {})
            artifacts["processed_audio_path"] = str(processed_audio_path)
        except Exception as e:
            logger.warning(f"Failed to save processed audio: {e}")

        return output_path, result_data

    def _write_markdown(self, path: Path, data: Dict[str, Any]) -> None:
        """Write a standardized, human-readable report."""
        if str(self.report_style).lower() == "dashboard":
            diar = (data.get("analysis") or {}).get("diarization")
            metrics = (data.get("analysis") or {}).get("metrics")
            source_path = str((data.get("metadata") or {}).get("source_path") or "")
            md = self.renderer.render_dashboard(
                audio_path=source_path if source_path else str((data.get("metadata") or {}).get("filename") or ""),
                segments=data["transcription"].get("segments", []),
                metrics=metrics,
                diarization=diar,
                engine_model=data["transcription"].get("model", "unknown"),
                backend="faster-whisper",
                formatting_style=data["transcription"].get("formatting_style", "auto"),
                processed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
            return

        risk = data["quality"]
        action = risk["action_recommendation"]
        stats = data.get("stats", {})
        
        # Color indicator for risk
        color = "🟢" if action == "Accept" else "🟡" if action == "Flag" else "🔴"

        # Optional timestamps section for detailed navigation
        segments = data["transcription"].get("segments", [])
        timestamps_section = ""
        if segments:
            timestamps_section = "\n## Timestamps\n\n" + create_timestamps_section(segments)

        # Restoration flags (multi-pass pass2_restore attaches `quality_flags` per segment)
        flag_counts: Dict[str, int] = {}
        stitched_count = 0
        total_segments = len(segments)
        for seg in segments:
            for flag in (seg.get("quality_flags") or []):
                flag_counts[str(flag)] = flag_counts.get(str(flag), 0) + 1
            if seg.get("stitched"):
                stitched_count += 1

        restoration_section = ""
        if flag_counts or stitched_count:
            sorted_flags = sorted(flag_counts.items(), key=lambda kv: (-kv[1], kv[0]))
            lines_flags = [f"- **{name}**: {count}" for name, count in sorted_flags]
            if stitched_count:
                lines_flags.append(f"- **stitched_segments**: {stitched_count}")
            restored_segments = sum(flag_counts.values())
            summary_line = (
                f"Pass 2 summary: {restored_segments}/{total_segments} segments "
                f"carried restoration flags; stitched spans: {stitched_count}."
            )
            restoration_section = (
                "\n## Restoration Notes\n\n"
                + summary_line
                + "\n\n"
                + "\n".join(lines_flags)
            )

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
            restoration_section.strip() if restoration_section else "",
            "",
            timestamps_section.strip() if timestamps_section else "",
            "",
            "---",
            "## Metadata",
            f"- **Model**: {data['transcription']['model']}",
            f"- **Formatting**: {data['transcription'].get('formatting_style', 'auto')}",
            f"- **Processing Time**: {stats.get('processing_time', 0.0):.1f}s",
            f"- **RTF**: {stats.get('rtf', 0.0):.3f}",
        ]

        with open(path, "w", encoding="utf-8") as f:
            # Preserve intentional blank lines ("" entries) for markdown spacing,
            # while still skipping any accidental None values.
            f.write("\n".join(line for line in lines if line is not None))
