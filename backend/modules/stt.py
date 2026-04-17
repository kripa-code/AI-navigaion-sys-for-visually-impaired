"""
BlindBuddy — Speech-to-Text Module (OpenAI Whisper)
Transcribes audio bytes into text.
"""
import io
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.m4a") -> str:
    """
    Transcribe audio bytes using OpenAI Whisper API.
    Returns the transcribed text string.
    """
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename  # Whisper API needs a filename hint for format detection

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
        return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
    except Exception as e:
        print(f"STT error: {e}")
        return ""
