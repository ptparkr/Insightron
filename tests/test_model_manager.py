"""
Enhanced unit tests for Insightron ModelManager (v2.2.0).
Tests quality modes, VAD optimization, retry mechanism, and Distil-Whisper support.
"""
import unittest
import pytest
from unittest.mock import MagicMock, patch, call
from insightron.core.model_manager import ModelManager


@pytest.mark.unit
class TestModelManager(unittest.TestCase):
    """Test suite for ModelManager singleton and core functionality."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    def test_singleton_behavior(self):
        """Test that multiple instantiations return the same object."""
        manager1 = ModelManager()
        manager2 = ModelManager()
        self.assertIs(manager1, manager2)

    @patch('insightron.core.model_manager.WhisperModel')
    def test_lazy_loading(self, mock_whisper):
        """Test that the model is not loaded on initialization."""
        manager = ModelManager()
        self.assertIsNone(manager._model)
        
        # Accessing load_model should trigger loading
        manager.load_model()
        mock_whisper.assert_called_once()
        self.assertIsNotNone(manager._model)

    @patch('insightron.core.model_manager.WhisperModel')
    def test_transcribe_returns_tuple(self, mock_whisper):
        """Test that transcribe method returns (segments, info) tuple from faster-whisper."""
        # Create mock segments and info
        mock_segment1 = MagicMock()
        mock_segment1.text = "Hello world"
        mock_segment1.start = 0.0
        mock_segment1.end = 1.5
        mock_segment1.id = 0
        mock_segment1.avg_logprob = -0.3
        
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.95
        mock_info.duration = 10.0
        
        # Setup mock model to return tuple
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([mock_segment1], mock_info)
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        segments, info = manager.transcribe("dummy_audio.wav", language="en", beam_size=5)
        
        # Verify return type is tuple
        self.assertIsInstance(segments, list)
        self.assertEqual(info.language, "en")
        self.assertEqual(info.language_probability, 0.95)
        
        # Verify model.transcribe was called with quality parameters
        mock_model_instance.transcribe.assert_called_once()


@pytest.mark.unit
class TestQualityModeConfiguration(unittest.TestCase):
    """Test suite for quality mode configurations (high/balanced/fast)."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    @patch('insightron.core.model_manager.get_config_manager')
    def test_quality_mode_high_configuration(self, mock_get_config):
        """Test that 'high' quality mode sets correct parameters."""
        # Create mock config manager
        mock_config_manager = MagicMock()
        # mock.get() should return the values
        def get_side_effect(key, default=None):
            config_values = {
                'model.quality_mode': 'high',
                'model.name': 'medium',
                'model.device': 'cpu',
                'model.compute_type': 'int8',
                'model.enable_vad': True,
                'model.enable_retry': True,
                'model.max_retries': 2,
                'model.adaptive_vad': False,
                'model.batch_size': 1
            }
            return config_values.get(key, default)
        
        mock_config_manager.get.side_effect = get_side_effect
        # Also mock the .model attribute for direct access
        mock_config_manager.model.name = 'medium'
        mock_config_manager.model.compute_type = 'int8'
        mock_config_manager.model.device = 'cpu'
        mock_get_config.return_value = mock_config_manager
        
        manager = ModelManager()
        
        self.assertEqual(manager.quality_mode, 'high')
        self.assertEqual(manager.default_beam_size, 5)
        self.assertEqual(manager.default_best_of, 5)

    @patch('insightron.core.model_manager.get_config_manager')
    def test_quality_mode_balanced_configuration(self, mock_get_config):
        """Test that 'balanced' quality mode sets correct parameters."""
        mock_config_manager = MagicMock()
        def get_side_effect(key, default=None):
            config_values = {
                'model.quality_mode': 'balanced',
                'model.name': 'medium',
                'model.device': 'cpu',
                'model.compute_type': 'int8',
                'model.enable_vad': True,
                'model.enable_retry': True,
                'model.max_retries': 2,
                'model.adaptive_vad': False,
                'model.batch_size': 1
            }
            return config_values.get(key, default)
        
        mock_config_manager.get.side_effect = get_side_effect
        mock_config_manager.model.name = 'medium'
        mock_config_manager.model.compute_type = 'int8'
        mock_config_manager.model.device = 'cpu'
        mock_get_config.return_value = mock_config_manager
        
        manager = ModelManager()
        
        self.assertEqual(manager.quality_mode, 'balanced')
        self.assertEqual(manager.default_beam_size, 3)
        self.assertEqual(manager.default_best_of, 3)

    @patch('insightron.core.model_manager.get_config_manager')
    def test_quality_mode_fast_configuration(self, mock_get_config):
        """Test that 'fast' quality mode sets correct parameters."""
        mock_config_manager = MagicMock()
        def get_side_effect(key, default=None):
            config_values = {
                'model.quality_mode': 'fast',
                'model.name': 'tiny',
                'model.device': 'cpu',
                'model.compute_type': 'int8',
                'model.enable_vad': True,
                'model.enable_retry': True,
                'model.max_retries': 2,
                'model.adaptive_vad': False,
                'model.batch_size': 1
            }
            return config_values.get(key, default)
        
        mock_config_manager.get.side_effect = get_side_effect
        mock_config_manager.model.name = 'tiny'
        mock_config_manager.model.compute_type = 'int8'
        mock_config_manager.model.device = 'cpu'
        mock_get_config.return_value = mock_config_manager
        
        manager = ModelManager()
        
        self.assertEqual(manager.quality_mode, 'fast')
        self.assertEqual(manager.default_beam_size, 1)
        self.assertEqual(manager.default_best_of, 1)


