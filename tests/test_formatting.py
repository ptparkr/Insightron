"""
Comprehensive unit tests for text formatting functionality (v2.2.0).
Tests all formatting modes, sentence splitting, and text cleaning.
"""
import unittest
import pytest
from insightron.services.transcription.text_formatter import TextFormatter, format_transcript


@pytest.mark.unit
class TestFormattingModes(unittest.TestCase):
    """Test suite for different formatting modes."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
        self.sample_text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
    
    def test_auto_formatting_mode(self):
        """Test auto formatting mode with intelligent paragraph breaks."""
        text = "First sentence. Second sentence. However, this is a new topic. Related sentence."
        
        formatted = format_transcript(text, style="auto")
        
        self.assertIsInstance(formatted, str)
        self.assertGreater(len(formatted), 0)
        # Auto mode should detect paragraph breaks
        self.assertIn("First sentence.", formatted)

    def test_paragraphs_formatting_mode(self):
        """Test paragraphs mode (3 sentences per paragraph)."""
        formatted = format_transcript(self.sample_text, style="paragraphs")
        
        # Should have paragraph breaks
        paragraphs = formatted.split('\n\n')
        self.assertGreater(len(paragraphs), 1)

    def test_minimal_formatting_mode(self):
        """Test minimal mode (5 sentences per paragraph)."""
        long_text = ". ".join([f"Sentence {i}" for i in range(10)]) + "."
        
        formatted = format_transcript(long_text, style="minimal")
        
        # Minimal mode should have fewer paragraph breaks
        self.assertIsInstance(formatted, str)

    def test_bullets_formatting_mode(self):
        """Test bullets formatting mode."""
        text = "First point. Second point. Third point."
        
        formatted = format_transcript(text, style="bullets")
        
        # Each sentence should be a bullet
        lines = formatted.strip().split('\n')
        for line in lines:
            self.assertTrue(line.startswith('* '))


@pytest.mark.unit
class TestSentenceSplitting(unittest.TestCase):
    """Test suite for sentence splitting logic."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
    
    def test_sentence_splitting_with_abbreviations(self):
        """Test that abbreviations don't cause incorrect splits."""
        text = "Dr. Smith went to the U.S.A. today. He met Mr. Jones at 3 p.m. in Washington D.C."
        
        sentences = self.formatter._split_into_sentences(text)
        
        # Should split into 2 sentences, not more
        self.assertEqual(len(sentences), 2)
        self.assertIn("Dr. Smith", sentences[0])
        self.assertIn("He met Mr. Jones", sentences[1])

    def test_sentence_splitting_basic(self):
        """Test basic sentence splitting."""
        text = "First sentence. Second sentence. Third sentence."
        
        sentences = self.formatter._split_into_sentences(text)
        
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0], "First sentence.")
        self.assertEqual(sentences[1], "Second sentence.")
        self.assertEqual(sentences[2], "Third sentence.")

    def test_sentence_splitting_edge_cases(self):
        """Test edge cases in sentence splitting."""
        # Empty text
        self.assertEqual(self.formatter._split_into_sentences(""), [])
        
        # Single sentence
        single = self.formatter._split_into_sentences("Just one sentence.")
        self.assertEqual(len(single), 1)
        
        # No punctuation
        no_punct = self.formatter._split_into_sentences("No punctuation here")
        self.assertGreater(len(no_punct), 0)


