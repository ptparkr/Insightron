from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from insightron.services.transcription.contracts import DiarizationResult


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


class SpeakerAttribution:
    """
    Attribute speakers to ASR segments/words by maximum overlap with diarization turns.
    """

    def apply(self, segments: List[Dict], diarization: Optional[DiarizationResult]) -> List[Dict]:
        if not segments or diarization is None or not diarization.turns:
            return segments

        turns = diarization.turns
        for seg in segments:
            seg_start = float(seg.get("start", 0.0))
            seg_end = float(seg.get("end", 0.0))
            seg["speaker"] = self._best_speaker(seg_start, seg_end, turns)

            words = seg.get("words") or []
            if isinstance(words, list):
                for w in words:
                    try:
                        w_start = float(w.get("start", 0.0))
                        w_end = float(w.get("end", 0.0))
                        w["speaker"] = self._best_speaker(w_start, w_end, turns, fallback=seg.get("speaker"))
                    except Exception:
                        continue

        return segments

    def _best_speaker(self, start: float, end: float, turns, fallback: Optional[str] = None) -> Optional[str]:
        best: Tuple[float, Optional[str]] = (0.0, None)
        for t in turns:
            ov = _overlap(start, end, float(t.start), float(t.end))
            if ov > best[0]:
                best = (ov, t.speaker)
        return best[1] or fallback

