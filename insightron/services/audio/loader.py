"""
Audio Loading - Optimized with indexed access

Features:
- O(1) metadata lookup
- O(1) chunk access via index
- Lazy loading for large files
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from bisect import bisect_right

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AudioMetadata:
    """Immutable audio metadata."""

    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    file_size_mb: Optional[float] = None


class AudioIndex:
    """
    Binary search index for O(log n) chunk access.
    Pre-computes chunk boundaries for fast lookup.
    """

    def __init__(self, total_samples: int, samples_per_chunk: int):
        self.total_samples = total_samples
        self.samples_per_chunk = samples_per_chunk
        self.chunk_count = (total_samples + samples_per_chunk - 1) // samples_per_chunk
        # Pre-compute boundary offsets
        self._boundaries = [i * samples_per_chunk for i in range(self.chunk_count + 1)]

    def get_chunk_range(self, index: int) -> tuple[int, int]:
        """O(1) chunk range lookup."""
        if index < 0 or index >= self.chunk_count:
            raise IndexError(f"Chunk {index} out of range [0, {self.chunk_count})")

        start = self._boundaries[index]
        end = min(self._boundaries[index + 1], self.total_samples)
        return start, end

    def find_chunk_at_time(self, time_seconds: float, sample_rate: int) -> int:
        """O(log n) find chunk at given time."""
        target_sample = int(time_seconds * sample_rate)
        return bisect_right(self._boundaries, target_sample) - 1


class AudioLoader:
    """
    Optimized audio loader with indexed access.
    O(1) metadata, O(log n) chunk access.
    """

    SUPPORTED = {".mp3", ".wav", ".m4a", ".flac", ".mp4", ".ogg", ".aac", ".wma"}
    TARGET_SR = 16000

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._index: Dict[str, AudioIndex] = {}

    def validate(self, path: str) -> bool:
        """Validate audio file - O(1)."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        if p.suffix.lower() not in self.SUPPORTED:
            raise ValueError(f"Unsupported: {p.suffix}")
        return True

    def get_metadata(self, path: str) -> AudioMetadata:
        """Get metadata - O(1) with caching."""
        if path in self._cache:
            return self._cache[path]

        p = Path(path)
        try:
            import soundfile as sf

            info = sf.info(path)
            meta = AudioMetadata(
                filename=p.name,
                duration_seconds=info.duration,
                sample_rate=info.samplerate,
                channels=info.channels,
                file_size_mb=p.stat().st_size / (1024 * 1024),
            )
        except Exception:
            import librosa

            duration = librosa.get_duration(filename=path)
            meta = AudioMetadata(
                filename=p.name,
                duration_seconds=duration,
                sample_rate=self.TARGET_SR,
                channels=1,
                file_size_mb=p.stat().st_size / (1024 * 1024),
            )

        self._cache[path] = meta
        return meta

    def load(self, path: str) -> Any:
        """Load audio signal - O(n) where n = audio length."""
        self.validate(path)

        try:
            import soundfile as sf

            audio, sr = sf.read(path, dtype="float32")
        except Exception:
            import librosa

            audio, sr = librosa.load(path, sr=self.TARGET_SR, mono=True)

        # Normalize to mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Resample if needed
        if sr != self.TARGET_SR:
            import librosa

            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.TARGET_SR)

        return audio.astype("float32")

    def build_index(self, path: str, chunk_seconds: float = 30.0) -> AudioIndex:
        """Build index for fast chunk access."""
        meta = self.get_metadata(path)
        total_samples = int(meta.duration_seconds * self.TARGET_SR)
        samples_per_chunk = int(chunk_seconds * self.TARGET_SR)

        index = AudioIndex(total_samples, samples_per_chunk)
        self._index[path] = index
        return index

    def get_chunk(
        self, path: str, chunk_index: int, chunk_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Get chunk by index - O(log n)."""
        if path not in self._index:
            self.build_index(path, chunk_seconds)

        index = self._index[path]
        start, end = index.get_chunk_range(chunk_index)

        # Lazy load full audio if not cached
        if path not in self._cache.get("_audio_data", {}):
            audio = self.load(path)
            self._cache.setdefault("_audio_data", {})[path] = audio
        else:
            audio = self._cache["_audio_data"][path]

        chunk = audio[start:end]
        return {
            "signal": chunk,
            "start_sample": start,
            "end_sample": end,
            "start_time": start / self.TARGET_SR,
            "end_time": end / self.TARGET_SR,
            "duration": (end - start) / self.TARGET_SR,
        }

    def iter_chunks(self, path: str, chunk_seconds: float = 30.0):
        """Iterate chunks - O(n) total."""
        if path not in self._index:
            self.build_index(path, chunk_seconds)

        index = self._index[path]
        audio = self.load(path)

        for i in range(index.chunk_count):
            start, end = index.get_chunk_range(i)
            yield {
                "signal": audio[start:end],
                "start_time": start / self.TARGET_SR,
                "end_time": end / self.TARGET_SR,
                "duration": (end - start) / self.TARGET_SR,
            }

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._index.clear()


def get_loader() -> AudioLoader:
    """Get singleton loader."""
    if not hasattr(get_loader, "_instance"):
        get_loader._instance = AudioLoader()
    return get_loader._instance
