"""
Progress Tracker Module
Event-driven progress tracking with milestone callbacks
"""

from typing import Callable, Optional, List
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Progress event types"""
    STARTED = "started"
    SEGMENT_COMPLETED = "segment_completed"
    MILESTONE = "milestone"  # 25%, 50%, 75%, 100%
    QUALITY_WARNING = "quality_warning"
    ERROR = "error"
    COMPLETED = "completed"

class ProgressTracker:
    """
    Event-driven progress tracking for transcription operations.
    Replaces percentage-based updates with meaningful milestones.
    """
    
    def __init__(self, total_segments: int, callback: Optional[Callable] = None):
        """
        Initialize progress tracker.
        
        Args:
            total_segments: Total number of segments to process
            callback: Callback function(event_type, data) for progress updates
        """
        self.total_segments = max(total_segments, 1)
        self.completed_segments = 0
        self.callback = callback
        self.start_time = datetime.now()
        self.milestones_hit = set()
        
        if self.callback:
            self._emit_event(EventType.STARTED, {
                'total_segments': total_segments,
                'timestamp': self.start_time.isoformat()
            })
    
    def segment_completed(self, segment_data: dict):
        """
        Record segment completion and emit events.
        
        Args:
            segment_data: Information about the completed segment
        """
        self.completed_segments += 1
        
        # Emit segment event
        if self.callback:
            self._emit_event(EventType.SEGMENT_COMPLETED, {
                'segment_number': self.completed_segments,
                'total': self.total_segments,
                'segment_data': segment_data
            })
        
        # Check for milestones (25%, 50%, 75%, 100%)
        progress_percent = int((self.completed_segments / self.total_segments) * 100)
        milestone = (progress_percent // 25) * 25
        
        if milestone not in self.milestones_hit and milestone > 0:
            self.milestones_hit.add(milestone)
            elapsed = (datetime.now() - self.start_time).total_seconds()
            eta_seconds = (elapsed / self.completed_segments) * (self.total_segments - self.completed_segments) if self.completed_segments > 0 else 0
            
            if self.callback:
                self._emit_event(EventType.MILESTONE, {
                    'milestone_percent': milestone,
                    'completed': self.completed_segments,
                    'total': self.total_segments,
                    'elapsed_seconds': elapsed,
                    'eta_seconds': eta_seconds
                })
    
    def quality_warning(self, warning: str, severity: str = 'medium'):
        """Emit quality warning event"""
        if self.callback:
            self._emit_event(EventType.QUALITY_WARNING, {
                'message': warning,
                'severity': severity,  # 'low'|'medium'|'high'
                'segment_number': self.completed_segments
            })
    
    def error_occurred(self, error: str):
        """Emit error event"""
        if self.callback:
            self._emit_event(EventType.ERROR, {
                'message': error,
                'segment_number': self.completed_segments
            })
    
    def completed(self):
        """Record completion and emit final event"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        if self.callback:
            self._emit_event(EventType.COMPLETED, {
                'total_segments': self.completed_segments,
                'total_time_seconds': total_time,
                'avg_time_per_segment': total_time / self.completed_segments if self.completed_segments > 0 else 0
            })
    
    def _emit_event(self, event_type: EventType, data: dict):
        """Emit progress event"""
        try:
            self.callback(event_type, data)
        except Exception as e:
            logger.error(f"Error in progress callback: {e}")

