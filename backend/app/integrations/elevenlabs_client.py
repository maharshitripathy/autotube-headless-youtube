"""ElevenLabs text-to-speech integration."""
from __future__ import annotations

from elevenlabs.client import ElevenLabs

from app.config import settings

DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # a neutral default voice
EST_TTS_USD_PER_1K_CHARS = 0.30


def _client() -> ElevenLabs:
    return ElevenLabs(api_key=settings.elevenlabs_api_key)


def synthesize(text: str, voice_id: str | None = None) -> bytes:
    """Generate speech audio (MP3 bytes) for the given narration text."""
    audio = _client().text_to_speech.convert(
        voice_id=voice_id or DEFAULT_VOICE_ID,
        model_id="eleven_multilingual_v2",
        text=text,
        output_format="mp3_44100_128",
    )
    if isinstance(audio, (bytes, bytearray)):
        return bytes(audio)
    return b"".join(chunk for chunk in audio)


def estimate_cost(text: str) -> float:
    return (len(text) / 1000.0) * EST_TTS_USD_PER_1K_CHARS


def list_voices() -> list[dict]:
    resp = _client().voices.get_all()
    return [{"voice_id": v.voice_id, "name": v.name} for v in resp.voices]
