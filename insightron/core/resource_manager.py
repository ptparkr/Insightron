import os
import logging
import platform
from typing import Dict, Any, Optional

# Try to import psutil for advanced metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceManager:
    """
    Singleton class to manage system resources dynamic allocation.
    Monitors CPU and RAM to suggest optimal worker counts and quantization settings.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.system_info = self._get_system_info()
        logger.info(f"ResourceManager initialized. System: {self.system_info['system']}, "
                   f"CPU Cores: {self.system_info['cpu_count']}, "
                   f"RAM: {self.system_info['total_ram_gb']:.1f}GB")

    def _get_system_info(self) -> Dict[str, Any]:
        """Gather static system information."""
        info = {
            "system": platform.system(),
            "cpu_count": os.cpu_count() or 1,
            "total_ram_gb": 0.0
        }
        
        if PSUTIL_AVAILABLE:
            try:
                vm = psutil.virtual_memory()
                info["total_ram_gb"] = vm.total / (1024**3)
            except Exception as e:
                logger.warning(f"Failed to get RAM info: {e}")
        
        return info

    def get_memory_stats(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        stats = {
            "total_gb": self.system_info["total_ram_gb"],
            "available_gb": 0.0,
            "percent_used": 0.0
        }
        
        if PSUTIL_AVAILABLE:
            try:
                vm = psutil.virtual_memory()
                stats["available_gb"] = vm.available / (1024**3)
                stats["percent_used"] = vm.percent
            except Exception:
                pass
                
        return stats

    def get_optimal_worker_count(self, model_size: str = "medium") -> int:
        """
        Calculate optimal worker count for batch processing based on system resources.
        
        Args:
            model_size: Size of the Whisper model (affects memory usage per worker)
            
        Returns:
            int: Recommended number of workers
        """
        cpu_count = self.system_info["cpu_count"]
        mem_stats = self.get_memory_stats()
        available_ram = mem_stats.get("available_gb", 0)
        
        # Estimate memory per worker based on model size (rough estimates)
        # tiny/base: 0.5GB, small: 1GB, medium: 2GB, large: 4GB
        mem_per_worker = {
            "tiny": 0.5, "base": 0.5,
            "small": 1.0, 
            "medium": 2.0, "distil-medium.en": 1.5,
            "large": 4.0, "large-v2": 4.0, "large-v3": 4.0, "distil-large-v2": 3.0
        }.get(model_size.split('.')[0], 1.5) # Default 1.5GB
        
        # CPU Constraint: Leave at least 1-2 cores free for system/main thread
        # If we have many cores (8+), can leave 2. If few (4), leave 1.
        reserved_cores = 2 if cpu_count >= 8 else 1
        max_cpu_workers = max(1, cpu_count - reserved_cores)
        
        # Memory Constraint: Ensure we don't swap
        # Reserve 2GB for system + other apps
        usable_ram = max(0, available_ram - 2.0) 
        max_mem_workers = int(usable_ram / mem_per_worker) if mem_per_worker > 0 else 1
        
        # If psutil not available, be conservative
        if not PSUTIL_AVAILABLE:
            max_mem_workers = max(1, int(cpu_count / 2))
            
        optimal = max(1, min(max_cpu_workers, max_mem_workers))
        
        logger.info(f"Optimal workers calc: CPU={max_cpu_workers}, RAM_limit={max_mem_workers} "
                   f"(Avail: {available_ram:.1f}GB, PerWorker: {mem_per_worker}GB) -> {optimal}")
        
        return optimal

    def recommend_quantization(self) -> str:
        """
        Recommend computation type (quantization) based on available RAM.
        """
        if not PSUTIL_AVAILABLE:
            return "int8" # Default safe choice
            
        mem_stats = self.get_memory_stats()
        # total_ram = mem_stats["total_gb"]
        available_ram = mem_stats["available_gb"]
        
        # If very tight on memory (< 4GB available), force int8
        if available_ram < 4.0:
            return "int8"
        
        # If plenty of memory (> 8GB available), could suggest float16 is faster on GPU?
        # But for CPU, int8 is usually best trade-off.
        # This hook allows future expansion.
        return "int8"

    def check_health(self) -> Dict[str, Any]:
        """Check if system is under heavy load."""
        health = {"status": "healthy", "warnings": []}
        
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            if mem.percent > 90:
                health["status"] = "constrained"
                health["warnings"].append("High Memory Usage")
            
            if cpu > 90:
                health["status"] = "constrained"
                health["warnings"].append("High CPU Usage")
                
        return health
