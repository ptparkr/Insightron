"""
Transcription module for Insightron.

Provides single-file transcription, batch processing, and text formatting.
"""

from transcription.transcribe import AudioTranscriber
from transcription.batch_processor import BatchTranscriber, batch_transcribe_files
from transcription.text_formatter import TextFormatter, format_transcript
from transcription.segment_analyzer import SegmentAnalyzer
from transcription.quality_metrics import QualityMetricsCalculator
from transcription.batch_state_manager import BatchState, FileStatus
from transcription.progress_tracker import ProgressTracker, EventType

__all__ = [
    'AudioTranscriber',
    'BatchTranscriber',
    'batch_transcribe_files',
    'TextFormatter',
    'format_transcript',
    'SegmentAnalyzer',
    'QualityMetricsCalculator',
    'BatchState',
    'FileStatus',
    'ProgressTracker',
    'EventType',
]
