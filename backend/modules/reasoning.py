"""
BlindBuddy — AI Reasoning Module
Combines navigation + vision data into prioritized, voice-ready guidance using GPT-4o.
"""
from openai import OpenAI
from config import OPENAI_API_KEY, URGENCY_HIGH_DISTANCE, URGENCY_MEDIUM_DISTANCE, HIGH_PRIORITY_OBJECTS

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are BlindBuddy, an AI assistant guiding a visually impaired person through their environment.

Your role:
- Combine real-time camera detections (obstacles, hazards) with navigation instructions
- Generate short, clear, actionable voice guidance (1–2 sentences MAX)
- Prioritize SAFETY over navigation — hazard warnings always come first
- Use plain, calm language (no markdown, no lists, no punctuation overload)

Urgency levels:
- HIGH: immediate danger (nearby vehicle, stairs directly ahead, sudden obstacle) → start with "Stop." or "Wait."
- MEDIUM: caution needed (obstacle a few meters away) → start with "Slow down."
- LOW: informational (clear path, distant object) → direct navigation instruction

Never say "I detected" or "Based on the data". Speak directly as a companion guiding the user."""


def classify_urgency(vision_scene: list[dict]) -> str:
    """Classify overall urgency based on detected objects and distances."""
    if not vision_scene:
        return "LOW"

    for obj in vision_scene:
        dist = obj.get("distance_m", 999)
        raw_class = obj.get("raw_class", "").lower()
        obj_name = obj.get("object", "").lower()

        # Always HIGH if it's a stairs/vehicle very close
        if raw_class in HIGH_PRIORITY_OBJECTS or any(k in raw_class for k in ["stair", "step"]):
            if dist <= URGENCY_MEDIUM_DISTANCE:
                return "HIGH"

        if dist <= URGENCY_HIGH_DISTANCE:
            return "HIGH"
        elif dist <= URGENCY_MEDIUM_DISTANCE:
            return "MEDIUM"

    return "LOW"


def build_prompt(nav_instruction: str, vision_scene: list[dict], urgency: str) -> str:
    """Compose the user-side prompt for GPT-4o."""
    scene_lines = []
    for obj in vision_scene[:5]:  # cap at top 5 closest objects
        scene_lines.append(
            f"  - {obj['object']} {obj['direction']}, ~{obj['distance']}, confidence {obj['confidence']}"
        )
    scene_text = "\n".join(scene_lines) if scene_lines else "  - No significant objects detected"

    return f"""Current navigation instruction: "{nav_instruction}"

Camera detections (closest first):
{scene_text}

Overall urgency: {urgency}

Generate a single voice guidance message (1–2 sentences) following the safety priority rules."""


def get_guidance(nav_instruction: str, vision_scene: list[dict]) -> dict:
    """
    Main reasoning entry point.
    Returns: { "guidance": str, "urgency": str }
    """
    urgency = classify_urgency(vision_scene)
    prompt = build_prompt(nav_instruction, vision_scene, urgency)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=80,
            temperature=0.3,
        )
        guidance = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM error: {e}")
        # Graceful fallback: return nav instruction directly
        guidance = nav_instruction if nav_instruction else "Path is clear. Continue forward."

    return {"guidance": guidance, "urgency": urgency}
