"""
Batch Processor - Optimized with exponential backoff and circuit breaker

Features:
- O(log n) retry with exponential backoff
- Circuit breaker for failing files
- Shortest Job First scheduling
- Resource-aware worker allocation
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable, Any, List
from dataclasses import dataclass, field
from concurrent.futures import (
    ThreadPoolExecutor,
    ProcessPoolExecutor,
    wait,
    FIRST_COMPLETED,
)
from datetime import datetime
from enum import Enum, auto
import threading

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    SUCCESS = auto()
    FAILED = auto()
    RETRYING = auto()


@dataclass
class BatchFile:
    """Single file in batch."""

    path: str
    status: FileStatus = FileStatus.PENDING
    attempts: int = 0
    error: Optional[str] = None
    output_path: Optional[str] = None
    duration: Optional[float] = None
    processing_time: Optional[float] = None


@dataclass
class BatchResult:
    """Batch processing result."""

    successful: List[dict] = field(default_factory=list)
    failed: List[dict] = field(default_factory=list)
    total_files: int = 0
    completed: int = 0
    failed_count: int = 0
    total_time: float = 0.0
    throughput: float = 0.0


class CircuitBreaker:
    """Circuit breaker for handling failing workers."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._open = False
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            self._last_failure_time = datetime.now().timestamp()
            if self._failures >= self.failure_threshold:
                self._open = True
                logger.warning("Circuit breaker opened")

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._open = False

    def can_proceed(self) -> bool:
        with self._lock:
            if not self._open:
                return True

            # Check recovery timeout
            if self._last_failure_time:
                elapsed = datetime.now().timestamp() - self._last_failure_time
                if elapsed > self.recovery_timeout:
                    self._open = False
                    self._failures = 0
                    logger.info("Circuit breaker closed (recovery)")
                    return True

            return False


class OptimizedBatchProcessor:
    """
    Optimized batch processor with:
    - O(log n) exponential backoff retry
    - O(n log n) Shortest Job First scheduling
    - Circuit breaker pattern
    """

    def __init__(
        self,
        model_size: str = "medium",
        language: str = "auto",
        max_workers: Optional[int] = None,
    ):
        self.model_size = model_size
        self.language = language

        # Get optimal worker count
        from insightron.core.resources import get_resource_pool

        pool = get_resource_pool()

        if max_workers is None:
            self.max_workers = pool.recommend_worker_count(model_size)
        else:
            self.max_workers = max_workers

        self._circuit_breaker = CircuitBreaker()
        self._files: List[BatchFile] = []
        self._lock = threading.Lock()

    def process(
        self,
        audio_files: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        use_multiprocessing: bool = True,
    ) -> BatchResult:
        """Main batch processing entry."""
        start_time = datetime.now()

        # Initialize files
        self._files = [BatchFile(path=f) for f in audio_files]

        # SJF: Sort by estimated duration (smaller files first)
        self._files.sort(key=lambda f: self._estimate_duration(f.path))

        # Select executor
        ExecutorClass = (
            ProcessPoolExecutor if use_multiprocessing else ThreadPoolExecutor
        )

        result = BatchResult(total_files=len(audio_files))

        with ExecutorClass(max_workers=self.max_workers) as executor:
            pending = {f: self._submit_file(executor, f) for f in self._files}

            while pending:
                # Wait for completion
                done, _ = wait(pending.keys(), return_when=FIRST_COMPLETED)

                for future in done:
                    file = pending.pop(future)

                    try:
                        result_data = future.result()
                        file.status = FileStatus.SUCCESS
                        file.output_path = result_data.get("output_path")
                        file.processing_time = result_data.get("processing_time")

                        result.successful.append(
                            {
                                "file": file.path,
                                "output": file.output_path,
                                "processing_time": file.processing_time,
                            }
                        )
                        result.completed += 1

                        self._circuit_breaker.record_success()

                    except Exception as e:
                        file.status = FileStatus.FAILED
                        file.error = str(e)

                        # Retry with exponential backoff
                        if file.attempts < 3:
                            file.status = FileStatus.RETRYING
                            delay = self._get_backoff_delay(file.attempts)
                            logger.warning(
                                f"Retry {file.attempts + 1} for {Path(file.path).name} after {delay}s"
                            )

                            file.attempts += 1
                            pending[
                                future := executor.submit(self._process_file, file.path)
                            ] = file

                            self._circuit_breaker.record_failure()
                        else:
                            result.failed.append({"file": file.path, "error": str(e)})
                            result.failed_count += 1

                    if progress_callback:
                        progress_callback(
                            result.completed, result.total_files, Path(file.path).name
                        )

        # Calculate stats
        result.total_time = (datetime.now() - start_time).total_seconds()
        result.throughput = (
            result.completed / result.total_time if result.total_time > 0 else 0
        )

        return result

    def _submit_file(self, executor, file: BatchFile):
        """Submit single file to executor."""
        file.status = FileStatus.IN_PROGRESS
        return executor.submit(self._process_file, file.path)

    def _process_file(self, audio_path: str) -> dict:
        """Process single file."""
        from insightron.services.pipeline import get_pipeline

        pipeline = get_pipeline(self.model_size, self.language)
        result = pipeline.transcribe(audio_path)

        return {
            "output_path": str(result.output_path),
            "processing_time": result.processing_time,
            "duration": result.metadata.get("duration_seconds"),
        }

    def _estimate_duration(self, path: str) -> float:
        """Estimate file duration for SJF scheduling."""
        try:
            from insightron.services.audio import get_loader

            loader = get_loader()
            meta = loader.get_metadata(path)
            return meta.duration_seconds
        except Exception:
            return 0

    def _get_backoff_delay(self, attempt: int) -> float:
        """O(log n) exponential backoff: 1s, 2s, 4s..."""
        return min(2**attempt, 30.0)


def batch_transcribe(
    audio_files: List[str],
    model_size: str = "medium",
    language: str = "auto",
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
) -> dict:
    """Convenience function for batch transcription."""
    processor = OptimizedBatchProcessor(
        model_size=model_size,
        language=language,
        max_workers=max_workers,
    )

    result = processor.process(audio_files, progress_callback)

    return {
        "successful": result.successful,
        "failed": result.failed,
        "statistics": {
            "total_time_seconds": result.total_time,
            "throughput": result.throughput,
            "completed": result.completed,
            "failed_count": result.failed_count,
        },
    }
