"""
Pipeline module - Unified transcription pipeline

Exports:
- TranscriptionPipeline: Main pipeline
- TranscriptionResult: Result container
- get_pipeline: Get pipeline instance
"""

from insightron.services.pipeline.core import (
    TranscriptionPipeline,
    TranscriptionResult,
    get_pipeline,
)

__all__ = [
    "TranscriptionPipeline",
    "TranscriptionResult",
    "get_pipeline",
]