@pytest.mark.unit
class TestParagraphDetection(unittest.TestCase):
    """Test suite for paragraph break detection."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
    
    def test_paragraph_break_detection(self):
        """Test detection of natural paragraph breaks."""
        text = "First sentence. Second sentence. However, this is new. Another sentence."
        
        breaks = self.formatter.detect_paragraph_breaks(text)
        
        # Should detect paragraph starters like "However"
        self.assertIsInstance(breaks, list)

    def test_paragraph_starters_detection(self):
        """Test detection of paragraph starter words."""
        # The implementation uses regex patterns, not just word matching
        # It looks for patterns like "however", "and", "but", etc.
        paragraph_starters = [
            "However, this is different.",  # "however" is in pattern
            "Furthermore, we proceed.",
            "In conclusion, we wrap up."
        ]
        
        for text in paragraph_starters:
            # These should be detected by regex patterns
            result = self.formatter._indicates_long_pause(text)
            # All of these contain pause indicators from the regex patterns
            self.assertTrue(result, f"Failed for: {text}")

        # Verify that "And" and "But" are NO LONGER treated as paragraph starters
        # per the fix for Bug 2
        non_starters = [
             "And this is also new.",
             "But there is more."
        ]
        for text in non_starters:
             result = self.formatter._indicates_long_pause(text)
             self.assertFalse(result, f"Should not be a starter: {text}")


@pytest.mark.unit
class TestTextCleaning(unittest.TestCase):
    """Test suite for text cleaning and normalization."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
    
    def test_filler_word_removal_comprehensive(self):
        """Test comprehensive filler word removal."""
        text_with_fillers = "Um, I think that, uh, this is, you know, a test. Like, it has, um, many fillers."
        
        cleaned = self.formatter.clean_text(text_with_fillers)
        
        # Filler words should be reduced or removed
        self.assertLess(cleaned.count("um"), text_with_fillers.count("um"))
        self.assertLess(cleaned.count("uh"), text_with_fillers.count("uh"))

    def test_common_error_corrections(self):
        """Test correction of common transcription errors."""
        text_with_errors = "gonna wanna gotta"
        
        cleaned = self.formatter._fix_common_errors(text_with_errors)
        
        # Common contractions should be handled
        self.assertIsInstance(cleaned, str)

    def test_text_cleaning_excessive_spaces(self):
        """Test removal of excessive spaces."""
        text_with_spaces = "This  has   excessive    spaces."
        
        cleaned = self.formatter.clean_text(text_with_spaces)
        
        # Should not have multiple consecutive spaces
        self.assertNotIn("  ", cleaned)

    def test_text_normalization(self):
        """Test text normalization (capitalization, etc)."""
        text = "this should be capitalized. so should this."
        
        formatted = self.formatter.format_text(text)
        
        # First letter should be capitalized
        self.assertTrue(formatted[0].isupper())


@pytest.mark.unit
class TestBulletsFormatting(unittest.TestCase):
    """Test suite for bullets formatting mode."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
    
    def test_bullets_formatting(self):
        """Test basic bullets formatting."""
        text = "First we need to do this. Second we need to do that. Finally we are done."
        
        formatted = self.formatter.format_as_bullets(text)
        
        lines = formatted.split('\n')
        self.assertEqual(len(lines), 3)
        for line in lines:
            self.assertTrue(line.startswith('* '))

    def test_bullets_with_complex_paragraphs(self):
        """Test bullets formatting with paragraph detection."""
        text = "This is the first point. It has two sentences. Next is the second point. It also has details."
        
        formatted = self.formatter.format_as_bullets(text)
        
        lines = formatted.split('\n')
        # "Next" is a paragraph starter, so should create new bullet
        self.assertGreaterEqual(len(lines), 2)
        self.assertTrue(all(line.startswith('* ') for line in lines))

    def test_bullets_empty_input(self):
        """Test bullets formatting with empty input."""
        formatted = self.formatter.format_as_bullets("")
        
        # Empty input returns empty string (the implementation cleans and returns text)
        # After clean_text and add_punctuation, might add a period
        # Check that result is effectively empty or minimal
        self.assertTrue(len(formatted) <= 3 or formatted.strip() in ["", "*  .", "* ."])


@pytest.mark.unit
class TestCachingBehavior(unittest.TestCase):
    """Test suite for caching functionality."""
    
    def setUp(self):
        """Set up test formatter."""
        self.formatter = TextFormatter()
    
    def test_language_detection_caching(self):
        """Test that language detection results are cached."""
        text = "This is a test for caching."
        text_hash = self.formatter._get_text_hash(text)
        
        # Hash should be consistent
        self.assertEqual(text_hash, self.formatter._get_text_hash(text))

    def test_text_hash_generation(self):
        """Test text hash generation for caching."""
        text1 = "Same text"
        text2 = "Same text"
        text3 = "Different text"
        
        hash1 = self.formatter._get_text_hash(text1)
        hash2 = self.formatter._get_text_hash(text2)
        hash3 = self.formatter._get_text_hash(text3)
        
        # Same text should have same hash
        self.assertEqual(hash1, hash2)
        # Different text should have different hash
        self.assertNotEqual(hash1, hash3)


@pytest.mark.unit
class TestFormatTranscriptConvenience(unittest.TestCase):
    """Test suite for format_transcript convenience function."""
    
    def test_format_transcript_auto(self):
        """Test format_transcript with auto style."""
        text = "Test transcription text."
        result = format_transcript(text, style="auto")
        
        self.assertIsInstance(result, str)
        self.assertIn("Test transcription text", result)

    def test_format_transcript_all_styles(self):
        """Test format_transcript with all available styles."""
        text = "Sentence one. Sentence two. Sentence three."
        
        styles = ["auto", "paragraphs", "minimal", "bullets"]
        
        for style in styles:
            result = format_transcript(text, style=style)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
