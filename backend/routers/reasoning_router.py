"""
BlindBuddy — AI Reasoning Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from modules.reasoning import get_guidance

router = APIRouter()


class VisionObject(BaseModel):
    object: str
    raw_class: Optional[str] = ""
    direction: str
    distance: str
    distance_m: Optional[float] = 999.0
    confidence: Optional[float] = 0.0


class ReasonRequest(BaseModel):
    nav_instruction: str
    vision_scene: List[VisionObject] = []


@router.post("", summary="Get AI-combined voice guidance from navigation + vision data")
async def reason(req: ReasonRequest):
    """
    Combines the current navigation instruction with detected objects
    to produce a short, safety-first voice guidance string.
    """
    try:
        scene_dicts = [v.model_dump() for v in req.vision_scene]
        result = get_guidance(req.nav_instruction, scene_dicts)
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning error: {e}")
