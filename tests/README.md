# Insightron Test Suite Documentation

## Overview

This directory contains the comprehensive test suite for Insightron v3.1.0. The tests cover all major components including core modules, efficiency layer, transcription functionality, realtime processing, batch operations, and text formatting.

## Test Organization

### Test Files

#### Core Module Tests
- **`test_config.py`** - Configuration system tests (existing, comprehensive)
- **`test_model_manager.py`** - Model manager tests with v2.2.0 enhancements
  - Quality mode configurations (high/balanced/fast)
  - VAD parameters and adaptive VAD
  - Retry mechanism with fallback strategies
  - Quality metrics calculation
  - Distil-Whisper model support
- **`test_efficiency_layer.py`** - Performance and resource management tests (v3.0.0)
  - Energy-based VAD logic
  - Sliding window buffer pruning
  - Dynamic file size limits
- **`test_resource_manager.py`** - Static and dynamic resource constraint tests
- **`test_vad.py`** - Dedicated VAD logic verification

#### Transcription Tests (Modular v3.1.0)
- **`test_audio_loader.py`** - Audio loading and preprocessing tests
- **`test_transcription_engine.py`** - Inference engine orchestration tests
- **`test_result_handler.py`** - Output generation and formatting tests
- **`test_transcribe.py`** - Legacy wrapper integration tests
- **`test_batch_processor_v2.py`** - Enhanced batch processing tests
  - ProcessPoolExecutor and ThreadPoolExecutor
  - Worker configuration
  - Progress callbacks
  - Error handling
- **`test_realtime_transcriber.py`** - Realtime transcription tests
  - Ring buffer operations
  - Producer-consumer threading
  - Audio processing
  - Microphone enumeration

#### Text Processing Tests
- **`test_formatting.py`** - Text formatting functionality
  - All formatting modes (auto, paragraphs, minimal, bullets)
  - Sentence splitting with abbreviations
  - Paragraph detection
  - Text cleaning and normalization
- **`test_text_formatter_v2.py`** - Additional formatter tests
- **`test_text_formatter_performance.py`** - Performance benchmarks

#### Integration and CLI Tests
- **`test_integration_suite.py`** - End-to-end integration tests
- **`test_cli.py`** - Command-line interface tests
- **`test_utils.py`** - Utility function tests

#### Test Infrastructure
- **`conftest.py`** - Pytest fixtures and common setup
- **`test_helpers.py`** - Helper utilities and test data
- **`pytest.ini`** - Pytest configuration

## Running Tests

### Run All Tests
```bash
# Run entire test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Run Specific Test Modules
```bash
# Run model manager tests
pytest tests/test_model_manager.py -v

# Run realtime tests
pytest tests/test_realtime_transcriber.py -v

# Run batch processing tests
pytest tests/test_batch_processor_v2.py -v

# Run integration tests
pytest tests/test_integration_suite.py -v
```

### Run Tests by Marker
```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run only batch tests
pytest tests/ -m batch

# Run only realtime tests
pytest tests/ -m realtime

# Skip slow tests
pytest tests/ -m "not slow"
```

### Run with Coverage
```bash
# Generate coverage report
pytest tests/ --cov=core --cov=transcription --cov=realtime --cov=gui --cov-report=html

# View HTML coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

## Test Markers

Tests are organized with the following markers:

- **`@pytest.mark.unit`** - Unit tests for individual components
- **`@pytest.mark.integration`** - Integration tests for multiple components
- **`@pytest.mark.performance`** - Performance and benchmark tests
- **`@pytest.mark.slow`** - Slow running tests requiring actual model download
- **`@pytest.mark.realtime`** - Tests for realtime transcription
- **`@pytest.mark.batch`** - Tests for batch processing

## Test Fixtures

### Available Fixtures (from `conftest.py`)

#### Audio Fixtures
- `sample_audio_file` - 1-second silence WAV file
- `sample_audio_file_long` - 10-second audio file
- `multiple_audio_files` - List of 3 audio files

#### Model and Segment Fixtures
- `mock_whisper_model` - Mocked Whisper model
- `sample_segments` - Sample segment data
- `sample_segments_with_gaps` - Segments with timing gaps

#### Configuration Fixtures
- `mock_config` - Mocked configuration
- `temp_output_dir` - Temporary output directory
- `temp_recordings_dir` - Temporary recordings directory

#### Text Fixtures
- `sample_transcript_text` - Sample transcript for formatting
- `sample_text_with_fillers` - Text with filler words
- `sample_text_with_abbreviations` - Text for sentence splitting tests

#### Callback Fixtures
- `mock_progress_callback` - Mocked progress callback
- `mock_audio_level_callback` - Mocked audio level callback

## Writing New Tests

### Basic Test Structure

```python
import unittest
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
class TestMyFeature(unittest.TestCase):
    """Test suite for my feature."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize test data
        pass
    
    def tearDown(self):
        """Clean up after tests."""
        # Cleanup code
        pass
    
    def test_my_feature_works(self):
        """Test that my feature works correctly."""
        # Arrange
        # Act
        # Assert
        self.assertTrue(True)
```

### Using Fixtures

```python
def test_with_audio_file(sample_audio_file):
    """Test using audio file fixture."""
    # sample_audio_file is automatically provided
    assert os.path.exists(sample_audio_file)
```

### Mocking External Dependencies

```python
@patch('module.ExternalDependency')
def test_with_mock(self, mock_dependency):
    """Test with mocked dependency."""
    mock_dependency.return_value = MagicMock()
    # Test code
```

## Coverage Requirements

### Target Coverage
- **Core modules**: 90%+ coverage
- **Transcription modules**: 85%+ coverage
- **Realtime modules**: 80%+ coverage
- **GUI modules**: 70%+ coverage
- **Overall**: 85%+ coverage

### Checking Coverage

```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=term-missing

# Show uncovered lines
pytest tests/ --cov=core --cov=transcription --cov-report=term-missing
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest tests/
```

#### Singleton Issues
```bash
# Solution: Singletons are automatically reset by conftest.py
# If issues persist, manually reset in setUp():
from core.model_manager import ModelManager
ModelManager._instance = None
```

#### Fixture Not Found
```bash
# Solution: Ensure pytest discovers conftest.py
# conftest.py must be in tests/ directory
ls tests/conftest.py
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Use Fixtures**: Leverage pytest fixtures for common setup
3. **Mock External Calls**: Mock file I/O, network calls, model loading
4. **Descriptive Names**: Use clear, descriptive test names
5. **AAA Pattern**: Arrange, Act, Assert structure
6. **Test Edge Cases**: Include edge cases and error conditions
7. **Skip Slow Tests**: Mark slow tests appropriately
8. **Document Tests**: Add docstrings to test classes and methods

## Contributing

When adding new features to Insightron:

1. **Write tests first** (TDD approach recommended)
2. **Ensure coverage** meets requirements (85%+)
3. **Add appropriate markers** (@pytest.mark.unit, etc.)
4. **Update this README** if adding new test categories
5. **Run full test suite** before submitting PR

## Support

For questions about the test suite:
- Check existing tests for examples
- Review pytest documentation: https://docs.pytest.org/
- See test helpers in `test_helpers.py`
- Review fixtures in `conftest.py`

---

**Test Suite Version**: 3.1.0  
**Last Updated**: 2026-01-27  
**Maintained by**: Insightron Development Team
