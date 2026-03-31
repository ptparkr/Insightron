"""
Batch processing services module.

Provides optimized batch transcription functionality.
"""

from insightron.services.batch.processor import (
    batch_transcribe,
    OptimizedBatchProcessor,
    BatchResult,
)

# Backward compatibility
from insightron.services.batch.batch_state_manager import BatchState, FileStatus

__all__ = [
    "batch_transcribe",
    "OptimizedBatchProcessor",
    "BatchResult",
    "BatchState",
    "FileStatus",
]
