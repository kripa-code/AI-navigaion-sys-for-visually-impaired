# BlindBuddy 🦯

> **Real-time AI-powered blind assistance system — navigation + obstacle detection + voice guidance**

BlindBuddy is a voice-first assistive system that guides visually impaired users safely through their environment by combining live GPS navigation (Google Maps), real-time object detection (YOLOv8), AI reasoning (Ollama/LLava), and natural text-to-speech output (PyTTSx3).

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
│   │   ├── reasoning.py           # Ollama / LLava intelligence
│   │   ├── stt.py                 # OpenAI Whisper transcription
│   │   └── tts.py                 # PyTTSx3 Local synthesis
├── frontend/web/                  # Local Web UI
└── ...
```

---

## 🚀 Integrated OpenCV Detection (From Branch1)
We have merged the OpenCV-based object detection logic from the `branch1` contribution. This provides an alternative high-performance detection pipeline using SSD MobileNet.

- See `source/main_webcam.py` for the standalone implementation.
- Configuration resides in `config_files/`.

---

## ⚙️ Setup

### 1. Configure environment
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_MAPS_API_KEY
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyttsx3
uvicorn main:app --reload
```

---

## 🔑 AI Features (Free & Local)
- **Reasoning:** Powered by Ollama. Run `ollama run llava`.
- **Speech:** Powered by PyTTSx3 (Local Mac Synthesis).
