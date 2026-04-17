"""
BlindBuddy — Navigation Router
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from modules.navigation import get_route, get_next_step, check_deviation

router = APIRouter()


class StartRequest(BaseModel):
    destination: str
    lat: float
    lng: float


class UpdateRequest(BaseModel):
    lat: float
    lng: float
    step_index: int
    steps: list  # pass steps back to avoid server-side session storage for simplicity


@router.post("/start", summary="Start navigation to a destination")
async def start_navigation(req: StartRequest):
    """
    Begin a navigation session.
    Returns route steps, ETA, and distance.
    """
    try:
        route = get_route(req.lat, req.lng, req.destination)
        return {
            "status": "ok",
            "route": route,
            "message": f"Route to '{req.destination}' found. {route['distance_km']} km, approximately {route['eta_minutes']} minutes walking.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Navigation error: {e}")


@router.post("/update", summary="Get next navigation instruction based on current location")
async def update_navigation(req: UpdateRequest):
    """
    Update navigation state with current GPS position.
    Returns next instruction, deviation flag, and whether to advance step.
    """
    try:
        step_info = get_next_step(req.steps, req.lat, req.lng, req.step_index)
        deviated = check_deviation(req.steps, req.lat, req.lng, req.step_index)
        return {
            "status": "ok",
            **step_info,
            "deviated": deviated,
            "deviation_message": "You have veered off the route. Please turn around." if deviated else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {e}")
