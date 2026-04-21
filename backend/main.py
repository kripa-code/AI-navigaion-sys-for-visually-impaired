"""
BlindBuddy Backend — Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from routers import navigation_router, vision_router, reasoning_router, voice_router, ws_router
from modules.vision import load_model
from config import GOOGLE_MAPS_API_KEY


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup."""
    print("🚀 BlindBuddy backend starting up...")
    load_model()
    print("✅ YOLOv8 model loaded.")
    yield
    print("🔒 BlindBuddy backend shutting down.")


app = FastAPI(
    title="BlindBuddy API",
    description="Real-time AI-powered blind assistance system: Navigation + Vision + AI Reasoning + Voice",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins for dev (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(navigation_router.router, prefix="/navigate", tags=["Navigation"])
app.include_router(vision_router.router, prefix="/vision", tags=["Vision"])
app.include_router(reasoning_router.router, prefix="/reason", tags=["AI Reasoning"])
app.include_router(voice_router.router, prefix="/voice", tags=["Voice I/O"])
app.include_router(ws_router.router, tags=["WebSocket Session"])


@app.get("/health", summary="Health check")
async def health():
    return {"status": "ok", "service": "BlindBuddy"}


@app.get("/config", summary="Frontend config (public keys)", tags=["Config"])
async def frontend_config():
    """Returns public configuration needed by the web frontend."""
    return {"google_maps_api_key": GOOGLE_MAPS_API_KEY}


# Serve web frontend — must be last so API routes take priority
_HERE    = os.path.dirname(os.path.abspath(__file__))
WEB_DIR  = os.path.abspath(os.path.join(_HERE, "..", "frontend", "web"))
print(f"📁 Web frontend dir: {WEB_DIR} (exists={os.path.isdir(WEB_DIR)})")
if os.path.isdir(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
