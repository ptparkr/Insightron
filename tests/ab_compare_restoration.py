#!/usr/bin/env python3
"""
Simple A/B harness for comparing restoration + layout outputs.

Usage (example):
    python -m tests.ab_compare_restoration
"""

from pathlib import Path
from copy import deepcopy

from insightron.services.transcription.multi_pass_transcriber import MultiPassTranscriber
from insightron.services.transcription.result_handler import ResultHandler


def load_example_segments() -> list[dict]:
    """
    Minimal placeholder for loading a representative segment list.
    In practice you can adapt this to load from a JSON artifact.
    """
    return [
        {"start": 0.0, "end": 1.0, "text": "this is the first example segment"},
        {"start": 1.0, "end": 2.0, "text": "and this is the second segment which continues the thought"},
    ]


def run_ab_compare(output_dir: Path | None = None) -> None:
    output_dir = output_dir or Path("output/ab_compare")
    output_dir.mkdir(parents=True, exist_ok=True)

    base_segments = load_example_segments()

    # A: baseline (Pass 2 disabled)
    config_a = {
        "contextual_restoration": {"enabled": False},
        "emotion_mapping": {"enabled": False},
        "chunk_duration": 30,
        "chunk_overlap": 2,
    }
    transcriber_a = MultiPassTranscriber(config_a)
    handler = ResultHandler()

    segments_a = transcriber_a.pass2_restore(deepcopy(base_segments))
    metadata = {"filename": "ab_compare_example.wav", "duration_seconds": 2.0}
    handler.save_result(
        audio_path=str(output_dir / "ab_compare_example.wav"),
        segments=segments_a,
        metadata=metadata,
        processing_time=0.0,
        model_size="medium",
        language="en",
        formatting_style="auto",
    )

    # B: multi-pass restoration enabled (uses current config defaults for provider)
    config_b = {
        "contextual_restoration": {"enabled": True},
        "emotion_mapping": {"enabled": False},
        "chunk_duration": 30,
        "chunk_overlap": 2,
    }
    transcriber_b = MultiPassTranscriber(config_b)
    segments_b = transcriber_b.pass2_restore(deepcopy(base_segments))
    handler.save_result(
        audio_path=str(output_dir / "ab_compare_example_restored.wav"),
        segments=segments_b,
        metadata=metadata,
        processing_time=0.0,
        model_size="medium",
        language="en",
        formatting_style="auto",
    )


if __name__ == "__main__":
    run_ab_compare()

