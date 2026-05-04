from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from insightron.core.config import get_config_manager
from insightron.services.transcription.contracts import DiarizationResult, DiarizationTurn

logger = logging.getLogger(__name__)


class Diarizer:
    """
    Thin wrapper over pyannote speaker diarization.

    This module is optional: if pyannote isn't installed or a token isn't
    configured, the caller can treat diarization as unavailable.
    """

    def __init__(self):
        self.cfg = get_config_manager()

    def enabled(self) -> bool:
        return bool(self.cfg.get("diarization.enabled", False))

    def run(self, audio_path: str) -> Optional[DiarizationResult]:
        if not self.enabled():
            return None

        pipeline_id = str(self.cfg.get("diarization.pipeline_id", "pyannote/speaker-diarization@2.1"))
        hf_token = str(self.cfg.get("diarization.hf_token", "") or "").strip()
        if not hf_token:
            hf_token = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or "").strip()

        if not hf_token:
            logger.warning("Diarization enabled but no HF token found; skipping diarization.")
            return None

        try:
            from pyannote.audio import Pipeline  # type: ignore
        except Exception as e:
            logger.warning(f"pyannote.audio not available; skipping diarization: {e}")
            return None

        try:
            pipeline = Pipeline.from_pretrained(pipeline_id, use_auth_token=hf_token)
        except Exception as e:
            logger.error(f"Failed to load diarization pipeline '{pipeline_id}': {e}")
            return None

        diar_kwargs: Dict[str, Any] = {}
        for k in ("num_speakers", "min_speakers", "max_speakers"):
            v = self.cfg.get(f"diarization.{k}", None)
            if v is not None:
                diar_kwargs[k] = v

        try:
            diarization = pipeline(audio_path, **diar_kwargs)
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return None

        turns: List[DiarizationTurn] = []
        speakers: set[str] = set()
        try:
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                s = str(speaker)
                speakers.add(s)
                turns.append(DiarizationTurn(start=float(segment.start), end=float(segment.end), speaker=s))
        except Exception as e:
            logger.error(f"Failed to iterate diarization tracks: {e}")
            return None

        return DiarizationResult(
            pipeline_id=pipeline_id,
            turns=turns,
            num_speakers=len(speakers) if speakers else None,
        )

