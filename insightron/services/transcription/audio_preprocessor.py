from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


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


class AudioPreProcessor:
    """
    Single-phase audio preprocessing pipeline.

    Output contract: float32 mono signal, same sample rate as input.
    """

    def __init__(self, sr: int, cfg: AudioPreprocessConfig):
        self.sr = int(sr)
        self.cfg = cfg

    def process(self, audio: np.ndarray) -> Tuple[np.ndarray, dict]:
        meta: dict = {"applied": [], "skipped": []}

        if audio is None:
            raise ValueError("audio is None")

        y = np.asarray(audio, dtype=np.float32)
        if y.ndim != 1:
            y = np.mean(y, axis=-1).astype(np.float32)

        if not self.cfg.enabled:
            meta["skipped"].append("preprocess_disabled")
            return y, meta

        # 1) Noise reduction (optional)
        if self.cfg.noise_reduction_enabled:
            try:
                import noisereduce as nr  # type: ignore

                y = nr.reduce_noise(
                    y=y,
                    sr=self.sr,
                    stationary=bool(self.cfg.noise_reduction_stationary),
                    prop_decrease=float(self.cfg.noise_reduction_prop_decrease),
                ).astype(np.float32)
                meta["applied"].append("noise_reduction")
            except Exception as e:
                meta["skipped"].append(f"noise_reduction({type(e).__name__})")
                logger.warning(f"Noise reduction skipped: {e}")

        # 2) Loudness normalization (LUFS) (optional)
        # If unavailable, fall back to peak normalization later (AudioLoader does it).
        if self.cfg.loudness_enabled:
            try:
                import pyloudnorm as pyln  # type: ignore

                meter = pyln.Meter(self.sr)
                loudness = meter.integrated_loudness(y)
                y = pyln.normalize.loudness(y, loudness, float(self.cfg.loudness_target_lufs)).astype(
                    np.float32
                )
                meta["applied"].append("lufs_normalize")
            except Exception as e:
                meta["skipped"].append(f"lufs_normalize({type(e).__name__})")
                logger.warning(f"LUFS normalization skipped: {e}")

        # 3) Pre-emphasis (optional)
        if self.cfg.pre_emphasis_enabled:
            coeff = float(self.cfg.pre_emphasis_coeff)
            if 0.0 <= coeff < 1.0 and len(y) >= 2:
                y = np.append(y[0], y[1:] - coeff * y[:-1]).astype(np.float32)
                meta["applied"].append("pre_emphasis")
            else:
                meta["skipped"].append("pre_emphasis(invalid_coeff_or_short)")

        # 4) Edge trim (optional)
        if self.cfg.trim_enabled:
            try:
                import librosa

                y, _ = librosa.effects.trim(y, top_db=float(self.cfg.trim_top_db))
                y = y.astype(np.float32)
                meta["applied"].append("trim")
            except Exception as e:
                meta["skipped"].append(f"trim({type(e).__name__})")
                logger.warning(f"Trim skipped: {e}")

        # Final safety: prevent NaNs / inf
        if not np.isfinite(y).all():
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
            meta["applied"].append("nan_to_num")

        return y, meta

