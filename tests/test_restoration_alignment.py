#!/usr/bin/env python3
"""
Unit tests for segment-aligned LLM restoration and proportional fallback.
"""

import unittest

from insightron.services.transcription.multi_pass_transcriber import MultiPassTranscriber
from insightron.services.transcription.llm_provider import RestorationResult, BaseLLMProvider


class DummyProvider(BaseLLMProvider):
    """Minimal provider used to exercise MultiPassTranscriber.pass2_restore."""

    def restore_text(self, text, prev_clean=None, next_raw=None, segment_count=None) -> RestorationResult:
        # Echo back a deterministic pattern so tests can assert alignment.
        if segment_count is not None:
            segment_texts = [f"seg-{i}" for i in range(segment_count)]
        else:
            segment_texts = None
        return RestorationResult(
            original_text=text,
            restored_text=" ".join(segment_texts) if segment_texts else text,
            segment_texts=segment_texts,
            processing_time=0.01,
            tokens_used=0,
            model_name="dummy",
            success=True,
            flags=[],
            stitched=False,
        )

    def is_available(self) -> bool:
        return True


class TestRestorationAlignment(unittest.TestCase):
    def setUp(self) -> None:
        config = {
            "contextual_restoration": {"enabled": True, "provider": "local"},
            "emotion_mapping": {"enabled": False},
            "chunk_duration": 30,
            "chunk_overlap": 2,
        }
        self.transcriber = MultiPassTranscriber(config)
        # Inject dummy provider directly to avoid external dependencies.
        self.transcriber.llm_provider = DummyProvider(config={})

    def test_segment_aligned_texts_applied_per_segment(self) -> None:
        segments = [
            {"start": 0.0, "end": 1.0, "text": "a"},
            {"start": 1.0, "end": 2.0, "text": "b"},
            {"start": 2.0, "end": 3.0, "text": "c"},
        ]

        restored = self.transcriber.pass2_restore(segments)

        # All segments should be restored and aligned with the dummy pattern.
        self.assertEqual(len(restored), 3)
        self.assertEqual(restored[0]["text"], "seg-0")
        self.assertEqual(restored[1]["text"], "seg-1")
        self.assertEqual(restored[2]["text"], "seg-2")

    def test_fallback_proportional_distribution_keeps_words(self) -> None:
        # Reconfigure provider to omit segment_texts and exercise the fallback.
        class FallbackProvider(DummyProvider):
            def restore_text(self, text, prev_clean=None, next_raw=None, segment_count=None) -> RestorationResult:
                return RestorationResult(
                    original_text=text,
                    restored_text="one two three four five six",
                    segment_texts=None,
                    processing_time=0.01,
                    tokens_used=0,
                    model_name="dummy",
                    success=True,
                    flags=[],
                    stitched=False,
                )

        self.transcriber.llm_provider = FallbackProvider(config={})

        segments = [
            {"start": 0.0, "end": 1.0, "text": "a"},
            {"start": 1.0, "end": 2.0, "text": "b c"},
        ]

        restored = self.transcriber.pass2_restore(segments)

        # Both segments should still receive at least one word of text.
        self.assertEqual(len(restored), 2)
        self.assertTrue(restored[0]["text"])
        self.assertTrue(restored[1]["text"])


if __name__ == "__main__":
    unittest.main()

