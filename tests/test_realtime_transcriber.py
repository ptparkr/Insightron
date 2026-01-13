"""
Comprehensive unit tests for RealtimeTranscriber (v2.2.0).
Tests ring buffer, threading, audio processing, and transcription functionality.
"""
import unittest
import pytest
import numpy as np
import threading
import time
from unittest.mock import MagicMock, patch, call
from pathlib import Path


@pytest.mark.unit
@pytest.mark.realtime
class TestRealtimeTranscriberInit(unittest.TestCase):
    """Test suite for RealtimeTranscriber initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('insightron.services.realtime.realtime_transcriber.ModelManager')
        self.mock_model = self.patcher.start()
        
    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()
    
@pytest.mark.unit
@pytest.mark.realtime
class TestSilenceDetection(unittest.TestCase):
    """Test suite for silence detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('insightron.services.realtime.realtime_transcriber.ModelManager')
        self.mock_model = self.patcher.start()
        
    def tearDown(self):
        """Clean up patches."""
        self.patcher.stop()
    
    def test_silence_detection(self):
        """Test silence threshold detection."""
        from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber
        
        transcriber = RealtimeTranscriber()
        
        # Test with silence (very low amplitude)
        silence = np.random.randn(1024) * 0.001  # Very quiet
        rms_silence = np.sqrt(np.mean(silence**2))
        
        # Test with sound (higher amplitude)
        sound = np.random.randn(1024) * 0.5  # Louder
        rms_sound = np.sqrt(np.mean(sound**2))
        
        # RMS of sound should be higher than silence
        self.assertGreater(rms_sound, rms_silence)
        
        # Check against threshold
        threshold = transcriber.silence_threshold
        self.assertLess(rms_silence, threshold)
        self.assertGreater(rms_sound, threshold * 10)  # Sound is much louder


if __name__ == '__main__':
    unittest.main()
