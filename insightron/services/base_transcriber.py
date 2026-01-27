from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import logging
from pathlib import Path
from insightron.core.model_manager import ModelManager
from insightron.core.resource_manager import ResourceManager

logger = logging.getLogger(__name__)

class BaseTranscriber(ABC):
    """
    Abstract Base Class for all transcription services (Normal, Batch, Real-time).
    Provides common validation, resource checking, and error handling.
    """
    
    def __init__(self, model_size: str = "medium", language: Optional[str] = None):
        self.model_manager = ModelManager()
        self.resource_manager = ResourceManager()
        self.model_size = model_size
        self.language = language
        self.status = "idle"
        
    @abstractmethod
    def transcribe(self, *args, **kwargs):
        """Core transcription method to be implemented by subclasses."""
        pass
    
    def validate_resources(self) -> bool:
        """
        Check if system resources are sufficient for operation.
        Returns:
            bool: True if safe to proceed, False if critical resource shortage.
        """
        health = self.resource_manager.check_health()
        if health["status"] == "constrained":
            logger.warning(f"System resource warning: {health['warnings']}")
            # In severe cases we might return False, but mostly just warn
        return True

    def validate_audio_file(self, audio_path: str) -> bool:
        """
        Common audio file validation.
        """
        path = Path(audio_path)
        if not path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return False
            
        if path.suffix.lower() not in ['.wav', '.mp3', '.m4a', '.flac', '.ogg']:
            logger.warning(f"Unsupported or unknown file extension: {path.suffix}")
            # We might still try to process it, but warn
            
        return True

    def _handle_error(self, e: Exception, context: str = ""):
        """
        Standardized error handling and logging.
        """
        error_msg = f"Error in {context}: {str(e)}"
        logger.error(error_msg)
        self.status = "error"
        # Could add telemetry or user notification hooks here
        return error_msg
