#!/usr/bin/env python3
"""
A/B compare formatting views for one transcript.

This is intentionally lightweight: it runs ASR once (single-pass) to get segments,
then renders multiple formatting views from the same segments so you can judge
readability without confounding model changes.
"""

import argparse
import logging
from pathlib import Path
from typing import List

from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.audio.formatter import TextFormatter
from insightron.core.config import WHISPER_MODEL, TRANSCRIPTION_FOLDER


logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B compare formatting views for one audio file.")
    parser.add_argument("audio_file", help="Path to audio file to transcribe once.")
    parser.add_argument(
        "--views",
        nargs="+",
        default=["thinking_session", "meeting_notes", "study_notes"],
        help="Formatting views to render from the same segments.",
    )
    parser.add_argument("--model", default=WHISPER_MODEL, help="Whisper model size to use.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    transcriber = AudioTranscriber(model_size=args.model)
    output_path, result_data = transcriber.transcribe_file(args.audio_file, formatting_style="auto")

    segments = result_data.get("transcription", {}).get("segments", [])
    if not segments:
        raise RuntimeError("No segments produced; cannot render views.")

    formatter = TextFormatter()
    stem = Path(args.audio_file).stem

    rendered_paths: List[Path] = []
    for view in args.views:
        rendered = formatter.format_structure(segments, style=view)
        view_path = TRANSCRIPTION_FOLDER / f"{stem}__view__{view}.md"
        with open(view_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        rendered_paths.append(view_path)

    logger.info(f"Original transcript: {output_path}")
    for p in rendered_paths:
        logger.info(f"View: {p}")


if __name__ == "__main__":
    main()

