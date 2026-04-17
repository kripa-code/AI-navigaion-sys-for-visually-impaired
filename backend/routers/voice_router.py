"""
BlindBuddy — Voice I/O Router
"""
import base64
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from modules.stt import transcribe_audio
from modules.tts import synthesize_speech

router = APIRouter()


@router.post("/transcribe", summary="Transcribe audio to text (Whisper)")
async def transcribe(audio: UploadFile = File(...)):
    """
    Accepts an audio file (m4a / wav / mp3 / webm) and returns the transcribed text.
    """
    try:
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.m4a"
        text = transcribe_audio(audio_bytes, filename=filename)
        return {"status": "ok", "text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {e}")


class SynthesizeRequest(BaseModel):
    text: str


@router.post("/synthesize", summary="Convert text to speech audio (TTS)")
async def synthesize(req: SynthesizeRequest):
    """
    Accepts a text string and returns an MP3 audio response.
    """
    try:
        audio_bytes = synthesize_speech(req.text)
        if not audio_bytes:
            raise ValueError("TTS returned empty audio")
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")


@router.post("/synthesize-base64", summary="Convert text to speech, returns base64 audio")
async def synthesize_base64(req: SynthesizeRequest):
    """
    Returns synthesized audio as a base64 string — used by WebSocket session flow.
    """
    try:
        audio_bytes = synthesize_speech(req.text)
        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        return {"status": "ok", "audio": b64_audio, "format": "mp3"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")
