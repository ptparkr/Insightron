from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto
import threading


class WorkloadType(Enum):
    """Types of ML workloads."""

    TRANSCRIPTION = auto()
    LLM_RESTORATION = auto()
    EMOTION_ANALYSIS = auto()
    BATCH = auto()


@dataclass
class QuotaInfo:
    """Resource quota information."""

    cpu_cores: int
    memory_gb: float
    gpu_available: bool

    @property
    def workers_allowed(self) -> int:
        """Optimal worker count based on resources."""
        return max(1, self.cpu_cores - 1)


@dataclass
class ResourceAllocation:
    """Resource allocation for a workload."""

    workload: WorkloadType
    quota: QuotaInfo
    acquired: bool = False


class ResourcePool:
    """
    Unified resource management for ML workloads.
    O(1) resource allocation and release.
    """

    _instance: Optional["ResourcePool"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = object.__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._allocations: dict[WorkloadType, ResourceAllocation] = {}
        self._quota: Optional[QuotaInfo] = None

    def _detect_quota(self) -> QuotaInfo:
        """Detect available system resources."""
        try:
            import psutil

            cpu_count = psutil.cpu_count(logical=True)
            mem = psutil.virtual_memory()
            mem_gb = mem.available / (1024**3)

            # Check for GPU
            gpu_available = False
            try:
                import ctypes

                gpu_available = ctypes.CDLL("cuda.dll") is not None
            except Exception:
                pass

            return QuotaInfo(
                cpu_cores=cpu_count or 4, memory_gb=mem_gb, gpu_available=gpu_available
            )
        except ImportError:
            return QuotaInfo(cpu_cores=4, memory_gb=8.0, gpu_available=False)

    def get_quota(self) -> QuotaInfo:
        """Get available resources - O(1)."""
        if self._quota is None:
            self._quota = self._detect_quota()
        return self._quota

    def acquire(self, workload: WorkloadType) -> ResourceAllocation:
        """O(1) resource allocation."""
        quota = self.get_quota()
        allocation = ResourceAllocation(workload=workload, quota=quota, acquired=True)
        self._allocations[workload] = allocation
        return allocation

    def release(self, workload: WorkloadType) -> None:
        """O(1) resource release."""
        self._allocations.pop(workload, None)

    def recommend_worker_count(self, model_size: str = "medium") -> int:
        """Recommend optimal worker count based on model size."""
        quota = self.get_quota()

        # Memory estimates per worker
        model_memory = {
            "tiny": 0.5,
            "base": 0.5,
            "small": 1.0,
            "medium": 2.0,
            "large": 4.0,
            "large-v2": 4.0,
            "large-v3": 4.0,
        }

        mem_per_worker = model_memory.get(model_size, 2.0)
        max_by_memory = int(quota.memory_gb / mem_per_worker)
        max_by_cpu = quota.workers_allowed

        return max(1, min(max_by_memory, max_by_cpu))

    def recommend_quantization(self) -> str:
        """Recommend compute type based on available memory."""
        quota = self.get_quota()

        if quota.memory_gb < 4:
            return "int8"
        elif quota.memory_gb < 8:
            return "int8_float16"
        else:
            return "float16"

    def check_health(self) -> dict:
        """Check system health status."""
        quota = self.get_quota()

        if quota.memory_gb < 2:
            return {"status": "critical", "warnings": ["Very low memory"]}
        elif quota.memory_gb < 4:
            return {"status": "constrained", "warnings": ["Low memory"]}
        else:
            return {"status": "healthy", "warnings": []}


# Singleton accessor
_pool: Optional[ResourcePool] = None


def get_resource_pool() -> ResourcePool:
    """Get global resource pool instance."""
    global _pool
    if _pool is None:
        _pool = ResourcePool()
    return _pool
