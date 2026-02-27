"""
Pytest configuration and shared fixtures for Insightron test suite.
Provides common test utilities, mock objects, and sample data.
"""
import pytest
import tempfile
import shutil
import os
import numpy as np
import soundfile as sf
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict, List, Any


# ============================================================================
# Audio File Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_file(tmp_path):
    """
    Create a temporary audio file for testing.
    Returns path to a 1-second WAV file with silence.
    """
    audio_path = tmp_path / "test_audio.wav"
    sample_rate = 16000
    duration = 1  # seconds
    
    # Generate silence
    audio_data = np.zeros(sample_rate * duration, dtype=np.float32)
    
    # Write to file
    sf.write(str(audio_path), audio_data, sample_rate)
    
    yield str(audio_path)
    
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def sample_audio_file_long(tmp_path):
    """
    Create a longer audio file (10 seconds) for stress testing.
    """
    audio_path = tmp_path / "test_audio_long.wav"
    sample_rate = 16000
    duration = 10  # seconds
    
    # Generate sine wave for more realistic audio
    t = np.linspace(0, duration, sample_rate * duration)
    audio_data = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.1
    
    sf.write(str(audio_path), audio_data, sample_rate)
    
    yield str(audio_path)


@pytest.fixture
def multiple_audio_files(tmp_path):
    """
    Create multiple audio files for batch testing.
    Returns list of 3 audio file paths.
    """
    files = []
    sample_rate = 16000
    
    for i in range(3):
        audio_path = tmp_path / f"test_audio_{i}.wav"
        audio_data = np.zeros(sample_rate, dtype=np.float32)
        sf.write(str(audio_path), audio_data, sample_rate)
        files.append(str(audio_path))
    
    yield files


# ============================================================================
# Model and Segment Fixtures
# ============================================================================

@pytest.fixture
def mock_whisper_model():
    """
    Create a mock WhisperModel for testing without actual model loading.
    """
    mock_model = MagicMock()
    
    # Mock transcribe method to return segments and info
    mock_segment = MagicMock()
    mock_segment.text = "This is a test transcription."
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    mock_segment.id = 0
    mock_segment.avg_logprob = -0.3
    mock_segment.no_speech_prob = 0.1
    
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.95
    mock_info.duration = 10.0
    
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    
    return mock_model


@pytest.fixture
def sample_segments():
    """
    Create sample segment data for testing.
    """
    segments = [
        {
            'id': 0,
            'start': 0.0,
            'end': 2.5,
            'text': 'This is the first segment.',
            'confidence': -0.2
        },
        {
            'id': 1,
            'start': 2.5,
            'end': 5.0,
            'text': 'This is the second segment.',
            'confidence': -0.3
        },
        {
            'id': 2,
            'start': 5.0,
            'end': 7.5,
            'text': 'This is the third segment.',
            'confidence': -0.4
        }
    ]
    return segments


@pytest.fixture
def sample_segments_with_gaps():
    """
    Create sample segments with gaps for testing merging logic.
    """
    segments = [
        {
            'id': 0,
            'start': 0.0,
            'end': 2.0,
            'text': 'First segment.',
            'confidence': -0.2
        },
        {
            'id': 1,
            'start': 2.1,  # Small gap
            'end': 4.0,
            'text': 'Second segment.',
            'confidence': -0.25
        },
        {
            'id': 2,
            'start': 5.0,  # Larger gap
            'end': 7.0,
            'text': 'Third segment.',
            'confidence': -0.3
        }
    ]
    return segments


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config(tmp_path):
    """
    Create a mock configuration for testing.
    """
    config = {
        'model': {
            'name': 'tiny',
            'compute_type': 'int8',
            'device': 'cpu',
            'quality_mode': 'high',
            'enable_vad': True,
            'vad_threshold': 0.5,
            'enable_retry': True,
            'max_retries': 2
        },
        'runtime': {
            'transcription_folder': str(tmp_path / 'transcriptions'),
            'recordings_folder': str(tmp_path / 'recordings'),
            'max_file_size_mb': 500,
            'log_level': 'INFO'
        },
        'realtime': {
            'sample_rate': 16000,
            'buffer_duration_seconds': 30,
            'chunk_duration_seconds': 5,
            'stride_seconds': 1,
            'silence_threshold': 0.015
        },
        'post_processing': {
            'formatting_style': 'auto',
            'cache_size': 128
        },
        'transcription': {
            'segment_merge_threshold': -0.5,
            'min_segment_duration': 0.1,
            'progress_update_frequency': 5,
            'enable_segment_filtering': True
        }
    }
    return config


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Create a temporary output directory for testing.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    
    yield output_dir
    
    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)


@pytest.fixture
def temp_recordings_dir(tmp_path):
    """
    Create a temporary recordings directory for testing.
    """
    recordings_dir = tmp_path / "recordings"
    recordings_dir.mkdir(exist_ok=True)
    
    yield recordings_dir


# ============================================================================
# Text and Formatting Fixtures
# ============================================================================

