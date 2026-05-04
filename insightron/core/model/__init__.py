"""
Model module - Optimized Whisper model handling

Exports:
- ModelManager: Singleton model manager
- get_model_manager: Get manager instance
- TranscriptionParams: Immutable params
- get_default_params: Get quality-based params
"""

from insightron.core.model.manager import (
    ModelManager,
    get_model_manager,
    TranscriptionParams,
    get_default_params,
    ModelPool,
)

__all__ = [
    "ModelManager",
    "get_model_manager",
    "TranscriptionParams",
    "get_default_params",
    "ModelPool",
]