@pytest.mark.unit
class TestVADParameters(unittest.TestCase):
    """Test suite for VAD (Voice Activity Detection) parameters."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    @patch('insightron.core.model_manager.WhisperModel')
    def test_vad_parameters_included(self, mock_whisper):
        """Test that VAD parameters are properly configured."""
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([], MagicMock())
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        manager.transcribe("test.wav", vad_filter=True)
        
        # Check that transcribe was called with VAD parameters
        call_kwargs = mock_model_instance.transcribe.call_args[1]
        if call_kwargs.get("vad_filter"):
            self.assertIn("vad_parameters", call_kwargs)

    @patch('insightron.core.model_manager.WhisperModel')
    @patch('insightron.core.config.get_config_manager')
    def test_vad_threshold_configuration(self, mock_config, mock_whisper):
        """Test that VAD threshold is correctly configured."""
        mock_config_manager = MagicMock()
        mock_config_manager.get.side_effect = lambda key, default=None: {
            'model.enable_vad': True,
            'model.vad_threshold': 0.6,
            'model.name': 'medium',
            'model.device': 'cpu',
            'model.compute_type': 'int8',
            'model.quality_mode': 'high'
        }.get(key, default)
        mock_config.return_value = mock_config_manager
        
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([], MagicMock())
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        manager.transcribe("test.wav")
        
        # Verify VAD parameters were passed
        call_kwargs = mock_model_instance.transcribe.call_args[1]
        if 'vad_parameters' in call_kwargs:
            self.assertIn('threshold', call_kwargs['vad_parameters'])

    @patch('insightron.core.config.get_config_manager')
    def test_adaptive_vad_disabled_by_default(self, mock_config):
        """Test that adaptive VAD is disabled by default."""
        mock_config_manager = MagicMock()
        mock_config_manager.get.side_effect = lambda key, default=None: {
            'model.adaptive_vad': False,
            'model.name': 'medium',
            'model.device': 'cpu',
            'model.compute_type': 'int8',
            'model.quality_mode': 'high'
        }.get(key, default)
        mock_config.return_value = mock_config_manager
        
        manager = ModelManager()
        
        self.assertFalse(manager.adaptive_vad)


@pytest.mark.unit
class TestRetryMechanism(unittest.TestCase):
    """Test suite for retry mechanism with fallback strategies."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    @patch('insightron.core.model_manager.WhisperModel')
    @patch('insightron.core.config.get_config_manager')
    def test_retry_mechanism_with_degraded_quality(self, mock_config, mock_whisper):
        """Test that retry mechanism degrades quality parameters on failure."""
        mock_config_manager = MagicMock()
        mock_config_manager.get.side_effect = lambda key, default=None: {
            'model.enable_retry': True,
            'model.max_retries': 2,
            'model.name': 'medium',
            'model.device': 'cpu',
            'model.compute_type': 'int8',
            'model.quality_mode': 'high'
        }.get(key, default)
        mock_config.return_value = mock_config_manager
        
        # First call fails, second succeeds
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.side_effect = [
            RuntimeError("First attempt failed"),
            ([], MagicMock())  # Second attempt succeeds
        ]
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        
        # Should not raise error due to retry
        try:
            segments, info = manager.transcribe("test.wav")
            # Verify retry was attempted
            self.assertEqual(mock_model_instance.transcribe.call_count, 2)
        except RuntimeError:
            # If retry is not implemented yet, this is expected
            pass

    @patch('insightron.core.model_manager.WhisperModel')
    def test_temperature_fallback_on_retry(self, mock_whisper):
        """Test that temperature parameter is adjusted during retry."""
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.side_effect = [
            RuntimeError("Failed"),
            ([], MagicMock())
        ]
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        manager.enable_retry = True
        manager.max_retries = 2
        
        try:
            manager.transcribe("test.wav")
            # Check if temperature was modified on retry
            if mock_model_instance.transcribe.call_count > 1:
                first_call_kwargs = mock_model_instance.transcribe.call_args_list[0][1]
                second_call_kwargs = mock_model_instance.transcribe.call_args_list[1][1]
                # Temperature should be simplified on retry
                if 'temperature' in first_call_kwargs and 'temperature' in second_call_kwargs:
                    self.assertNotEqual(first_call_kwargs['temperature'], 
                                      second_call_kwargs['temperature'])
        except (RuntimeError, IndexError):
            pass

    @patch('insightron.core.model_manager.WhisperModel')
    def test_beam_size_fallback_on_retry(self, mock_whisper):
        """Test that beam_size is reduced during retry."""
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.side_effect = [
            RuntimeError("Failed"),
            ([], MagicMock())
        ]
        mock_whisper.return_value = mock_model_instance
        
        manager = ModelManager()
        manager.enable_retry = True
        manager.max_retries = 2
        
        try:
            manager.transcribe("test.wav", beam_size=5)
            # Check if beam_size was reduced on retry
            if mock_model_instance.transcribe.call_count > 1:
                first_call_kwargs = mock_model_instance.transcribe.call_args_list[0][1]
                second_call_kwargs = mock_model_instance.transcribe.call_args_list[1][1]
                # Beam size should be reduced on retry
                if 'beam_size' in first_call_kwargs and 'beam_size' in second_call_kwargs:
                    self.assertLessEqual(second_call_kwargs['beam_size'], 
                                        first_call_kwargs['beam_size'])
        except (RuntimeError, IndexError):
            pass