@pytest.fixture
def sample_transcript_text():
    """
    Sample transcript text for formatting tests.
    """
    return """
    one thing that I have recognized is that see I am the molar type face of clearing 
    and I am purifying my earth element and also my cellular intelligence is getting 
    sharper and also all the cells are being out chose to divine frequencies and also 
    this is the last step of completing the 3D Transcendence and being liberated while living
    """


@pytest.fixture
def sample_text_with_fillers():
    """
    Sample text with filler words for cleaning tests.
    """
    return "Um, I think that, uh, this is, you know, a test. Like, it has, um, many fillers."


@pytest.fixture
def sample_text_with_abbreviations():
    """
    Sample text with abbreviations for sentence splitting tests.
    """
    return "Dr. Smith went to the U.S.A. today. He met Mr. Jones at 3 p.m. in Washington D.C."


# ============================================================================
# Mock Callback Fixtures
# ============================================================================

@pytest.fixture
def mock_progress_callback():
    """
    Create a mock progress callback function.
    """
    callback = MagicMock()
    return callback


@pytest.fixture
def mock_audio_level_callback():
    """
    Create a mock audio level callback for realtime tests.
    """
    callback = MagicMock()
    return callback


# ============================================================================
# Cleanup Utilities
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances before each test to ensure test isolation.
    """
    # Import here to avoid circular imports
    try:
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
    except ImportError:
        pass


# ============================================================================
# Test gating (LLM/GPU/network/model downloads)
# ============================================================================

def _env_truthy(name: str) -> bool:
    val = (os.getenv(name) or "").strip().lower()
    return val in {"1", "true", "yes", "y", "on"}


def _torch_cuda_available() -> bool:
    try:
        import torch  # type: ignore
    except Exception:
        return False
    try:
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-llm",
        action="store_true",
        default=False,
        help="Run tests marked 'llm' (may be slow / require extra deps).",
    )
    parser.addoption(
        "--run-model-download",
        action="store_true",
        default=False,
        help="Run tests marked 'model_download' (may download models).",
    )
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="Run tests marked 'network' (requires external connectivity).",
    )
    parser.addoption(
        "--run-gpu",
        action="store_true",
        default=False,
        help="Run tests marked 'gpu' (requires CUDA GPU).",
    )
    parser.addoption(
        "--allow-cpu-llm",
        action="store_true",
        default=False,
        help="Allow 'llm' tests to run without CUDA (can be extremely slow).",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    run_llm = bool(config.getoption("--run-llm")) or _env_truthy("INSIGHTRON_RUN_LLM_TESTS")
    run_model_download = bool(config.getoption("--run-model-download")) or _env_truthy(
        "INSIGHTRON_RUN_MODEL_DOWNLOAD_TESTS"
    )
    run_network = bool(config.getoption("--run-network")) or _env_truthy("INSIGHTRON_RUN_NETWORK_TESTS")
    run_gpu = bool(config.getoption("--run-gpu")) or _env_truthy("INSIGHTRON_RUN_GPU_TESTS")
    allow_cpu_llm = bool(config.getoption("--allow-cpu-llm")) or _env_truthy("INSIGHTRON_ALLOW_CPU_LLM")

    has_cuda = _torch_cuda_available()

    skip_llm = pytest.mark.skip(
        reason="LLM tests are opt-in. Use --run-llm or set INSIGHTRON_RUN_LLM_TESTS=1."
    )
    skip_model_download = pytest.mark.skip(
        reason="Model download tests are opt-in. Use --run-model-download or set INSIGHTRON_RUN_MODEL_DOWNLOAD_TESTS=1."
    )
    skip_network = pytest.mark.skip(
        reason="Network tests are opt-in. Use --run-network or set INSIGHTRON_RUN_NETWORK_TESTS=1."
    )
    skip_gpu = pytest.mark.skip(
        reason="GPU tests require CUDA. Use --run-gpu / INSIGHTRON_RUN_GPU_TESTS=1 on a CUDA machine."
    )
    skip_llm_no_cuda = pytest.mark.skip(
        reason="LLM test requires CUDA GPU by default (this machine appears CPU-only). "
        "Set INSIGHTRON_ALLOW_CPU_LLM=1 or pass --allow-cpu-llm to override."
    )

    for item in items:
        if item.get_closest_marker("model_download") and not run_model_download:
            item.add_marker(skip_model_download)
        if item.get_closest_marker("network") and not run_network:
            item.add_marker(skip_network)
        if item.get_closest_marker("gpu"):
            if not run_gpu:
                item.add_marker(skip_gpu)
            elif not has_cuda:
                item.add_marker(skip_gpu)
        if item.get_closest_marker("llm"):
            if not run_llm:
                item.add_marker(skip_llm)
            elif not has_cuda and not allow_cpu_llm:
                item.add_marker(skip_llm_no_cuda)
    
    try:
        from insightron.core.config import ConfigManager
        ConfigManager._instance = None
    except ImportError:
        pass
    
    yield
    
    # Cleanup after test
    try:
        from insightron.core.model_manager import ModelManager
        ModelManager._instance = None
        ModelManager._model = None
    except ImportError:
        pass
