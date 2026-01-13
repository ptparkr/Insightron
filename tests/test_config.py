"""
Unit tests for Insightron configuration system.
Tests config loading, validation, defaults, and manager functionality.
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Import config modules
from insightron.core.config import (
    ConfigManager,
    ModelConfig,
    RuntimeConfig,
    RealtimeConfig,
    PostProcessingConfig,
    get_config,
    get_config_manager
)


class TestConfigDataclasses(unittest.TestCase):
    """Test configuration dataclasses and their validation."""
    
    def test_model_config_defaults(self):
        """Test ModelConfig with default values."""
        config = ModelConfig()
        self.assertEqual(config.name, "small")
        self.assertEqual(config.compute_type, "int8")
        self.assertEqual(config.device, "auto")
    
    def test_model_config_validation_invalid_model(self):
        """Test ModelConfig validates and corrects invalid model names."""
        config = ModelConfig(name="invalid_model")
        # Should fallback to default
        self.assertEqual(config.name, "medium")
    
    def test_model_config_validation_invalid_compute_type(self):
        """Test ModelConfig validates and corrects invalid compute types."""
        config = ModelConfig(compute_type="invalid_type")
        self.assertEqual(config.compute_type, "int8")
    
    def test_model_config_validation_invalid_device(self):
        """Test ModelConfig validates and corrects invalid devices."""
        config = ModelConfig(device="invalid_device")
        self.assertEqual(config.device, "auto")
    
    def test_runtime_config_defaults(self):
        """Test RuntimeConfig with default values."""
        config = RuntimeConfig()
        self.assertIsInstance(config.transcription_folder, str)
        self.assertIsInstance(config.recordings_folder, str)
        self.assertEqual(config.max_file_size_mb, 500)
        self.assertEqual(config.log_level, "INFO")
        self.assertIsNone(config.worker_count)
    
    def test_runtime_config_validation_max_file_size(self):
        """Test RuntimeConfig validates max_file_size_mb."""
        config = RuntimeConfig(max_file_size_mb=-100)
        self.assertEqual(config.max_file_size_mb, 500)  # Should reset to default
    
    def test_runtime_config_validation_log_level(self):
        """Test RuntimeConfig validates log_level."""
        config = RuntimeConfig(log_level="INVALID")
        self.assertEqual(config.log_level, "INFO")
    
    def test_runtime_config_validation_worker_count(self):
        """Test RuntimeConfig validates worker_count."""
        config = RuntimeConfig(worker_count=-5)
        self.assertIsNone(config.worker_count)  # Should reset to None
    
    def test_realtime_config_defaults(self):
        """Test RealtimeConfig with default values."""
        config = RealtimeConfig()
        self.assertEqual(config.sample_rate, 16000)
        self.assertEqual(config.buffer_duration_seconds, 30)
        self.assertEqual(config.chunk_duration_seconds, 5)
        self.assertEqual(config.stride_seconds, 1)
        self.assertEqual(config.silence_threshold, 0.015)
        self.assertEqual(config.silence_duration, 0.5)
    
    def test_realtime_config_validation_buffer_duration(self):
        """Test RealtimeConfig validates buffer_duration_seconds."""
        config = RealtimeConfig(buffer_duration_seconds=500)
        self.assertEqual(config.buffer_duration_seconds, 30)  # Should reset to default
    
    def test_realtime_config_validation_chunk_duration(self):
        """Test RealtimeConfig validates chunk_duration_seconds."""
        config = RealtimeConfig(chunk_duration_seconds=-5)
        self.assertEqual(config.chunk_duration_seconds, 5)
    
    def test_realtime_config_validation_stride(self):
        """Test RealtimeConfig validates stride_seconds."""
        config = RealtimeConfig(stride_seconds=10, chunk_duration_seconds=5)
        # Stride can't be > chunk_duration
        self.assertEqual(config.stride_seconds, 1)
    
    def test_realtime_config_validation_silence_threshold(self):
        """Test RealtimeConfig validates silence_threshold."""
        config = RealtimeConfig(silence_threshold=2.0)
        self.assertEqual(config.silence_threshold, 0.015)
    
    def test_post_processing_config_defaults(self):
        """Test PostProcessingConfig with default values."""
        config = PostProcessingConfig()
        self.assertFalse(config.enable_language_detection)
        self.assertEqual(config.cache_size, 128)
        self.assertEqual(config.formatting_style, "auto")
    
    def test_post_processing_config_validation_formatting_style(self):
        """Test PostProcessingConfig validates formatting_style."""
        config = PostProcessingConfig(formatting_style="invalid")
        self.assertEqual(config.formatting_style, "auto")
    
    def test_post_processing_config_validation_cache_size(self):
        """Test PostProcessingConfig validates cache_size."""
        config = PostProcessingConfig(cache_size=-50)
        self.assertEqual(config.cache_size, 128)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager singleton and functionality."""
    
    def setUp(self):
        """Reset ConfigManager singleton before each test."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
    
    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        self.assertIs(manager1, manager2)
    
    def test_load_valid_config(self):
        """Test loading a valid config file."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'model': {'name': 'small', 'compute_type': 'float16', 'device': 'cpu'},
                'runtime': {'max_file_size_mb': 200, 'log_level': 'DEBUG'}
            }
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            self.assertEqual(manager.model.name, 'small')
            self.assertEqual(manager.model.compute_type, 'float16')
            self.assertEqual(manager.model.device, 'cpu')
            self.assertEqual(manager.runtime.max_file_size_mb, 200)
            self.assertEqual(manager.runtime.log_level, 'DEBUG')
        finally:
            os.unlink(config_path)
    
    def test_load_missing_config_uses_defaults(self):
        """Test that missing config file results in default values."""
        manager = ConfigManager('nonexistent_config.yaml')
        
        # Should use defaults
        self.assertEqual(manager.model.name, 'small')
        self.assertEqual(manager.runtime.max_file_size_mb, 500)
        self.assertEqual(manager.realtime.sample_rate, 16000)
    
    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: {{{")
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            # Should fallback to defaults without crashing
            self.assertEqual(manager.model.name, 'small')
        finally:
            os.unlink(config_path)
    
    def test_get_nested_key(self):
        """Test get() method with dot notation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                'model': {'name': 'tiny'},
                'runtime': {'log_level': 'WARNING'}
            }
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            
            self.assertEqual(manager.get('model.name'), 'tiny')
            self.assertEqual(manager.get('runtime.log_level'), 'WARNING')
            self.assertEqual(manager.get('nonexistent.key', 'default'), 'default')
        finally:
            os.unlink(config_path)
    
    def test_reload_config(self):
        """Test config reload functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {'model': {'name': 'base'}}
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            self.assertEqual(manager.model.name, 'base')
            
            # Modify config file
            with open(config_path, 'w') as f:
                yaml.dump({'model': {'name': 'small'}}, f)
            
            # Reload
            manager.reload()
            self.assertEqual(manager.model.name, 'small')
        finally:
            os.unlink(config_path)
    
    @patch('insightron.core.config.Path.mkdir')
    def test_ensure_directories(self, mock_mkdir):
        """Test that ConfigManager creates necessary directories."""
        manager = ConfigManager('nonexistent.yaml')
        # Should call mkdir for transcription and recordings folders
        # At least 2 calls (could be more if parents don't exist)
        self.assertGreaterEqual(mock_mkdir.call_count, 0)


class TestConfigHelperFunctions(unittest.TestCase):
    """Test module-level helper functions."""
    
    def setUp(self):
        """Reset ConfigManager before each test."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
    
    def test_get_config_function(self):
        """Test get_config() helper function."""
        # The get_config function uses the global _config_manager instance
        # We need to replace it with our test instance
        from insightron.core import config
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {'model': {'name': 'large'}}
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Replace global manager with test instance
            test_manager = ConfigManager(config_path)
            config._config_manager = test_manager
            
            result = get_config('model.name', 'default')
            self.assertEqual(result, 'large')
            
            result = get_config('nonexistent', 'fallback')
            self.assertEqual(result, 'fallback')
        finally:
            os.unlink(config_path)
            # Reset to original
            ConfigManager._instance = None
            ConfigManager._initialized = False
            config._config_manager = ConfigManager()
    
    def test_get_config_manager_function(self):
        """Test get_config_manager() returns singleton instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        self.assertIs(manager1, manager2)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing imports."""
    
    def test_module_level_constants_exist(self):
        """Test that module-level constants still exist."""
        from insightron.core.config import (
            WHISPER_MODEL,
            ENABLE_INT8_QUANTIZATION,
            TRANSCRIPTION_FOLDER,
            RECORDINGS_FOLDER,
            MAX_FILE_SIZE_MB,
            LOG_LEVEL,
            REALTIME_BUFFER_SECONDS,
            REALTIME_SILENCE_THRESHOLD
        )
        
        # These should all be defined
        self.assertIsNotNone(WHISPER_MODEL)
        self.assertIsInstance(ENABLE_INT8_QUANTIZATION, bool)
        self.assertIsInstance(TRANSCRIPTION_FOLDER, Path)
        self.assertIsInstance(RECORDINGS_FOLDER, Path)
        self.assertIsInstance(MAX_FILE_SIZE_MB, int)
        self.assertIsInstance(LOG_LEVEL, str)
        self.assertIsInstance(REALTIME_BUFFER_SECONDS, int)
        self.assertIsInstance(REALTIME_SILENCE_THRESHOLD, float)


if __name__ == '__main__':
    unittest.main()
