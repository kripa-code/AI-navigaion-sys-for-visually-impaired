"""
BlindBuddy — WebSocket Session Router
The real-time loop that drives the entire guidance pipeline:
Client sends → {type:"frame", image:base64, lat, lng, step_index, steps, nav_instruction}
Server responds → {type:"guidance", text, urgency, audio:base64_mp3, step_info}
"""
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from modules.vision import detect_objects_from_base64
from modules.reasoning import get_guidance
from modules.tts import synthesize_speech
from modules.navigation import get_next_step, check_deviation

router = APIRouter()


@router.websocket("/ws/session")
async def session(websocket: WebSocket):
    """
    Persistent WebSocket session for a single navigation journey.
    Accepts frames + location, returns real-time guidance audio.
    """
    await websocket.accept()
    print("🔌 WebSocket session opened.")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            msg_type = msg.get("type", "frame")

            # ── PING / keepalive ────────────────────────────────────────────
            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            # ── FRAME: Full guidance pipeline ───────────────────────────────
            if msg_type == "frame":
                b64_image = msg.get("image", "")
                lat = float(msg.get("lat", 0))
                lng = float(msg.get("lng", 0))
                step_index = int(msg.get("step_index", 0))
                steps = msg.get("steps", [])
                nav_instruction = msg.get("nav_instruction", "Continue forward.")

                # 1. Navigation update
                step_info = {}
                if steps:
                    step_info = get_next_step(steps, lat, lng, step_index)
                    deviated = check_deviation(steps, lat, lng, step_index)
                    if deviated:
                        nav_instruction = "You have veered off the route. Please turn around."
                    elif step_info.get("instruction"):
                        nav_instruction = step_info["instruction"]
                    if step_info.get("arrived"):
                        await websocket.send_text(json.dumps({
                            "type": "arrived",
                            "text": "You have arrived at your destination.",
                        }))
                        break

                # 2. Vision detection
                vision_scene = []
                if b64_image:
                    try:
                        vision_scene = detect_objects_from_base64(b64_image)
                    except Exception as e:
                        print(f"Vision error in WS: {e}")

                # 3. AI Reasoning
                result = get_guidance(nav_instruction, vision_scene)
                guidance_text = result["guidance"]
                urgency = result["urgency"]

                # 4. TTS synthesis
                audio_b64 = ""
                try:
                    audio_bytes = synthesize_speech(guidance_text)
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                except Exception as e:
                    print(f"TTS error in WS: {e}")

                # 5. Send guidance back to client
                await websocket.send_text(json.dumps({
                    "type": "guidance",
                    "text": guidance_text,
                    "urgency": urgency,
                    "audio": audio_b64,
                    "step_info": step_info,
                    "detections": vision_scene[:5],
                }))

    except WebSocketDisconnect:
        print("🔌 WebSocket session closed by client.")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
