"""
Memory Monitor Module
Tracks memory usage and provides warnings before OOM conditions
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available. Memory monitoring disabled.")

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """
    Monitors memory usage and alerts when approaching limits.
    Useful for batch processing large files.
    """
    
    def __init__(self, warning_threshold_percent: float = 80.0):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold_percent: Alert when memory usage exceeds this percentage
        """
        if not PSUTIL_AVAILABLE:
            logger.warning("psutil not available. Memory monitoring will be limited.")
            self.process = None
            self.initial_memory = 0
        else:
            self.process = psutil.Process()
            self.initial_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        
        self.warning_threshold = warning_threshold_percent
        
        logger.info(f"Memory monitor initialized. Initial: {self.initial_memory:.1f}MB")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory metrics in MB
        """
        if not PSUTIL_AVAILABLE or self.process is None:
            return {
                'process_memory_mb': 0,
                'memory_increase_mb': 0,
                'system_memory_percent': 0,
                'available_memory_mb': 0,
                'timestamp': datetime.now().isoformat(),
                'monitoring_available': False
            }
        
        mem_info = self.process.memory_info()
        virtual_mem = psutil.virtual_memory()
        
        current_process_mb = mem_info.rss / (1024 * 1024)
        memory_increase = current_process_mb - self.initial_memory
        
        return {
            'process_memory_mb': current_process_mb,
            'memory_increase_mb': memory_increase,
            'system_memory_percent': virtual_mem.percent,
            'available_memory_mb': virtual_mem.available / (1024 * 1024),
            'timestamp': datetime.now().isoformat(),
            'monitoring_available': True
        }
    
    def check_memory_health(self) -> Dict[str, Any]:
        """
        Check memory health and return warnings if necessary.
        
        Returns:
            Dictionary with health status and warnings
        """
        stats = self.get_memory_stats()
        
        if not stats.get('monitoring_available', False):
            return {
                'status': 'unavailable',
                'warnings': [],
                'memory_stats': stats
            }
        
        warnings = []
        status = 'healthy'
        
        # Check system memory usage
        if stats['system_memory_percent'] > self.warning_threshold:
            warnings.append(
                f"System memory usage at {stats['system_memory_percent']:.1f}% "
                f"(available: {stats['available_memory_mb']:.1f}MB)"
            )
            status = 'warning'
        
        # Check process memory growth
        if stats['memory_increase_mb'] > 2000:  # 2GB growth
            warnings.append(
                f"Process memory growth: {stats['memory_increase_mb']:.1f}MB. "
                f"Consider reducing batch size."
            )
            status = 'warning'
        
        return {
            'status': status,
            'warnings': warnings,
            'memory_stats': stats
        }
    
    def should_continue_batch(self) -> bool:
        """
        Determine if batch processing should continue.
        
        Returns:
            True if safe to continue, False if approaching OOM
        """
        health = self.check_memory_health()
        
        if not health['memory_stats'].get('monitoring_available', False):
            return True  # Can't monitor, assume safe
        
        for warning in health['warnings']:
            logger.warning(f"Memory: {warning}")
        
        # Stop if system memory exceeds 95% or available memory < 500MB
        stats = health['memory_stats']
        if stats['system_memory_percent'] > 95 or stats['available_memory_mb'] < 500:
            logger.error("Memory threshold exceeded. Halting batch processing.")
            return False
        
        return True

