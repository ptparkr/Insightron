import pytest


from insightron.services.transcription.metrics_calculator import MetricsCalculator
from insightron.services.transcription.contracts import DiarizationResult, DiarizationTurn
from insightron.services.transcription.speaker_attribution import SpeakerAttribution
from insightron.services.transcription.markdown_renderer import MarkdownRenderer


@pytest.mark.unit
def test_metrics_calculator_basic_words_pauses():
    segments = [
        {
            "start": 0.0,
            "end": 2.0,
            "text": "Hello world.",
            "confidence": -0.1,
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.4, "probability": 0.95},
                {"word": "world", "start": 1.0, "end": 1.4, "probability": 0.60},  # pause + low conf
            ],
        }
    ]
    calc = MetricsCalculator(confidence_threshold=0.75, pause_gap_seconds=0.3)
    m = calc.compute(
        segments,
        language_detected="en",
        language_confidence=0.99,
        duration_seconds=2.0,
        no_speech_probability=0.1,
        compression_ratio=1.5,
    )

    assert m.total_words == 2
    assert m.pause_count == 1
    assert m.low_confidence_ratio == pytest.approx(0.5)
    assert len(m.low_confidence_words) == 1
    assert m.low_confidence_words[0].word.lower() == "world"


@pytest.mark.unit
def test_speaker_attribution_assigns_segment_and_words():
    diar = DiarizationResult(
        pipeline_id="pyannote/speaker-diarization@2.1",
        turns=[
            DiarizationTurn(start=0.0, end=1.0, speaker="SPEAKER_00"),
            DiarizationTurn(start=1.0, end=2.0, speaker="SPEAKER_01"),
        ],
        num_speakers=2,
    )
    segments = [
        {
            "start": 0.0,
            "end": 2.0,
            "text": "A B",
            "words": [
                {"word": "A", "start": 0.1, "end": 0.2, "probability": 0.9},
                {"word": "B", "start": 1.2, "end": 1.3, "probability": 0.9},
            ],
        }
    ]

    out = SpeakerAttribution().apply(segments, diar)
    assert out[0]["speaker"] in {"SPEAKER_00", "SPEAKER_01"}
    assert out[0]["words"][0]["speaker"] == "SPEAKER_00"
    assert out[0]["words"][1]["speaker"] == "SPEAKER_01"


@pytest.mark.unit
def test_markdown_renderer_dashboard_contains_sections():
    renderer = MarkdownRenderer()
    md = renderer.render_dashboard(
        audio_path="audio.wav",
        segments=[
            {"start": 0.0, "end": 1.0, "text": "Hello.", "words": [], "speaker": "SPEAKER_00"}
        ],
        metrics=MetricsCalculator().compute(
            [{"start": 0.0, "end": 1.0, "text": "Hello.", "confidence": -0.1, "words": []}],
            language_detected="en",
            language_confidence=0.9,
            duration_seconds=1.0,
            no_speech_probability=0.0,
            compression_ratio=1.0,
        ),
        diarization=DiarizationResult(
            pipeline_id="pyannote/speaker-diarization@2.1",
            turns=[DiarizationTurn(start=0.0, end=1.0, speaker="SPEAKER_00")],
            num_speakers=1,
        ),
        engine_model="large-v3",
        backend="faster-whisper",
        formatting_style="thinking_session",
        processed_at="2026-02-27 12:00:00",
    )

    assert "## Transcription Quality Dashboard" in md
    assert "## Full Transcript" in md
    assert "## Timestamped Segments" in md
    assert "## Low-Confidence Flags" in md
    assert "## Raw Metadata" in md

