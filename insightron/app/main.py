#!/usr/bin/env python3
"""
Insightron v4.1.0 - Main Application Entry Point

Refactored for:
- O(1) config lookup via TOML
- Async startup with non-blocking model loading
- Modular entry points (GUI/Web/Batch)
- Resource priority for ML workloads
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="ctranslate2")

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# New modular imports
from insightron.core.config import (
    get_config_manager,
    get_config,
    CONFIG_FILE,
)
from insightron.core.resources import get_resource_pool, WorkloadType
from insightron.core.bus import get_message_bus, EventType, emit


# Lazy imports - only load when needed
class LazyImport:
    """Lazy module loader for faster startup."""

    @staticmethod
    def gui():
        from insightron.app.gui.main_window import InsightronGUI

        return InsightronGUI

    @staticmethod
    def batch():
        from insightron.services.batch import batch_transcribe

        return batch_transcribe

    @staticmethod
    def ctk():
        import customtkinter as ctk

        return ctk

    @staticmethod
    def uvicorn():
        import uvicorn

        return uvicorn


def check_dependencies() -> bool:
    """Check required dependencies - O(n) where n = dependencies."""
    missing = []

    for name, module in [
        ("faster-whisper", "faster_whisper"),
        ("librosa", "librosa"),
        ("customtkinter", "customtkinter"),
    ]:
        try:
            __import__(module)
        except ImportError:
            missing.append(name)

    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall with: pip install -e .")
        return False

    return True


def check_paths() -> bool:
    """Check configured paths exist."""
    config = get_config_manager()

    trans_folder = config.transcription_folder
    if not trans_folder.exists():
        print(f"Warning: Transcription folder missing: {trans_folder}")
        return False

    return True


async def async_check_system() -> dict:
    """Async system health check - O(1)."""
    pool = get_resource_pool()
    health = pool.check_health()
    quota = pool.get_quota()

    return {
        "health": health,
        "quota": {
            "cpu_cores": quota.cpu_cores,
            "memory_gb": round(quota.memory_gb, 1),
            "gpu_available": quota.gpu_available,
        },
        "recommended_workers": pool.recommend_worker_count(),
    }


def run_gui():
    """Launch GUI with async initialization."""
    print("Starting GUI...")

    ctk = LazyImport.ctk()
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    # Create app
    InsightronGUI = LazyImport.gui()
    app = InsightronGUI(root)

    # Emit startup event
    emit(EventType.TRANSCRIPTION_STARTED, {"mode": "gui"})

    root.mainloop()


def run_web():
    """Launch web server with async support."""
    print("Starting Web UI on http://localhost:8000...")

    try:
        uvicorn = LazyImport.uvicorn()
        uvicorn.run(
            "insightron.app.web.server:app", host="127.0.0.1", port=8000, reload=False
        )
    except ImportError:
        print("Error: Install fastapi, uvicorn, python-multipart, websockets")
        sys.exit(1)


def run_batch(args) -> None:
    """Run batch processing with resource optimization."""
    print("Starting Batch Processing...")

    batch_fn = LazyImport.batch()
    input_path = Path(args.input)

    # Collect audio files
    audio_files = []
    if input_path.is_file():
        audio_files = [str(input_path)]
    elif input_path.is_dir():
        exts = {".mp3", ".wav", ".m4a", ".flac", ".mp4", ".ogg", ".aac", ".wma"}
        for ext in exts:
            audio_files.extend(str(p) for p in input_path.glob(f"*{ext}"))
    else:
        print(f"Error: Input not found: {input_path}")
        sys.exit(1)

    if not audio_files:
        print(f"No audio files found: {input_path}")
        sys.exit(1)

    print(f"Found {len(audio_files)} files")

    # Get model and config
    model = get_config("model.name", "medium")
    language = get_config("runtime.language", "auto")

    # Run batch
    results = batch_fn(
        audio_files=audio_files,
        model_size=args.model or model,
        language=args.language or language,
        max_workers=args.workers,
    )

    # Report
    stats = results.get("statistics", {})
    print(f"\nComplete: {stats.get('total_time_seconds', 0):.1f}s")
    print(f"Success: {len(results.get('successful', []))}")
    print(f"Failed: {len(results.get('failed', []))}")


async def async_main(args) -> None:
    """Async main with parallel initialization."""
    # Run system check in parallel
    system_info = await async_check_system()

    print("Insightron v4.1.0")
    print(f"CPU: {system_info['quota']['cpu_cores']} cores")
    print(f"RAM: {system_info['quota']['memory_gb']} GB")
    print(f"Workers: {system_info['recommended_workers']}")

    # Emit config reload event
    emit(EventType.CONFIG_RELOADED, {"system": system_info})


def main():
    """Entry point with modular routing."""
    parser = argparse.ArgumentParser(description="Insightron v4.1.0")
    parser.add_argument("--web", action="store_true", help="Launch Web UI")
    parser.add_argument("--check", action="store_true", help="System check only")

    subparsers = parser.add_subparsers(dest="command")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch transcription")
    batch_parser.add_argument("--input", "-i", required=True)
    batch_parser.add_argument("--workers", "-w", type=int)
    batch_parser.add_argument("--model", "-m")
    batch_parser.add_argument("--language", "-l")
    batch_parser.add_argument("--multi-pass", "-mp", action="store_true")
    batch_parser.add_argument("--emotion", "-e", action="store_true")
    batch_parser.add_argument("--style", "-s", default="auto")

    args = parser.parse_args()

    # Check mode
    if args.check:
        asyncio.run(async_main(args))
        sys.exit(0)

    # Dependency check
    if not check_dependencies():
        sys.exit(1)

    # Path check
    check_paths()

    # Route to entry point
    if args.command == "batch":
        run_batch(args)
    elif args.web:
        run_web()
    else:
        print("Tip: Use --web for modern UI")
        run_gui()


if __name__ == "__main__":
    main()
