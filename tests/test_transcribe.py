import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project directory to the path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestAudioTranscriber(unittest.TestCase):
    def setUp(self):
        # Create a mock for the model_manager module
        self.mock_model_manager_module = MagicMock()
        self.mock_model_manager_class = MagicMock()
        self.mock_model_manager_instance = MagicMock()
        
        # Setup the mock class to return the mock instance
        self.mock_model_manager_class.return_value = self.mock_model_manager_instance
        self.mock_model_manager_module.ModelManager = self.mock_model_manager_class
        
        # Set default attributes for the mock instance
        self.mock_model_manager_instance.model_size = "base"
        
        # Patch sys.modules to return our mock module
        self.modules_patcher = patch.dict(sys.modules, {'insightron.core.model_manager': self.mock_model_manager_module})
        self.modules_patcher.start()
        
        # Now import AudioTranscriber (it will use the mocked model_manager)
        from insightron.services.transcription.transcribe import AudioTranscriber
        self.AudioTranscriber = AudioTranscriber
        
        # Initialize AudioTranscriber
        self.transcriber = self.AudioTranscriber()

    def tearDown(self):
        self.modules_patcher.stop()

    def test_initialization(self):
        """Test that AudioTranscriber initializes with ModelManager."""
        self.mock_model_manager_class.assert_called_once()
        # AudioTranscriber now uses TranscriptionEngine which holds the ModelManager
        self.assertEqual(self.transcriber.engine.model_manager, self.mock_model_manager_instance)
        self.assertEqual(self.transcriber.model_size, "base")

    def test_transcribe_file_calls_model_manager(self):
        """Test that transcribe_file calls ModelManager.transcribe."""
        # Mock loader methods to avoid file system operations
        self.transcriber.loader = MagicMock()
        self.transcriber.loader.validate_audio_file.return_value = True
        self.transcriber.loader.get_audio_metadata.return_value = {
            'filename': 'test.wav',
            'file_size_mb': 1.0,
            'duration_seconds': 10.0,
            'duration_formatted': '0:10',
            'file_extension': '.wav',
            'sample_rate': 16000,
            'channels': 1
        }
        # Also mock load_and_preprocess
        self.transcriber.loader.load_and_preprocess.return_value = "dummy_audio_data"
        
        # Mock the return value of ModelManager.transcribe
        mock_segments = []
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_info.duration = 10.0
        self.mock_model_manager_instance.transcribe.return_value = (mock_segments, mock_info)
        
        # Mock handler to avoid file writing
        self.transcriber.handler = MagicMock()
        self.transcriber.handler.save_result.return_value = (MagicMock(), {})

        # We don't need to patch create_markdown etc anymore as they are called by handler, which is mocked
        # But we do need to ensure transcribe_file returns correctly
        
        self.transcriber.transcribe_file("dummy_path.wav")
            
        # Verify ModelManager.transcribe was called (via Engine)
        self.mock_model_manager_instance.transcribe.assert_called_once()
        args, kwargs = self.mock_model_manager_instance.transcribe.call_args
        # Audio loader returns "dummy_audio_data", so that should be passed to model
        self.assertEqual(args[0], "dummy_audio_data")
        self.assertEqual(kwargs['task'], "transcribe")

if __name__ == '__main__':
    unittest.main()
