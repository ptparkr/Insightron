"""
Batch processing services module.

Provides batch transcription functionality:
- batch_transcribe_files: Main batch processing function
- BatchState: State management for batch operations
- ProgressTracker: Progress tracking and reporting
"""

from insightron.services.batch.batch_processor import batch_transcribe_files
from insightron.services.batch.batch_state_manager import BatchState, FileStatus
from insightron.services.batch.progress_tracker import ProgressTracker

__all__ = [
    'batch_transcribe_files',
    'BatchState',
    'FileStatus',
    'ProgressTracker',
]
