"""
BlindBuddy — Vision Router
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from modules.vision import detect_objects, detect_objects_from_base64
from pydantic import BaseModel

router = APIRouter()


@router.post("/detect", summary="Detect objects in an uploaded image frame")
async def detect(image: UploadFile = File(...)):
    """
    Accepts an image file (JPEG/PNG/WEBP) and returns detected scene objects.
    """
    try:
        image_bytes = await image.read()
        detections = detect_objects(image_bytes)
        return {
            "status": "ok",
            "detections": detections,
            "count": len(detections),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {e}")


class Base64Request(BaseModel):
    image: str  # base64-encoded image


@router.post("/detect-base64", summary="Detect objects from a base64 image string")
async def detect_base64(req: Base64Request):
    """
    Accepts a base64-encoded image string. Used by the WebSocket session flow.
    """
    try:
        detections = detect_objects_from_base64(req.image)
        return {
            "status": "ok",
            "detections": detections,
            "count": len(detections),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection error: {e}")
