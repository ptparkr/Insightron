#!/usr/bin/env python3
"""
Insightron - Main Application Entry Point

Modern, professional audio transcription application.
Clean entry point with minimal dependencies.
"""

import os
import sys
import argparse
from pathlib import Path

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

# Suppress deprecated pkg_resources warnings from ctranslate2
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ctranslate2")

# Force UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add src directory to Python path
# Add root directory to Python path (parent of 'insightron' folder)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from insightron.app.gui.main_window import InsightronGUI
    import customtkinter as ctk
    from insightron.services.batch.batch_processor import batch_transcribe_files
    from insightron.core.config import WHISPER_MODEL, DEFAULT_LANGUAGE, TRANSCRIPTION_FOLDER
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install the required dependencies:")
    print("pip install -r setup/requirements.txt")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []
    
    try:
        import faster_whisper
    except ImportError:
        missing_deps.append("faster-whisper")
    
    try:
        import librosa
    except ImportError:
        missing_deps.append("librosa")
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nPlease install them using:")
        print("pip install -r setup/requirements.txt")
        return False
    
    return True


def check_paths():
    """Check if required paths are configured correctly."""
    if not TRANSCRIPTION_FOLDER.exists():
        print(f"⚠️  Warning: Transcription folder doesn't exist: {TRANSCRIPTION_FOLDER}")
        print("Please update the transcription_folder in config.yaml")
        return False
    
    return True


def run_gui():
    """Run the GUI application."""
    print("✅ All checks passed!")
    print("🚀 Starting GUI application...")
    
    try:
        # Configure CustomTkinter
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Create root window
        root = ctk.CTk()
        app = InsightronGUI(root)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_batch(args):
    """Run batch processing from CLI."""
    print("🚀 Starting Batch Processing...")
    
    input_path = Path(args.input)
    audio_files = []
    
    if input_path.is_file():
        audio_files = [str(input_path)]
    elif input_path.is_dir():
        supported_exts = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac', '.wma'}
        for ext in supported_exts:
            audio_files.extend([str(p) for p in input_path.glob(f"*{ext}")])
    else:
        print(f"❌ Error: Input path not found: {input_path}")
        sys.exit(1)
    
    if not audio_files:
        print(f"❌ No audio files found in: {input_path}")
        sys.exit(1)
    
    print(f"Found {len(audio_files)} files to process.")
    
    try:
        results = batch_transcribe_files(
            audio_files=audio_files,
            model_size=args.model,
            language=args.language,
            max_workers=args.workers,
            use_multiprocessing=True,
            progress_callback=lambda c, t, f: print(f"[{c}/{t}] Processing: {f}")
        )
        
        print("\nBatch Processing Complete!")
        print(f"Total time: {results['statistics']['total_time_seconds']:.2f}s")
        print(f"Successful: {len(results['successful'])}")
        print(f"Failed: {len(results['failed'])}")
        
        if results['failed']:
            print("\nFailed files:")
            for fail in results['failed']:
                print(f" - {fail['file']}: {fail['error']}")
                
    except Exception as e:
        print(f"❌ Error during batch processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main application entry point."""
    print("🎤 Insightron - AI Audio Transcriber")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check paths
    if not check_paths():
        print("Please fix the configuration and try again.")
        sys.exit(1)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Insightron - AI Audio Transcriber")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Run batch transcription')
    batch_parser.add_argument('--input', '-i', required=True, help='Input file or directory')
    batch_parser.add_argument('--workers', '-w', type=int, default=None, help='Number of worker processes')
    batch_parser.add_argument('--model', '-m', default=WHISPER_MODEL, help='Whisper model size')
    batch_parser.add_argument('--language', '-l', default=DEFAULT_LANGUAGE, help='Language code')
    
    args = parser.parse_args()
    
    if args.command == 'batch':
        run_batch(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
