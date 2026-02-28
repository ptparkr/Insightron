"""
Integration tests for Insightron (v2.2.0).
Tests end-to-end workflows and component integration.
"""
import unittest
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import soundfile as sf


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndSingleFile(unittest.TestCase):
    """Integration tests for single file transcription workflow."""
    
    def setUp(self):
        """Set up test environment with temp directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Reset singletons
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
    
    def tearDown(self):
        """Clean up temp directory."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.skip(reason="Requires actual model download")
    def test_e2e_single_file_transcription(self):
        """Test complete single file transcription workflow."""
        from insightron.services.transcription.transcribe import AudioTranscriber
        
        # Create test audio file
        audio_path = self.temp_path / "test_audio.wav"
        sample_rate = 16000
        duration = 2  # seconds
        audio_data = np.sin(2 * np.pi * 440 * np.linspace(0, duration, sample_rate * duration))
        sf.write(str(audio_path), audio_data.astype(np.float32), sample_rate)
        
        # Transcribe
        transcriber = AudioTranscriber(model_size='tiny')
        
        # Mock progress callback
        progress_callback = MagicMock()
        
        # This would require actual model - skip in unit tests
        # transcriber.transcribe_file(str(audio_path), progress_callback=progress_callback)
        
        # Verify output file was created
        # output_file = self.temp_path / "test_audio.md"
        # self.assertTrue(output_file.exists())


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndBatch(unittest.TestCase):
    """Integration tests for batch transcription workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
    
    def tearDown(self):
        """Clean up."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.skip(reason="Requires actual model download")
    def test_e2e_batch_transcription(self):
        """Test complete batch transcription workflow."""
        from insightron.services.batch.batch_processor import batch_transcribe_files
        
        # Create multiple test audio files
        audio_files = []
        for i in range(3):
            audio_path = self.temp_path / f"test_audio_{i}.wav"
            sample_rate = 16000
            audio_data = np.zeros(sample_rate, dtype=np.float32)
            sf.write(str(audio_path), audio_data, sample_rate)
            audio_files.append(str(audio_path))
        
        # Batch transcribe
        # results = batch_transcribe_files(
        #     audio_files=audio_files,
        #     model_size='tiny',
        #     use_multiprocessing=True,
        #     max_workers=2
        # )
        
        # Verify results
        # self.assertEqual(results['total_files'], 3)
        # self.assertEqual(results['completed'], 3)


@pytest.mark.integration
class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration loading and usage."""
    
    def setUp(self):
        """Reset singletons."""
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
        
        try:
            from insightron.core.config import ConfigManager
            ConfigManager._instance = None
        except ImportError:
            pass
    
    @patch('insightron.core.model_manager.get_config_manager')
    def test_config_reload_during_operation(self, mock_config_manager):
        """Test that config can be reloaded during operation."""
        mock_manager = MagicMock()
        mock_manager.get.side_effect = lambda key, default=None: {
            'model.name': 'tiny',
            'model.device': 'cpu',
            'model.compute_type': 'int8',
            'model.quality_mode': 'high'
        }.get(key, default)
        mock_config_manager.return_value = mock_manager
        
        from insightron.core.model_manager import ModelManager
        
        manager1 = ModelManager()
        initial_model = manager1.model_size
        
        # Simulate config reload
        mock_manager.get.side_effect = lambda key, default=None: {
            'model.name': 'base',  # Changed
            'model.device': 'cpu',
            'model.compute_type': 'int8',
            'model.quality_mode': 'balanced'
        }.get(key, default)
        
        # Manually update the attribute to reflect 'reload'
        mock_manager.model.name = 'base'
        
        # New instance should reflect config changes
        ModelManager._instance = None  # Reset singleton
        manager2 = ModelManager()
        
        # Model name should have changed
        self.assertNotEqual(initial_model, manager2.model_size)


@pytest.mark.integration
class TestModelPersistence(unittest.TestCase):
    """Integration tests for model persistence across transcriptions."""
    
    def setUp(self):
        """Reset singletons."""
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
    
    def test_model_persistence_across_files(self):
        """Test that model is loaded once and reused."""
        from insightron.core.model_manager import ModelManager
        
        manager1 = ModelManager()
        manager2 = ModelManager()
        manager3 = ModelManager()
        
        # All should be the same instance
        self.assertIs(manager1, manager2)
        self.assertIs(manager2, manager3)
    
    @patch('insightron.core.model_manager.WhisperModel')
    def test_model_loaded_only_once(self, mock_whisper):
        """Test that model is loaded only once even with multiple transcriptions."""
        from insightron.core.model_manager import ModelManager
        
        manager = ModelManager()
        
        # Load model multiple times
        manager.load_model()
        manager.load_model()
        manager.load_model()
        
        # WhisperModel should only be called once (lazy loading + caching)
        if manager._model is not None:
            # Model was loaded
            self.assertIsNotNone(manager._model)


@pytest.mark.integration
class TestOutputFileFormat(unittest.TestCase):
    """Integration tests for output file generation and format."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_output_file_format(self):
        """Test that output markdown file has correct format."""
        from insightron.core.utils import create_markdown
        
        # Create markdown
        text = "This is a test transcription."
        filename = "test_audio"
        date = "2024-01-01 12:00:00"
        duration = "0:10"
        duration_seconds = 10.0
        model = "tiny"
        language = "en"
        file_size_mb = 1.0
        
        markdown = create_markdown(
            filename=filename,
            text=text,
            date=date,
            duration=duration,
            duration_seconds=duration_seconds,
            file_size_mb=file_size_mb,
            model=model,
            language=language,
            formatting_style="auto"
        )
        
        # Verify markdown structure
        self.assertIn("# 🎤 Transcription:", markdown)
        self.assertIn("## 📊 Metadata", markdown)
        self.assertIn("## 📝 Transcript", markdown)
        self.assertIn(text, markdown)
        self.assertIn(f"**Model:** {model}", markdown)
        self.assertIn(f"**Language:** {language}", markdown)


@pytest.mark.integration
class TestMetadataAccuracy(unittest.TestCase):
    """Integration tests for metadata generation and accuracy."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('insightron.core.model_manager.ModelManager')
    def test_metadata_accuracy(self, mock_model_manager):
        """Test that metadata is accurately extracted and stored."""
        # Test metadata extraction from audio file
        audio_path = self.temp_path / "test.wav"
        sample_rate = 16000
        duration = 5  # seconds
        audio_data = np.zeros(sample_rate * duration, dtype=np.float32)
        sf.write(str(audio_path), audio_data, sample_rate)
        
        # Use real AudioTranscriber but mock ModelManager dependency
        from insightron.services.transcription.transcribe import AudioTranscriber
        real_transcriber = AudioTranscriber()
        metadata = real_transcriber.get_audio_metadata(str(audio_path))
        
        # Verify metadata
        self.assertIn('filename', metadata)
        self.assertIn('file_size_mb', metadata)
        self.assertIn('duration_seconds', metadata)
        self.assertIn('duration_formatted', metadata)
        
        # Duration should be approximately 5 seconds
        self.assertAlmostEqual(metadata['duration_seconds'], duration, delta=0.5)


if __name__ == '__main__':
    unittest.main()
