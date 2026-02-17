#!/usr/bin/env python3
"""
Enhanced Command Line Interface for Insightron
Optimized CLI for quick and efficient audio transcriptions with improved UX.
"""

import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Optional
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.core.config import WHISPER_MODEL, SUPPORTED_LANGUAGES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Enhanced main function with improved argument parsing and error handling."""
    parser = argparse.ArgumentParser(
        description="Insightron - Enhanced Whisper AI Transcriber CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single file transcription:
    %(prog)s audio.mp3                    # Basic transcription with auto-detection
    %(prog)s audio.wav -m large -v        # Use large model with verbose output
    %(prog)s audio.m4a -f paragraphs      # Use paragraph formatting
    %(prog)s audio.flac -m tiny -f minimal # Fast transcription with minimal formatting
    %(prog)s audio.mp3 -l es              # Spanish transcription
    %(prog)s audio.wav -l fr -m medium    # French transcription with medium model
  
  Batch processing (multiple files):
    %(prog)s audio1.mp3 audio2.mp3 audio3.mp3        # Batch process multiple files
    %(prog)s *.mp3 -b                                # Batch process all MP3 files
    %(prog)s *.wav -b -w 8                           # Use 8 workers
    %(prog)s *.mp3 -b --use-processes                # Use process pool (better for CPU-bound)
    %(prog)s audio*.mp3 -b -w 4 -m medium            # Batch with 4 workers, medium model
        """
    )
    
    parser.add_argument("audio_file", nargs='+', help="Path to audio file(s) to transcribe (supports multiple files for batch processing)")
    parser.add_argument("-m", "--model", default=WHISPER_MODEL, 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size to use (default: %(default)s)")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Enable verbose output with detailed progress")
    parser.add_argument("-f", "--format", default="auto", 
                       choices=["auto", "paragraphs", "minimal"],
                       help="Text formatting style (default: %(default)s)")
    parser.add_argument("-l", "--language", default="auto",
                       help="Language for transcription (e.g., 'en', 'es', 'fr') or 'auto' for detection (default: %(default)s)")
    parser.add_argument("--output", "-o", type=str,
                       help="Custom output path for the transcript file")
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress all output except errors")
    parser.add_argument("--batch", "-b", action="store_true",
                       help="Enable batch processing mode with parallel workers")
    parser.add_argument("--workers", "-w", type=int, default=None,
                       help="Number of parallel workers for batch processing (default: auto-detect)")
    parser.add_argument("--use-processes", action="store_true",
                       help="Use process pool instead of thread pool (better for CPU-bound tasks)")
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle multiple files or batch mode
    audio_files = [Path(f) for f in args.audio_file]
    
    # Check if files exist
    missing_files = [f for f in audio_files if not f.exists()]
    if missing_files:
        logger.error(f"Audio file(s) not found: {', '.join(str(f) for f in missing_files)}")
        print(f"❌ Error: Audio file(s) not found:")
        for f in missing_files:
            print(f"  - {f}")
        sys.exit(1)
    
    # Validate file extensions
    supported_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.ogg', '.aac', '.wma'}
    invalid_files = [f for f in audio_files if f.suffix.lower() not in supported_extensions]
    if invalid_files:
        logger.error(f"Unsupported file format(s): {', '.join(str(f) for f in invalid_files)}")
        print(f"❌ Error: Unsupported file format(s):")
        for f in invalid_files:
            print(f"  - {f} ({f.suffix})")
        print(f"Supported formats: {', '.join(supported_extensions)}")
        sys.exit(1)
    
    # Validate language
    if args.language not in SUPPORTED_LANGUAGES:
        logger.warning(f"Language '{args.language}' not supported. Using auto-detection.")
        if not args.quiet:
            print(f"⚠️  Warning: Language '{args.language}' not supported. Using auto-detection.")
            print(f"Supported languages: {', '.join(list(SUPPORTED_LANGUAGES.keys())[:10])}...")
        args.language = 'auto'
    
    # Determine if batch processing should be used
    use_batch = args.batch or len(audio_files) > 1
    
    try:
        start_time = time.time()
        
        if not args.quiet:
            print(f"🎤 Insightron - Whisper AI Transcriber")
            print(f"📁 File(s): {len(audio_files)}")
            print(f"🤖 Model: {args.model}")
            print(f"🎨 Format: {args.format}")
            print(f"🌍 Language: {args.language} ({SUPPORTED_LANGUAGES.get(args.language, 'Unknown')})")
            if use_batch:
                print(f"⚡ Batch Mode: {'Process Pool' if args.use_processes else 'Thread Pool'}")
                if args.workers:
                    print(f"👷 Workers: {args.workers}")
            print("-" * 50)
        
        if use_batch and len(audio_files) > 1:
            # Use batch processor for multiple files
            from insightron.services.batch.batch_processor import batch_transcribe_files
            
            logger.info(f"Starting batch transcription of {len(audio_files)} files")
            
            # Progress callback
            def progress_callback(completed, total, filename):
                if not args.quiet:
                    print(f"⏳ [{completed}/{total}] Processing: {filename}")
                logger.info(f"Progress: {completed}/{total} - {filename}")
            
            results = batch_transcribe_files(
                [str(f) for f in audio_files],
                model_size=args.model,
                language=args.language,
                max_workers=args.workers,
                use_multiprocessing=args.use_processes,
                progress_callback=progress_callback
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Show results
            if not args.quiet:
                print(f"\n✅ Batch transcription completed in {processing_time:.1f}s!")
                print(f"📊 Statistics:")
                print(f"  - Total files: {results['total_files']}")
                print(f"  - Successful: {results['completed']}")
                print(f"  - Failed: {results['failed_count']}")
                print(f"  - Success rate: {results['statistics']['success_rate']:.1f}%")
                print(f"  - Throughput: {results['statistics']['throughput']:.2f} files/sec")
                print(f"  - Avg time per file: {results['statistics']['average_time_per_file']:.1f}s")
                
                if results['successful']:
                    print(f"\n✅ Successful transcriptions:")
                    for success in results['successful']:
                        print(f"  ✓ {Path(success['file']).name} -> {success['output']}")
                
                if results['failed']:
                    print(f"\n❌ Failed transcriptions:")
                    for failure in results['failed']:
                        print(f"  ✗ {Path(failure['file']).name}: {failure['error']}")
            
            logger.info(f"Batch transcription completed: {results['completed']}/{results['total_files']} successful")
            
        else:
            # Single file processing
            audio_path = audio_files[0]
            
            if not args.quiet:
                print(f"📁 File: {audio_path.name}")
            
            # Initialize transcriber
            logger.info(f"Initializing transcriber with model: {args.model}")
            transcriber = AudioTranscriber(args.model)
            
            # Progress callback for CLI
            def progress_callback(message: str) -> None:
                if args.verbose and not args.quiet:
                    print(f"⏳ {message}")
                logger.debug(f"Progress: {message}")
            
            # Transcribe file
            logger.info(f"Starting transcription of {audio_path}")
            output_path, transcription_data = transcriber.transcribe_file(
                str(audio_path), 
                progress_callback=progress_callback,
                formatting_style=args.format,
                language=args.language
            )
            
            # Handle custom output path
            if args.output:
                custom_output = Path(args.output)
                custom_output.parent.mkdir(parents=True, exist_ok=True)
                output_path.rename(custom_output)
                output_path = custom_output
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Show results
            if not args.quiet:
                print(f"\n✅ Transcription completed in {processing_time:.1f}s!")
                print(f"📄 Output: {output_path}")
                metadata = transcription_data.get("metadata", {})
                transcript = transcription_data.get("transcription", {})
                stats = transcription_data.get("stats", {})

                duration_s = metadata.get("duration_seconds")
                file_size_mb = metadata.get("file_size_mb")
                language = transcript.get("language")
                full_text = transcript.get("full_text", "")
                proc_s = stats.get("processing_time")

                if duration_s is not None:
                    print(f"⏱️  Duration: {duration_s:.1f}s")
                if file_size_mb is not None:
                    print(f"📊 File Size: {file_size_mb:.1f} MB")
                if language:
                    print(f"🌍 Language: {language}")
                print(f"📝 Characters: {len(full_text):,}")

                if proc_s and proc_s > 0:
                    print(f"⚡ Processing Speed: {len(full_text) / proc_s:.1f} chars/sec")
                
                if args.verbose:
                    print(f"\n📝 Preview of transcript:")
                    print("-" * 50)
                    preview = full_text[:300]
                    print(preview + "..." if len(full_text) > 300 else preview)
            
            logger.info(f"Transcription completed successfully: {output_path}")
        
    except KeyboardInterrupt:
        logger.info("Transcription interrupted by user")
        print("\n⏹️  Transcription interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
