#!/usr/bin/env python3
"""
Batch Processor for Insightron
Provides optimized batch processing with thread and process pool support.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
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
from insightron.services.batch.batch_state_manager import BatchState, FileStatus
from insightron.core.config import WHISPER_MODEL, DEFAULT_LANGUAGE, get_config
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_single_file_worker(audio_file: str, model_size: str, language: str, formatting_style: str) -> Dict[str, Any]:
    """
    Top-level worker function for batch processing.
    Must be at module level for multiprocessing pickling.
    """
    try:
        # Create a new transcriber instance for this process
        # ModelManager singleton will handle model loading/sharing within the process
        transcriber = AudioTranscriber(model_size, language)
        
        output_path, transcription_data = transcriber.transcribe_file(
            audio_file,
            formatting_style=formatting_style
        )
        
        # Note: Audio saving is handled in transcribe_file() method
        
        return {
            'output_path': str(output_path),
            'duration': transcription_data['duration'],
            'language': transcription_data['language'],
            'processing_time': transcription_data['processing_time_seconds'],
            'status': 'success'
        }
    except Exception as e:
        return {
            'file': audio_file,
            'error': str(e),
            'status': 'failed'
        }

class BatchTranscriber:
    """
    Batch transcription processor with optimized concurrency support.
    """
    
    def __init__(
        self, 
        model_size: str = WHISPER_MODEL,
        language: str = DEFAULT_LANGUAGE,
        max_workers: Optional[int] = None,
        use_multiprocessing: bool = True, # Default to True for better CPU utilization
        transcriber: Optional[AudioTranscriber] = None
    ):
        self.model_size = model_size
        self.language = language
        self.use_multiprocessing = use_multiprocessing
        
        # Determine optimal worker count from config or defaults (optimized)
        if max_workers is None:
            # Try to get worker_count from config first
            worker_count_config = get_config('runtime.worker_count')
            if worker_count_config is not None:
                self.max_workers = worker_count_config
            else:
                # Auto-detect based on CPU and device (improved algorithm)
                cpu_count = os.cpu_count() or 1
                try:
                    import torch
                    has_gpu = torch.cuda.is_available()
                except ImportError:
                    has_gpu = False
                
                if has_gpu:
                    # GPU: More conservative to avoid memory issues
                    # Use 2-4 workers depending on CPU cores
                    self.max_workers = max(1, min(4, cpu_count // 2))
                else:
                    # CPU: Use more workers but leave one core free for system
                    # Use 75% of cores, minimum 2, maximum 8 for stability
                    self.max_workers = max(2, min(8, int(cpu_count * 0.75)))
        else:
            self.max_workers = max_workers
            
        # Initialize transcriber ONLY if using threads (shared instance)
        self.transcriber = transcriber
        if not self.use_multiprocessing and self.transcriber is None:
            logger.info("Initializing shared model for thread pool...")
            self.transcriber = AudioTranscriber(model_size, language)
        
        logger.info(f"BatchTranscriber initialized: model={model_size}, workers={self.max_workers}, "
                   f"multiprocessing={use_multiprocessing}")
    
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
            future_to_file = {}
            
            for audio_file in audio_files:
                if self.use_multiprocessing:
                    # Pass simple types for multiprocessing
                    future = executor.submit(
                        transcribe_single_file_worker,
                        audio_file,
                        self.model_size,
                        self.language,
                        formatting_style
                    )
                else:
                    # Use internal method for threading (can share self.transcriber)
                    future = executor.submit(
                        self._transcribe_single_file_threaded,
                        audio_file,
                        formatting_style
                    )
                future_to_file[future] = audio_file
            
            for future in as_completed(future_to_file):
                audio_file = future_to_file[future]
                batch_state.set_file_status(audio_file, FileStatus.IN_PROGRESS)
                
                try:
                    result = future.result()
                    
                    if result.get('status') == 'failed':
                        raise Exception(result.get('error', 'Unknown error'))
                    
                    # Success
                    batch_state.set_file_status(
                        audio_file, 
                        FileStatus.SUCCESS,
                        output_path=result.get('output_path')
                    )
                    
                    results['successful'].append({
                        'file': audio_file,
                        'output': result['output_path'],
                        'duration': result['duration'],
                        'language': result['language']
                    })
                    results['completed'] += 1
                    
                    if progress_callback:
                        progress_callback(
                            results['completed'],
                            results['total_files'],
                            Path(audio_file).name
                        )
                    logger.info(f"✓ Completed: {Path(audio_file).name}")
                    
                except Exception as e:
                    error_msg = str(e)
                    file_state = batch_state.state['files'].get(str(Path(audio_file).resolve()), {})
                    attempts = file_state.get('attempts', 0)
                    
                    if attempts < max_retries:
                        # Retry
                        logger.warning(f"Retrying {Path(audio_file).name} (attempt {attempts + 1}/{max_retries})")
                        batch_state.set_file_status(
                            audio_file, 
                            FileStatus.FAILED,
                            last_error=error_msg
                        )
                        # Re-queue for retry
                        if self.use_multiprocessing:
                            future = executor.submit(
                                transcribe_single_file_worker,
                                audio_file,
                                self.model_size,
                                self.language,
                                formatting_style
                            )
                        else:
                            future = executor.submit(
                                self._transcribe_single_file_threaded,
                                audio_file,
                                formatting_style
                            )
                        future_to_file[future] = audio_file
                    else:
                        # Max retries reached
                        batch_state.set_file_status(
                            audio_file, 
                            FileStatus.FAILED,
                            last_error=error_msg
                        )
                        results['failed'].append({'file': audio_file, 'error': error_msg})
                        results['failed_count'] += 1
                        logger.error(f"✗ Failed: {Path(audio_file).name} - {error_msg}")
        
        # Statistics
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        batch_stats = batch_state.get_statistics()
        
        results['statistics'] = {
            'total_time_seconds': total_time,
            'throughput': results['completed'] / total_time if total_time > 0 else 0,
            'success_rate': batch_stats['success_rate'],
            'batch_id': batch_state.batch_id
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
        
        output_path, transcription_data = transcriber.transcribe_file(
            audio_file,
            formatting_style=formatting_style
        )
        
        # Note: Audio saving is handled in transcribe_file() method
        
        return {
            'output_path': str(output_path),
            'duration': transcription_data['duration'],
            'language': transcription_data['language'],
            'processing_time': transcription_data['processing_time_seconds'],
            'status': 'success'
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
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Enhanced batch transcription with resume and retry capabilities.
    
    Args:
        enable_resume: Enable resume from previous failed batch
        max_retries: Maximum retry attempts per file
        ...existing args...
    """
    batch_transcriber = BatchTranscriber(
        model_size=model_size,
        language=language,
        max_workers=max_workers,
        use_multiprocessing=use_multiprocessing,
        transcriber=transcriber
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
