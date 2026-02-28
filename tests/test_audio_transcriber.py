import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from insightron.services.transcription.transcribe import AudioTranscriber
from insightron.services.base_transcriber import BaseTranscriber
from insightron.core.model_manager import ModelManager

class TestAudioTranscriber(unittest.TestCase):
    
    def setUp(self):
        # Reset singletons if necessary or just mock things out
        pass

    def test_inheritance(self):
        """Test that AudioTranscriber inherits from BaseTranscriber."""
        transcriber = AudioTranscriber()
        self.assertIsInstance(transcriber, BaseTranscriber)
        self.assertTrue(hasattr(transcriber, 'resource_manager'))
        self.assertTrue(hasattr(transcriber, 'model_manager'))

    @patch('insightron.services.transcription.transcribe.TranscriptionEngine')
    @patch('insightron.services.transcription.transcribe.AudioLoader')
    @patch('insightron.services.transcription.transcribe.ResultHandler')
    def test_initialization(self, MockHandler, MockLoader, MockEngine):
        """Test proper initialization of components."""
        transcriber = AudioTranscriber(model_size="small", language="en")
        
        self.assertEqual(transcriber.model_size, "small")
        self.assertEqual(transcriber.language, "en")
        
        # Check components are initialized
        MockLoader.assert_called_once()
        MockEngine.assert_called_once()
        MockHandler.assert_called_once()
        
        # Check engine has model manager (inherited/managed)
        # Note: AudioTranscriber creates its own engine instance.
    
    @patch('insightron.services.transcription.transcribe.TranscriptionEngine')
    @patch('insightron.services.transcription.transcribe.AudioLoader')
    @patch('insightron.services.transcription.transcribe.ResultHandler')
    def test_transcribe_file_flow(self, MockHandler, MockLoader, MockEngine):
        """Test the orchestration flow of transcribe_file."""
        transcriber = AudioTranscriber()
        
        # Setup Mocks
        mock_loader = MockLoader.return_value
        mock_engine = MockEngine.return_value
        mock_handler = MockHandler.return_value
        
        mock_loader.validate_audio_file.return_value = True
        mock_loader.get_audio_metadata.return_value = {'filename': 'test.wav', 'duration': 60}
        mock_loader.load_signal.return_value = "dummy_signal"
        mock_loader.segment_by_time.return_value = [
            {'signal': 'chunk1', 'start_time': 0, 'language': 'en'},
            {'signal': 'chunk2', 'start_time': 30, 'language': 'en'}
        ]
        
        mock_engine.process_signal_single_pass.return_value = [{'text': 'test segment'}]
        mock_handler.save_result.return_value = (Path("test_output.json"), {})
        
        # Execute
        path, data = transcriber.transcribe_file("test.wav")
        
        # Assertions
        mock_loader.validate_audio_file.assert_called_with("test.wav")
        mock_loader.segment_by_time.assert_called()
        self.assertEqual(mock_engine.process_signal_single_pass.call_count, 2)
        mock_handler.save_result.assert_called_once()

    def test_resource_validation_call(self):
        """Test that validate_resources (inherited) is available."""
        with patch('insightron.services.base_transcriber.BaseTranscriber.validate_resources') as mock_validate:
            transcriber = AudioTranscriber()
            # Manually call checking health (BaseTranscriber logic)
            # In BaseTranscriber, resource check is often in transcribe_literal or manual
            # But here we just check availability
            transcriber.validate_resources()
            mock_validate.assert_called_once()

if __name__ == '__main__':
    unittest.main()
