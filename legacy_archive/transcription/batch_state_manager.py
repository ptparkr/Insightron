"""
Batch State Manager
Manages batch processing state, persistence, and resumable operations
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class FileStatus(str, Enum):
    """Status of a file in batch processing"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class BatchState:
    """
    Manages batch processing state with JSON persistence.
    Allows resume after crashes or cancellations.
    """
    
    def __init__(self, batch_id: str, state_dir: Path = Path('.batch_state')):
        """
        Initialize batch state manager.
        
        Args:
            batch_id: Unique identifier for this batch (e.g., timestamp-based)
            state_dir: Directory to store state files
        """
        self.batch_id = batch_id
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / f"{batch_id}.json"
        self.state: Dict[str, Any] = self._load_state()
        
        logger.info(f"BatchState initialized: {batch_id}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from disk, or create new"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}. Starting fresh.")
        
        return {
            'batch_id': self.batch_id,
            'created_at': datetime.now().isoformat(),
            'files': {},
            'statistics': {
                'total': 0,
                'completed': 0,
                'failed': 0,
                'skipped': 0
            }
        }
    
    def add_file(self, file_path: str):
        """Register a file in the batch"""
        file_key = str(Path(file_path).resolve())
        self.state['files'][file_key] = {
            'path': file_path,
            'status': FileStatus.PENDING.value,
            'attempts': 0,
            'last_error': None,
            'output_path': None,
            'started_at': None,
            'completed_at': None
        }
        self.state['statistics']['total'] += 1
        self._save_state()
    
    def set_file_status(
        self, 
        file_path: str, 
        status: FileStatus,
        **kwargs
    ):
        """
        Update file status with optional metadata.
        
        Args:
            file_path: Path to the file
            status: FileStatus enum value
            **kwargs: Additional metadata (error, output_path, etc.)
        """
        file_key = str(Path(file_path).resolve())
        if file_key not in self.state['files']:
            self.add_file(file_path)
        
        file_state = self.state['files'][file_key]
        previous_status = file_state['status']
        
        file_state['status'] = status.value
        file_state['updated_at'] = datetime.now().isoformat()
        
        # Update timestamps
        if status == FileStatus.IN_PROGRESS and not file_state.get('started_at'):
            file_state['started_at'] = datetime.now().isoformat()
        elif status in [FileStatus.SUCCESS, FileStatus.FAILED, FileStatus.SKIPPED]:
            file_state['completed_at'] = datetime.now().isoformat()
        
        # Update statistics if status changed
        if previous_status != status.value:
            # Decrement old status count
            old_status_key = {
                FileStatus.PENDING.value: None,
                FileStatus.IN_PROGRESS.value: None,
                FileStatus.SUCCESS.value: 'completed',
                FileStatus.FAILED.value: 'failed',
                FileStatus.SKIPPED.value: 'skipped'
            }.get(previous_status)
            
            if old_status_key:
                self.state['statistics'][old_status_key] = max(0, self.state['statistics'][old_status_key] - 1)
            
            # Increment new status count
            new_status_key = {
                FileStatus.PENDING.value: None,
                FileStatus.IN_PROGRESS.value: None,
                FileStatus.SUCCESS.value: 'completed',
                FileStatus.FAILED.value: 'failed',
                FileStatus.SKIPPED.value: 'skipped'
            }.get(status.value)
            
            if new_status_key:
                self.state['statistics'][new_status_key] = self.state['statistics'].get(new_status_key, 0) + 1
        
        # Store additional metadata
        for key, value in kwargs.items():
            file_state[key] = value
        
        # Track attempts for failed files
        if status == FileStatus.FAILED:
            file_state['attempts'] = file_state.get('attempts', 0) + 1
        
        self._save_state()
        
        logger.debug(f"File status updated: {Path(file_path).name} → {status.value}")
    
    def get_pending_files(self) -> List[str]:
        """Get list of files that haven't been processed yet"""
        return [
            file_state['path']
            for file_state in self.state['files'].values()
            if file_state['status'] in [
                FileStatus.PENDING.value,
                FileStatus.FAILED.value  # Retry failed files
            ]
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current batch statistics"""
        stats = self.state['statistics']
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        
        return {
            **stats,
            'success_rate': (
                completed / total * 100
                if total > 0 else 0
            ),
            'pending': total - completed - stats.get('failed', 0) - stats.get('skipped', 0)
        }
    
    def _save_state(self):
        """Persist state to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def cleanup(self):
        """Remove state file after successful completion"""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            logger.info(f"Cleaned up batch state: {self.batch_id}")
        except Exception as e:
            logger.warning(f"Could not clean up state file: {e}")

