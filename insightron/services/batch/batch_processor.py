#!/usr/bin/env python3
"""
Batch Processor for Insightron
Provides optimized batch processing with thread and process pool support.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, FIRST_COMPLETED
import logging
from datetime import datetime
import multiprocessing

# Force UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.transcription.multi_pass_transcriber import MultiPassTranscriber
from insightron.services.base_transcriber import BaseTranscriber
from insightron.services.batch.batch_state_manager import BatchState, FileStatus
from insightron.core.config import WHISPER_MODEL, DEFAULT_LANGUAGE, get_config
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_single_file_worker(
    audio_file: str, 
    model_size: str, 
    language: str, 
    formatting_style: str,
    use_multi_pass: bool = False,
    enable_emotion: bool = False
) -> Dict[str, Any]:
    """
    Top-level worker function for batch processing.
    Must be at module level for multiprocessing pickling.
    """
    try:
        # Create a new transcriber instance for this process
        # ModelManager singleton will handle model loading/sharing within the process
        if use_multi_pass:
            config = {
                'contextual_restoration': {'enabled': True},
                'emotion_mapping': {'enabled': enable_emotion}
            }
            transcriber = MultiPassTranscriber(config=config)
            
            # Note: MultiPassTranscriber has a different interface
            result = transcriber.transcribe_multipass(
                audio_file,
                language=language if language != "auto" else None
            )
            
            # Export to file using ResultHandler (mimicking AudioTranscriber logic)
            from insightron.services.transcription.result_handler import ResultHandler
            handler = ResultHandler()
            
            output_path, result_data = handler.save_result(
                audio_path=audio_file,
                segments=result.segments,
                metadata=result.metadata,
                processing_time=result.processing_times.get('total', 0),
                model_size=model_size,
                language=result.metadata.get('language', language),
                formatting_style=formatting_style,
            )
            
            return {
                "output_path": str(output_path),
                "duration": result.metadata.get("duration"),
                "language": result.metadata.get("language"),
                "processing_time": result.processing_times.get('total'),
                "status": "success",
            }
        else:
            transcriber = AudioTranscriber(model_size, language)
            
            output_path, transcription_data = transcriber.transcribe_file(
                audio_file,
                formatting_style=formatting_style
            )
            
            metadata = transcription_data.get("metadata", {})
            stats = transcription_data.get("stats", {})
            transcription = transcription_data.get("transcription", {})

            return {
                "output_path": str(output_path),
                "duration": metadata.get("duration_seconds"),
                "language": transcription.get("language", language),
                "processing_time": stats.get("processing_time"),
                "status": "success",
            }
    except Exception as e:
        return {
            'file': audio_file,
            'error': str(e),
            'status': 'failed'
        }

class BatchTranscriber(BaseTranscriber):
    """
    Batch transcription processor with optimized concurrency support.
    """
    
    def __init__(
        self, 
        model_size: str = WHISPER_MODEL,
        language: str = DEFAULT_LANGUAGE,
        max_workers: Optional[int] = None,
        use_multiprocessing: bool = True, # Default to True for better CPU utilization
        transcriber: Optional[AudioTranscriber] = None,
        use_multi_pass: bool = False,
        enable_emotion: bool = False
    ):
        # Initialize BaseTranscriber (creates ResourceManager)
        super().__init__(model_size=model_size)
        self.language = language
        self.use_multi_pass = use_multi_pass
        self.enable_emotion = enable_emotion
        
        # Prefer threads when CUDA is available; multi-process often forces
        # multiple model loads/VRAM allocations and can OOM or thrash.
        self.use_multiprocessing = use_multiprocessing and not self._cuda_available()
        if use_multiprocessing and not self.use_multiprocessing:
            logger.info("CUDA detected: switching batch execution to ThreadPoolExecutor for stability.")
        
        # Determine optimal worker count from config or defaults (optimized using ResourceManager)
        if max_workers is None:
            # Try to get worker_count from config first
            worker_count_config = get_config('runtime.worker_count')
            if worker_count_config is not None:
                self.max_workers = worker_count_config
            else:
                # Use ResourceManager calculation
                self.max_workers = self.resource_manager.get_optimal_worker_count(model_size)
        else:
            self.max_workers = max_workers
            
        # Initialize transcriber ONLY if using threads (shared instance)
        self.transcriber = transcriber
        if not self.use_multiprocessing and self.transcriber is None:
            if self.use_multi_pass:
                logger.info("Initializing shared multi-pass engine for thread pool...")
                config = {
                    'contextual_restoration': {'enabled': True},
                    'emotion_mapping': {'enabled': self.enable_emotion}
                }
                self.transcriber = MultiPassTranscriber(config=config)
            else:
                logger.info("Initializing shared model for thread pool...")
                self.transcriber = AudioTranscriber(model_size, language)
        
        logger.info(f"BatchTranscriber initialized: model={model_size}, workers={self.max_workers}, "
                   f"multiprocessing={self.use_multiprocessing}")

    @staticmethod
    def _cuda_available() -> bool:
        """Best-effort CUDA availability check (safe fallback)."""
        try:
            import ctranslate2  # type: ignore

            return bool(getattr(ctranslate2, "get_cuda_device_count")() > 0)
        except Exception:
            return False

    def transcribe(self, audio_files: List[str], **kwargs):
        """Satisfy BaseTranscriber contract."""
        return self.transcribe_batch(audio_files, **kwargs)
    
    def transcribe_batch(
        self,
        audio_files: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        formatting_style: str = "auto",
        batch_state: Optional[BatchState] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Transcribe multiple audio files in batch with resume and retry support.
        
        Args:
            audio_files: List of audio file paths
            progress_callback: Optional callback for progress updates
            formatting_style: Text formatting style
            batch_state: Optional BatchState for resume capability
            max_retries: Maximum retry attempts per file
        """
        start_time = datetime.now()
        
        # Check resources before starting batch
        self.validate_resources()
        
        # Initialize or use provided batch state
        if batch_state is None:
            batch_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_state = BatchState(batch_id)
            # Register all files
            for audio_file in audio_files:
                batch_state.add_file(audio_file)
        else:
            # Resume mode: only process pending files
            audio_files = batch_state.get_pending_files()
            logger.info(f"Resuming batch: {len(audio_files)} files remaining")
        
        results = {
            'successful': [],
            'failed': [],
            'total_files': batch_state.state['statistics']['total'],
            'completed': batch_state.state['statistics']['completed'],
            'failed_count': batch_state.state['statistics']['failed']
        }
        
        logger.info(f"Starting batch transcription of {len(audio_files)} files with {self.max_workers} workers")
        
        ExecutorClass = ProcessPoolExecutor if self.use_multiprocessing else ThreadPoolExecutor
        
        with ExecutorClass(max_workers=self.max_workers) as executor:
            future_to_file: Dict[Any, str] = {}

            def submit_file(file_path: str) -> None:
                """Submit a file for transcription and mark it in progress."""
                batch_state.set_file_status(file_path, FileStatus.IN_PROGRESS)
                if self.use_multiprocessing:
                    future = executor.submit(
                        transcribe_single_file_worker,
                        file_path,
                        self.model_size,
                        self.language,
                        formatting_style,
                        self.use_multi_pass,
                        self.enable_emotion,
                    )
                else:
                    future = executor.submit(
                        self._transcribe_single_file_threaded,
                        file_path,
                        formatting_style,
                    )
                future_to_file[future] = file_path

            # Initial submission
            for audio_file in audio_files:
                submit_file(audio_file)

            # Robust completion loop that supports retries.
            while future_to_file:
                done, _ = wait(set(future_to_file.keys()), return_when=FIRST_COMPLETED)

                for future in done:
                    audio_file = future_to_file.pop(future)

                    try:
                        result = future.result()
                        if result.get("status") == "failed":
                            raise RuntimeError(result.get("error", "Unknown error"))

                        # Success
                        batch_state.set_file_status(
                            audio_file,
                            FileStatus.SUCCESS,
                            output_path=result.get("output_path"),
                        )

                        results["successful"].append(
                            {
                                "file": audio_file,
                                "output": result["output_path"],
                                "duration": result.get("duration"),
                                "language": result.get("language"),
                                "processing_time": result.get("processing_time"),
                            }
                        )
                        results["completed"] += 1

                        if progress_callback:
                            progress_callback(
                                results["completed"],
                                results["total_files"],
                                Path(audio_file).name,
                            )
                        logger.info(f"✓ Completed: {Path(audio_file).name}")

                    except Exception as e:
                        error_msg = str(e)
                        file_state = batch_state.state["files"].get(str(Path(audio_file).resolve()), {})
                        attempts = int(file_state.get("attempts", 0))

                        if attempts < max_retries:
                            # Record failed attempt (increments attempts) then retry.
                            logger.warning(
                                f"Retrying {Path(audio_file).name} (attempt {attempts + 1}/{max_retries}): {error_msg}"
                            )
                            batch_state.set_file_status(
                                audio_file,
                                FileStatus.FAILED,
                                last_error=error_msg,
                            )
                            submit_file(audio_file)
                        else:
                            # Final failure
                            batch_state.set_file_status(
                                audio_file,
                                FileStatus.FAILED,
                                last_error=error_msg,
                            )
                            results["failed"].append({"file": audio_file, "error": error_msg})
                            results["failed_count"] += 1
                            logger.error(f"✗ Failed: {Path(audio_file).name} - {error_msg}")
        
        # Statistics
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        batch_stats = batch_state.get_statistics()
        
        results['statistics'] = {
            'total_time_seconds': total_time,
            'throughput': results['completed'] / total_time if total_time > 0 else 0,
            'success_rate': batch_stats['success_rate'],
            'batch_id': batch_state.batch_id,
            'average_time_per_file': (
                total_time / max(1, (results['completed'] + results['failed_count']))
            ),
        }
        
        # Cleanup state if all files completed successfully
        if batch_stats['failed'] == 0 and batch_stats['pending'] == 0:
            batch_state.cleanup()
        
        return results
    
    def _transcribe_single_file_threaded(self, audio_file: str, formatting_style: str) -> Dict[str, Any]:
        """Worker method for ThreadPoolExecutor (can use shared self.transcriber)."""
        # Use shared transcriber if available, otherwise create new
        if self.transcriber:
            transcriber = self.transcriber
        else:
            transcriber = AudioTranscriber(self.model_size, self.language)
        
        if self.use_multi_pass:
            # Handle multi-pass transcription
            result = transcriber.transcribe_multipass(
                audio_file,
                language=self.language if self.language != "auto" else None
            )
            
            # Export to file
            from insightron.services.transcription.result_handler import ResultHandler
            handler = ResultHandler()
            
            output_path, result_data = handler.save_result(
                audio_path=audio_file,
                segments=result.segments,
                metadata=result.metadata,
                processing_time=result.processing_times.get('total', 0),
                model_size=self.model_size,
                language=result.metadata.get('language', self.language),
                formatting_style=formatting_style,
            )
            
            return {
                "output_path": str(output_path),
                "duration": result.metadata.get("duration"),
                "language": result.metadata.get("language", self.language),
                "processing_time": result.processing_times.get('total'),
                "status": "success",
            }
        else:
            # Standard single-pass
            output_path, transcription_data = transcriber.transcribe_file(
                audio_file,
                formatting_style=formatting_style
            )
            
            metadata = transcription_data.get("metadata", {})
            stats = transcription_data.get("stats", {})
            transcription = transcription_data.get("transcription", {})

            return {
                "output_path": str(output_path),
                "duration": metadata.get("duration_seconds"),
                "language": transcription.get("language", self.language),
                "processing_time": stats.get("processing_time"),
                "status": "success",
            }

