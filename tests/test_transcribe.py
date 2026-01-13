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
        self.assertEqual(self.transcriber.model_manager, self.mock_model_manager_instance)
        self.assertEqual(self.transcriber.model_size, "base")

    def test_transcribe_file_calls_model_manager(self):
        """Test that transcribe_file calls ModelManager.transcribe."""
        # Mock validate_audio_file and get_audio_metadata to avoid file system operations
        self.transcriber.validate_audio_file = MagicMock(return_value=True)
        self.transcriber.get_audio_metadata = MagicMock(return_value={
            'filename': 'test.wav',
            'file_size_mb': 1.0,
            'duration_seconds': 10.0,
            'duration_formatted': '0:10',
            'file_extension': '.wav'
        })
        
        # Mock the return value of ModelManager.transcribe
        mock_segments = []
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_info.duration = 10.0
        self.mock_model_manager_instance.transcribe.return_value = (mock_segments, mock_info)
        
        # Mock create_markdown and file operations to avoid writing to disk
        with patch('insightron.services.transcription.transcribe.create_markdown', return_value="Mock Markdown"), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.rename'), \
             patch('pathlib.Path.exists', return_value=False), \
             patch('insightron.services.transcription.transcribe.TRANSCRIPTION_FOLDER'):
            
            self.transcriber.transcribe_file("dummy_path.wav")
            
            # Verify ModelManager.transcribe was called
            self.mock_model_manager_instance.transcribe.assert_called_once()
            args, kwargs = self.mock_model_manager_instance.transcribe.call_args
            self.assertEqual(args[0], "dummy_path.wav")
            self.assertEqual(kwargs['task'], "transcribe")

if __name__ == '__main__':
    unittest.main()
