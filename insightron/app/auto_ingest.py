#!/usr/bin/env python3
"""
Lightweight automation layer for Insightron.

Scans the configured recordings folder for audio files and runs batch
transcription using the existing batch processor and profiles.
"""

import argparse
import logging
from pathlib import Path
from typing import List

from insightron.core.config import (
    RECORDINGS_FOLDER,
    WHISPER_MODEL,
    DEFAULT_LANGUAGE,
    get_config,
)
from insightron.services.batch.batch_processor import batch_transcribe_files


logger = logging.getLogger(__name__)


def discover_audio_files(root: Path) -> List[Path]:
    """Recursively find audio files under the given root."""
    supported_extensions = {
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".mp4",
        ".ogg",
        ".aac",
        ".wma",
    }
    return [
        p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in supported_extensions
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Auto-ingest recordings from the configured recordings folder and "
            "generate transcripts into the transcription folder."
        )
    )
    parser.add_argument(
        "--profile",
        choices=["fast", "balanced", "deep"],
        help="Transcription profile to use (overrides model.profile from config.yaml).",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Language code or 'auto' (default from config).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Optional worker override for batch processing.",
    )
    parser.add_argument(
        "--use-processes",
        action="store_true",
        help="Use a process pool instead of threads for batch work.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    recordings_root = RECORDINGS_FOLDER
    logger.info(f"Scanning recordings folder: {recordings_root}")

    audio_files = discover_audio_files(recordings_root)
    if not audio_files:
        logger.info("No audio files found to transcribe.")
        return

    # Resolve profile and multi-pass behavior
    profile = args.profile or get_config("model.profile", "balanced")
    use_multi_pass = profile == "deep"
    enable_emotion = False  # kept simple for now

    logger.info(
        f"Discovered {len(audio_files)} audio files. "
        f"Profile={profile}, model={WHISPER_MODEL}, language={args.language}"
    )

    results = batch_transcribe_files(
        [str(p) for p in audio_files],
        model_size=WHISPER_MODEL,
        language=args.language,
        max_workers=args.workers,
        use_multiprocessing=args.use_processes,
        use_multi_pass=use_multi_pass,
        enable_emotion=enable_emotion,
    )

    logger.info(
        "Auto-ingest completed: "
        f"{results.get('completed')}/{results.get('total_files')} successful. "
        f"Summary: {results.get('summary_path')}"
    )


if __name__ == "__main__":
    main()

