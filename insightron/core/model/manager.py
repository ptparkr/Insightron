"""
Model Manager - Optimized Whisper model handling

Features:
- Async warmup for non-blocking startup
- Parameter caching for O(1) config access
- Thread-safe singleton with lazy loading
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Tuple, Iterator
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionParams:
    """Immutable transcription parameters."""

    beam_size: int = 5
    best_of: int = 5
    temperature: tuple = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    vad_filter: bool = True
    word_timestamps: bool = True
    condition_on_previous_text: bool = True


class ModelPool:
    """Pool of loaded models for different sizes."""

    _pool: Dict[str, Any] = {}
    _lock = Lock()

    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        return cls._pool.get(name)

    @classmethod
    def set(cls, name: str, model: Any) -> None:
        with cls._lock:
            cls._pool[name] = model

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._pool.clear()


def get_default_params(quality_mode: str = "balanced") -> TranscriptionParams:
    """Get default params based on quality mode. O(1)."""
    if quality_mode == "high":
        return TranscriptionParams(beam_size=5, best_of=5)
    elif quality_mode == "balanced":
        return TranscriptionParams(beam_size=3, best_of=3)
    else:  # fast
        return TranscriptionParams(beam_size=1, best_of=1)


# Lazy import for faster startup
def _get_whisper():
    from faster_whisper import WhisperModel

    return WhisperModel


class ModelManager:
    """
    Optimized Whisper model manager.
    O(1) model access after initial load.
    """

    _instance: Optional["ModelManager"] = None
    _lock = Lock()
    _model: Optional[Any] = None
    _loaded_size: Optional[str] = None
    _warmup_done: bool = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = object.__new__(cls)
                    cls._instance._init = False
        return cls._instance

    def __init__(self):
        if self._init:
            return
        self._init = True

        # Lazy imports for config
        from insightron.core.config import get_config_manager
        from insightron.core.resources import get_resource_pool

        config = get_config_manager()
        self._config = config
        self._pool = get_resource_pool()

        # Load config once at init
        self.model_size = config.model.name
        self.compute_type = config.model.compute_type
        self.device = config.model.device
        self.quality_mode = config.model.quality_mode
        self.enable_vad = config.model.enable_vad
        self.enable_retry = config.model.enable_retry

        # Pre-compute params
        self._params = get_default_params(self.quality_mode)

        # Resource-based compute override
        recommended = self._pool.recommend_quantization()
        if self.compute_type not in ("int8", "int8_float16") and recommended == "int8":
            logger.warning(f"Low memory: downgrading compute_type to int8")
            self.compute_type = "int8"

        logger.info(
            f"ModelManager: {self.model_size}/{self.device}/{self.compute_type}"
        )

    @property
    def model(self):
        """Lazy load model - O(n) only on first access."""
        if ModelManager._model is None or ModelManager._loaded_size != self.model_size:
            self.load()
        return ModelManager._model

    def load(self, async_warmup: bool = False) -> Any:
        """Load model with optional async warmup."""
        if (
            ModelManager._model is not None
            and ModelManager._loaded_size == self.model_size
        ):
            return ModelManager._model

        WhisperModel = _get_whisper()
        model_name = self.model_size
        if model_name.startswith("openai/whisper-"):
            model_name = model_name.replace("openai/whisper-", "")

        logger.info(f"Loading {model_name}...")

        try:
            ModelManager._model = WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            ModelManager._loaded_size = self.model_size

            # Warmup - async if requested
            if async_warmup:
                asyncio.create_task(self._async_warmup())
            elif self._config.model.enable_warmup and not ModelManager._warmup_done:
                self._warmup()

            return ModelManager._model

        except Exception as e:
            logger.error(f"Model load failed: {e}")
            raise

    async def _async_warmup(self) -> None:
        """Non-blocking warmup."""
        import numpy as np

        try:
            logger.info("Async warmup...")
            dummy = np.zeros(16000, dtype=np.float32)
            segments, _ = ModelManager._model.transcribe(
                dummy, beam_size=1, vad_filter=False
            )
            list(segments)  # Consume
            ModelManager._warmup_done = True
            logger.info("Warmup complete")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

    def _warmup(self) -> None:
        """Synchronous warmup."""
        import numpy as np
        import time

        try:
            logger.info("Warming up...")
            dummy = np.zeros(16000, dtype=np.float32)
            start = time.time()
            segments, _ = ModelManager._model.transcribe(
                dummy, beam_size=1, vad_filter=False
            )
            list(segments)
            ModelManager._warmup_done = True
            logger.info(f"Warmup: {time.time() - start:.2f}s")
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

    def transcribe(
        self, audio, language: Optional[str] = None, task: str = "transcribe", **kwargs
    ) -> Tuple[Iterator, Any]:
        """Transcribe with retry support."""
        model = self.model

        # Build params (O(1) from cached config)
        params = self._build_params(language, task, **kwargs)

        if self.enable_retry:
            return self._transcribe_with_retry(model, audio, params)
        return model.transcribe(audio, **params)

    def _build_params(self, language, task, **kwargs) -> Dict:
        """Build transcription params - O(1)."""
        base = {
            "beam_size": kwargs.get("beam_size", self._params.beam_size),
            "best_of": kwargs.get("best_of", self._params.best_of),
            "temperature": kwargs.get("temperature", self._params.temperature),
            "vad_filter": kwargs.get("vad_filter", self._params.vad_filter),
            "word_timestamps": kwargs.get(
                "word_timestamps", self._params.word_timestamps
            ),
            "task": task,
            "language": language,
        }

        # Add VAD params if enabled
        if base.get("vad_filter"):
            base["vad_parameters"] = {
                "threshold": 0.5,
                "min_speech_duration_ms": 250,
                "min_silence_duration_ms": 2000,
                "speech_pad_ms": 400,
            }

        return base

    def _transcribe_with_retry(self, model, audio, params) -> Tuple:
        """Transcribe with exponential backoff retry."""
        for attempt in range(3):
            try:
                return model.transcribe(audio, **params)
            except Exception as e:
                if attempt == 2:
                    raise
                # Reduce quality on retry
                params["beam_size"] = max(1, params["beam_size"] // 2)
                params["temperature"] = [0.0]
                logger.warning(f"Retry {attempt + 1}: {e}")

    def get_quality_metrics(self, segments) -> Dict:
        """Calculate quality metrics."""
        if not segments:
            return {"avg_confidence": 0.0, "total_segments": 0}

        confidences = [s.avg_logprob for s in segments if hasattr(s, "avg_logprob")]
        return {
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "total_segments": len(segments),
            "min_confidence": min(confidences) if confidences else 0,
            "max_confidence": max(confidences) if confidences else 0,
        }


# Singleton accessor
def get_model_manager() -> ModelManager:
    return ModelManager()
