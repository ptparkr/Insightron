import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insightron.services.transcription.text_formatter import TextFormatter, format_transcript

class TestTextFormatterV2(unittest.TestCase):
    def setUp(self):
        self.formatter = TextFormatter()

    def test_sentence_splitting_abbreviations(self):
        text = "Dr. Smith went to the U.S.A. today. He met Mr. Jones."
        sentences = self.formatter._split_into_sentences(text)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0], "Dr. Smith went to the U.S.A. today.")
        self.assertEqual(sentences[1], "He met Mr. Jones.")

    def test_bullets_formatting(self):
        text = "First we need to do this. Second we need to do that. Finally we are done."
        formatted = self.formatter.format_as_bullets(text)
        lines = formatted.split('\n')
        self.assertTrue(all(line.startswith('* ') for line in lines))
        self.assertEqual(len(lines), 3)
        self.assertIn("* First we need to do this.", lines)

    def test_bullets_formatting_with_paragraphs(self):
        text = "This is the first point. It has two sentences. Next is the second point. It also has details."
        formatted = self.formatter.format_as_bullets(text)
        lines = formatted.split('\n')
        # "Next" is a paragraph starter, so it should split
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("* This is the first point. It has two sentences."))
        self.assertTrue(lines[1].startswith("* Next is the second point. It also has details."))

    def test_format_transcript_convenience_function(self):
        text = "hello world. this is a test."
        bullets = format_transcript(text, style="bullets")
        self.assertTrue(bullets.startswith("* Hello world."))

if __name__ == '__main__':
    unittest.main()
