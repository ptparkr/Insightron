import pytest


def test_faster_whisper_dependency_installed():
    """
    Hard dependency check.

    Insightron's core transcription pipeline depends on faster-whisper,
    so if this fails the app is unlikely to work either.
    """
    try:
        import faster_whisper  # noqa: F401
    except Exception as e:
        pytest.fail(f"faster-whisper is not importable: {e}")


@pytest.mark.slow
@pytest.mark.model_download
def test_faster_whisper_can_load_tiny_model_cpu():
    """
    Optional smoke test that may download a model on first run.

    Marked as model_download so it is skipped by default on developer machines.
    """
    from faster_whisper import WhisperModel

    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    assert model is not None