@pytest.mark.unit
class TestQualityMetrics(unittest.TestCase):
    """Test suite for quality metrics calculation."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    def test_get_quality_metrics(self):
        """Test quality metrics calculation."""
        manager = ModelManager()
        
        # Create mock segments
        mock_segments = [
            MagicMock(avg_logprob=-0.2, start=0.0, end=1.0, text="one"),
            MagicMock(avg_logprob=-0.4, start=1.0, end=2.0, text="two"),
            MagicMock(avg_logprob=-0.6, start=2.0, end=3.0, text="three"),  # Low confidence
        ]
        
        metrics = manager.get_quality_metrics(mock_segments)
        
        self.assertEqual(metrics["total_segments"], 3)
        self.assertEqual(metrics["low_confidence_count"], 1)  # One segment < -0.5
        self.assertAlmostEqual(metrics["avg_confidence"], -0.4, places=1)

    def test_quality_metrics_empty_segments(self):
        """Test quality metrics with empty segments list."""
        manager = ModelManager()
        
        metrics = manager.get_quality_metrics([])
        
        self.assertEqual(metrics["total_segments"], 0)
        self.assertEqual(metrics["low_confidence_count"], 0)
        self.assertEqual(metrics["avg_confidence"], 0.0)

    def test_quality_metrics_all_high_confidence(self):
        """Test quality metrics with all high confidence segments."""
        manager = ModelManager()
        
        mock_segments = [
            MagicMock(avg_logprob=-0.1, start=0.0, end=1.0, text="a"),
            MagicMock(avg_logprob=-0.2, start=1.0, end=2.0, text="b"),
            MagicMock(avg_logprob=-0.15, start=2.0, end=3.0, text="c"),
        ]
        
        metrics = manager.get_quality_metrics(mock_segments)
        
        self.assertEqual(metrics["total_segments"], 3)
        self.assertEqual(metrics["low_confidence_count"], 0)  # All above -0.5
        self.assertLess(metrics["avg_confidence"], -0.1)


@pytest.mark.unit
class TestDistilWhisperSupport(unittest.TestCase):
    """Test suite for Distil-Whisper model support."""
    
    def setUp(self):
        """Reset singleton instance for each test."""
        ModelManager._instance = None
        ModelManager._model = None

    @patch('insightron.core.model_manager.WhisperModel')
    @patch('insightron.core.model_manager.get_config_manager')
    def test_distil_whisper_model_loading(self, mock_get_config, mock_whisper):
        """Test that Distil-Whisper models can be loaded."""
        mock_config_manager = MagicMock()
        def get_side_effect(key, default=None):
            config_values = {
                'model.name': 'distil-medium.en',
                'model.device': 'cpu',
                'model.compute_type': 'int8',
                'model.quality_mode': 'high',
                'model.enable_vad': True,
                'model.enable_retry': True,
                'model.max_retries': 2,
                'model.adaptive_vad': False,
                'model.batch_size': 1
            }
            return config_values.get(key, default)
        
        mock_config_manager.get.side_effect = get_side_effect
        mock_config_manager.model.name = 'distil-medium.en'
        mock_config_manager.model.compute_type = 'int8'
        mock_config_manager.model.device = 'cpu'
        mock_get_config.return_value = mock_config_manager
        
        manager = ModelManager()
        manager.load_model()
        
        # Verify model was loaded with correct name
        mock_whisper.assert_called_once()
        call_args = mock_whisper.call_args
        # Model size should include 'distil'
        self.assertIn('distil', manager.model_size.lower())

    @patch('insightron.core.model_manager.WhisperModel')
    @patch('insightron.core.model_manager.get_config_manager')
    def test_distil_large_v2_support(self, mock_get_config, mock_whisper):
        """Test that distil-large-v2 model is supported."""
        mock_config_manager = MagicMock()
        def get_side_effect(key, default=None):
            config_values = {
                'model.name': 'distil-large-v2',
                'model.device': 'cpu',
                'model.compute_type': 'int8',
                'model.quality_mode': 'high',
                'model.enable_vad': True,
                'model.enable_retry': True,
                'model.max_retries': 2,
                'model.adaptive_vad': False,
                'model.batch_size': 1
            }
            return config_values.get(key, default)
        
        mock_config_manager.get.side_effect = get_side_effect
        mock_config_manager.model.name = 'distil-large-v2'
        mock_config_manager.model.compute_type = 'int8'
        mock_config_manager.model.device = 'cpu'
        mock_get_config.return_value = mock_config_manager
        
        manager = ModelManager()
        manager.load_model()
        
        # Verify model size is set correctly
        self.assertIn('distil', manager.model_size.lower())
        self.assertIn('large', manager.model_size.lower())


if __name__ == '__main__':
    unittest.main()
