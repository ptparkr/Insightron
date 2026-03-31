"""
Audio module - Optimized audio loading and preprocessing

Exports:
- AudioLoader: Indexed audio loader
- AudioMetadata: Immutable metadata
- AudioIndex: Binary search index
- get_loader: Get singleton
"""

from insightron.services.audio.loader import (
    AudioLoader,
    AudioMetadata,
    AudioIndex,
    get_loader,
)

__all__ = [
    "AudioLoader",
    "AudioMetadata",
    "AudioIndex",
    "get_loader",
]
