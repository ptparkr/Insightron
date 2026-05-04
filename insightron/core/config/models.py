from pathlib import Path
from typing import Literal, Optional
from dataclasses import dataclass, field

LatexMode = Literal["off", "safe", "math"]


@dataclass(frozen=True)
class ModelConfig:
    name: str = "medium"
    compute_type: str = "int8"
    device: str = "auto"
    quality_mode: str = "balanced"
    enable_vad: bool = True
    enable_retry: bool = True
    max_retries: int = 2
    adaptive_vad: bool = False
    batch_size: int = 1
    enable_warmup: bool = True
    enable_dynamic_beam: bool = True


@dataclass(frozen=True)
class DecodeConfig:
    beam_size: int = 5
    best_of: int = 5
    temperature: list = field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    condition_on_previous_text: bool = True
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    word_timestamps: bool = True
    initial_prompt: str = ""


@dataclass(frozen=True)
class AudioPreprocessConfig:
    enabled: bool = True
    noise_reduction_enabled: bool = True
    noise_reduction_stationary: bool = True
    noise_reduction_prop_decrease: float = 0.75
    loudness_enabled: bool = True
    loudness_target_lufs: float = -23.0
    pre_emphasis_enabled: bool = True
    pre_emphasis_coeff: float = 0.97
    trim_enabled: bool = True
    trim_top_db: float = 20.0


@dataclass(frozen=True)
class DiarizationConfig:
    enabled: bool = False
    model: str = "pyannote/embedding"
    cluster_threshold: float = 0.5


@dataclass(frozen=True)
class RealtimeConfig:
    buffer_duration_seconds: float = 30.0
    chunk_duration_seconds: float = 5.0
    stride_seconds: float = 1.0
    silence_threshold: float = 0.015
    silence_duration: float = 0.5


@dataclass(frozen=True)
class PostProcessingConfig:
    formatting_profile: str = "thinking_session"


@dataclass(frozen=True)
class TranscriptionConfig:
    segment_merge_threshold: float = -0.5
    enable_audio_preprocessing: bool = True
    min_confidence: float = -1.0
    filename_template: str = "{stem}_transcription.md"


@dataclass(frozen=True)
class MultiPassConfig:
    enabled: bool = True
    chunk_duration: float = 30.0
    chunk_overlap: float = 2.0


@dataclass(frozen=True)
class MultiPassRestorationConfig:
    enabled: bool = True
    provider: str = "local"


@dataclass(frozen=True)
class MultiPassEmotionConfig:
    enabled: bool = False
    enabled_emotions: list = field(
        default_factory=lambda: ["cheerful", "urgent", "calm", "excited", "serious"]
    )


@dataclass(frozen=True)
class RuntimeConfig:
    worker_count: Optional[int] = None
    transcription_folder: Path = field(default_factory=lambda: Path("transcriptions"))
    processed_audio_folder: Path = field(
        default_factory=lambda: Path("processed_audio")
    )


@dataclass(frozen=True)
class ReportConfig:
    style: str = "classic"
