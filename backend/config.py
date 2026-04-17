"""
BlindBuddy Backend — Configuration
Loads all settings from the .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

# Server
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# YOLO
YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolov8n.pt")
YOLO_CONFIDENCE: float = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.45"))

# Safety thresholds (in meters)
URGENCY_HIGH_DISTANCE: float = float(os.getenv("MAX_DISTANCE_URGENCY_HIGH", "1.5"))
URGENCY_MEDIUM_DISTANCE: float = float(os.getenv("MAX_DISTANCE_URGENCY_MEDIUM", "3.0"))

# Session
FRAME_INTERVAL_MS: int = int(os.getenv("FRAME_INTERVAL_MS", "1500"))

# Object classes that are always HIGH priority regardless of distance
HIGH_PRIORITY_OBJECTS = {"stairs", "step", "staircase", "car", "truck", "bus", "motorcycle", "bicycle"}
