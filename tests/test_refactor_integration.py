import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from insightron.core.resource_manager import ResourceManager
from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.batch.batch_processor import BatchTranscriber
from insightron.services.realtime.realtime_transcriber import RealtimeTranscriber
from insightron.core.model_manager import ModelManager

class TestRefactorIntegration(unittest.TestCase):
    
    def setUp(self):
        # Reset singletons
        ResourceManager._instance = None
        ModelManager._instance = None
        ModelManager._model = None
        
    def test_resource_manager_singleton(self):
        """Test ResourceManager singleton behavior."""
        rm1 = ResourceManager()
        rm2 = ResourceManager()
        self.assertIs(rm1, rm2)
        
    def test_resource_manager_worker_count(self):
        """Test dynamic worker calculation."""
        rm = ResourceManager()
        # Mock system info
        rm.system_info = {
            "system": "Windows",
            "cpu_count": 8,
            "total_ram_gb": 16.0
        }
        # Mock memory stats
        with patch.object(rm, 'get_memory_stats', return_value={"available_gb": 10.0}):
            # Medium model uses ~2GB. 10GB avail - 2GB reserved = 8GB usable. 
            # 8GB / 2GB = 4 workers.
            # TCP: 8 cores -> 6 workers.
            # Min(4, 6) = 4.
            workers = rm.get_optimal_worker_count("medium")
            self.assertEqual(workers, 4)
            
    def test_audio_transcriber_inheritance(self):
        """Test AudioTranscriber inherits BaseTranscriber and validates resources."""
        # Mock validation to avoid actual resource check logging
        with patch('insightron.services.base_transcriber.BaseTranscriber.validate_resources') as mock_validate:
            transcriber = AudioTranscriber()
            self.assertTrue(hasattr(transcriber, 'resource_manager'))
            
            # Test transcribe calls validate
            with patch.object(transcriber.loader, 'validate_audio_file', return_value=True), \
                 patch.object(transcriber.loader, 'get_audio_metadata', return_value={'filename': 'test.wav'}), \
                 patch.object(transcriber.loader, 'load_and_preprocess', return_value="test.wav"), \
                 patch.object(transcriber.engine, 'transcribe', return_value=([], MagicMock())), \
                 patch.object(transcriber.handler, 'save_result', return_value=(Path("out.txt"), {})):
                
                transcriber.transcribe_file("test.wav")
                mock_validate.assert_called_once()

    def test_batch_transcriber_optimization(self):
        """Test BatchTranscriber uses ResourceManager."""
        with patch('insightron.services.batch.batch_processor.get_config', return_value=None), \
             patch('insightron.core.resource_manager.ResourceManager.get_optimal_worker_count', return_value=5):
            
            batch = BatchTranscriber(model_size="medium", max_workers=None)
            self.assertEqual(batch.max_workers, 5)

    def test_realtime_transcriber_vad(self):
        """Test RealtimeTranscriber VAD integration."""
        with patch('insightron.core.config.get_config', side_effect=lambda k, d=None: d):
             rt = RealtimeTranscriber()
             self.assertTrue(hasattr(rt, 'model_manager'))
             # Verify it's a BaseTranscriber
             from insightron.services.base_transcriber import BaseTranscriber
             self.assertIsInstance(rt, BaseTranscriber)

if __name__ == "__main__":
    unittest.main()