def batch_transcribe_files(
    audio_files: List[str],
    model_size: str = WHISPER_MODEL,
    language: str = DEFAULT_LANGUAGE,
    max_workers: Optional[int] = None,
    use_multiprocessing: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    transcriber: Optional[AudioTranscriber] = None,
    enable_resume: bool = True,
    max_retries: int = 2,
    use_multi_pass: bool = False,
    enable_emotion: bool = False
) -> Dict[str, Any]:
    """
    Enhanced batch transcription with resume and retry capabilities.
    
    Args:
        enable_resume: Enable resume from previous failed batch
        max_retries: Maximum retry attempts per file
        use_multi_pass: Enable 3-pass transcription pipeline
        enable_emotion: Enable emotion detection markers
        ...existing args...
    """
    batch_transcriber = BatchTranscriber(
        model_size=model_size,
        language=language,
        max_workers=max_workers,
        use_multiprocessing=use_multiprocessing,
        transcriber=transcriber,
        use_multi_pass=use_multi_pass,
        enable_emotion=enable_emotion
    )
    
    batch_state = None
    if enable_resume:
        batch_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_state = BatchState(batch_id)
        for audio_file in audio_files:
            batch_state.add_file(audio_file)
    
    return batch_transcriber.transcribe_batch(
        audio_files,
        progress_callback=progress_callback,
        batch_state=batch_state,
        max_retries=max_retries
    )

if __name__ == "__main__":
    # Simple test when running directly
    print("Batch Processor Module")
    # You can add a simple test here if needed
