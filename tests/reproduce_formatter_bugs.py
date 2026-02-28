import unittest
from insightron.services.transcription.text_formatter import TextFormatter

class TestReproduction(unittest.TestCase):
    def setUp(self):
        self.formatter = TextFormatter()

    def test_bug_1_false_positives_long_pause(self):
        # "Secondary" should not match "second"
        self.assertFalse(self.formatter._indicates_long_pause("Secondary school is important."), 
                         "Bug 1: 'Secondary' incorrectly identified as pause indicator 'second'")
        
        # "Firsthand" should not match "first"
        self.assertFalse(self.formatter._indicates_long_pause("Firsthand accounts suggest."),
                         "Bug 1: 'Firsthand' incorrectly identified as pause indicator 'first'")

        # "Thence" should not match "then"
        self.assertFalse(self.formatter._indicates_long_pause("Thence we proceeded."),
                         "Bug 1: 'Thence' incorrectly identified as pause indicator 'then'")
        
        # Verify positives still work
        self.assertTrue(self.formatter._indicates_long_pause("First, we eat."), "Regression: 'First' failed to identify")

    def test_bug_2_clean_text_aggressive_removal(self):
        # "like" as a verb should be preserved
        original = "I like pizza."
        cleaned = self.formatter.clean_text(original)
        self.assertEqual(cleaned, "I like pizza.", f"Bug 2: 'like' removed from '{original}' -> '{cleaned}'")

        # "you know" as legitimate phrase
        original = "Do you know the answer?"
        cleaned = self.formatter.clean_text(original)
        self.assertEqual(cleaned, "Do you know the answer?", f"Bug 2: 'you know' removed from '{original}' -> '{cleaned}'")
        
        # Verify filler removal still works for non-ambiguous fillers
        self.assertEqual(self.formatter.clean_text("It is, um, uh, cool."), "It is, cool.", "Regression: filler 'um/uh' not removed")
        
        # Verify 'like' is NOT removed even in filler-like context (safety first)
        self.assertEqual(self.formatter.clean_text("It is, like, cool."), "It is, like, cool.", "Safety: 'like' should be preserved to avoid false positives")

if __name__ == '__main__':
    unittest.main()
