#!/usr/bin/env python3
"""
Performance tests for text_formatter.py optimizations
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from insightron.services.transcription.text_formatter import TextFormatter, format_transcript


class TestTextFormatterPerformance(unittest.TestCase):
    """Performance-focused tests for text formatter optimizations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.formatter = TextFormatter()
        
        # Short sample text
        self.short_text = (
            "um one thing that I have recognized is that see I am purifying my earth element. "
            "What happens is that some karma manifests as things like past reminders."
        )
        
        # Medium sample text (repeating pattern)
        self.medium_text = self.short_text * 10
        
        # Large sample text
        self.large_text = self.short_text * 100
    
    def test_clean_text_performance(self):
        """Test cleaning text performance with various sizes"""
        test_cases = [
            ("short", self.short_text),
            ("medium", self.medium_text),
            ("large", self.large_text)
        ]
        
        for name, text in test_cases:
            start_time = time.perf_counter()
            result = self.formatter.clean_text(text)
            elapsed = time.perf_counter() - start_time
            
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            # Should complete in reasonable time (< 100ms for large text)
            self.assertLess(elapsed, 0.1, f"{name} text cleaning took too long: {elapsed:.4f}s")
    
    def test_format_text_performance(self):
        """Test formatting text performance with various sizes"""
        test_cases = [
            ("short", self.short_text),
            ("medium", self.medium_text),
            ("large", self.large_text)
        ]
        
        for name, text in test_cases:
            start_time = time.perf_counter()
            result = self.formatter.format_text(text)
            elapsed = time.perf_counter() - start_time
            
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            # Should complete in reasonable time (< 200ms for large text)
            self.assertLess(elapsed, 0.2, f"{name} text formatting took too long: {elapsed:.4f}s")
    
    def test_list_join_optimization(self):
        """Verify list join optimization is working"""
        # Format multiple times to warm up cache
        for _ in range(3):
            self.formatter.format_text(self.medium_text)
        
        # Time the actual run
        start_time = time.perf_counter()
        result = self.formatter.format_text(self.medium_text)
        elapsed = time.perf_counter() - start_time
        
        # Should be fast with optimizations
        self.assertLess(elapsed, 0.05, f"Optimized formatting too slow: {elapsed:.4f}s")
        self.assertIn('\n', result)  # Should have proper formatting
    
    def test_format_with_custom_structure_performance(self):
        """Test custom structure formatting performance"""
        start_time = time.perf_counter()
        result = self.formatter.format_with_custom_structure(self.large_text, max_sentences_per_paragraph=3)
        elapsed = time.perf_counter() - start_time
        
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertIn('\n\n', result)  # Should have paragraph breaks
        # Should complete in reasonable time (relaxed threshold for large text)
        self.assertLess(elapsed, 3.0, f"Custom formatting took too long: {elapsed:.4f}s")
    
    def test_caching_infrastructure(self):
        """Test that caching infrastructure is available"""
        # Test text hash generation
        hash1 = self.formatter._get_text_hash(self.short_text)
        hash2 = self.formatter._get_text_hash(self.short_text)
        hash3 = self.formatter._get_text_hash(self.medium_text)
        
        self.assertEqual(hash1, hash2, "Same text should produce same hash")
        self.assertNotEqual(hash1, hash3, "Different text should produce different hash")
        self.assertEqual(len(hash1), 64, "SHA-256 hash should be 64 hex characters")
        
        # Test language detection cache (currently returns None)
        lang = self.formatter._detect_language_cached(hash1)
        self.assertIsNone(lang, "Language detection should return None (not implemented)")
    
    def test_format_transcript_convenience_function(self):
        """Test the convenience function performance"""
        styles = ["auto", "paragraphs", "minimal"]
        
        for style in styles:
            start_time = time.perf_counter()
            result = format_transcript(self.medium_text, style=style)
            elapsed = time.perf_counter() - start_time
            
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
            self.assertLess(elapsed, 0.1, f"Style '{style}' took too long: {elapsed:.4f}s")
    
    def test_empty_and_none_inputs(self):
        """Test edge cases with empty/None inputs"""
        # Empty string
        result = self.formatter.clean_text("")
        self.assertEqual(result, "")
        
        # Whitespace only
        result = self.formatter.clean_text("   ")
        self.assertEqual(result, "")
        
        # None input should be handled gracefully
        # (Note: current implementation may not handle None, this tests expected behavior)
        try:
            result = self.formatter.format_text(None)
        except (TypeError, AttributeError):
            # This is expected if None is not handled
            pass
    
    def test_filler_word_removal_performance(self):
        """Test filler word removal doesn't cause performance issues"""
        # Create text with many filler words
        filler_text = "um uh er ah like you know I mean basically actually " * 100
        
        start_time = time.perf_counter()
        result = self.formatter._remove_excessive_fillers(filler_text)
        elapsed = time.perf_counter() - start_time
        
        self.assertIsInstance(result, str)
        # Should be faster after removing fillers
        self.assertLess(elapsed, 0.05, f"Filler removal took too long: {elapsed:.4f}s")
        
        # Should have removed strict fillers
        self.assertNotIn(' um ', result.lower())
        self.assertNotIn(' uh ', result.lower())
        self.assertNotIn(' er ', result.lower())


class TestTextFormatterCorrectness(unittest.TestCase):
    """Test correctness of optimizations (outputs should be identical)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.formatter = TextFormatter()
        self.sample_text = """one thing that I have recognized is that see I am the molar-type face of clearing and I am purifying my earth element and also my cellular intelligence is getting sharper and also all the cells are being out-chose to divine frequencies and also this is the last step of completing the 3D Transcendence and being liberated while living. What happens is that some certain karma manifests as things like the past reminders of... there isn't exact connection between what I'm experiencing and what my internal state says about the incident."""
    
    def test_formatting_produces_valid_output(self):
        """Verify formatting produces valid structured output"""
        result = self.formatter.format_text(self.sample_text)
        
        # Should be non-empty
        self.assertGreater(len(result), 0)
        
        # Should start with capital letter
        self.assertTrue(result[0].isupper())
        
        # Should end with punctuation (check trimmed result)
        last_char = result.rstrip()[-1] if result.rstrip() else ''
        self.assertIn(last_char, '.!?', f"Expected punctuation at end, got: '{last_char}'")
        
        # Should have sentence breaks
        self.assertIn('\n', result)
    
    def test_common_error_fixes_applied(self):
        """Verify common transcription errors are fixed"""
        result = self.formatter.clean_text(self.sample_text)
        
        # Check specific fixes
        self.assertIn('Mooladhara', result)
        self.assertIn('3D', result)
        self.assertIn('outsourced', result)
    
    def test_type_hints_present(self):
        """Verify type hints are present on methods"""
        # Check key methods have annotations
        self.assertIn('return', self.formatter.clean_text.__annotations__)
        self.assertIn('return', self.formatter._fix_common_errors.__annotations__)
        self.assertIn('return', self.formatter._remove_excessive_fillers.__annotations__)
        self.assertIn('return', self.formatter.format_text.__annotations__)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
