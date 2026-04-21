"""
BlindBuddy — Text-to-Speech Module
Synthesizes speech using Google Cloud TTS (primary) or ElevenLabs (premium).
Falls back to a simple gTTS if no cloud credentials are configured.
"""
import io
import requests
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


import pyttsx3

import threading

def _speak_async(text: str):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"pyttsx3 thread error: {e}")

def synthesize_speech(text: str) -> bytes:
    """
    100% Free, Local TTS using pyttsx3 (Non-blocking).
    """
    if text:
        threading.Thread(target=_speak_async, args=(text,), daemon=True).start()
        
    return b""
