from faster_whisper import WhisperModel

_model = None


def get_model() -> WhisperModel:
    # loaded on first use, so the server starts fast
    global _model
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    return _model


def transcribe_file(fileobj, language: str = "ja") -> str:
    segments, _ = get_model().transcribe(fileobj, language=language, vad_filter=True)
    return "".join(s.text for s in segments).strip()