from __future__ import annotations

import re
import statistics
from typing import Any, Dict, List, Optional, Tuple

from insightron.services.transcription.contracts import LowConfidenceWord, TranscriptionMetrics


class MetricsCalculator:
    def __init__(self, confidence_threshold: float = 0.75, pause_gap_seconds: float = 0.3):
        self.confidence_threshold = float(confidence_threshold)
        self.pause_gap_seconds = float(pause_gap_seconds)

    def compute(
        self,
        segments: List[Dict[str, Any]],
        *,
        language_detected: str = "unknown",
        language_confidence: float = 0.0,
        duration_seconds: float = 0.0,
        no_speech_probability: float = 0.0,
        compression_ratio: float = 1.0,
    ) -> TranscriptionMetrics:
        words = self._extract_words(segments)
        word_texts = [w["word"].strip() for w in words if (w.get("word") or "").strip()]
        total_words = len(word_texts)

        probs = [float(w.get("probability", 1.0)) for w in words] or [1.0]
        avg_conf = float(statistics.mean(probs))
        min_conf = float(min(probs))

        low_conf_words = [
            LowConfidenceWord(
                word=str(w.get("word", "")).strip(),
                start=float(w.get("start", 0.0)),
                end=float(w.get("end", 0.0)),
                confidence=float(w.get("probability", 0.0)),
            )
            for w in words
            if float(w.get("probability", 1.0)) < self.confidence_threshold
        ]

        pauses = self._detect_pauses(words)

        unique_words = len({t.lower() for t in word_texts})
        vocab_density = (unique_words / max(total_words, 1)) if total_words else 0.0

        sentence_count = self._count_sentences(" ".join(seg.get("text", "") for seg in segments))

        speaking_rate_wpm = (total_words / max(float(duration_seconds) or 1.0, 1e-6)) * 60.0

        return TranscriptionMetrics(
            avg_confidence=avg_conf,
            min_confidence=min_conf,
            low_confidence_ratio=len(low_conf_words) / max(total_words, 1),
            low_confidence_words=low_conf_words,
            duration_seconds=float(duration_seconds),
            speaking_rate_wpm=float(speaking_rate_wpm),
            pause_count=len(pauses),
            avg_pause_duration=float(statistics.mean(pauses)) if pauses else 0.0,
            total_words=total_words,
            unique_words=unique_words,
            vocabulary_density=float(vocab_density),
            sentence_count=sentence_count,
            no_speech_probability=float(no_speech_probability),
            language_detected=str(language_detected or "unknown"),
            language_confidence=float(language_confidence),
            compression_ratio=float(compression_ratio),
        )

    def _extract_words(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for seg in segments or []:
            for w in (seg.get("words") or []):
                if w is None:
                    continue
                out.append(w)
        return out

    def _detect_pauses(self, words: List[Dict[str, Any]]) -> List[float]:
        pauses: List[float] = []
        if not words or len(words) < 2:
            return pauses

        prev_end = float(words[0].get("end", 0.0))
        for w in words[1:]:
            start = float(w.get("start", 0.0))
            gap = start - prev_end
            if gap > self.pause_gap_seconds:
                pauses.append(float(gap))
            prev_end = float(w.get("end", prev_end))
        return pauses

    def _count_sentences(self, text: str) -> int:
        t = (text or "").strip()
        if not t:
            return 0
        # Conservative: count explicit sentence-ending punctuation.
        return len(re.findall(r"[.!?]+", t))

