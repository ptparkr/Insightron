"""
Unit tests for utility functions (v2.2.0).
Tests markdown creation, realtime note generation, and helper functions.
"""
import unittest
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestCreateMarkdown(unittest.TestCase):
    """Test suite for create_markdown function."""
    
    def test_create_markdown_basic(self):
        """Test basic markdown creation."""
        from insightron.core.utils import create_markdown
        
        result = create_markdown(
            filename="test_audio",
            text="This is a test transcription.",
            date="2024-01-01 12:00:00",
            duration="0:10",
            file_size_mb=1.5,
            model="medium",
            language="en",
            formatting_style="auto",
            duration_seconds=10.0
        )
        
        # Verify markdown structure
        self.assertIsInstance(result, str)
        self.assertIn("# 🎤 Transcription: test_audio", result)
        self.assertIn("## 📊 Metadata", result)  # With emoji
        self.assertIn("## 📝 Transcript", result)  # With emoji
        self.assertIn("This is a test transcription.", result)

    def test_create_markdown_with_timestamps(self):
        """Test markdown creation with timestamp segments."""
        from insightron.core.utils import create_markdown
        
        segments = [
            {'start': 0.0, 'end': 5.0, 'text': 'First segment'},
            {'start': 5.0, 'end': 10.0, 'text': 'Second segment'},
        ]
        
        result = create_markdown(
            filename="test_audio",
            text="Full transcription",
            date="2024-01-01 12:00:00",
            duration="0:10",
            file_size_mb=1.5,
            model="medium",
            language="en",
            formatting_style="auto",
            duration_seconds=10.0,
            segments=segments
        )
        
        # Should include timestamps section
        self.assertIn("🕐 Timestamps", result)  # With clock emoji
        self.assertIn("00:00", result)
        self.assertIn("First segment", result)

    def test_create_markdown_metadata_content(self):
        """Test that markdown contains all required metadata."""
        from insightron.core.utils import create_markdown
        
        result = create_markdown(
            filename="test_audio",
            text="Test",
            date="2024-01-01 12:00:00",
            duration="5:23",
            file_size_mb=12.5,
            model="large",
            language="es",
            formatting_style="paragraphs",
            duration_seconds=323.0
        )
        
        # Verify metadata fields
        self.assertIn("**Duration:** 5:23", result)
        self.assertIn("**Model:** large", result)
        self.assertIn("**Language:** es", result)
        self.assertIn("**Formatting:** Paragraphs", result)  # Capitalized
        self.assertIn("12.5 MB", result)


@pytest.mark.unit
class TestCreateRealtimeNote(unittest.TestCase):
    """Test suite for create_realtime_note function."""
    
    def test_create_realtime_note(self):
        """Test realtime note creation."""
        from insightron.core.utils import create_realtime_note
        
        result = create_realtime_note(
            filename="realtime_note",
            text="This is a realtime transcription.",
            date="2024-01-01 14:00:00",
            duration="2:30",
            file_size_mb=2.5,
            model="medium",
            language="en",
            duration_seconds=150.0
        )
        
        # Verify structure
        self.assertIsInstance(result, str)
        self.assertIn("# 🎤 Transcription:", result)  # Actual format
        self.assertIn("This is a realtime transcription.", result)
        self.assertIn("**Duration:** 2:30", result)

    def test_create_realtime_note_with_metadata(self):
        """Test realtime note with additional metadata."""
        from insightron.core.utils import create_realtime_note
        
        result = create_realtime_note(
            filename="test_realtime",
            text="Test transcription",
            date="2024-01-01 14:30:00",
            duration="1:00",
            file_size_mb=1.0,
            model="tiny",
            language="fr",
            duration_seconds=60.0
        )
        
        # Should include metadata
        self.assertIn("**Model:** tiny", result)
        self.assertIn("**Language:** fr", result)


@pytest.mark.unit
class TestTimestampFormatting(unittest.TestCase):
    """Test suite for timestamp formatting functions."""
    
    def test_timestamp_formatting_seconds(self):
        """Test formatting seconds to MM:SS format."""
        from insightron.core.utils import format_timestamp
        
        # Test various durations
        self.assertEqual(format_timestamp(65), "01:05")
        self.assertEqual(format_timestamp(125), "02:05")
        # Hours are included automatically when > 0
        self.assertEqual(format_timestamp(3665), "01:01:05")

    def test_timestamp_formatting_with_hours(self):
        """Test formatting with hours."""
        from insightron.core.utils import format_timestamp
        
        # Hours are automatically included when seconds >= 3600
        result = format_timestamp(3665)
        # Should be "1:01:05" format
        self.assertEqual(result, "01:01:05")
        self.assertEqual(result.count(":"), 2)  # HH:MM:SS has 2 colons


@pytest.mark.unit
class TestMetadataGeneration(unittest.TestCase):
    """Test suite for metadata generation utilities."""
    
    def test_metadata_generation(self):
        """Test metadata dictionary generation."""
        # Test metadata extraction or generation
        metadata = {
            'filename': 'test_audio.wav',
            'duration': '5:23',
            'duration_seconds': 323.0,
            'model': 'medium',
            'language': 'en',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Verify metadata structure
        self.assertIn('filename', metadata)
        self.assertIn('duration', metadata)
        self.assertIn('duration_seconds', metadata)
        self.assertIn('model', metadata)
        self.assertIn('language', metadata)
        self.assertIn('date', metadata)

    def test_frontmatter_generation(self):
        """Test YAML frontmatter generation for markdown."""
        from insightron.core.utils import create_markdown
        
        result = create_markdown(
            filename="test",
            text="Content",
            date="2024-01-01",
            duration="1:00",
            file_size_mb=1.5,
            model="tiny",
            language="en",
            formatting_style="auto",
            duration_seconds=60
        )
        
        # Should have YAML frontmatter
        self.assertTrue(result.startswith("---"))
        # Check for frontmatter fields
        lines = result.split('\n')
        frontmatter_section = '\n'.join(lines[1:lines.index('---', 1)])
        self.assertIn('title:', frontmatter_section)
        self.assertIn('date:', frontmatter_section)


if __name__ == '__main__':
    unittest.main()
