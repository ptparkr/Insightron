from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


@dataclass(frozen=True)
class WordTimestamp:
    word: str
    start: float
    end: float
    probability: float
    speaker: Optional[str] = None


@dataclass(frozen=True)
class SegmentData:
    start: float
    end: float
    text: str
    confidence: float
    words: List[WordTimestamp]
    speaker: Optional[str] = None
    quality_flags: Optional[List[str]] = None
    stitched: Optional[bool] = None


@dataclass(frozen=True)
class LowConfidenceWord:
    word: str
    start: float
    end: float
    confidence: float


@dataclass(frozen=True)
class TranscriptionMetrics:
    avg_confidence: float
    min_confidence: float
    low_confidence_ratio: float
    low_confidence_words: List[LowConfidenceWord]

    duration_seconds: float
    speaking_rate_wpm: float
    pause_count: int
    avg_pause_duration: float

    total_words: int
    unique_words: int
    vocabulary_density: float
    sentence_count: int

    language_detected: str
    language_confidence: float
    no_speech_probability: float
    compression_ratio: float


@dataclass(frozen=True)
class DiarizationTurn:
    start: float
    end: float
    speaker: str


@dataclass(frozen=True)
class DiarizationResult:
    pipeline_id: str
    turns: List[DiarizationTurn]
    num_speakers: Optional[int] = None


ReportStyle = Literal["classic", "dashboard"]


@dataclass(frozen=True)
class TranscriptionReport:
    version: str
    audio_path: str
    metadata: Dict[str, Any]
    segments: List[SegmentData]
    full_text: str

    metrics: Optional[TranscriptionMetrics] = None
    diarization: Optional[DiarizationResult] = None

    model: Optional[str] = None
    backend: str = "faster-whisper"
    language: str = "auto"
    formatting_style: str = "auto"
    report_style: ReportStyle = "dashboard"

