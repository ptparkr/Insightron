import json
from pathlib import Path
from typing import Dict, Any

from insightron.core.config import TRANSCRIPTION_FOLDER


def save_batch_summary(results: Dict[str, Any]) -> Path:
    """
    Persist a compact, machine-readable batch summary alongside transcripts.

    The summary captures:
    - Per-file outputs and basic metrics
    - Aggregate statistics for the batch
    """
    batch_id = results.get("statistics", {}).get("batch_id") or results.get("batch_id", "batch")

    summary_filename = f"{batch_id}_summary.json"
    summary_path = TRANSCRIPTION_FOLDER / summary_filename

    payload: Dict[str, Any] = {
        "batch_id": batch_id,
        "total_files": results.get("total_files"),
        "completed": results.get("completed"),
        "failed_count": results.get("failed_count"),
        "statistics": results.get("statistics", {}),
        "successful": results.get("successful", []),
        "failed": results.get("failed", []),
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return summary_path

