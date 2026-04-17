"""
BlindBuddy — WebSocket Client Test Script
Simulates a real-time guidance session without needing a physical device.
Usage: python tests/ws_client_test.py
"""
import asyncio
import json
import base64
import websockets

# ── Config ────────────────────────────────────────────────────────────────────
WS_URL = "ws://localhost:8000/ws/session"

# Minimal sample nav steps
MOCK_STEPS = [
    {"instruction": "Head north on Main Street", "distance_m": 100, "start_lat": 37.7749, "start_lng": -122.4194, "end_lat": 37.7758, "end_lng": -122.4194, "maneuver": "", "duration_s": 80, "index": 0},
    {"instruction": "Turn right onto Market Street", "distance_m": 200, "start_lat": 37.7758, "start_lng": -122.4194, "end_lat": 37.7758, "end_lng": -122.4175, "maneuver": "turn-right", "duration_s": 160, "index": 1},
]

# A tiny 1x1 white pixel JPEG as placeholder (in real usage, it's a real camera frame)
PLACEHOLDER_IMAGE_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
    "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAARC"
    "AABAAEDASIA..."  # truncated placeholder
)


async def simulate_session():
    print(f"🔌 Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL, ping_interval=20) as ws:
            print("✅ Connected!\n")

            # Simulate 5 frames (each ~1.5 seconds apart)
            for frame_num in range(1, 6):
                step_idx = min(frame_num - 1, len(MOCK_STEPS) - 1)
                nav_instruction = MOCK_STEPS[step_idx]["instruction"]

                payload = {
                    "type": "frame",
                    "image": PLACEHOLDER_IMAGE_B64,  # real app sends camera base64
                    "lat": 37.7749 + (frame_num * 0.0001),
                    "lng": -122.4194,
                    "step_index": step_idx,
                    "steps": MOCK_STEPS,
                    "nav_instruction": nav_instruction,
                }

                print(f"📤 [Frame {frame_num}] Sending: nav='{nav_instruction}'")
                await ws.send(json.dumps(payload))

                # Wait for response
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10)
                    msg = json.loads(raw)

                    if msg.get("type") == "guidance":
                        print(f"📥 [Frame {frame_num}] Guidance: {msg.get('text', '')}")
                        print(f"    Urgency : {msg.get('urgency', 'N/A')}")
                        print(f"    Detects : {[d['object'] for d in msg.get('detections', [])]}")
                        audio = msg.get("audio", "")
                        print(f"    Audio   : {'✅ received (' + str(len(audio)) + ' chars)' if audio else '❌ none'}")
                        print()
                    elif msg.get("type") == "arrived":
                        print("🎉 Arrived at destination!")
                        break
                    else:
                        print(f"ℹ️  Received: {msg}")
                except asyncio.TimeoutError:
                    print(f"⏰ [Frame {frame_num}] Timeout waiting for response")

                await asyncio.sleep(1.5)  # simulate 1.5s frame interval

    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure the backend is running: uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    asyncio.run(simulate_session())
