#!/usr/bin/env python3
"""
Sanity checks for TextFormatter layout views.
"""

import unittest

from insightron.services.transcription.text_formatter import TextFormatter


class TestFormatterViews(unittest.TestCase):
    def setUp(self) -> None:
        self.formatter = TextFormatter()

    def test_thinking_session_paragraphs_are_longer(self) -> None:
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. Sentence six."
        auto_out = self.formatter.format_text(text, style="auto")
        thinking_out = self.formatter.format_text(text, style="thinking_session")

        auto_paragraphs = auto_out.split("\n\n")
        thinking_paragraphs = thinking_out.split("\n\n")

        # thinking_session should tend toward fewer / longer paragraphs than auto.
        self.assertLessEqual(len(thinking_paragraphs), len(auto_paragraphs))

    def test_meeting_notes_uses_bullets(self) -> None:
        text = "First point. Second point. Third point."
        out = self.formatter.format_text(text, style="meeting_notes")
        lines = [l for l in out.split("\n") if l.strip()]
        self.assertTrue(all(line.startswith("- ") for line in lines))


if __name__ == "__main__":
    unittest.main()

