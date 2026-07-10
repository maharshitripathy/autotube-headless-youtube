"""Local word-level captions via faster-whisper (no paid API)."""
from __future__ import annotations

import tempfile

from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            settings.whisper_model, device=settings.whisper_device, compute_type="int8"
        )
    return _model


def transcribe_words(audio_bytes: bytes) -> list[dict]:
    """Return word-level caption tokens: [{word, start, end}]."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        path = f.name

    segments, _info = _get_model().transcribe(path, word_timestamps=True)
    words: list[dict] = []
    for segment in segments:
        for w in (segment.words or []):
            words.append({"word": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3)})
    return words
