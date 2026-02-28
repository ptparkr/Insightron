"""
Test helper utilities for Insightron test suite.
Provides common functions for test setup, data generation, and assertions.
"""
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import MagicMock


# ============================================================================
# Audio File Generators
# ============================================================================

def generate_audio_file(filepath: str, duration: float = 1.0, 
                       sample_rate: int = 16000, 
                       frequency: float = 440.0) -> str:
    """
    Generate a test audio file with a sine wave.
    
    Args:
        filepath: Path where to save the audio file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        frequency: Frequency of the sine wave in Hz
        
    Returns:
        Path to the generated audio file
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32) * 0.3
    
    sf.write(filepath, audio_data, sample_rate)
    return filepath


def generate_silence_file(filepath: str, duration: float = 1.0,
                         sample_rate: int = 16000) -> str:
    """
    Generate a silent audio file for testing.
    
    Args:
        filepath: Path where to save the audio file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Path to the generated audio file
    """
    audio_data = np.zeros(int(sample_rate * duration), dtype=np.float32)
    sf.write(filepath, audio_data, sample_rate)
    return filepath


def generate_noise_file(filepath: str, duration: float = 1.0,
                       sample_rate: int = 16000,
                       amplitude: float = 0.1) -> str:
    """
    Generate an audio file with white noise.
    
    Args:
        filepath: Path where to save the audio file
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        amplitude: Amplitude of the noise
        
    Returns:
        Path to the generated audio file
    """
    audio_data = np.random.randn(int(sample_rate * duration)).astype(np.float32) * amplitude
    sf.write(filepath, audio_data, sample_rate)
    return filepath


# ============================================================================
# Mock Segment Creators
# ============================================================================

def create_mock_segment(text: str, start: float, end: float,
                       avg_logprob: float = -0.3,
                       no_speech_prob: float = 0.1) -> MagicMock:
    """
    Create a mock Whisper segment.
    
    Args:
        text: Segment text
        start: Start time in seconds
        end: End time in seconds
        avg_logprob: Average log probability (confidence)
        no_speech_prob: No speech probability
        
    Returns:
        Mock segment object
    """
    segment = MagicMock()
    segment.text = text
    segment.start = start
    segment.end = end
    segment.avg_logprob = avg_logprob
    segment.no_speech_prob = no_speech_prob
    segment.id = 0
    return segment


def create_mock_segments(count: int = 3,
                        duration_per_segment: float = 2.5) -> List[MagicMock]:
    """
    Create multiple mock segments.
    
    Args:
        count: Number of segments to create
        duration_per_segment: Duration of each segment in seconds
        
    Returns:
        List of mock segment objects
    """
    segments = []
    for i in range(count):
        start = i * duration_per_segment
        end = (i + 1) * duration_per_segment
        text = f"This is segment {i + 1}."
        avg_logprob = -0.3 - (i * 0.05)  # Decreasing confidence
        
        segment = create_mock_segment(text, start, end, avg_logprob)
        segment.id = i
        segments.append(segment)
    
    return segments


def create_mock_transcription_info(language: str = "en",
                                   language_probability: float = 0.95,
                                   duration: float = 10.0) -> MagicMock:
    """
    Create mock transcription info object.
    
    Args:
        language: Detected language code
        language_probability: Confidence of language detection
        duration: Audio duration in seconds
        
    Returns:
        Mock TranscriptionInfo object
    """
    info = MagicMock()
    info.language = language
    info.language_probability = language_probability
    info.duration = duration
    return info


# ============================================================================
# Assertion Helpers
# ============================================================================

def assert_segment_structure(segment: Dict[str, Any]) -> None:
    """
    Assert that a segment dictionary has the required structure.
    
    Args:
        segment: Segment dictionary to validate
        
    Raises:
        AssertionError: If segment structure is invalid
    """
    required_keys = ['id', 'start', 'end', 'text']
    for key in required_keys:
        assert key in segment, f"Segment missing required key: {key}"
    
    assert isinstance(segment['id'], int), "Segment ID must be an integer"
    assert isinstance(segment['start'], (int, float)), "Start time must be numeric"
    assert isinstance(segment['end'], (int, float)), "End time must be numeric"
    assert isinstance(segment['text'], str), "Text must be a string"
    assert segment['start'] >= 0, "Start time must be non-negative"
    assert segment['end'] > segment['start'], "End time must be greater than start time"


def assert_audio_file_valid(filepath: str) -> None:
    """
    Assert that an audio file exists and is valid.
    
    Args:
        filepath: Path to audio file
        
    Raises:
        AssertionError: If audio file is invalid
    """
    path = Path(filepath)
    assert path.exists(), f"Audio file does not exist: {filepath}"
    assert path.is_file(), f"Path is not a file: {filepath}"
    assert path.suffix.lower() in ['.wav', '.mp3', '.m4a', '.flac'], \
        f"Unsupported audio format: {path.suffix}"
    
    # Try to read file
    try:
        data, sr = sf.read(filepath)
        assert len(data) > 0, "Audio file is empty"
        assert sr > 0, "Invalid sample rate"
    except Exception as e:
        raise AssertionError(f"Failed to read audio file: {e}")


def assert_markdown_file_valid(filepath: str) -> None:
    """
    Assert that a markdown file exists and has valid content.
    
    Args:
        filepath: Path to markdown file
        
    Raises:
        AssertionError: If markdown file is invalid
    """
    path = Path(filepath)
    assert path.exists(), f"Markdown file does not exist: {filepath}"
    assert path.is_file(), f"Path is not a file: {filepath}"
    assert path.suffix == '.md', f"Not a markdown file: {filepath}"
    
    # Read and validate content
    content = path.read_text(encoding='utf-8')
    assert len(content) > 0, "Markdown file is empty"
    assert '# 🎤 Transcription:' in content or '## Transcript' in content, \
        "Markdown file missing expected headers"


# ============================================================================
# Test Data Constants
# ============================================================================

SAMPLE_TRANSCRIPT_SHORT = "This is a short test transcript."

SAMPLE_TRANSCRIPT_MEDIUM = """
This is a medium length test transcript. It contains multiple sentences.
The sentences should be properly formatted with punctuation and capitalization.
This allows us to test paragraph breaks and text formatting.
"""

SAMPLE_TRANSCRIPT_LONG = """
This is a longer test transcript that spans multiple paragraphs.
It's designed to test more complex formatting scenarios.

The transcript includes various elements like paragraph breaks.
It also tests how the formatter handles different types of content.
We want to ensure that the formatting is consistent and accurate.

Finally, this last paragraph tests the handling of multiple sections.
The formatter should properly detect paragraph boundaries.
And it should maintain proper spacing and structure throughout.
"""

SAMPLE_TEXT_WITH_ERRORS = """
um I think that uh this is you know a test
it has like many errors and uh needs cleaning
"""

SAMPLE_TEXT_WITH_ABBREVIATIONS = """
Dr. Smith met Mr. Jones at the U.S.A. embassy.
They discussed the C.I.A. report at 3 p.m. yesterday.
The meeting in Washington D.C. was very productive.
"""

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']

# Test model sizes
TEST_MODEL_SIZES = ['tiny', 'base', 'small']

# Test languages
TEST_LANGUAGES = ['en', 'es', 'fr', 'de', 'zh', 'ja']

# Test formatting styles
TEST_FORMATTING_STYLES = ['auto', 'paragraphs', 'minimal', 'bullets']
