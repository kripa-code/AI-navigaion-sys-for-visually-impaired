"""
BlindBuddy — AI Reasoning Module
Combines navigation + vision data into prioritized, voice-ready guidance using GPT-4o.
"""
from openai import OpenAI
from config import OPENAI_API_KEY, URGENCY_HIGH_DISTANCE, URGENCY_MEDIUM_DISTANCE, HIGH_PRIORITY_OBJECTS

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are BlindBuddy, an AI assistant guiding a visually impaired person through their environment.

Your role:
- Combine real-time YOLO distance detections with your own rigorous visual analysis of the provided image.
- Actively scan the image specifically to catch complex objects including: obstacles, doors, vehicles, traffic signals, sign boards, lifts, escalators, stairs, flap barriers, footpaths, glass doors, potholes, humps, stray animals.
- Generate short, clear, actionable voice guidance (1–2 sentences MAX).
- Prioritize SAFETY over navigation — hazard warnings always come first.
- Use plain, calm language (no markdown, no lists, no punctuation overload).

Urgency levels:
- HIGH: immediate danger (e.g., pothole immediately ahead, flap barrier closing, very close vehicle/staircase) → start with "Stop." or "Wait."
- MEDIUM: caution needed (e.g., hump or glass door a few meters away) → start with "Slow down." or "Caution."
- LOW: informational (clear path, distant objects) → direct navigation instruction.

Never say "I detected", "I see", or "Based on the image". Speak directly as a companion guiding the user."""


def classify_urgency(vision_scene: list[dict]) -> str:
    """Classify basic urgency from YOLO object distances (overridden by GPT-4o implicitly in text)."""
    if not vision_scene:
        return "LOW"

    for obj in vision_scene:
        dist = obj.get("distance_m", 999)
        raw_class = obj.get("raw_class", "").lower()

        if raw_class in HIGH_PRIORITY_OBJECTS or any(k in raw_class for k in ["stair", "step"]):
            if dist <= URGENCY_MEDIUM_DISTANCE:
                return "HIGH"

        if dist <= URGENCY_HIGH_DISTANCE:
            return "HIGH"
        elif dist <= URGENCY_MEDIUM_DISTANCE:
            return "MEDIUM"

    return "LOW"


def build_prompt(nav_instruction: str, vision_scene: list[dict], urgency: str) -> str:
    """Compose the text portion of the user prompt for GPT-4o."""
    scene_lines = []
    for obj in vision_scene[:5]:
        scene_lines.append(
            f"  - {obj['object']} {obj['direction']}, ~{obj['distance']}, confidence {obj['confidence']}"
        )
    scene_text = "\n".join(scene_lines) if scene_lines else "  - No YOLO objects detected, rely fully on the image."

    return f"""Current navigation instruction: "{nav_instruction}"

Initial YOLO distance estimations (closest first):
{scene_text}

Base urgency level: {urgency}. Look at the attached image carefully to see if there are unlisted hazards (like potholes, glass doors, steps, animals, or barriers) that increase urgency to HIGH. Generate a single voice guidance message (1–2 sentences) following the safety priority rules."""


import requests
import json

def get_guidance(nav_instruction: str, vision_scene: list[dict], b64_image: str = None) -> dict:
    """
    100% Free, Local AI Reasoning entry point via Ollama.
    Returns: { "guidance": str, "urgency": str }
    """
    urgency = classify_urgency(vision_scene)
    text_prompt = build_prompt(nav_instruction, vision_scene, urgency)

    payload = {
        "model": "llama3.2",  # Targeting higher reasoning quality model
        "prompt": f"System Role: {SYSTEM_PROMPT}\n\nNavigation Context: {nav_instruction}\nVision Detections: {json.dumps(vision_scene)}\n\nTask: Generate short guidance.",
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 50
        }
    }

    # Attach the raw image directly if provided, so the local AI can see it
    if b64_image:
        payload["images"] = [b64_image]

    try:
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        guidance = data.get("response", "").strip()
        
        # If the local AI returns empty string, fallback gracefully
        if not guidance:
            raise ValueError("Ollama returned empty response")
            
    except Exception as e:
        print(f"Local AI Reasoning error (is Ollama running?): {e}")
        # Standard safety fallback if Ollama isn't installed or is booting up
        guidance = nav_instruction if nav_instruction else "Path is clear. Continue forward."

    return {"guidance": guidance, "urgency": urgency}

