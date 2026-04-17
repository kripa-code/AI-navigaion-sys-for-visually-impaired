# BlindBuddy 🦯

> **Real-time AI-powered blind assistance system — navigation + obstacle detection + voice guidance**

BlindBuddy is a voice-first assistive system that guides visually impaired users safely through their environment by combining live GPS navigation (Google Maps), real-time object detection (YOLOv8), AI reasoning (GPT-4o), and natural text-to-speech output.

---

## 🏗️ Project Structure

```
BlindBuddy/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Environment variable loader
│   ├── requirements.txt
│   ├── modules/
│   │   ├── navigation.py          # Google Maps Directions + step tracking
│   │   ├── vision.py              # YOLOv8 object detection
│   │   ├── reasoning.py           # GPT-4o safety-first guidance
│   │   ├── stt.py                 # OpenAI Whisper transcription
│   │   └── tts.py                 # ElevenLabs / gTTS synthesis
│   ├── routers/
│   │   ├── navigation_router.py
│   │   ├── vision_router.py
│   │   ├── reasoning_router.py
│   │   ├── voice_router.py
│   │   └── ws_router.py           # WebSocket real-time session hub
│   └── tests/
│       ├── test_navigation.py
│       ├── test_reasoning.py
│       └── ws_client_test.py      # WebSocket simulation script
├── frontend/                      # React Native (Expo)
│   ├── App.js
│   ├── app.json
│   ├── screens/
│   │   ├── HomeScreen.js          # Voice destination input
│   │   └── NavigationScreen.js    # Live guidance + camera
│   └── services/
│       ├── config.js              # Backend URL config
│       └── api.js                 # REST service helpers
├── docs/
│   └── architecture.md            # System diagram + API reference
└── .env.example
```

---

## ⚙️ Setup

### 1. Clone and configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
#   GOOGLE_MAPS_API_KEY=...
#   OPENAI_API_KEY=...
#   ELEVENLABS_API_KEY=... (optional — falls back to gTTS)
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Also install gTTS for the TTS fallback:
pip install gtts
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

> On first run, YOLOv8 will auto-download `yolov8n.pt` (~6 MB).

### 3. Frontend (Expo)

```bash
cd frontend
npm install
npx expo start
```

Scan the QR code with **Expo Go** on a physical iOS/Android device.

> Update `frontend/services/config.js` with your machine's local IP address (e.g., `http://192.168.1.42:8000`) so the device can reach the backend.

---

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
pip install pytest
pytest tests/test_navigation.py tests/test_reasoning.py -v
```

### Simulate a WebSocket session (no device needed)

```bash
# Make sure backend is running first, then:
python tests/ws_client_test.py
```

---

## 🔑 API Keys Required

| Key | Where to get it | Required |
|-----|----------------|----------|
| `GOOGLE_MAPS_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) — enable Directions API | ✅ Yes |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) | ✅ Yes |
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io) | ⭕ Optional |

---

## 🧠 System Flow

```
User: "Take me to the nearest bus stop"
  ↓
[Whisper STT] → destination text
  ↓
[Google Maps] → route steps + ETA
  ↓
[WebSocket Loop every 1.5s]:
  Camera frame → [YOLOv8] → detections
  GPS position → [Navigation] → nav instruction
  Both → [GPT-4o] → safety-first guidance text
  Text → [TTS] → MP3 audio
  ↓
User hears: "Slow down. A car is approaching on your right. Wait before turning."
```

---

## 🚨 Safety Priority

| Urgency | Trigger | Example Output |
|---------|---------|----------------|
| 🚨 HIGH | Object < 1.5m or vehicle / stairs nearby | "Stop. Stairs directly ahead." |
| ⚠️ MEDIUM | Object 1.5–3m away | "Slow down. A pedestrian is crossing." |
| ✅ LOW | Clear path | "Turn left in 10 meters." |

---

## 📱 Demo Interaction Examples

| User Says | System Detects | Voice Output |
|-----------|---------------|--------------|
| "Take me to Central Park" | Car 1m right | "Stop. A car is very close on your right. Wait." |
| (Walking) | Stairs ahead 2m | "Stop. Stairs ahead. Reach for the handrail." |
| (Off route) | Nothing | "You've veered off the path. Turn around and head north." |
| (Clear path) | Bench 6m left | "Turn right in 30 meters. Path is clear ahead." |

---

## 🔮 Advanced Features (Roadmap)

- [ ] Offline YOLOv8 inference (no server needed)
- [ ] Haptic pattern encoding for urgency levels
- [ ] Smart glasses (AR) integration
- [ ] Learning user walking pace for better distance estimates
- [ ] Edge AI on Raspberry Pi / Jetson Nano

---

## 📄 License

MIT — Build something that helps people. 💙
