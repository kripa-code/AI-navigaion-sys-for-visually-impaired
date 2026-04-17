"""
BlindBuddy — Text-to-Speech Module
Synthesizes speech using Google Cloud TTS (primary) or ElevenLabs (premium).
Falls back to a simple gTTS if no cloud credentials are configured.
"""
import io
import requests
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


def synthesize_speech(text: str) -> bytes:
    """
    Convert text to MP3 audio bytes.
    Priority: ElevenLabs (if key set) → Google Cloud TTS → gTTS fallback
    """
    if ELEVENLABS_API_KEY:
        return _elevenlabs_tts(text)
    return _gtts_fallback(text)


def _elevenlabs_tts(text: str) -> bytes:
    """ElevenLabs TTS — high quality, low latency."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",  # low-latency model
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"ElevenLabs TTS error: {e}. Falling back to gTTS.")
        return _gtts_fallback(text)


def _gtts_fallback(text: str) -> bytes:
    """
    gTTS fallback — uses Google Translate TTS (no API key required).
    Limited to ~200 chars per request. Good for short guidance sentences.
    """
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        tts = gTTS(text=text, lang="en", slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"gTTS error: {e}")
        return b""
